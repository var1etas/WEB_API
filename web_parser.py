from fastapi import FastAPI, HTTPException, BackgroundTasks
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import List
import requests

app = FastAPI()

DATABASE_URL = "sqlite:///./products.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)

# Pydantic модели
class ProductBase(BaseModel):
    name: str
    price: str

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int

    class Config:
        orm_mode = True

HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
}
COOKIES = {'city_slug': 'ekb'}
URL = "https://api-ecomm.sdvor.com/occ/v2/sd/products/search?fields=algorithmsForAddingRelatedProducts%2CcategoryCode%2Cproducts(code%2Cbonus%2Cslug%2CdealType%2Cname%2Cunit%2Cunits(FULL)%2CunitPrices(FULL)%2CavailableInStores(FULL)%2Cbadges(DEFAULT)%2Cmultiunit%2Cprice(FULL)%2CcrossedPrice(FULL)%2CtransitPrice(FULL)%2CpersonalPrice(FULL)%2Cimages(DEFAULT)%2Cstock(FULL)%2CmarketingAttributes%2CisArchive%2Ccategories(FULL)%2CcategoryNamesForAnalytics)%2Cfacets%2Cbreadcrumbs%2Cpagination(DEFAULT)%2Csorts(DEFAULT)%2Cbanners(FULL)%2CfreeTextSearch%2CcurrentQuery%2CkeywordRedirectUrl&currentPage=0&pageSize=99999&facets=allCategories%3Anapolnye-pokrytija-5448&lang=ru&curr=RUB&deviceType=mobile&baseStore=ekb"

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
    session.query(Product).delete()  # Очистка таблицы
    for product in products:
        new_product = Product(name=product["name"], price=product["price"])
        session.add(new_product)
    session.commit()
    session.close()

def parse_and_save():
    products = fetch_products()
    save_products_to_db(products)

# Эндпоинты
@app.get("/products", response_model=List[ProductResponse])
def get_products():
    session = SessionLocal()
    products = session.query(Product).all()
    session.close()
    return products

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int):
    session = SessionLocal()
    product = session.query(Product).filter(Product.id == product_id).first()
    session.close()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate):
    session = SessionLocal()
    new_product = Product(name=product.name, price=product.price)
    session.add(new_product)
    session.commit()
    session.refresh(new_product)
    session.close()
    return new_product

@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductCreate):
    session = SessionLocal()
    db_product = session.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        session.close()
        raise HTTPException(status_code=404, detail="Product not found")
    db_product.name = product.name
    db_product.price = product.price
    session.commit()
    session.refresh(db_product)
    session.close()
    return db_product

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    session = SessionLocal()
    db_product = session.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        session.close()
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(db_product)
    session.commit()
    session.close()
    return {"message": "Product deleted"}

@app.get("/start-parsing")
def start_parsing(background_tasks: BackgroundTasks):
    background_tasks.add_task(parse_and_save)
    return {"message": "Parsing started"}
