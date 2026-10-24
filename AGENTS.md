# AGENTS.md

This file provides guidance to agents working with code in this repository.

## Что это

Веб-прототип режима карьеры тренера для GameplayFootball. MVP на HTML/CSS/JS + Python-бэкенд
(FastAPI). Клиент — SPA в одном HTML-файле, сервер отдаёт данные о игроках, клубах, чемпионатах
и сохранениях карьеры. Данные подготовлены скриптами из
[transfermarkt_scrapper](https://github.com/Churikov0112/transfermarkt_scrapper) через
transfermarkt-api; канон и конвейер — в [[данные-из-transfermarkt]] вики GameplayFootball.

**Актуальная картина проекта живёт в вики: `docs/wiki/index.md` — начинать оттуда.** Этот файл —
только то, что сломаешь, не зная, где посмотреть.

## Ядро архитектуры

- Сервер — `server.py` (FastAPI, порт 8765): эндпоинты `/api/careers`, `/api/clubs`,
  `/api/players`, `/api/leagues`. Данные — моки в том же файле, позже заменятся на реальную БД.
- Клиент — `index.html`: SPA с экранами (главное меню, выбор карьеры, хаб, состав, матч,
  трансферы). Стили — из UI kit (`palette-cozy.html` в соседнем проекте `GameplayFootball-of_port`).
- Данные — `data/json/` (JSON-экспорт из transfermarkt) + `data/raster/` (лица игроков, тренеров,
  эмблемы, флаги). Пути к фото шаблонные: `data/raster/{players_faces|coaches_faces|…}/{id}.jpg`.

**Актуальная картина проекта живёт в вики: `docs/wiki/index.md` — начинать оттуда.**

## Сборка / запуск

```bash
pip install -r requirements.txt
python scripts/build_canon_db.py   # canon.db из data/json + ratings_output.json
cd web && npm install && npm run build
cd .. && python server.py           # FastAPI + собранный Svelte на :8765
python -m pytest                    # тесты канона и API
```

Для разработки UI: `cd web && npm run dev` (Vite на :5173, проксирует `/api` и `/raster` на :8765).

## Устройство вики

- `docs/wiki/` — **текущее состояние**, одна страница на подсистему, кросс-ссылки вида
  `[[имя-страницы]]`, каталог в `docs/wiki/index.md`. Обновляй страницы после правки кода.
- `docs/wiki/глоссарий.md` — имена предметной области. `CONTEXT.md` в корне — только указатель.
- `log.md` (корень) — append-only хронология. Записи `## [YYYY-MM-DD] тип | описание`.

**Правило: после любого содержательного изменения обнови соответствующую страницу вики — не
создавай новый датированный документ.**

## Workflow

- Код и комментарии — на английском; вики и этот файл — на русском.
- Git: комментарии коммитов на английском, осмысленный subject.
- Три хука (.agent/hooks/ + плагин opencode в .opencode/plugins/) поддерживают контур вики
  механически: оглавление на старте сессии, подсказка «прочитай страницу» по пути правимого
  файла, stop-проверка. Карта «файл → страница» — в `wiki-hint.sh`.

## Working principles

## 1. Think Before Coding
Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing: state assumptions, ask if uncertain, name what's confusing.

## 2. Simplicity First
Minimum code that solves the problem. Nothing speculative. No features beyond what was asked.

## 3. Surgical Changes
Touch only what you must. Match existing style. When your changes create orphans — remove what
YOUR changes made unused; don't delete pre-existing dead code unless asked.

## 4. Goal-Driven Execution
Define success criteria. Loop until verified. For multi-step tasks, state a brief plan with
verifiable checkpoints.

## Agent skills

### Issue tracker

GitHub Issues in `polite-cat-2001/gf-career-prototype`, via `gh`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context. See `docs/agents/domain.md`.
