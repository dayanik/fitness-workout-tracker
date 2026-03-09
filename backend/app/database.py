from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from sqlalchemy import select, func, and_, insert
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import DATABASE_URL
from app import models, utils, schemas, exceptions


# echo=true -- sql logs
engine = create_async_engine(DATABASE_URL, echo=False)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


MUSCLE_GROUPS = [
    {"muscle_group_id": 0, "title": "верхняя", "description": "Верхняя группа мышцы: руки, шея, верхняя часть спины, грудь."},
    {"muscle_group_id": 1, "title": "средняя", "description": "Средняя группа мышц: живот и нижняя часть спины."},
    {"muscle_group_id": 2, "title": "нижняя", "description": "Нижняя группа мышц: ноги, ягодицы."}
]

MUSCLES = [
    {"title": "грудные", "description": "база", "muscle_group_id": 0},
    {"title": "плечи", "description": "база", "muscle_group_id": 0},
    {"title": "трапеции", "description": "второстепенная", "muscle_group_id": 0},
    {"title": "широчайшие", "description": "база", "muscle_group_id": 0},
    {"title": "ромбовидные", "description": "второстепенная", "muscle_group_id": 0},
    {"title": "бицепс", "description": "второстепенная", "muscle_group_id": 0},
    {"title": "трицепс", "description": "второстепенная", "muscle_group_id": 0},
    {"title": "предплечья", "description": "второстепенная", "muscle_group_id": 0},
    {"title": "прямые мышцы живота", "description": "второстепенная", "muscle_group_id": 1},
    {"title": "косые мышцы живота", "description": "второстепенная", "muscle_group_id": 1},
    {"title": "поперечная мышца живота", "description": "второстепенная", "muscle_group_id": 1},
    {"title": "разгибатели спины", "description": "база", "muscle_group_id": 1},
    {"title": "квадратная мышца поясницы", "description": "второстепенная", "muscle_group_id": 1},
    {"title": "ягодичные", "description": "база", "muscle_group_id": 2},
    {"title": "квадрицепсы", "description": "база", "muscle_group_id": 2},
    {"title": "бицепс бедра", "description": "база", "muscle_group_id": 2},
    {"title": "приводящие мышцы бедра", "description": "база", "muscle_group_id": 2},
    {"title": "икроножные", "description": "второстепенная", "muscle_group_id": 2},
    {"title": "камбаловидная мышца", "description": "второстепенная", "muscle_group_id": 2}
]

EXERCISES = [
    {"title": "Barbell Bench Press", "description": "Жим штанги лёжа для грудных, плеч и трицепсов."},
    {"title": "Dumbbell Fly", "description": "Разведения гантелей лёжа, изоляция грудных."},
    {"title": "Push-Up", "description": "Отжимания для грудных, трицепсов и передних дельт."},

    {"title": "Overhead Press", "description": "Жим штанги над головой для плеч и трапеций."},
    {"title": "Lateral Raise", "description": "Подъёмы гантелей в стороны для средних дельт."},
    {"title": "Front Raise", "description": "Подъёмы гантелей перед собой для передних дельт."},

    {"title": "Barbell Shrug", "description": "Шраги со штангой для трапеций."},
    {"title": "Dumbbell Shrug", "description": "Шраги с гантелями для трапеций."},

    {"title": "Pull-Up", "description": "Подтягивания для широчайших, бицепсов, ромбовидных и предплечий."},
    {"title": "Lat Pulldown", "description": "Тяга верхнего блока для широчайших и бицепсов."},

    {"title": "Bent Over Row", "description": "Тяга штанги в наклоне для середины спины и бицепсов."},
    {"title": "Seated Cable Row", "description": "Гребная тяга для ромбовидных, широчайших и бицепсов."},

    {"title": "Barbell Curl", "description": "Сгибание рук со штангой на бицепс."},
    {"title": "Dumbbell Curl", "description": "Сгибание рук с гантелями на бицепс."},

    {"title": "Triceps Pushdown", "description": "Разгибание рук на блоке для трицепса."},
    {"title": "Dips", "description": "Отжимания на брусьях для трицепсов и грудных."},

    {"title": "Wrist Curl", "description": "Сгибания кистей для предплечий."},
    {"title": "Reverse Wrist Curl", "description": "Разгибания кистей для предплечий."},

    {"title": "Crunch", "description": "Классические скручивания для прямых мышц живота."},
    {"title": "Leg Raise", "description": "Подъём ног в висе для нижнего пресса."},
    {"title": "Russian Twist", "description": "Повороты корпуса для косых мышц живота."},
    {"title": "Plank", "description": "Планка для поперечной мышцы живота."},
    {"title": "Back Extension", "description": "Гиперэкстензия для разгибателей спины."},
    {"title": "Side Plank", "description": "Боковая планка для стабилизаторов корпуса."},

    {"title": "Barbell Squat", "description": "Приседания со штангой для квадрицепсов, ягодиц, бицепса бедра и спины."},
    {"title": "Hip Thrust", "description": "Ягодичный мост для ягодиц и бицепса бедра."},
    {"title": "Leg Press", "description": "Жим ногами для квадрицепсов, ягодиц и икр."},
    {"title": "Romanian Deadlift", "description": "Румынская тяга для бицепса бедра и ягодиц."},
    {"title": "Adductor Machine", "description": "Сведение ног для приводящих мышц."},
    {"title": "Standing Calf Raise", "description": "Подъём на носки стоя для икроножных."},
    {"title": "Seated Calf Raise", "description": "Подъём на носки сидя для камбаловидной мышцы."}
]

