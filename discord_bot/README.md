# Bot utilitário para Discord

Bot para tarefas comuns do servidor. O token fica apenas nos Secrets do projeto;
ele não deve ser colocado nos arquivos do bot.

## Comandos

- `/ajuda` — mostra a lista de comandos.
- `/ping` — verifica se o bot está respondendo.
- `/servidor` — mostra informações básicas do servidor.
- `/calcular` — converte Robux e Reais pela taxa de 1.000 Robux = R$ 45,00; o resultado é privado.
- `/regras` — publica as regras configuradas.
- `/configurar_regras` — salva as regras; somente administradores.
- `!embed Título | Descrição | Cor` — publica somente o embed; somente o dono do servidor.

## Configuração do bot no Discord

1. No Discord Developer Portal, abra a aplicação do bot e convide-a para o
   servidor com os escopos `bot` e `applications.commands`.
2. Em **Bot > Privileged Gateway Intents**, ative **Message Content Intent**.
3. Conceda as permissões `View Channels`, `Send Messages`, `Embed Links` e
   `Manage Messages`.
4. Em **Replit Secrets**, salve o token como `DISCORD_BOT_TOKEN`.
5. Inicie o workflow **Discord Bot**.
6. Use `/configurar_regras` como administrador antes de divulgar `/regras`.

O comando `!embed` deve ser escrito no canal, por exemplo:
`!embed Aviso | Mensagem para o servidor | Azul`. O bot apaga a mensagem do
comando e publica somente o embed. O dono do servidor é o único autorizado a
usá-lo.

Os comandos são sincronizados globalmente por padrão. Pode levar algum tempo
para aparecerem no Discord. Para desenvolvimento, defina `DISCORD_GUILD_ID` com
o ID do servidor de teste; os comandos serão sincronizados apenas nesse servidor.

As regras configuradas ficam em `discord_bot/data/guild_settings.json` e não são
incluídas no controle de versão.
