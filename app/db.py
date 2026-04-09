from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import aiomysql

from app.config import Settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.pool: aiomysql.Pool | None = None

    async def connect(self) -> None:
        if self.pool is not None:
            return

        self.pool = await aiomysql.create_pool(
            host=self.settings.db_host,
            port=self.settings.db_port,
            user=self.settings.db_user,
            password=self.settings.db_password,
            db=self.settings.db_name,
            minsize=self.settings.db_pool_min_size,
            maxsize=self.settings.db_pool_max_size,
            charset="utf8mb4",
            autocommit=False,
        )
        logger.info("Connected to database %s", self.settings.masked_database_url)

    async def disconnect(self) -> None:
        if self.pool is None:
            return

        self.pool.close()
        await self.pool.wait_closed()
        self.pool = None
        logger.info("Database connection pool closed.")

    @asynccontextmanager
    async def acquire(self):
        if self.pool is None:
            raise RuntimeError("Database pool is not initialized.")

        async with self.pool.acquire() as connection:
            yield connection

    async def initialize_schema(self, schema_path: Path) -> None:
        sql = schema_path.read_text(encoding="utf-8")
        statements = [statement.strip() for statement in sql.split(";") if statement.strip()]

        async with self.acquire() as connection:
            async with connection.cursor() as cursor:
                for statement in statements:
                    await cursor.execute(statement)
            await connection.commit()

        logger.info("Database schema checked using %s", schema_path)
