from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from sqlalchemy import select, func, and_, insert
from sqlalchemy.orm import joinedload
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
async def get_user(email: str, session: AsyncSession) -> models.User:
    query = select(models.User).where(models.User.email == email)
    user_row = await session.execute(query)
    return user_row.scalar_one_or_none()


@connection
async def create_expense(
        data: schemas.ExpenseRequest, 
        user_id: int,
        session: AsyncSession
    ) -> models.Expense:

    category_query = (
        select(models.Category)
        .where(models.Category.category_id == data.category_id)
    )
    category_result = await session.execute(category_query)
    category = category_result.scalar_one_or_none()
    if category is None:
        raise exceptions.HTTPException(400, "Category_id is not found")

    expense = models.Expense(
        title = data.title,
        description = data.description,
        amount = data.amount,
        category=category
    )
    expense.user_id = user_id 
    session.add(expense)
    await session.commit()
    await session.refresh(expense, ["category"])
    return expense


@connection
async def get_expenses(
        user_id: int,
        page: int,
        limit: int,
        category_id: int | None, 
        date_from: datetime, 
        date_to: datetime,
        session: AsyncSession
    ) -> list[models.Expense]:
    filters = [
        models.Expense.user_id == user_id,
        models.Expense.updated_at >= date_from,
        models.Expense.updated_at <= date_to
    ]
    if category_id:
        filters.append(models.Expense.category_id == category_id)
    query = (
        select(models.Expense)
        .options(joinedload(models.Expense.category))
        .where(*filters)
        .order_by(models.Expense.updated_at)
        .limit(limit)
        .offset((page - 1) * limit)
    )
    result = await session.execute(query)
    expenses = result.scalars().all()
    return expenses


@connection
async def get_expenses_count(
        user_id: int,
        category_id: int | None, 
        date_from: datetime, 
        date_to: datetime,
        session: AsyncSession
    ):
    filters = [
        models.Expense.user_id == user_id,
        models.Expense.updated_at >= date_from,
        models.Expense.updated_at <= date_to
    ]
    if category_id:
        filters.append(models.Expense.category_id == category_id)

    count_query = (
        select(func.count())
        .select_from(models.Expense)
        .where(*filters)
    )
    total_expenses = await session.scalar(count_query)
    return total_expenses


@connection
async def get_expense(
        expense_id: int, 
        session: AsyncSession
    ) -> models.Expense | None:
    query = (
        select(models.Expense)
        .options(joinedload(models.Expense.category))
        .where(models.Expense.expense_id == expense_id)
        )
    result = await session.execute(query)
    return result.scalar_one_or_none()


@connection
async def update_expense(
        expense_id: int, 
        data: schemas.ExpenseRequest,
        session: AsyncSession
    ) -> models.Expense:
    
    query = (
        select(models.Expense)
        .where(models.Expense.expense_id == expense_id)
    )
    result = await session.execute(query)
    expense = result.scalar_one_or_none()

    if not expense:
        raise exceptions.HTTPExpenseNotExistsException()
    
    expense.title = data.title
    expense.description = data.description
    expense.category_id = data.category_id
    expense.amount = data.amount
    await session.commit()
    
    return expense


@connection
async def delete_expense(
        expense_id: int,
        session: AsyncSession
    ):
    query = (
        select(models.Task)
        .where(models.Expense.expense_id == expense_id)
    )
    result = await session.execute(query)
    expense = result.scalar_one_or_none()
    if not expense:
        raise exceptions.HTTPExpenseNotExistsException()
    await session.delete(expense)
    await session.commit()
