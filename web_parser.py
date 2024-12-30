from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic import BaseModel
from typing import List
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import logging

app = FastAPI()

db_active_websockets = []

DATABASE_URL = "sqlite:///./products.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logging.basicConfig(level=logging.INFO)

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)

class ProductBase(BaseModel):
    name: str
    price: str


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True

HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 '
                  'Safari/537.36',
}
COOKIES = {'city_slug': 'ekb'}
URL = ("https://api-ecomm.sdvor.com/occ/v2/sd/products/search?fields=algorithmsForAddingRelatedProducts%2CcategoryCode"
       "%2Cproducts(code%2Cbonus%2Cslug%2CdealType%2Cname%2Cunit%2Cunits(FULL)%2CunitPrices(" 
       "FULL)%2CavailableInStores(FULL)%2Cbadges(DEFAULT)%2Cmultiunit%2Cprice(FULL)%2CcrossedPrice(" 
       "FULL)%2CtransitPrice(FULL)%2CpersonalPrice(FULL)%2Cimages(DEFAULT)%2Cstock(" 
       "FULL)%2CmarketingAttributes%2CisArchive%2Ccategories(" 
       "FULL)%2CcategoryNamesForAnalytics)%2Cfacets%2Cbreadcrumbs%2Cpagination(DEFAULT)%2Csorts(DEFAULT)%2Cbanners(" 
       "FULL)%2CfreeTextSearch%2CcurrentQuery%2CkeywordRedirectUrl&currentPage=0&pageSize=99999&facets=allCategories"
       "%3Anapolnye-pokrytija-5448&lang=ru&curr=RUB&deviceType=mobile&baseStore=ekb")


def fetch_products():
    response = requests.get(URL, headers=HEADERS, cookies=COOKIES)
    if response.status_code != 200:
        print(f"Ошибка: статус код {response.status_code}")
        return []

    data = response.json()
    products = []

    if "products" in data:
        for product in data["products"]:
            name = product.get("name", "Нет названия")
            price_data = product.get("price", {})
            price = price_data.get("formattedValue", "Нет цены")
            products.append({"name": name, "price": price})

    return products


def save_products_to_db(products):
    session = SessionLocal()
    session.query(Product).delete()  # Clear existing products
    for product in products:
        new_product = Product(name=product["name"], price=product["price"])
        session.add(new_product)
    session.commit()
    session.close()


def parse_and_save():
    products = fetch_products()
    save_products_to_db(products)
    notify_websockets("Parsing completed")


def start_periodic_parsing():
    scheduler = BackgroundScheduler()
    scheduler.add_job(parse_and_save, 'interval', hours=1)
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    scheduler.start()


def job_listener(event):
    if event.exception:
        logging.error(f"Job {event.job_id} failed")
    else:
        logging.info(f"Job {event.job_id} completed successfully")


@app.get("/products", response_model=List[ProductResponse])
async def get_products():
    session = SessionLocal()
    products = session.query(Product).all()
    session.close()
    await notify_websockets("Product list accessed")  # Await the call
    return products


@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int):
    session = SessionLocal()
    product = session.query(Product).filter(Product.id == product_id).first()
    session.close()
    if not product:
        await notify_websockets(f"Product {product_id} not found")
        raise HTTPException(status_code=404, detail="Product not found")
    await notify_websockets(f"Product '{product.name}' accessed")
    return product


@app.post("/products", response_model=ProductResponse)
async def create_product(product: ProductCreate):
    session = SessionLocal()
    new_product = Product(name=product.name, price=product.price)
    session.add(new_product)
    session.commit()
    session.refresh(new_product)
    session.close()
    await notify_websockets(f"Product '{new_product.name}' created")
    return new_product


@app.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, product: ProductCreate):
    session = SessionLocal()
    db_product = session.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        session.close()
        await notify_websockets(f"Product '{product_id}' not found for update")
        raise HTTPException(status_code=404, detail="Product not found")
    db_product.name = product.name
    db_product.price = product.price
    session.commit()
    session.refresh(db_product)
    session.close()
    await notify_websockets(f"Product '{product.name}' updated")
    return db_product


@app.delete("/products/{product_id}")
async def delete_product(product_id: int):
    session = SessionLocal()
    db_product = session.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        session.close()
        await notify_websockets(f"Product {product_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(db_product)
    session.commit()
    session.close()
    await notify_websockets(f"Product '{db_product.name}' deleted")
    return {"message": "Product deleted"}


@app.get("/start-parsing")
async def start_parsing(background_tasks: BackgroundTasks):
    background_tasks.add_task(parse_and_save)
    await notify_websockets("Parsing started")
    return {"message": "Parsing started"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    db_active_websockets.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        db_active_websockets.remove(websocket)


async def notify_websockets(message: str):
    for ws in db_active_websockets:
        try:
            await ws.send_text(message)
        except Exception as e:
            print(f"Failed to send message: {e}")
            db_active_websockets.remove(ws)


if __name__ == "__main__":
    import uvicorn

    start_periodic_parsing()
    uvicorn.run(app, host="0.0.0.0", port=8000)
