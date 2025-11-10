# app/main.py
from typing import Optional

from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import engine, SessionLocal
from app.models import Base, CustomerDB, OrderDB
from app.schemas import (
    CustomerCreate, CustomerRead,
    OrderCreate, OrderRead,
    CustomerUpdate
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (dev/exam). Prefer Alembic in production.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)

def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()

def commit_or_rollback(db: Session, error_msg:str):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=error_msg)

# ---- Health ----
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/customers", response_model=CustomerCreate, status_code=201)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    db.customer = CustomerDB(**customer.model_dump())
    db.add(db.customer)
    commit_or_rollback(db, "Customer already exists")
    db.refresh(db.customer)
    return db.customer

@app.get("/api/customers", response_model=List[CustomerRead])
def list_customers(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    stmt = select(CustomerDB).order_by(CustomerDB.id).limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()

@app.get("/api/customers/{id}", response_model=CustomerRead, status_code=200)
def get_customer_by_id(customer_id: int, db: Session = Depends(get_db)):
    customer = db.get(CustomerDB, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer



@app.put("/api/customers/{id}", response_model=CustomerCreate)
def update_customer_put(customer_id: int, payload: CustomerCreate, db: Session = Depends(get_db)):
    customer = db.get(CustomerDB, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    data = payload.model_dump()
    customer.name = data["name"]
    customer.email = data["email"]
    customer.customer_since = data["customer_since"]

    commit_or_rollback(db, "User update failed")
    db.refresh(customer)
    return customer

@app.patch("/api/customers/{id}", response_model=CustomerRead)
def update_customer_patch(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)):
    customer = db.get(CustomerDB, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(customer, field, value)

    commit_or_rollback(db, "Customer update failed")
    db.refresh(customer)
    return customer

@app.delete("/api/customers/{id}", response_model=CustomerCreate, status_code=209)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.get(CustomerDB, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(customer)
    return customer

@app.post("/api/orders", response_model=OrderCreate, status_code=201)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    db.order = OrderDB(**order.model_dump())
    db.add(db.order)
    commit_or_rollback(db, "Order already exists")
    db.refresh(db.order)
    return db.order

@app.get("/api/orders", response_model=List[OrderRead])
def list_orders(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    stmt = select(OrderDB).order_by(OrderDB.id).limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()

@app.get("/api/orders/{id}", response_model=OrderRead, status_code=200)
def get_order_by_id(order_id: int, db: Session = Depends(get_db)):
    order = db.get(OrderDB, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

