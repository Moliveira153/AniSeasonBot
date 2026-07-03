# Deploy no Render.com

Guia para rodar o bot **sem cair** no Render, inclusive no plano gratuito.

## Por que webhook e não polling?

| Modo | Problema no Render |
|---|---|
| Polling | Processo contínuo cai quando o container reinicia; duplica se houver 2 instâncias |
| **Webhook** ✅ | Telegram envia updates via HTTP; compatível com Web Services; health check nativo |

## Arquitetura no plano FREE

```
Telegram ──POST──▶ Web Service (FastAPI)
                      ├── POST /webhook/{secret}
                      ├── GET  /health
                      ├── Embedded Worker (sync + notificações)
                      ├── PostgreSQL (Render)
                      └── Key Value / Redis (Render)
```

No plano free, **Background Workers e Cron Jobs são pagos**. Por isso o worker ARQ roda **embutido** no processo web (`EMBEDDED_WORKER=true`).

## Passo a passo

### 1. Subir o código no GitHub

```bash
git init
git add .
git commit -m "Anime Season Bot"
git remote add origin https://github.com/SEU_USUARIO/anime-season-bot.git
git push -u origin main
```

### 2. Criar Blueprint no Render

1. Acesse [dashboard.render.com](https://dashboard.render.com)
2. **New +** → **Blueprint**
3. Conecte o repositório
4. O Render detecta o `render.yaml` automaticamente
5. Clique **Apply**

> **Nota:** O Render **não suporta** `dockerTarget` no blueprint. O deploy usa **runtime Python nativo** com `requirements.txt`. Se preferir Docker, use `Dockerfile.render` (estágio único) e defina `runtime: docker` + `dockerfilePath: ./Dockerfile.render` — sem `dockerTarget`.

### 3. Configurar variáveis secretas

No serviço **anime-season-bot**, adicione:

| Variável | Valor |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token do @BotFather |
| `ADMIN_TELEGRAM_IDS` | Seu ID Telegram (opcional) |

O Render gera automaticamente:
- `WEBHOOK_SECRET`
- `DATABASE_URL`
- `REDIS_URL`
- `RENDER_EXTERNAL_URL`

### 4. Aguardar o deploy

O bot irá:
1. Rodar migrações (`alembic upgrade head`)
2. Registrar webhook no Telegram
3. Iniciar worker embutido
4. Responder em `/health`

### 5. Evitar cold start (plano free)

Serviços free **hibernam após ~15 min** sem tráfego. Opções:

**Gratuito — UptimeRobot:**
1. Crie conta em [uptimerobot.com](https://uptimerobot.com)
2. Adicione monitor HTTP(s) para `https://SEU-APP.onrender.com/health`
3. Intervalo: 5 minutos

**Pago — Cron Job no Render** (descomente no `render.yaml`)

## Variáveis de ambiente

```env
BOT_MODE=webhook
EMBEDDED_WORKER=true
RUN_MIGRATIONS_ON_STARTUP=true
IS_RENDER=true
WEBHOOK_SECRET=<gerado pelo Render>
RENDER_EXTERNAL_URL=<automático>
DATABASE_URL=<automático — postgres://...>
REDIS_URL=<automático — rediss://...>
DB_POOL_SIZE=3
DB_MAX_OVERFLOW=5
```

## Upgrade para plano pago (opcional)

Se quiser worker ARQ separado:

1. Descomente o serviço `anime-season-worker` no `render.yaml`
2. No web service, defina `EMBEDDED_WORKER=false`
3. Faça redeploy

## Verificar se está funcionando

```bash
# Health check
curl https://SEU-APP.onrender.com/health

# Deve retornar:
# {"database":"ok","redis":"ok","overall":"healthy"}
```

No Telegram, envie `/start` para @aniseasonbot.

## Troubleshooting

| Problema | Solução |
|---|---|
| Bot não responde | Verifique logs do web service; confirme `TELEGRAM_BOT_TOKEN` |
| `database: error` | Aguarde Postgres ficar healthy; redeploy |
| `redis: error` | Verifique Key Value provisionado; URL com `rediss://` usa TLS automaticamente |
| Webhook inválido | Confirme `RENDER_EXTERNAL_URL` está definido |
| Notificações não chegam | Confirme `EMBEDDED_WORKER=true` nos logs |
| Cold start lento | Configure UptimeRobot no `/health` |

## Segurança

- **Nunca** commite o token no Git
- O `WEBHOOK_SECRET` protege o endpoint `/webhook/{secret}`
- Revogue o token se ele vazar