MUSCLES_EXERCISES = [
    {"muscle_id":0,"exercise_id":0},
    {"muscle_id":1,"exercise_id":0},
    {"muscle_id":6,"exercise_id":0},
    {"muscle_id":0,"exercise_id":1},
    {"muscle_id":0,"exercise_id":2},
    {"muscle_id":1,"exercise_id":2},
    {"muscle_id":6,"exercise_id":2},

    {"muscle_id":1,"exercise_id":3},
    {"muscle_id":2,"exercise_id":3},
    {"muscle_id":1,"exercise_id":4},
    {"muscle_id":1,"exercise_id":5},

    {"muscle_id":2,"exercise_id":6},
    {"muscle_id":2,"exercise_id":7},

    {"muscle_id":3,"exercise_id":8},
    {"muscle_id":4,"exercise_id":8},
    {"muscle_id":5,"exercise_id":8},
    {"muscle_id":7,"exercise_id":8},
    {"muscle_id":3,"exercise_id":9},
    {"muscle_id":5,"exercise_id":9},

    {"muscle_id":4,"exercise_id":10},
    {"muscle_id":3,"exercise_id":10},
    {"muscle_id":5,"exercise_id":10},
    {"muscle_id":4,"exercise_id":11},
    {"muscle_id":3,"exercise_id":11},
    {"muscle_id":5,"exercise_id":11},

    {"muscle_id":5,"exercise_id":12},
    {"muscle_id":5,"exercise_id":13},

    {"muscle_id":6,"exercise_id":14},
    {"muscle_id":0,"exercise_id":14},
    {"muscle_id":1,"exercise_id":14},
    {"muscle_id":6,"exercise_id":15},
    {"muscle_id":0,"exercise_id":15},

    {"muscle_id":7,"exercise_id":16},
    {"muscle_id":7,"exercise_id":17},

    {"muscle_id":8,"exercise_id":18},
    {"muscle_id":8,"exercise_id":19},
    {"muscle_id":9,"exercise_id":20},
    {"muscle_id":10,"exercise_id":21},
    {"muscle_id":11,"exercise_id":22},
    {"muscle_id":12,"exercise_id":23},
    {"muscle_id":14,"exercise_id":24},
    {"muscle_id":15,"exercise_id":24},
    {"muscle_id":16,"exercise_id":24},
    {"muscle_id":15,"exercise_id":25},
    {"muscle_id":16,"exercise_id":25},
    {"muscle_id":14,"exercise_id":26},
    {"muscle_id":15,"exercise_id":26},
    {"muscle_id":17,"exercise_id":27},
    {"muscle_id":18,"exercise_id":28}
]


async def seed_tables(session: AsyncSession) -> None:
    result = await session.execute(
        select(func.count(models.MuscleGroup.muscle_group_id))
    )
    count = result.scalar()

    if count > 0:
        return

    session.add_all(
        models.MuscleGroup(**muscle_group) for muscle_group in MUSCLE_GROUPS
    )
    session.add_all(
        models.Muscle(**muscle) for muscle in MUSCLES
    )
    session.add_all(
        models.Exercise(**exercise) for exercise in EXERCISES
    )
    await session.commit()

    # добавление связей many-to-many
    stmt = insert(models.muscles_exercises_table)
    await session.execute(stmt, MUSCLES_EXERCISES)
    await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    async with async_session_maker() as session:
        await seed_tables(session)
    yield


# декоратор создания сессии
def connection(method):
	async def wrapper(*args, **kwargs):
		async with async_session_maker() as session:
			try:
				return await method(*args, session=session, **kwargs)
			except Exception as e:
				await session.rollback()
				raise e
			finally:
				await session.close()
	return wrapper


@connection
async def create_user(
        data: schemas.UserRegisterRequest, session: AsyncSession
    ) -> models.User | None:
    user = models.User(**data.model_dump())
    user.password = utils.get_password_hash(user.password)
    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
        return user
    except IntegrityError:
        await session.rollback()
        raise exceptions.HTTPEmailNotUniqueException()


@connection
async def get_user(username: str, session: AsyncSession) -> models.User:
    query = select(models.User).where(models.User.username == username)
    user_row = await session.execute(query)
    return user_row.scalar_one_or_none()


