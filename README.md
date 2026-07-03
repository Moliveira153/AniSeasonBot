# Anime Season Tracker — Bot Telegram

Bot completo para acompanhamento de animes da temporada atual, com notificações inteligentes, integração AniList/Jikan, PostgreSQL, Redis e worker assíncrono.

## Visão geral

O **Anime Season Tracker** permite que cada usuário:

- Descubra animes da temporada vigente (inverno, primavera, verão ou outono)
- Escolha quais animes acompanhar
- Receba notificações sobre novos episódios, mudanças de horário, hiatos e finalizações
- Consulte detalhes completos de qualquer anime
- Gerencie lista pessoal, preferências, idioma e fuso horário

## Tecnologias

| Componente | Tecnologia |
|---|---|
| Linguagem | Python 3.12+ |
| Bot Telegram | Aiogram 3 |
| API principal | AniList GraphQL |
| API fallback | Jikan (MyAnimeList) |
| Banco de dados | PostgreSQL + SQLAlchemy 2 (async) |
| Migrações | Alembic |
| Cache / Locks | Redis |
| Agendador | **ARQ** (ver decisão abaixo) |
| HTTP | HTTPX |
| Config | Pydantic Settings |
| Testes | Pytest |
| Qualidade | Ruff, mypy |
| Deploy | Docker Compose |

## Decisão arquitetural: APScheduler vs Celery vs ARQ

| Opção | Prós | Contras |
|---|---|---|
| **APScheduler** | Simples, in-process | Não escala bem com múltiplas instâncias; sem fila de retry nativa |
| **Celery** | Maduro, distribuído | Pesado; broker extra; stack síncrona misturada com async |
| **ARQ** ✅ | Nativo async; usa Redis já presente; cron jobs; locks; leve | Menos ecossistema que Celery |

**Escolha: ARQ** — O projeto é 100% assíncrono (Aiogram, SQLAlchemy async, HTTPX). Redis já é obrigatório para cache, FSM e locks. ARQ oferece cron jobs para sincronização periódica, fila de notificações, retry e proteção contra múltiplas instâncias via locks distribuídos, com footprint mínimo.

## Arquitetura

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Telegram   │────▶│  Bot (main)  │────▶│  PostgreSQL │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────▼───────┐     ┌─────────────┐
                    │    Redis     │◀───▶│   Worker    │
                    │ (FSM/cache)  │     │    (ARQ)    │
                    └──────────────┘     └──────┬──────┘
                                                  │
                           ┌──────────────────────┼──────────────────────┐
                           ▼                      ▼                      ▼
                    ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
                    │   AniList   │        │    Jikan    │        │ Notificações│
                    │  GraphQL    │        │   (fallback)│        │  Telegram   │
                    └─────────────┘        └─────────────┘        └─────────────┘
```

### Módulos

```
app/
├── main.py                 # Entry point do bot
├── config.py               # Variáveis de ambiente
├── health.py               # Health check
├── bot/
│   ├── handlers/           # Comandos e callbacks
│   ├── keyboards/          # Teclados inline
│   ├── middlewares/        # DB, throttle, manutenção
│   ├── states/             # FSM (onboarding, busca)
│   └── texts/i18n.py       # Traduções pt-BR / en
├── clients/
│   ├── anilist.py          # Cliente GraphQL
│   └── jikan.py            # Cliente REST fallback
├── database/
│   ├── models/             # SQLAlchemy models
│   ├── repositories/       # Acesso a dados
│   └── migrations/         # Alembic
├── services/               # Lógica de negócio
├── workers/                # ARQ tasks e cron
├── schemas/                # Pydantic
└── utils/                  # Helpers
```

## Pré-requisitos

- Python 3.12+
- Docker e Docker Compose (recomendado)
- Token do bot Telegram (via [@BotFather](https://t.me/BotFather))

## Configuração

### 1. Criar o bot no BotFather

1. Abra [@BotFather](https://t.me/BotFather) no Telegram
2. Envie `/newbot` e siga as instruções
3. Copie o token gerado
4. Opcional: `/setcommands` — os comandos são registrados automaticamente na inicialização

### 2. Variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env`:

```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
DATABASE_URL=postgresql+asyncpg://animebot:animebot@postgres:5432/animebot
REDIS_URL=redis://redis:6379/0
ADMIN_TELEGRAM_IDS=123456789
```

## Execução com Docker (recomendado)

