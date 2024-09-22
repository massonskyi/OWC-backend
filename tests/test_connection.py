import asyncio
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy import select
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from database.connection import AsyncSessionLocal, async_engine, Base

class TestModel(Base):
    __tablename__ = 'test_table'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    is_active = Column(Boolean, default=True)

async def test_connection():
    async with AsyncSessionLocal() as session:
        # Создаем таблицы, если их нет, используя async_engine
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with session.begin():
            # Добавляем запись в тестовую таблицу
            new_record = TestModel(name="Test Record")
            session.add(new_record)
            await session.commit()  # Сохраняем изменения в базе данных

        # Выполняем запрос для проверки после добавления записи
        async with session.begin():
            result = await session.execute(select(TestModel).filter_by(name="Test Record"))
            record = result.scalars().first()

            if record:
                print(f"Запись найдена: ID = {record.id}, Name = {record.name}")
            else:
                print("Запись не найдена")

# Запуск асинхронной функции
asyncio.run(test_connection())