@connection
async def create_workout(
    data: schemas.WorkoutRequest,
    user_id: int,
    session: AsyncSession
) -> models.Workout:
    async with session.begin():
        workout = models.Workout(
            title = data.title,
            description = data.description,
            set_rest = data.set_rest,
            user_id = user_id,
            active = True
        )
        session.add(workout)

        workout_exercises = [
            models.WorkoutExercise(
                workout = workout,
                sets = ex.sets,
                weight= ex.weight,
                repetitions = ex.repetitions,
                rep_rest = ex.rep_rest,
                set_number = ex.set_number,
                exercise_id = ex.exercise_id
            ) for ex in data.exercises
        ]
        session.add_all(workout_exercises)

    return workout


@connection
async def get_workouts(
        user: models.User,
        session: AsyncSession
    ) -> list[models.Workout]:

    query = (
        select(models.Workout)
        .options(selectinload(models.Workout.workout_exercises)
        )
        .where(models.Workout.user == user)
    )
    result = await session.execute(query)
    workouts = result.scalars().all()
    return workouts


@connection
async def get_workout(
        workout_id: int, 
        session: AsyncSession
    ) -> models.Workout | None:
    query = (
        select(models.Workout)
        .options(selectinload(models.Workout.workout_exercises))
        .where(models.Workout.workout_id == workout_id)
        )
    result = await session.execute(query)
    return result.scalar_one_or_none()


@connection
async def update_workout(
        workout_id: int, 
        data: schemas.WorkoutRequest,
        session: AsyncSession
    ) -> models.Workout:
    
    query = (
        select(models.Workout)
        .options(selectinload(models.Workout.workout_exercises))
        .where(models.Workout.workout_id == workout_id)
    )
    result = await session.execute(query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise exceptions.HTTPExpenseNotExistsException()
    
    workout.title = data.title
    workout.description = data.description
    workout.active = data.active
    workout.set_rest = data.set_rest
    await session.commit()
    
    return workout


@connection
async def delete_workout(
        workout_id: int,
        session: AsyncSession
    ):
    query = (
        select(models.Workout)
        .where(models.Workout.workout_id == workout_id)
    )
    result = await session.execute(query)
    workout = result.scalar_one_or_none()
    if not workout:
        raise exceptions.HTTPExpenseNotExistsException()
    await session.delete(workout)
    await session.commit()


@connection
async def get_muscle_groups(
    session: AsyncSession
) -> list[models.MuscleGroup]:
    result = await session.execute(select(models.MuscleGroup))
    muscle_groups = result.scalars().all()
    return muscle_groups


@connection
async def get_muscle_group(
    muscle_group_id: int,
    session: AsyncSession
) -> models.MuscleGroup:
    query = (
        select(models.MuscleGroup)
        .where(models.MuscleGroup.muscle_group_id == muscle_group_id)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


@connection
async def get_muscle(
    muscle_id: int,
    muscle_group_id: int | None,
    session: AsyncSession
) -> models.Muscle:
    if muscle_group_id is None:
        query = (
            select(models.Muscle)
            .where(models.Muscle.muscle_id == muscle_id)
        )
    else:
        query = (
            select(models.Muscle)
            .where(
                and_(
                    models.Muscle.muscle_id == muscle_id,
                    models.Muscle.muscle_group_id == muscle_group_id
                )
            )
        )
    result = await session.execute(query)
    return result.scalar_one_or_none()


@connection
async def get_muscles(
    muscle_group_id: int,
    session: AsyncSession
) -> list[models.Muscle]:
    if muscle_group_id is None:
        query = select(models.Muscle)
    else:
        query = (
            select(models.Muscle)
            .where(models.Muscle.muscle_group_id == muscle_group_id)
        )
    result = await session.execute(query)
    muscles = result.scalars().all()
    return muscles


@connection
async def get_exercises(
    muscle_id: int,
    session: AsyncSession
) -> list[models.Exercise]:
    if muscle_id is None:
        query = (
            select(models.Exercise)
            .options(selectinload(models.Exercise.muscles))
        )
    else:
        query = (
            select(models.Exercise)
            .options(selectinload(models.Exercise.muscles))
            .join(models.Exercise.muscles)
            .where(models.Muscle.muscle_id == muscle_id)
        )

    result = await session.execute(query)
    exercises = result.scalars().all()
    return exercises


@connection
async def get_exercise(
    exercise_id: int,
    muscle_id: int | None,
    muscle_group_id: int | None,
    session: AsyncSession
) -> models.Exercise:
    query = (
        select(models.Exercise)
        .options(selectinload(models.Exercise.muscles))
        .where(models.Exercise.exercise_id == exercise_id)
    )
    result = await session.execute(query)
    exercise = result.scalar_one_or_none()
    for muscle in exercise.muscles:
        if muscle.muscle_id == muscle_id:
            if muscle.muscle_group_id == muscle_group_id:
                return exercise
    raise exceptions.HTTPExpenseNotExistsException()
