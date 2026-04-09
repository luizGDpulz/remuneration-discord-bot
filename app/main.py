from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from app.config import Settings
from app.db import Database
from app.logging_config import setup_logging
from app.repositories.poop_break_repository import PoopBreakRepository
from app.services.poop_break_service import PoopBreakService

logger = logging.getLogger(__name__)


class RemunerationBot(commands.Bot):
    def __init__(self, settings: Settings, database: Database) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.settings = settings
        self.database = database
        self.poop_service = PoopBreakService(
            repository=PoopBreakRepository(database),
            app_timezone=settings.timezone,
        )

    async def setup_hook(self) -> None:
        await self.database.connect()
        schema_path = Path(__file__).resolve().parent.parent / "schema.sql"
        await self.database.initialize_schema(schema_path)
        await self.load_extension("app.cogs.cagada")
        await self._sync_application_commands()

    async def _sync_application_commands(self) -> None:
        if self.settings.sync_guild_id:
            guild = discord.Object(id=self.settings.sync_guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info(
                "Synced %s slash command(s) to guild %s",
                len(synced),
                self.settings.sync_guild_id,
            )
            return

        synced = await self.tree.sync()
        logger.info("Synced %s global slash command(s)", len(synced))

    async def on_ready(self) -> None:
        if self.user is None:
            return
        logger.info("Bot connected as %s (id=%s)", self.user, self.user.id)

    async def close(self) -> None:
        try:
            await super().close()
        finally:
            await self.database.disconnect()

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        logger.exception("Unhandled slash command error", exc_info=error)
        message = "Ocorreu um erro inesperado ao processar o comando."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


async def main() -> None:
    load_dotenv()
    settings = Settings.from_env()
    setup_logging(settings.log_level)

    logger.info("Starting bot with timezone %s", settings.timezone_name)
    database = Database(settings)
    bot = RemunerationBot(settings, database)
    await bot.start(settings.discord_bot_token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested by keyboard interrupt.")
