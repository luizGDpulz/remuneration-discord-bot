from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

import discord
from discord import app_commands
from discord.ext import commands

from app.services.poop_break_service import (
    AverageReport,
    RankingEntry,
    RankingReport,
    ServerReport,
    UserReport,
)
from app.utils.time_utils import format_datetime, format_duration

if TYPE_CHECKING:
    from app.main import RemunerationBot

logger = logging.getLogger(__name__)

PeriodChoice = Literal["mes_atual", "7d", "30d"]
ReportViewChoice = Literal["pessoal", "servidor"]


class CagadaCog(
    commands.GroupCog,
    group_name="cagada",
    group_description="Controle humorístico de pausas remuneradas.",
):
    def __init__(self, bot: "RemunerationBot") -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(name="iniciar", description="Inicia uma nova cagada remunerada.")
    async def iniciar(self, interaction: discord.Interaction) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "Esse comando funciona apenas dentro de um servidor.",
                ephemeral=True,
            )
            return

        user = interaction.user
        result = await self.bot.poop_service.start_break(
            guild_id=interaction.guild_id,
            user_id=user.id,
            user_name=user.display_name,
        )

        if result.status == "already_open":
            started_at = format_datetime(result.existing_started_at, self.bot.settings.timezone)
            await interaction.response.send_message(
                f"Você já tem uma cagada aberta desde `{started_at}`. "
                "Finalize a atual antes de abrir outra.",
                ephemeral=True,
            )
            return

        started_at = format_datetime(result.started_at, self.bot.settings.timezone)
        embed = discord.Embed(
            title="Cagada iniciada",
            description="Registro aberto com sucesso. O RH segue sem saber de nada.",
            color=discord.Color.orange(),
        )
        embed.add_field(name="Usuário", value=user.mention, inline=True)
        embed.add_field(name="Início", value=started_at, inline=True)
        embed.add_field(name="Status", value="Aberta", inline=True)
        embed.set_footer(text="Use /cagada finalizar quando encerrar a missão.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="finalizar", description="Finaliza a sua cagada remunerada aberta.")
    async def finalizar(self, interaction: discord.Interaction) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "Esse comando funciona apenas dentro de um servidor.",
                ephemeral=True,
            )
            return

        result = await self.bot.poop_service.finish_break(
            guild_id=interaction.guild_id,
            user_id=interaction.user.id,
        )

        if result.status == "not_found":
            await interaction.response.send_message(
                "Não encontrei nenhuma cagada aberta para você neste servidor.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="Cagada finalizada",
            description="Missão concluída e registrada com sucesso.",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="Início",
            value=format_datetime(result.started_at, self.bot.settings.timezone),
            inline=True,
        )
        embed.add_field(
            name="Fim",
            value=format_datetime(result.finished_at, self.bot.settings.timezone),
            inline=True,
        )
        embed.add_field(
            name="Duração",
            value=format_duration(result.duration_seconds or 0),
            inline=True,
        )
        embed.set_footer(text="Cada segundo será cuidadosamente auditado em relatórios futuros.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="relatorio", description="Mostra o relatório pessoal ou o resumo do servidor.")
    @app_commands.describe(
        periodo="Período do relatório.",
        visao="Escolha entre relatório pessoal ou do servidor.",
        usuario="Opcional: consultar outro usuário no modo pessoal.",
    )
    async def relatorio(
        self,
        interaction: discord.Interaction,
        periodo: PeriodChoice = "mes_atual",
        visao: ReportViewChoice = "pessoal",
        usuario: discord.Member | None = None,
    ) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "Esse comando funciona apenas dentro de um servidor.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        if visao == "servidor":
            report = await self.bot.poop_service.get_server_report(interaction.guild_id, periodo)
            embed = self._build_server_report_embed(interaction.guild, report)
        else:
            target_user = usuario or interaction.user
            report = await self.bot.poop_service.get_user_report(
                interaction.guild_id,
                target_user.id,
                periodo,
            )
            embed = self._build_user_report_embed(target_user, report)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="media", description="Compara a sua média com a média geral do servidor.")
    @app_commands.describe(
        periodo="Período da média.",
        usuario="Opcional: consultar a média de outro usuário.",
    )
    async def media(
        self,
        interaction: discord.Interaction,
        periodo: PeriodChoice = "mes_atual",
        usuario: discord.Member | None = None,
    ) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "Esse comando funciona apenas dentro de um servidor.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        target_user = usuario or interaction.user
        report = await self.bot.poop_service.get_average_report(
            interaction.guild_id,
            target_user.id,
            periodo,
        )
        embed = self._build_average_embed(target_user, report)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ranking", description="Exibe os rankings do servidor.")
    @app_commands.describe(periodo="Período do ranking.")
    async def ranking(
        self,
        interaction: discord.Interaction,
        periodo: PeriodChoice = "mes_atual",
    ) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "Esse comando funciona apenas dentro de um servidor.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        report = await self.bot.poop_service.get_ranking_report(interaction.guild_id, periodo)
        embed = self._build_ranking_embed(interaction.guild, report)
        await interaction.followup.send(embed=embed)

    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        logger.exception("Slash command failed", exc_info=error)
        message = "Algo deu errado ao processar o comando. Confira os logs do container."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)

    def _build_user_report_embed(
        self,
        target_user: discord.Member | discord.User,
        report: UserReport,
    ) -> discord.Embed:
        embed = discord.Embed(
            title="Relatório individual",
            description=f"Resumo de {target_user.mention} no período `{report.period_label}`.",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Quantidade", value=str(report.total_count), inline=True)
        embed.add_field(name="Tempo total", value=format_duration(report.total_duration), inline=True)
        embed.add_field(name="Tempo médio", value=format_duration(report.average_duration), inline=True)
        embed.set_footer(text="Os números consideram apenas cagadas concluídas.")
        return embed

    def _build_server_report_embed(
        self,
        guild: discord.Guild | None,
        report: ServerReport,
    ) -> discord.Embed:
        guild_name = guild.name if guild else "Servidor"
        embed = discord.Embed(
            title="Relatório geral do servidor",
            description=f"Resumo de `{guild_name}` no período `{report.period_label}`.",
            color=discord.Color.gold(),
        )
        embed.add_field(name="Total de cagadas", value=str(report.total_count), inline=True)
        embed.add_field(name="Tempo total", value=format_duration(report.total_duration), inline=True)
        embed.add_field(name="Tempo médio", value=format_duration(report.average_duration), inline=True)
        embed.set_footer(text="Tudo separado por guild_id para não misturar servidores.")
        return embed

    def _build_average_embed(
        self,
        target_user: discord.Member | discord.User,
        report: AverageReport,
    ) -> discord.Embed:
        embed = discord.Embed(
            title="Média de tempo",
            description=f"Comparativo de {target_user.mention} no período `{report.period_label}`.",
            color=discord.Color.teal(),
        )
        embed.add_field(
            name="Média do usuário",
            value=(
                f"{format_duration(report.user_average_duration)}\n"
                f"em {report.user_total_count} cagada(s)"
            ),
            inline=True,
        )
        embed.add_field(
            name="Média do servidor",
            value=(
                f"{format_duration(report.server_average_duration)}\n"
                f"em {report.server_total_count} cagada(s)"
            ),
            inline=True,
        )

        if report.user_total_count == 0:
            verdict = "Ainda sem histórico suficiente para uma análise séria."
        elif report.user_average_duration > report.server_average_duration:
            verdict = "Acima da média do servidor. O trono está aquecido."
        elif report.user_average_duration < report.server_average_duration:
            verdict = "Abaixo da média do servidor. Eficiência digna de estudo."
        else:
            verdict = "Empatado com a média geral. Regularidade impressionante."

        embed.add_field(name="Leitura rápida", value=verdict, inline=False)
        return embed

    def _build_ranking_embed(
        self,
        guild: discord.Guild | None,
        report: RankingReport,
    ) -> discord.Embed:
        guild_name = guild.name if guild else "Servidor"
        embed = discord.Embed(
            title="Ranking do servidor",
            description=f"Placar de `{guild_name}` no período `{report.period_label}`.",
            color=discord.Color.purple(),
        )
        embed.add_field(
            name="Top por quantidade",
            value=self._format_ranking_section(report.by_count, mode="count"),
            inline=False,
        )
        embed.add_field(
            name="Top por tempo total",
            value=self._format_ranking_section(report.by_duration, mode="duration"),
            inline=False,
        )
        embed.add_field(
            name="Ranking combinado",
            value=self._format_ranking_section(report.combined, mode="combined"),
            inline=False,
        )
        embed.set_footer(text="Ranking combinado = soma das posições em quantidade e tempo.")
        return embed

    def _format_ranking_section(
        self,
        entries: list[RankingEntry],
        mode: Literal["count", "duration", "combined"],
    ) -> str:
        if not entries:
            return "Sem dados suficientes no período."

        lines: list[str] = []
        for index, entry in enumerate(entries, start=1):
            if mode == "count":
                metric = (
                    f"{entry.total_count} vez(es) | "
                    f"{format_duration(entry.total_duration)} total"
                )
            elif mode == "duration":
                metric = (
                    f"{format_duration(entry.total_duration)} total | "
                    f"{entry.total_count} vez(es)"
                )
            else:
                metric = (
                    f"{entry.total_count} vez(es) | "
                    f"{format_duration(entry.total_duration)} | "
                    f"{entry.combined_points} ponto(s)"
                )
            lines.append(f"`#{index}` {entry.user_name} - {metric}")
        return "\n".join(lines)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CagadaCog(bot))
