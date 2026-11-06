"""Slash-command bot for common Discord server tasks."""

from __future__ import annotations

import logging
import math
import os
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlsplit

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

REAIS_PER_ROBUX = Decimal("45") / Decimal("1000")


def format_number_pt_br(value: Decimal, decimal_places: int) -> str:
    """Format a number using Brazilian thousands and decimal separators."""
    quantum = Decimal("1").scaleb(-decimal_places)
    rounded = value.quantize(quantum, rounding=ROUND_HALF_UP)
    formatted = f"{rounded:,.{decimal_places}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


async def send_ephemeral(
    interaction: discord.Interaction, message: str
) -> None:
    """Respond privately whether or not the interaction was already acknowledged."""
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


async def is_server_owner(interaction: discord.Interaction) -> bool:
    """Allow the command only to the owner of its Discord server."""
    return (
        interaction.guild is not None
        and interaction.user.id == interaction.guild.owner_id
    )


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
            "`/ping` — verifica se o bot está respondendo.\n"
            "`/calcular` — converte pela taxa de 1.000 Robux = R$ 45,00."
        ),
        inline=False,
    )
    embed.add_field(
        name="Comandos restritos",
        value=(
            "`/configurar_regras` — define as regras mostradas em `/regras`.\n"
            "`/embed` — publica uma embed com imagem opcional; somente o dono do servidor."
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


@bot.tree.command(
    name="calcular",
    description="Converte Robux e Reais pela taxa de 1.000 = R$ 45,00.",
)
@app_commands.describe(
    tipo="Escolha se deseja calcular a partir de Robux ou de Reais",
    quantidade="A quantidade que você quer converter",
)
@app_commands.choices(
    tipo=[
        app_commands.Choice(
            name="Robux para Reais (ex.: 1.000 → R$ 45,00)",
            value="robux",
        ),
        app_commands.Choice(
            name="Reais para Robux (ex.: R$ 45,00 → 1.000)",
            value="reais",
        ),
    ]
)
@app_commands.guild_only()
async def calcular(
    interaction: discord.Interaction,
    tipo: app_commands.Choice[str],
    quantidade: float,
) -> None:
    if not math.isfinite(quantidade) or quantidade <= 0:
        await send_ephemeral(
            interaction, "Informe uma quantidade válida maior que zero."
        )
        return

    amount = Decimal(str(quantidade))
    if tipo.value == "robux":
        if amount != amount.to_integral_value():
            await send_ephemeral(
                interaction, "Informe a quantidade de Robux como um número inteiro."
            )
            return

        reais = (amount * REAIS_PER_ROBUX).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        description = (
            f"**{format_number_pt_br(amount, 0)} Robux** equivalem a "
            f"**R$ {format_number_pt_br(reais, 2)}**"
        )
        footer = "Taxa usada: 1.000 Robux = R$ 45,00"
        color = discord.Color.green()
    else:
        reais = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        robux = (reais / REAIS_PER_ROBUX).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        description = (
            f"**R$ {format_number_pt_br(reais, 2)}** equivalem a "
            f"**{format_number_pt_br(robux, 0)} Robux**"
        )
        footer = "Taxa usada: R$ 45,00 = 1.000 Robux"
        color = discord.Color.blue()

    embed = discord.Embed(
        title="🧮 Calculadora de conversão",
        description=description,
        color=color,
    )
    embed.set_footer(text=footer)
    await interaction.response.send_message(embed=embed, ephemeral=False)


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


@bot.tree.command(
    name="embed",
    description="Envia uma mensagem embed personalizada com foto no canal.",
)
@app_commands.choices(cor=COLORS)
@app_commands.describe(
    titulo="Título que aparecerá na embed",
    descricao="Mensagem ou conteúdo da embed",
    cor="Cor da borda da embed",
    imagem="Link direto da imagem (opcional)",
)
@app_commands.guild_only()
@app_commands.check(is_server_owner)
async def embed_command(
    interaction: discord.Interaction,
    titulo: app_commands.Range[str, 1, 256],
    descricao: app_commands.Range[str, 1, 4000],
    cor: app_commands.Choice[str],
    imagem: str | None = None,
) -> None:
    if imagem:
        image_url = urlsplit(imagem)
        if image_url.scheme not in {"http", "https"} or not image_url.netloc:
            await send_ephemeral(
                interaction,
                "O link da imagem precisa começar com `http://` ou `https://`.",
            )
            return

    message_embed = discord.Embed(
        title=titulo,
        description=descricao,
        color=discord.Color(int(cor.value, 16)),
    )
    if imagem:
        message_embed.set_image(url=imagem)

    await interaction.response.send_message(embed=message_embed, ephemeral=False)


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

    if isinstance(error, app_commands.CheckFailure):
        if interaction.command and interaction.command.name == "embed":
            await send_ephemeral(
                interaction,
                "Somente o dono do servidor pode usar o comando `/embed`.",
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
