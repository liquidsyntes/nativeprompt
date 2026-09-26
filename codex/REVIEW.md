# REVIEW — Codex-аудит

Дата проверки: 2026-07-29. После первичного аудита четыре Codex-связанные проблемы core исправлены; каталог правил и корневой навык Claude Code не изменялись.

## Итог

Codex-интеграции в исходном состоянии не было: корневой `SKILL.md` ориентирован на Claude Code, а Codex обнаруживает локальные навыки в `.agents/skills/<name>/SKILL.md` и распространяемые навыки — в plugin-пакетах. Добавлены отдельный Codex-навык, skill-only plugin, безопасная обёртка CLI и фрагмент `AGENTS.md`.

Официальные основания:

- навыки и `.agents/skills`: https://learn.chatgpt.com/docs/build-skills
- упаковка plugin: https://developers.openai.com/plugins/build/plugins
- постоянные инструкции: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- prompting Codex: https://learn.chatgpt.com/docs/prompting

## Что проверено

- `54 passed` — весь pytest-набор после добавления регрессионных тестов.
- Чистая editable-установка в отдельной временной копии и запуск `nativeprompt 0.1.0`.
- Контраст `--model gpt-5.6` и `--model claude-opus-5`.
- Codex JSON-контракт: `target`, `findings`, `harness`, `improved`, `metaprompt`.
- `nativeprompt update`: OpenAI-источники без изменений; один Claude-источник изменился, но по границе задачи не обновлялся.

## Оставшийся блокер

### P0 — заявленные удалённые способы установки пока недоступны

`pip index versions nativeprompt` возвращает `No matching distribution found`, `git ls-remote https://github.com/edvardgrishin27/nativeprompt.git` — `Repository not found`, а локальный Git не имеет remote и коммитов. Поэтому команды `pipx install nativeprompt` и `git clone ...` из корневого README сейчас невоспроизводимы.

Предложение: сначала опубликовать репозиторий/пакет, затем проверить установку на чистом окружении и только после этого включать удалённые команды в Codex installer.

## Исправлено в core

### Исправлено — актуальные имена параметров Codex

`nativeprompt/rules/openai.json` теперь использует документированные `model_reasoning_effort` (`minimal|low|medium|high|xhigh`) и `model_verbosity` (`low|medium|high`). Недокументированные `reasoning.mode: pro`, `reasoning.effort` и `text.verbosity` удалены из заметки. Добавлен регрессионный тест.

Источник: https://learn.chatgpt.com/docs/config-file/config-reference

### Исправлено — URL внутри мета-промпта

`build_metaprompt()` теперь добавляет `finding["source"]` к каждой строке правила и `harness["source"]` к рекомендации запуска. Контракт «каждое объяснение со ссылкой» стал самодостаточным и покрыт тестом.

### Исправлено — приоритет активной CLI-сессии

Детектор учитывает маркеры активной Codex/Claude Code сессии. В Codex `CODEX_MODEL`, `OPENAI_MODEL` и `~/.codex/config.toml` имеют приоритет над остаточным `ANTHROPIC_MODEL`; если точная модель не задана, используется семейство `codex`. Симметричный тест защищает Claude-сессию от остаточного `CODEX_MODEL`.

### Исправлено — автономность не показывается для trivial

Правила `always` теперь могут декларативно задавать `when_shapes`. Для `codex-autonomy` исключён `trivial`, поэтому рекомендация отсутствует и в `findings`, и в отчёте короткой задачи. Длинные задачи сохраняют прежнее поведение.

### Ошибка с кодировкой в тестах на Windows

Тесты падают на русской Windows с ошибкой `UnicodeDecodeError: 'charmap' codec can't decode byte` из-за вызовов `subprocess.run` с `text=True` без явного указания кодировки. По умолчанию используется системная кодировка cp1251. В `codex/patches/01-test-subprocess-encoding.patch` добавлен фикс: явное указание `encoding='utf-8'`. (Патч сломан из-за плохой конвертации, поэтому предложен `02-fix-subprocess-encoding.patch`).

## Аудит (Сентябрь 2026)

Сделана нативная интеграция для Codex по конвенциям Antigravity:
1. Очищен `plugins/nativeprompt/plugin.json` (в корне плагина).
2. Фрагмент `AGENTS.md` перемещен в `plugins/nativeprompt/rules/AGENTS.md`, так что он применяется автоматически при активации плагина.
3. Обертка `improve_prompt.py` проверена на работоспособность с Codex.

### Улучшения эвристик `analyze.py`

В `codex/patches/03-improve-analyze-heuristics.patch` предложены следующие улучшения:
- Добавлены статические анализаторы и инструменты проверки типов в `_VERIFY_MEANS`: `mypy`, `flake8`, `tsc`, `type check`, `coverage`. Это позволит не требовать от пользователя просить о проверке, если он уже попросил прогнать линтеры.
- Добавлены недостающие термины в списки `_CODE_NOUN_LOOSE` и `_CODE_NOUN_EN`: `интерфейс`, `токен`, `бд`, `архитектур` (`interface`, `token`, `db`, `database`, `architecture`). Это исправит пропуски детектора `code_task`, когда речь идет о базе данных или архитектуре.

### Дальнейшие предложения по UX и `analyze.py`

1. Эвристика длинной задачи `_c_long_task`: сейчас условие `len(_ACTION_VERB.findall(low)) >= 3` может ложно срабатывать на коротких промптах вроде «сделай X, обнови Y и удали Z» (3 глагола-действия), навязывая режим планирования. Стоит комбинировать подсчет глаголов с порогом по длине промпта в символах.
2. CLI UI: команда `detect` отлично справляется и выдает корректную цепочку находок (вплоть до `~/.codex/config.toml` для Codex), что значительно облегчает отладку. Контраст правок отлично работает (`gpt-5.6` vs `claude-opus-5`).
