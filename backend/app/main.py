import math

from datetime import timedelta, date
from fastapi import FastAPI, status, Response, Request, Depends
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from typing import Annotated

from app import database, models, config, utils, schemas, exceptions


# инициализация приложения с базой данных
app = FastAPI(lifespan=database.lifespan)


# общий обработчик исключения валидации длинной ссылки
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
    return Response(status_code=status.HTTP_400_BAD_REQUEST)


@app.exception_handler(HTTPException)
async def validation_exception_handler(
        request: Request, exc: HTTPException
    ):
    return JSONResponse(content=exc.detail, status_code=exc.status_code)


@app.post(
        "/register",
        response_model=schemas.Token,
        status_code=status.HTTP_201_CREATED
    )
async def create_user(data: schemas.UserRegisterRequest):
    user = await database.create_user(data)
    token_expires = timedelta(minutes=config.TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.email},
        expires_delta=token_expires
    )
    return schemas.Token(access_token=access_token, token_type="Bearer")


@app.post("/login", response_model=schemas.Token)
async def login_user(data: schemas.UserLoginRequest):
    user = await utils.authenticate_user(
            email=data.email,
            password=data.password
        )
    if not user:
        raise exceptions.HTTPUnauthorizedException()
    token_expires = timedelta(minutes=config.TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.email},
        expires_delta=token_expires
    )
    return schemas.Token(access_token=access_token, token_type="Bearer")


@app.post(
        "/expenses",
        response_model=schemas.ExpenseResponse, 
        status_code=status.HTTP_201_CREATED
    )
async def create_expense(
        data: schemas.ExpenseRequest,
        user: Annotated[models.User, Depends(utils.get_current_user)]
    ):
    expense = await database.create_expense(data, user.user_id)
    return expense


@app.get("/expenses", response_model=schemas.ExpenseListResponse)
async def get_expenses(
        user: Annotated[schemas.UserInDB, Depends(utils.get_current_user)],
        page: int=1,
        limit: int=10,
        category_id: int | None = None,
        period: schemas.Period | None = None,
        date_from: date | None = None,
        date_to: date | None = None
    ):

    date_from, date_to = utils.get_period(period, date_from, date_to)
    
    expenses = await database.get_expenses(
            user_id=user.user_id, 
            page=page, 
            limit=limit, 
            category_id=category_id, 
            date_from=date_from, 
            date_to=date_to
        )
    expenses_count = await database.get_expenses_count(
            user.user_id, category_id, date_from, date_to
        )

    expenses_response = schemas.ExpenseListResponse(
        data=expenses,
        limit=limit,
        page=page,
        total=math.ceil(expenses_count / limit)
    )
    return expenses_response


@app.get("/expenses/{expense_id}", response_model=schemas.ExpenseResponse)
async def get_expense(
        expense_id: int, 
        user: Annotated[schemas.UserInDB, Depends(utils.get_current_user)]
    ):
    expense = await database.get_expense(expense_id)
    if not expense:
        raise exceptions.HTTPExpenseNotExistsException()
    return expense


@app.put("/expenses/{expense_id}", response_model=schemas.ExpenseResponse)
async def update_expense(
        expense_id: int, 
        data: schemas.ExpenseRequest,
        user: Annotated[schemas.UserInDB, Depends(utils.get_current_user)]
    ):
    expense = await database.update_expense(expense_id, data)
    return expense

@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
        expense_id: int,
        user: Annotated[schemas.UserInDB, Depends(utils.get_current_user)]
    ):
    await database.delete_expense(expense_id)
