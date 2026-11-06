# Bot utilitário para Discord

Bot de comandos slash para tarefas comuns do servidor. O token fica apenas nos
Secrets do projeto; ele não deve ser colocado nos arquivos do bot.

## Comandos

- `/ajuda` — mostra a lista de comandos.
- `/ping` — verifica se o bot está respondendo.
- `/servidor` — mostra informações básicas do servidor.
- `/regras` — publica as regras configuradas.
- `/configurar_regras` — salva as regras; somente administradores.
- `/embed` — publica uma embed com título, descrição e cor; somente administradores.

## Configuração do bot no Discord

1. No Discord Developer Portal, abra a aplicação do bot e convide-a para o
   servidor com os escopos `bot` e `applications.commands`.
2. Conceda as permissões `View Channels`, `Send Messages` e `Embed Links`.
3. Em **Replit Secrets**, salve o token como `DISCORD_BOT_TOKEN`.
4. Inicie o workflow **Discord Bot**.
5. Use `/configurar_regras` como administrador antes de divulgar `/regras`.

Os comandos são sincronizados globalmente por padrão. Pode levar algum tempo
para aparecerem no Discord. Para desenvolvimento, defina `DISCORD_GUILD_ID` com
o ID do servidor de teste; os comandos serão sincronizados apenas nesse servidor.

As regras configuradas ficam em `discord_bot/data/guild_settings.json` e não são
incluídas no controle de versão.
