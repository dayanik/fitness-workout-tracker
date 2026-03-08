from datetime import datetime
from pydantic import BaseModel, ConfigDict
from enum import Enum


class Period(str, Enum):
    week = "week"
    month = "month"
    quarter = "quarter"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserInDB(BaseModel):
    user_id: int
    username: str
    email: str
    password: str


class ExpenseRequest(BaseModel):
    title: str
    description: str
    amount: int
    category_id: int


class CategoryResponse(BaseModel):
    title: str

    model_config = ConfigDict(from_attributes=True)


class ExpenseResponse(BaseModel):
    expense_id: int
    title: str
    description: str
    amount: int
    category_id: int
    category: CategoryResponse
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExpenseListResponse(BaseModel):
    data: list[ExpenseResponse]
    page: int
    limit: int
    total: int


class WeekdayEnum(Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"
