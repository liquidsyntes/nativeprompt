"""Веб-интерфейс для nativeprompt на базе Gradio.

Позволяет вводить промпт, выбирать или вводить целевую модель,
и просматривать улучшенный промпт вместе с применёнными правилами
и объяснениями вендоров.
"""

from typing import Optional, Tuple

from .analyze import normalize_prompt
from .explain import build_report

DEFAULT_MODELS = [
    "gpt-5.6",
    "claude-opus-5",
    "claude-opus-5.5",
    "claude-sonnet-4.5",
    "claude-fable-5.1",
    "codex",
    "gpt-6-astra",
    "gpt-6-sol",
    "gemini-2.5",
    "gemini",
    "grok-3",
    "grok",
    "kimi-k2",
    "kimi",
    "qwen-2.5",
    "qwen",
]


def format_explanations(report: Optional[dict]) -> str:
    """Сформировать читаемый Markdown-отчёт с правилами и объяснениями."""
    if not isinstance(report, dict):
        return ""

    if report.get("error"):
        target = report.get("target")
        target = target if isinstance(target, dict) else {}
        model = target.get("model_id") or "не указана"
        return (
            f"### ⚠️ Не удалось определить модель: `{model}`\n\n"
            f"Модель не найдена в каталоге правил. Пожалуйста, выберите или укажите "
            f"поддерживаемую модель (например: `gpt-5.6`, `claude-opus-5`, `codex`, "
            f"`gemini-2.5`, `grok-3`, `kimi-k2`, `qwen-2.5`)."
        )

    lines = []
    target = report.get("target")
    target = target if isinstance(target, dict) else {}
    model_id = target.get("model_id") or target.get("family") or "—"
    family = target.get("family") or "—"
    cli = target.get("cli") or family
    generation = target.get("generation")
    gen_str = f" · поколение: `{generation}`" if generation else ""
    shape = report.get("shape") or "normal"

    lines.append(f"### 🎯 Целевая модель: **{model_id}** ({cli}){gen_str}")
    lines.append(f"**Семейство:** `{family}` · **Форма задачи:** `{shape}`\n")

    applied_raw = report.get("applied")
    applied_ids = set(applied_raw) if isinstance(applied_raw, (list, tuple, set)) else set()
    findings_raw = report.get("findings")
    findings = [f for f in findings_raw if isinstance(f, dict)] if isinstance(findings_raw, (list, tuple)) else []

    applied_findings = [f for f in findings if f.get("id") in applied_ids]
    other_findings = [f for f in findings if f.get("id") not in applied_ids]

    ACTION_MARKS = {
        "add": "[+] Добавить",
        "remove": "[-] Убрать",
        "restructure": "[~] Перестроить",
        "warn": "[!] Предупредить",
    }

    if applied_findings:
        lines.append("#### ✅ Применённые правила:")
        for f in applied_findings:
            action = f.get("action", "")
            action_tag = f" `{ACTION_MARKS.get(action, f'[{action}]')}`" if action else ""
            title = f.get("title") or f.get("id") or "Правило"
            rule_id = f" (`{f.get('id')}`)" if f.get("id") else ""
            lines.append(f"- **{title}**{rule_id}{action_tag}")
            if f.get("why"):
                lines.append(f"  - **Почему:** {f.get('why')}")
            if f.get("source"):
                src = str(f.get("source"))
                if src.startswith("http://") or src.startswith("https://"):
                    lines.append(f"  - **Источник:** [{src}]({src})")
                else:
                    lines.append(f"  - **Источник:** `{src}`")
        lines.append("")

    if other_findings:
        lines.append("#### ℹ️ Рекомендации и предупреждения:")
        for f in other_findings:
            title = f.get("title") or f.get("id") or "Правило"
            rule_id = f" (`{f.get('id')}`)" if f.get("id") else ""
            lines.append(f"- **{title}**{rule_id}")
            if f.get("why"):
                lines.append(f"  - **Совет:** {f.get('why')}")
            if f.get("unless"):
                lines.append(f"  - *Неприменимо если:* {f.get('unless')}")
            if f.get("source"):
                src = str(f.get("source"))
                if src.startswith("http://") or src.startswith("https://"):
                    lines.append(f"  - **Источник:** [{src}]({src})")
                else:
                    lines.append(f"  - **Источник:** `{src}`")
        lines.append("")

    if not applied_findings and not other_findings:
        lines.append("✅ **Промпт соответствует официальным правилам модели!** Дополнительных правок не требуется.\n")

    harness = report.get("harness")
    if isinstance(harness, dict) and harness.get("command"):
        harness_line = f"💡 **Рекомендуемый запуск:** `{harness.get('command')}` ({harness.get('title', '')})"
        if harness.get("why"):
            harness_line += f" — *{harness.get('why')}*"
        lines.append(harness_line + "\n")

    mp = report.get("metaprompt")
    if mp and isinstance(mp, str):
        clean_mp = mp.strip()
        fence = "````" if "```" in clean_mp else "```"
        lines.append("<details><summary>📋 <b>Мета-промпт для модели (нажмите, чтобы развернуть)</b></summary>\n")
        lines.append(f"{fence}text\n{clean_mp}\n{fence}\n</details>")

    return "\n".join(lines)


