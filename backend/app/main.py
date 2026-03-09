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
        "/signup",
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
            username=data.username,
            password=data.password
        )
    if not user:
        raise exceptions.HTTPUnauthorizedException()
    token_expires = timedelta(minutes=config.TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.username},
        expires_delta=token_expires
    )
    return schemas.Token(access_token=access_token, token_type="Bearer")


@app.post(
    "/workouts",
    response_model=schemas.WorkoutResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_workout(
    data: schemas.WorkoutRequest,
    user: Annotated[models.User, Depends(utils.get_current_user)]
):
    workout = await database.create_workout(data, user.user_id)
    return workout


@app.get("/workouts", response_model=schemas.WorkoutListResponse)
async def get_workouts(
    user: Annotated[schemas.UserInDB, Depends(utils.get_current_user)],
):
    workouts = await database.get_workouts(user=user)
    workouts_response = schemas.WorkoutListResponse(data=workouts)
    return workouts_response


@app.get("/workouts/{workout_id}", response_model=schemas.WorkoutResponse)
async def get_workout(
    workout_id: int,
    user: Annotated[schemas.UserInDB, Depends(utils.get_current_user)]
):
    workout = await database.get_workout(workout_id=workout_id)
    if not workout:
        raise exceptions.HTTPExpenseNotExistsException()
    return workout


@app.put("/workouts/{workout_id}", response_model=schemas.WorkoutResponse)
async def update_workout(
        workout_id: int, 
        data: schemas.WorkoutRequest,
        user: Annotated[schemas.UserInDB, Depends(utils.get_current_user)]
    ):
    workout = await database.update_workout(workout_id, data)
    return workout


@app.delete("/workouts/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout(
        workout_id: int,
        user: Annotated[schemas.UserInDB, Depends(utils.get_current_user)]
    ):
    await database.delete_workout(workout_id)


@app.get("/muscle_groups", response_model=schemas.MuscleGroups)
async def get_muscle_groups(
    user: Annotated[schemas.UserInDB, Depends(utils.get_current_user)],
):
    muscle_groups = await database.get_muscle_groups()
    muscle_groups_response = schemas.MuscleGroups(data=muscle_groups)
    return muscle_groups_response


@app.get(
    "/muscle_groups/{muscle_group_id}",
    response_model=schemas.MuscleGroupResponse
)
async def get_muscle_group(
    muscle_group_id: int,
    user: Annotated[schemas.UserInDB, Depends(utils.get_current_user)]
):
    muscle_group = await database.get_muscle_group(
        muscle_group_id=muscle_group_id
    )
    if not muscle_group:
        raise exceptions.HTTPExpenseNotExistsException()
    return muscle_group


@app.get(
    "/muscle_groups/{muscle_group_id}/muscles",
    response_model=schemas.Muscles
)
@app.get("/muscles", response_model=schemas.Muscles)
async def get_muscles(
    user: Annotated[schemas.UserInDB, Depends(utils.get_current_user)],
    muscle_group_id: int | None = None
):
    muscles = await database.get_muscles(muscle_group_id=muscle_group_id)
    muscles_response = schemas.Muscles(data=muscles)
    return muscles_response


@app.get(
    "/muscle_groups/{muscle_group_id}/muscles/{muscle_id}",
    response_model=schemas.MuscleResponse
)
@app.get("/muscles/{muscle_id}", response_model=schemas.MuscleResponse)
async def get_muscle(
    muscle_id: int,
    user: Annotated[schemas.UserInDB, Depends(utils.get_current_user)],
    muscle_group_id: int | None = None
):
    muscle = await database.get_muscle(
        muscle_id=muscle_id,
        muscle_group_id=muscle_group_id
    )
    if not muscle:
        raise exceptions.HTTPExpenseNotExistsException()
    return muscle


@app.get(
    "/muscle_groups/{muscle_group_id}/muscles/{muscle_id}/exercises",
    response_model=schemas.Exercises
)
@app.get("/exercises", response_model=schemas.Exercises)
async def get_exercises(
    user: Annotated[schemas.UserInDB, Depends(utils.get_current_user)],
    muscle_id: int | None = None,
    muscle_group_id: int | None = None
):
    exercises = await database.get_exercises(muscle_id=muscle_id)
    exercises_response = schemas.Exercises(data=exercises)
    return exercises_response


@app.get(
    "/muscle_groups/{muscle_group_id}/muscles/{muscle_id}/exercises/{exercise_id}",
    response_model=schemas.ExerciseResponse
)
@app.get("/exercises/{exercise_id}", response_model=schemas.ExerciseResponse)
async def get_exercise(
    exercise_id: int,
    user: Annotated[schemas.UserInDB, Depends(utils.get_current_user)],
    muscle_id: int | None = None,
    muscle_group_id: int | None = None
):
    exercise = await database.get_exercise(
        exercise_id=exercise_id,
        muscle_id=muscle_id,
        muscle_group_id=muscle_group_id
    )
    if not exercise:
        raise exceptions.HTTPExpenseNotExistsException()
    return exercise
