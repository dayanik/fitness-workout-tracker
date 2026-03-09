from fastapi import status, HTTPException


class HTTPEmailNotUniqueException(HTTPException):
    def __init__(
            self, 
            detail: str="User with than email is already exist", 
            headers: dict={"WWW-Authenticate": "Bearer"}
            ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT, 
            detail=detail, 
            headers=headers)


class HTTPExpenseNotExistsException(HTTPException):
    def __init__(
            self, 
            detail: str="Instanse with that id not found", 
            headers: dict={"WWW-Authenticate": "Bearer"}
            ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=detail, 
            headers=headers)


class HTTPUnauthorizedException(HTTPException):
    def __init__(
            self, 
            detail: str="Could not validate credentials", 
            headers: dict={"WWW-Authenticate": "Bearer"}
            ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=detail, 
            headers=headers)