def process_prompt(prompt: str, model: Optional[str] = "gpt-5.6") -> Tuple[str, str]:
    """Обработать исходный промпт через внутреннее API nativeprompt.

    Возвращает кортеж (улучшенный_промпт, объяснения_в_markdown).
    """
    try:
        prompt_str = str(prompt) if prompt is not None else ""
        cleaned = normalize_prompt(prompt_str)
        if not cleaned:
            return (
                "",
                "ℹ️ *Введите текст промпта в поле слева для начала работы.*",
            )

        model_arg = (str(model) if model is not None else "").strip() or None
        report = build_report(cleaned, model=model_arg)

        if report.get("error"):
            return "", format_explanations(report)

        improved = str(report.get("improved") or "")
        explanations = format_explanations(report)
        return improved, explanations
    except Exception as e:
        return "", f"### ⚠️ Ошибка при обработке промпта\n\n`{type(e).__name__}: {e}`"


def create_app(default_model: Optional[str] = None):
    """Создать и настроить приложение Gradio."""
    try:
        import gradio as gr
    except ImportError as e:
        raise ImportError(
            "Для работы веб-интерфейса требуется пакет gradio. "
            "Установите его через pip install gradio"
        ) from e

    initial_model = (default_model or "").strip() or "gpt-5.6"

    with gr.Blocks(title="nativeprompt — веб-интерфейс") as demo:
        gr.Markdown(
            "# 🚀 nativeprompt\n"
            "Перепиши свой промпт под **официальные правила вендора** "
            "(Claude Code, Codex, Gemini, Grok, Kimi, Qwen) и узнай почему."
        )

        with gr.Row():
            with gr.Column(scale=1):
                prompt_input = gr.Textbox(
                    label="Исходный промпт / Original Prompt",
                    placeholder="Введите текст промпта (например: почини баг, думай пошагово, перепроверь себя)...",
                    lines=8,
                )
                model_input = gr.Dropdown(
                    label="Целевая модель / Target Model",
                    choices=DEFAULT_MODELS,
                    value=initial_model,
                    allow_custom_value=True,
                    info="Выберите модель из списка или введите название вручную (например: gpt-5.6, claude-opus-5, codex)",
                )
                with gr.Row():
                    improve_btn = gr.Button("✨ Улучшить промпт / Improve", variant="primary")
                    clear_btn = gr.ClearButton(
                        value="Очистить / Clear",
                    )

                gr.Examples(
                    examples=[
                        ["почини баг, думай пошагово, перепроверь себя", "gpt-5.6"],
                        ["ОБЯЗАТЕЛЬНО почини баг в @src/a.py, прогони тесты и перепроверь себя", "claude-opus-5"],
                        ["Напиши функцию валидации email", "claude-opus-5"],
                        ["Создай REST API для аутентификации пользователей", "codex"],
                    ],
                    inputs=[prompt_input, model_input],
                    label="Примеры / Examples",
                )

            with gr.Column(scale=1):
                textbox_kwargs = {
                    "label": "Улучшенный промпт / Improved Prompt",
                    "lines": 8,
                }
                import inspect
                sig = inspect.signature(gr.Textbox.__init__)
                if "buttons" in sig.parameters:
                    textbox_kwargs["buttons"] = ["copy"]
                elif "show_copy_button" in sig.parameters:
                    textbox_kwargs["show_copy_button"] = True

                improved_output = gr.Textbox(**textbox_kwargs)
                explanation_output = gr.Markdown(
                    label="Применённые правила и объяснения / Applied Rules & Explanations",
                    value="*Здесь появятся применённые правила и рекомендации вендора после улучшения промпта.*",
                )

        clear_btn.add([prompt_input, improved_output, explanation_output])

        prompt_input.submit(
            fn=process_prompt,
            inputs=[prompt_input, model_input],
            outputs=[improved_output, explanation_output],
        )

        improve_btn.click(
            fn=process_prompt,
            inputs=[prompt_input, model_input],
            outputs=[improved_output, explanation_output],
        )

    return demo


create_ui = create_app


def launch_web(
    host: str = "127.0.0.1",
    port: int = 7860,
    share: bool = False,
    inbrowser: bool = False,
    default_model: Optional[str] = None,
    **kwargs,
):
    """Запустить локальный сервер Gradio."""
    demo = create_app(default_model=default_model)
    print(f"Запуск локального веб-сервера nativeprompt на http://{host}:{port}")
    try:
        demo.launch(
            server_name=host,
            server_port=port,
            share=share,
            inbrowser=inbrowser,
            **kwargs,
        )
    except BaseException:
        demo.close()
        raise
    if kwargs.get("prevent_thread_lock"):
        return demo
    return 0
