import jwt

from datetime import datetime, timedelta, timezone
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from typing import Annotated

from app import database, models, config, schemas, exceptions


password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_period(period: str | None, date_from: str | None, date_to: str | None):
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if date_from and date_to:
        return date_from, date_to
    elif period == schemas.Period.month:
        date_from = datetime(today.year, today.month, 1)
    elif period == schemas.Period.quarter:
        month = today.month - 2
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        date_from = datetime(year, month, 1)
    elif period == schemas.Period.week or date_from is None:
        date_from = today - timedelta(days=today.weekday())

    date_to = today + timedelta(days=1)
    return date_from, date_to


def verify_password(plain_pswd, hashed_pswd):
    return password_hash.verify(plain_pswd, hashed_pswd)


def get_password_hash(password):
    return password_hash.hash(password)


async def authenticate_user(username: str, password: str) -> models.User:
    user = await database.get_user(username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire_minutes = timedelta(minutes=config.TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + expire_minutes
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
            to_encode, 
            config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM
        )
    return encoded_jwt


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)]) -> models.User:
    try:
        payload = jwt.decode(
                token,
                config.JWT_SECRET_KEY,
                algorithms=[config.JWT_ALGORITHM]
            )
        username = payload.get("sub")
        if username is None:
            raise exceptions.HTTPUnauthorizedException()
        token_data = schemas.TokenData(username=username)
    except InvalidTokenError:
        raise exceptions.HTTPUnauthorizedException()
    user = await database.get_user(username=token_data.username)
    if user is None:
        raise exceptions.HTTPUnauthorizedException()
    return user
