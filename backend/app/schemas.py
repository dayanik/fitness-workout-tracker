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
    username: str | None = None


class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    first_name: str
    last_name: str


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserInDB(BaseModel):
    user_id: int
    username: str
    email: str
    password: str


class WorkoutExerciseRequest(BaseModel):
    sets: int
    weight: int
    repetitions: int
    exercise_id: int
    rep_rest: int
    set_number: int


class WorkoutRequest(BaseModel):
    title: str
    description: str
    active: bool
    set_rest: int
    exercises: list[WorkoutExerciseRequest]


class WorkoutExerciseResponse(BaseModel):
    workout_exercise_id: int
    sets: int
    weight: int
    repetitions: int
    exercise_id: int
    workout_id: int
    rep_rest: int
    set_number: int

    model_config = ConfigDict(from_attributes=True)


class WorkoutResponse(BaseModel):
    workout_id: int
    title: str
    description: str
    active: bool
    set_rest: int
    workout_exercises: list[WorkoutExerciseResponse]

    model_config = ConfigDict(from_attributes=True)


class WorkoutListResponse(BaseModel):
    data: list[WorkoutResponse]


class MuscleGroupResponse(BaseModel):
    muscle_group_id: int
    title: str
    description: str

    model_config = ConfigDict(from_attributes=True)


class MuscleGroups(BaseModel):
    data: list[MuscleGroupResponse]


class MuscleResponse(BaseModel):
    muscle_id: int
    title: str
    description: str
    muscle_group_id: int

    model_config = ConfigDict(from_attributes=True)


class Muscles(BaseModel):
    data: list[MuscleResponse]


class ExerciseResponse(BaseModel):
    exercise_id: int
    title: str
    description: str
    muscles: list[MuscleResponse]

    model_config = ConfigDict(from_attributes=True)


class Exercises(BaseModel):
    data: list[ExerciseResponse]


class WeekdayEnum(Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"
