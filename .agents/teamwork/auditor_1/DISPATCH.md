## 2026-09-26T21:58:03Z
You are teamwork_preview_victory_auditor.
Your working directory is: c:\nativeprompt\.agents\teamwork\auditor_1
The project root is: c:\nativeprompt

<original_task>
Create a simple, minimalist, and functional Gradio-based web interface for nativeprompt.
The command `nativeprompt web` should launch the local web server.
This is a focused, self-contained task.

Requirements:
- R1: Integrate `web` command into the nativeprompt CLI to launch the local Gradio server.
- R2: Gradio UI allowing user to enter an initial prompt, select/input target model (e.g. gpt-5.6, claude-opus-5), and see the improved prompt along with applied rules/explanations. Directly use internal API of `nativeprompt`.

Acceptance Criteria:
- Automated test (e.g. tests/test_web.py) verifying Gradio interface logic and prompt processing.
- `python -m nativeprompt web --help` works and does not fail.
- All pytest tests pass cleanly without breaking existing tests.

Authoritative specification from c:\nativeprompt\.agents\teamwork\ORIGINAL_REQUEST.md:
Создание простого, минималистичного и функционального веб-интерфейса на базе Gradio для CLI-инструмента nativeprompt. Команда `nativeprompt web` должна запускать локальный веб-сервер. Это разовая, изолированная задача; держите изменения сфокусированными.

Working directory: c:\nativeprompt
Integrity mode: development

Requirements:
R1. Интеграция CLI команды `web`
Добавить новую подкоманду `web` в существующий CLI-интерфейс `nativeprompt`, которая будет запускать локальный веб-сервер на базе Gradio.

R2. Пользовательский интерфейс (Gradio)
Реализовать минималистичный и понятный веб-интерфейс, который позволяет:
1. Ввести исходный промпт (текстовое поле).
2. Выбрать или указать целевую модель (например, `gpt-5.6`, `claude-opus-5`).
3. Увидеть результат: улучшенный промпт и список примененных правил/объяснений.
Интерфейс должен напрямую использовать внутреннее API пакета `nativeprompt` (а не вызывать CLI через shell).

Acceptance Criteria:
- [ ] Существует тест (например, в `tests/test_web.py`), который программно импортирует и проверяет логику Gradio-интерфейса.
- [ ] Тест подтверждает, что интерфейс успешно инициализируется без ошибок и его основная функция обработки промпта возвращает ожидаемые данные.
- [ ] При вызове `python -m nativeprompt web --help` команда отображается и не падает.
- [ ] Код проходит общие линтеры и проверки проекта (выполнение `pytest` должно завершаться успешно, не ломая существующие тесты).
</original_task>

Please conduct your independent 3-phase audit:
1. Timeline & git history audit
2. Cheating detection (ensure tests test real behavior, not hardcoded mock results or weakened invariants)
3. Independent test execution against the repository
Provide a structured verdict (CONFIRMED / REJECTED) with full findings.
