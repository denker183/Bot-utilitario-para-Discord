"""Small persistent store for per-server bot settings."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any


class GuildSettingsStore:
    """Stores server rules in a JSON file without exposing them to the console."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = asyncio.Lock()

    async def get_rules(self, guild_id: int) -> str | None:
        async with self._lock:
            data = await asyncio.to_thread(self._read)
            guild_settings = data.get(str(guild_id), {})
            rules = guild_settings.get("rules")
            return rules if isinstance(rules, str) else None

    async def set_rules(self, guild_id: int, rules: str) -> None:
        async with self._lock:
            data = await asyncio.to_thread(self._read)
            guild_settings = data.setdefault(str(guild_id), {})
            guild_settings["rules"] = rules
            await asyncio.to_thread(self._write, data)

    def _read(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}

        try:
            with self._path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"Não foi possível ler as configurações em {self._path}."
            ) from error

        if not isinstance(data, dict):
            raise RuntimeError(
                f"O arquivo de configurações {self._path} precisa conter um objeto JSON."
            )
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self._path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        temporary_path.replace(self._path)
