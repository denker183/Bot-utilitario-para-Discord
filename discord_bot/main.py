"""Slash-command bot for common Discord server tasks."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import discord
from discord import app_commands

from discord_bot.settings_store import GuildSettingsStore


LOGGER = logging.getLogger("discord_server_bot")
SETTINGS = GuildSettingsStore(Path(__file__).parent / "data" / "guild_settings.json")

COLORS = [
    app_commands.Choice(name="Azul", value="0x3498db"),
    app_commands.Choice(name="Vermelho", value="0xe74c3c"),
    app_commands.Choice(name="Verde", value="0x2ecc71"),
    app_commands.Choice(name="Amarelo", value="0xf1c40f"),
    app_commands.Choice(name="Roxo", value="0x9b59b6"),
    app_commands.Choice(name="Preto", value="0x000000"),
    app_commands.Choice(name="Branco", value="0xffffff"),
]


async def send_ephemeral(
    interaction: discord.Interaction, message: str
) -> None:
    """Respond privately whether or not the interaction was already acknowledged."""
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


class ServerBot(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        guild_id = os.getenv("DISCORD_GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            LOGGER.info("Sincronizados %s comando(s) no servidor de teste.", len(synced))
            return

        synced = await self.tree.sync()
        LOGGER.info("Sincronizados %s comando(s) globais.", len(synced))

    async def on_ready(self) -> None:
        LOGGER.info("Bot conectado como %s.", self.user)


bot = ServerBot()


@bot.tree.command(name="ajuda", description="Mostra os comandos disponíveis do bot.")
@app_commands.guild_only()
async def ajuda(interaction: discord.Interaction) -> None:
    embed = discord.Embed(
        title="Comandos do servidor",
        description="Use os comandos abaixo para consultar e configurar este servidor.",
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Disponíveis para todos",
        value=(
            "`/servidor` — mostra informações do servidor.\n"
            "`/regras` — exibe as regras configuradas.\n"
            "`/ping` — verifica se o bot está respondendo."
        ),
        inline=False,
    )
    embed.add_field(
        name="Somente administradores",
        value=(
            "`/configurar_regras` — define as regras mostradas em `/regras`.\n"
            "`/embed` — publica uma embed personalizada no canal."
        ),
        inline=False,
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="ping", description="Verifica se o bot está respondendo.")
@app_commands.guild_only()
async def ping(interaction: discord.Interaction) -> None:
    latency_ms = round(bot.latency * 1000)
    await interaction.response.send_message(
        f"Pong! Latência: **{latency_ms} ms**.", ephemeral=True
    )


@bot.tree.command(name="servidor", description="Mostra informações deste servidor.")
@app_commands.guild_only()
async def servidor(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    if guild is None:
        await send_ephemeral(interaction, "Este comando só pode ser usado em um servidor.")
        return

    embed = discord.Embed(
        title=guild.name,
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(name="Membros", value=str(guild.member_count or "—"))
    embed.add_field(name="Canais de texto", value=str(len(guild.text_channels)))
    embed.add_field(name="Canais de voz", value=str(len(guild.voice_channels)))
    embed.add_field(
        name="Criado em",
        value=discord.utils.format_dt(guild.created_at, style="D"),
        inline=False,
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="configurar_regras", description="Define as regras deste servidor.")
@app_commands.describe(texto="Texto exibido quando alguém usa /regras")
@app_commands.guild_only()
@app_commands.checks.has_permissions(administrator=True)
async def configurar_regras(
    interaction: discord.Interaction,
    texto: app_commands.Range[str, 1, 2000],
) -> None:
    guild = interaction.guild
    if guild is None:
        await send_ephemeral(interaction, "Este comando só pode ser usado em um servidor.")
        return

    await SETTINGS.set_rules(guild.id, texto)
    await send_ephemeral(interaction, "Regras do servidor salvas.")


@bot.tree.command(name="regras", description="Exibe as regras configuradas deste servidor.")
@app_commands.guild_only()
async def regras(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    if guild is None:
        await send_ephemeral(interaction, "Este comando só pode ser usado em um servidor.")
        return

    rules = await SETTINGS.get_rules(guild.id)
    if not rules:
        await send_ephemeral(
            interaction,
            "As regras ainda não foram configuradas. Um administrador pode usar "
            "`/configurar_regras`.",
        )
        return

    embed = discord.Embed(
        title=f"Regras de {guild.name}",
        description=rules,
        color=discord.Color.gold(),
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="embed", description="Envia uma mensagem embed personalizada.")
@app_commands.describe(
    titulo="Título que aparecerá na embed",
    descricao="Mensagem ou conteúdo da embed",
    cor="Cor da borda da embed",
)
@app_commands.choices(cor=COLORS)
@app_commands.guild_only()
@app_commands.checks.has_permissions(administrator=True)
async def embed_command(
    interaction: discord.Interaction,
    titulo: app_commands.Range[str, 1, 256],
    descricao: app_commands.Range[str, 1, 4000],
    cor: app_commands.Choice[str],
) -> None:
    color_value = int(cor.value, 16)
    message_embed = discord.Embed(
        title=titulo,
        description=descricao,
        color=discord.Color(color_value),
    )

    channel = interaction.channel
    if channel is None or not hasattr(channel, "send"):
        await send_ephemeral(
            interaction, "Não consegui enviar a embed neste canal."
        )
        return

    await channel.send(embed=message_embed)
    await send_ephemeral(interaction, "Embed enviada com sucesso.")


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
) -> None:
    if isinstance(error, app_commands.MissingPermissions):
        await send_ephemeral(
            interaction,
            "Você precisa ser administrador para usar este comando.",
        )
        return

    if isinstance(error, app_commands.NoPrivateMessage):
        await send_ephemeral(
            interaction, "Este comando só pode ser usado em um servidor."
        )
        return

    LOGGER.error(
        "Falha no comando /%s: %s",
        interaction.command.name if interaction.command else "desconhecido",
        error,
        exc_info=(type(error), error, error.__traceback__),
    )
    await send_ephemeral(
        interaction, "Ocorreu um erro ao executar o comando. Tente novamente."
    )


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise SystemExit(
            "DISCORD_BOT_TOKEN não está configurado. Adicione-o aos Secrets do projeto."
        )

    guild_id = os.getenv("DISCORD_GUILD_ID")
    if guild_id:
        try:
            int(guild_id)
        except ValueError as error:
            raise SystemExit("DISCORD_GUILD_ID precisa ser um número inteiro.") from error

    bot.run(token, log_handler=None)


if __name__ == "__main__":
    main()
