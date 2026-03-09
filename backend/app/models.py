from datetime import datetime
from sqlalchemy import (
    Enum as sqlEnum, 
    func, 
    ForeignKey, 
    Table, Column, 
    CheckConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from app import schemas


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now())


class MuscleGroup(Base):
    __tablename__ = "muscle_groups"

    muscle_group_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    title: Mapped[str]
    description: Mapped[str]
    muscles: Mapped[list["Muscle"]] = relationship(
        back_populates="muscle_group"
    )


muscles_exercises_table = Table(
    "muscles_exercises_table",
    Base.metadata,
    Column(
        "muscle_id", 
        ForeignKey("muscles.muscle_id"), 
        primary_key=True
    ),
    Column(
        "exercise_id", 
        ForeignKey("exercises.exercise_id"), 
        primary_key=True
    )
)


class Muscle(Base):
    __tablename__ = "muscles"

    muscle_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    title: Mapped[str]
    description: Mapped[str]
    muscle_group_id: Mapped[int] = mapped_column(
        ForeignKey("muscle_groups.muscle_group_id")
    )
    muscle_group: Mapped["MuscleGroup"] = relationship(
        "MuscleGroup", back_populates="muscles"
    )
    exercises: Mapped[list["Exercise"]] = relationship(
        secondary=muscles_exercises_table,
        back_populates="muscles"
    )


class Exercise(Base):
    __tablename__ = "exercises"

    exercise_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    title: Mapped[str]
    description: Mapped[str]
    muscles: Mapped[list["Muscle"]] = relationship(
        secondary=muscles_exercises_table,
        back_populates="exercises"
    )
    workout_exercises: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="exercise"
    )
    workout_exercise_history: Mapped[list["WorkoutExerciseHistory"]] = relationship(
        back_populates="exercise"
    )


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]
    workouts: Mapped[list["Workout"]] = relationship(back_populates="user")
    schedules: Mapped[list["Schedule"]] = relationship(back_populates="user")


class Workout(Base):
    __tablename__ = "workouts"

    workout_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    title: Mapped[str]
    description: Mapped[str]
    active: Mapped[bool]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    user: Mapped["User"] = relationship(back_populates="workouts")
    set_rest: Mapped[int]
    workout_exercises: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="workout",
        cascade="all, delete-orphan"
    )


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    workout_exercise_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    sets: Mapped[int]
    weight: Mapped[int]
    repetitions: Mapped[int]
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.exercise_id")
    )
    exercise: Mapped["Exercise"] = relationship(
        "Exercise", back_populates="workout_exercises"
    )
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.workout_id"))
    workout: Mapped["Workout"] = relationship(
        "Workout", back_populates="workout_exercises"
    )
    rep_rest: Mapped[int]
    set_number: Mapped[int]


class WorkoutHistory(Base):
    
    __tablename__ = "workout_histories"

    workout_history_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    workout_id: Mapped[int] = mapped_column(
        ForeignKey("workouts.workout_id")
    )
    workout: Mapped["Workout"] = relationship()
    workout_exercise_histories: Mapped[
        list["WorkoutExerciseHistory"]
    ] = relationship(
        back_populates="workout_history",
    )


class WorkoutExerciseHistory(Base):
    __tablename__ = "workout_exercise_histories"

    workout_exercise_history_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    sets: Mapped[int]
    weight: Mapped[int]
    repetitions: Mapped[int]
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.exercise_id")
    )
    exercise: Mapped["Exercise"] = relationship(
        "Exercise", back_populates="workout_exercise_history"
    )
    workout_history_id: Mapped[int] = mapped_column(
        ForeignKey("workout_histories.workout_history_id")
    )
    workout_history: Mapped["WorkoutHistory"] = relationship(
        "WorkoutHistory", back_populates="workout_exercise_histories"
    )
    rep_rest: Mapped[int]


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = (
        CheckConstraint("hour BETWEEN 0 AND 23"),
        CheckConstraint("minutes BETWEEN 0 AND 59"),
    )

    schedule_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id")
    )
    user: Mapped["User"] = relationship(back_populates="schedules")
    weekday: Mapped[str] = mapped_column(
        sqlEnum(schemas.WeekdayEnum),unique=True
    )
    workout_id: Mapped[int] = mapped_column(
        ForeignKey("workouts.workout_id")
    )
    workout: Mapped["Workout"] = relationship()
    hour: Mapped[int]
    minutes: Mapped[int]
