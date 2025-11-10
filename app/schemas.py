from typing import Annotated, Optional
from pydantic import BaseModel, EmailStr, Field, StringConstraints, ConfigDict
from annotated_types import Ge, Le

NameStr = Annotated[str, StringConstraints(min_length=1, max_length=100)]
CustomerSinceInt = Annotated[int, Ge(2000), Le(2100)]
OrderNumberInt = Annotated[int, Ge(3), Le(20)]
TotalCentsInt = Annotated[int, Ge(1), Le(1000000)]

class CustomerCreate(BaseModel):
    name: NameStr
    email: EmailStr
    customer_since: CustomerSinceInt

class CustomerRead(CustomerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

class OrderCreate(BaseModel):
    order_number: OrderNumberInt
    total_cents = TotalCentsInt
    customer_id = int