```bash
cp .env.example .env
# Edite .env com seu TELEGRAM_BOT_TOKEN

docker compose up -d --build
docker compose run --rm migrate
# ou: docker compose exec bot alembic upgrade head
```

Serviços:
- `bot` — Bot Telegram (polling)
- `worker` — Sincronização e notificações (ARQ)
- `postgres` — Banco de dados
- `redis` — Cache, FSM, filas

## Execução local

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e ".[dev]"

# Inicie PostgreSQL e Redis localmente, depois:
cp .env.example .env
# Ajuste DATABASE_URL e REDIS_URL para localhost

alembic upgrade head
python -m app.main            # Terminal 1: bot
arq app.workers.scheduler.WorkerSettings  # Terminal 2: worker
```

## Migrações

```bash
alembic upgrade head          # Aplicar
alembic downgrade -1          # Reverter última
alembic revision --autogenerate -m "descricao"  # Nova migração
```

## Testes

```bash
pytest -v
pytest --cov=app
ruff check app tests
mypy app
```

## Comandos do bot

| Comando | Descrição |
|---|---|
| `/start` | Onboarding (idioma, fuso, temporada) |
| `/temporada` | Animes da temporada atual |
| `/buscar` | Buscar anime por nome |
| `/anime` | Detalhes por ID ou nome |
| `/minhalista` | Lista de acompanhamento |
| `/proximos` | Próximos episódios da sua lista |
| `/hoje` | Episódios previstos para hoje |
| `/semana` | Calendário semanal |
| `/lancamentos` | Lançamentos recentes |
| `/configuracoes` | Preferências |
| `/pausar` / `/retomar` | Notificações |
| `/excluirme` | Excluir dados pessoais |
| `/ajuda` | Ajuda |
| `/sobre` | Sobre o bot |
| `/privacidade` | Política de privacidade |

### Comandos admin

| Comando | Descrição |
|---|---|
| `/stats` | Estatísticas do bot |
| `/sync <anilist_id>` | Forçar sincronização |
| `/retry_notifications` | Ver falhas pendentes |

## Como funciona o agendador

O worker ARQ executa cron jobs:

1. **sync_tracked_animes** — A cada 5 min: sincroniza animes acompanhados (prioridade inteligente)
2. **send_notifications** — A cada 30s: envia notificações pendentes
3. **retry_failed_notifications** — 4x/dia: reprocessa falhas
4. **health_check** — A cada 30 min: verifica saúde

### Sincronização inteligente

| Situação | Intervalo |
|---|---|
| Episódio em < 1h | 5 min |
| Em exibição | 15 min |
| Pré-estreia | 1 h |
| Finalizado | 24 h |

Falhas usam backoff exponencial (60s → 120s → ... → max 1h).

## Deduplicação de notificações

1. **Evento global** — Chave única por anime + tipo + episódio (`anime_events.idempotency_key`)
2. **Entrega por usuário** — Chave única por usuário + anime + tipo + episódio (`notification_deliveries.idempotency_key`)
3. **Lock distribuído** — Redis `lock:anime_sync` evita processamento concorrente
4. **Transações** — Commit atômico no banco
5. **Retry** — Até 5 tentativas com registro de erro
6. **Persistência** — Chaves no PostgreSQL sobrevivem reinícios

## Limitações das APIs

- **AniList**: Rate limit ~90 req/min; não fornece lista completa de títulos de episódios
- **Jikan**: Rate limit ~60 req/min; usado apenas como complemento
- **Trailers**: Apenas links oficiais (YouTube/Dailymotion); sem download
- **Horários**: Podem ser estimados quando a API não confirma

## Política de privacidade

- Armazenamos: ID Telegram, nome, preferências, lista de animes
- Não armazenamos: mensagens, dados desnecessários
- Exclusão: `/excluirme` remove todos os dados pessoais
- Logs: sem tokens ou dados sensíveis

## Diagnóstico de erros comuns

| Erro | Solução |
|---|---|
| `TELEGRAM_BOT_TOKEN is required` | Configure `.env` |
| Bot não responde | Verifique `docker compose logs bot` |
| Sem notificações | Verifique `docker compose logs worker` |
| Rate limit AniList | Aguarde; cache Redis reduz chamadas |
| `Connection refused` PostgreSQL | Aguarde health check ou reinicie compose |

## Exemplos de uso

```
/start
/temporada
/buscar Frieren
/anime 154587
/minhalista
/proximos
/configuracoes
```

## Licença

MIT — Use livremente para projetos pessoais e educacionais.