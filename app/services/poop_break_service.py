from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from app.repositories.poop_break_repository import PoopBreakRepository
from app.utils.time_utils import ensure_utc, now_utc_naive, resolve_period_range


@dataclass(slots=True)
class SessionStartResult:
    status: str
    session_id: int | None = None
    started_at: datetime | None = None
    existing_started_at: datetime | None = None


@dataclass(slots=True)
class SessionFinishResult:
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_seconds: int | None = None


@dataclass(slots=True)
class UserReport:
    total_count: int
    total_duration: int
    average_duration: int
    period_key: str
    period_label: str


@dataclass(slots=True)
class ServerReport:
    total_count: int
    total_duration: int
    average_duration: int
    period_key: str
    period_label: str


@dataclass(slots=True)
class AverageReport:
    user_average_duration: int
    user_total_count: int
    server_average_duration: int
    server_total_count: int
    period_key: str
    period_label: str


@dataclass(slots=True)
class RankingEntry:
    user_id: int
    user_name: str
    total_count: int
    total_duration: int
    average_duration: int
    combined_points: int


@dataclass(slots=True)
class RankingReport:
    period_key: str
    period_label: str
    by_count: list[RankingEntry]
    by_duration: list[RankingEntry]
    combined: list[RankingEntry]


class PoopBreakService:
    def __init__(self, repository: PoopBreakRepository, app_timezone: ZoneInfo) -> None:
        self.repository = repository
        self.app_timezone = app_timezone

    async def start_break(
        self,
        guild_id: int,
        user_id: int,
        user_name: str,
    ) -> SessionStartResult:
        open_session = await self.repository.get_open_session(guild_id, user_id)
        if open_session:
            return SessionStartResult(
                status="already_open",
                existing_started_at=ensure_utc(open_session["started_at"]),
            )

        started_at = now_utc_naive()
        session_id = await self.repository.create_session(guild_id, user_id, user_name, started_at)
        return SessionStartResult(
            status="started",
            session_id=session_id,
            started_at=ensure_utc(started_at),
        )

    async def finish_break(self, guild_id: int, user_id: int) -> SessionFinishResult:
        open_session = await self.repository.get_open_session(guild_id, user_id)
        if not open_session:
            return SessionFinishResult(status="not_found")

        started_at = ensure_utc(open_session["started_at"])
        finished_at = datetime.now(timezone.utc)
        duration_seconds = max(int((finished_at - started_at).total_seconds()), 1)

        await self.repository.complete_session(
            session_id=int(open_session["id"]),
            finished_at=finished_at.replace(tzinfo=None),
            duration_seconds=duration_seconds,
        )
        return SessionFinishResult(
            status="finished",
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration_seconds,
        )

    async def get_user_report(
        self,
        guild_id: int,
        user_id: int,
        period_key: str,
    ) -> UserReport:
        started_from, started_until, period_label = resolve_period_range(
            period_key,
            self.app_timezone,
        )
        row = await self.repository.fetch_user_summary(guild_id, user_id, started_from, started_until)
        return UserReport(
            total_count=int(row.get("total_count", 0) or 0),
            total_duration=int(row.get("total_duration", 0) or 0),
            average_duration=int(round(float(row.get("average_duration", 0) or 0))),
            period_key=period_key,
            period_label=period_label,
        )

    async def get_server_report(self, guild_id: int, period_key: str) -> ServerReport:
        started_from, started_until, period_label = resolve_period_range(
            period_key,
            self.app_timezone,
        )
        row = await self.repository.fetch_server_summary(guild_id, started_from, started_until)
        return ServerReport(
            total_count=int(row.get("total_count", 0) or 0),
            total_duration=int(row.get("total_duration", 0) or 0),
            average_duration=int(round(float(row.get("average_duration", 0) or 0))),
            period_key=period_key,
            period_label=period_label,
        )

    async def get_average_report(
        self,
        guild_id: int,
        user_id: int,
        period_key: str,
    ) -> AverageReport:
        user_report = await self.get_user_report(guild_id, user_id, period_key)
        server_report = await self.get_server_report(guild_id, period_key)
        return AverageReport(
            user_average_duration=user_report.average_duration,
            user_total_count=user_report.total_count,
            server_average_duration=server_report.average_duration,
            server_total_count=server_report.total_count,
            period_key=period_key,
            period_label=user_report.period_label,
        )

    async def get_ranking_report(
        self,
        guild_id: int,
        period_key: str,
        limit: int = 10,
    ) -> RankingReport:
        started_from, started_until, period_label = resolve_period_range(
            period_key,
            self.app_timezone,
        )
        rows = await self.repository.fetch_ranking_rows(guild_id, started_from, started_until)
        normalized_rows = [self._normalize_ranking_row(row) for row in rows]

        count_sorted = sorted(
            normalized_rows,
            key=lambda row: (-row["total_count"], -row["total_duration"], row["user_name"].lower()),
        )
        duration_sorted = sorted(
            normalized_rows,
            key=lambda row: (-row["total_duration"], -row["total_count"], row["user_name"].lower()),
        )

        count_positions = {row["user_id"]: index + 1 for index, row in enumerate(count_sorted)}
        duration_positions = {row["user_id"]: index + 1 for index, row in enumerate(duration_sorted)}

        combined_rows = []
        for row in normalized_rows:
            combined_points = count_positions[row["user_id"]] + duration_positions[row["user_id"]]
            combined_rows.append({**row, "combined_points": combined_points})

        combined_sorted = sorted(
            combined_rows,
            key=lambda row: (
                row["combined_points"],
                -row["total_count"],
                -row["total_duration"],
                row["user_name"].lower(),
            ),
        )

        return RankingReport(
            period_key=period_key,
            period_label=period_label,
            by_count=[self._to_ranking_entry(row) for row in count_sorted[:limit]],
            by_duration=[self._to_ranking_entry(row) for row in duration_sorted[:limit]],
            combined=[self._to_ranking_entry(row) for row in combined_sorted[:limit]],
        )

    @staticmethod
    def _normalize_ranking_row(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "user_id": int(row["user_id"]),
            "user_name": str(row["user_name"]),
            "total_count": int(row["total_count"] or 0),
            "total_duration": int(row["total_duration"] or 0),
            "average_duration": int(round(float(row["average_duration"] or 0))),
        }

    @staticmethod
    def _to_ranking_entry(row: dict[str, Any]) -> RankingEntry:
        return RankingEntry(
            user_id=int(row["user_id"]),
            user_name=str(row["user_name"]),
            total_count=int(row["total_count"]),
            total_duration=int(row["total_duration"]),
            average_duration=int(row["average_duration"]),
            combined_points=int(row.get("combined_points", 0)),
        )
