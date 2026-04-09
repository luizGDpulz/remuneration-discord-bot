from __future__ import annotations

from datetime import datetime

import aiomysql

from app.db import Database


class PoopBreakRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def get_open_session(self, guild_id: int, user_id: int) -> dict | None:
        query = """
            SELECT id, guild_id, user_id, user_name, started_at, finished_at, duration_seconds, status
            FROM poop_break_sessions
            WHERE guild_id = %s AND user_id = %s AND status = 'aberta'
            ORDER BY started_at DESC
            LIMIT 1
        """
        async with self.database.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, (guild_id, user_id))
                return await cursor.fetchone()

    async def create_session(
        self,
        guild_id: int,
        user_id: int,
        user_name: str,
        started_at: datetime,
    ) -> int:
        query = """
            INSERT INTO poop_break_sessions (
                guild_id,
                user_id,
                user_name,
                started_at,
                status
            )
            VALUES (%s, %s, %s, %s, 'aberta')
        """
        async with self.database.acquire() as connection:
            async with connection.cursor() as cursor:
                try:
                    await cursor.execute(query, (guild_id, user_id, user_name, started_at))
                    session_id = cursor.lastrowid
                    await connection.commit()
                    return int(session_id)
                except Exception:
                    await connection.rollback()
                    raise

    async def complete_session(
        self,
        session_id: int,
        finished_at: datetime,
        duration_seconds: int,
    ) -> None:
        query = """
            UPDATE poop_break_sessions
            SET
                finished_at = %s,
                duration_seconds = %s,
                status = 'concluida'
            WHERE id = %s
        """
        async with self.database.acquire() as connection:
            async with connection.cursor() as cursor:
                try:
                    await cursor.execute(query, (finished_at, duration_seconds, session_id))
                    await connection.commit()
                except Exception:
                    await connection.rollback()
                    raise

    async def fetch_user_summary(
        self,
        guild_id: int,
        user_id: int,
        started_from: datetime,
        started_until: datetime,
    ) -> dict:
        query = """
            SELECT
                COUNT(*) AS total_count,
                COALESCE(SUM(duration_seconds), 0) AS total_duration,
                COALESCE(AVG(duration_seconds), 0) AS average_duration
            FROM poop_break_sessions
            WHERE guild_id = %s
              AND user_id = %s
              AND status = 'concluida'
              AND started_at >= %s
              AND started_at < %s
        """
        async with self.database.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, (guild_id, user_id, started_from, started_until))
                return await cursor.fetchone() or {}

    async def fetch_server_summary(
        self,
        guild_id: int,
        started_from: datetime,
        started_until: datetime,
    ) -> dict:
        query = """
            SELECT
                COUNT(*) AS total_count,
                COALESCE(SUM(duration_seconds), 0) AS total_duration,
                COALESCE(AVG(duration_seconds), 0) AS average_duration
            FROM poop_break_sessions
            WHERE guild_id = %s
              AND status = 'concluida'
              AND started_at >= %s
              AND started_at < %s
        """
        async with self.database.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, (guild_id, started_from, started_until))
                return await cursor.fetchone() or {}

    async def fetch_ranking_rows(
        self,
        guild_id: int,
        started_from: datetime,
        started_until: datetime,
    ) -> list[dict]:
        query = """
            SELECT
                user_id,
                MAX(user_name) AS user_name,
                COUNT(*) AS total_count,
                COALESCE(SUM(duration_seconds), 0) AS total_duration,
                COALESCE(AVG(duration_seconds), 0) AS average_duration
            FROM poop_break_sessions
            WHERE guild_id = %s
              AND status = 'concluida'
              AND started_at >= %s
              AND started_at < %s
            GROUP BY user_id
        """
        async with self.database.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, (guild_id, started_from, started_until))
                rows = await cursor.fetchall()
                return list(rows or [])
