"""Автотесты для веб-интерфейса nativeprompt на базе Gradio."""

import subprocess
import sys
import unittest.mock as mock

import pytest

import nativeprompt
from nativeprompt.web import (
    DEFAULT_MODELS,
    create_app,
    create_ui,
    format_explanations,
    process_prompt,
)


def test_package_exports():
    """Функции веб-интерфейса доступны из корня пакета nativeprompt."""
    assert callable(nativeprompt.create_app)
    assert callable(nativeprompt.create_ui)
    assert callable(nativeprompt.process_prompt)
    assert callable(nativeprompt.launch_web)


def test_create_app_initialization():
    """Gradio-интерфейс успешно инициализируется без ошибок и регистрирует события."""
    import gradio as gr

    demo = create_app()
    assert isinstance(demo, gr.Blocks)

    # Проверяем регистрацию обработчиков событий submit и click
    callbacks = [getattr(fn, "fn", None) for fn in demo.fns.values()]
    assert callbacks.count(process_prompt) >= 2

    # create_ui является алиасом к create_app
    demo_ui = create_ui(default_model="claude-opus-5")
    assert isinstance(demo_ui, gr.Blocks)


def test_default_models_list():
    """Список моделей по умолчанию содержит ключевые модели gpt-5.6 и claude-opus-5."""
    assert "gpt-5.6" in DEFAULT_MODELS
    assert "claude-opus-5" in DEFAULT_MODELS
    assert "codex" in DEFAULT_MODELS


def test_process_prompt_gpt56():
    """Проверка основной функции обработки промпта на модели gpt-5.6."""
    prompt = "почини баг, думай пошагово, перепроверь себя"
    improved, explanations = process_prompt(prompt, model="gpt-5.6")

    assert isinstance(improved, str)
    assert isinstance(explanations, str)
    assert len(improved) > 0
    # На gpt-5.6 правило codex-no-forced-cot предупреждает о «думай пошагово»
    assert "gpt-5.6" in explanations.lower() or "codex" in explanations.lower()
    assert "codex-no-forced-cot" in explanations or "пошагово" in explanations
    assert "http" in explanations  # ссылка на источник вендора


def test_process_prompt_claude_opus():
    """Проверка обработки промпта на модели claude-opus-5."""
    prompt = "ОБЯЗАТЕЛЬНО почини баг в @src/a.py, прогони тесты и перепроверь себя"
    improved, explanations = process_prompt(prompt, model="claude-opus-5")

    assert isinstance(improved, str)
    assert isinstance(explanations, str)
    # КАПС должен быть смягчён
    assert "ОБЯЗАТЕЛЬНО" not in improved
    assert "Обязательно" in improved
    # В объяснениях должны быть отражены применённые правила или рекомендации
    assert "claude-opus-5" in explanations or "claude" in explanations.lower()
    assert "claude-dial-caps" in explanations or "капс" in explanations.lower() or "caps" in explanations.lower()


def test_process_prompt_empty_input():
    """Пустой ввод, пробелы, None или нестроковые типы обрабатываются корректно."""
    improved, explanations = process_prompt("", model="gpt-5.6")
    assert improved == ""
    assert "введите" in explanations.lower() or "enter" in explanations.lower()

    improved_spaces, explanations_spaces = process_prompt("   \n\t  ", model="gpt-5.6")
    assert improved_spaces == ""
    assert "введите" in explanations_spaces.lower() or "enter" in explanations_spaces.lower()

    improved_none, explanations_none = process_prompt(None, model="gpt-5.6")
    assert improved_none == ""
    assert "введите" in explanations_none.lower()

    # Нестроковые типы входных данных приводятся к строкам без падений
    imp_int, exp_int = process_prompt(12345, model=5.6)
    assert isinstance(imp_int, str)
    assert isinstance(exp_int, str)


def test_process_prompt_unknown_model():
    """Неизвестная модель обрабатывается без исключений с информативным сообщением."""
    improved, explanations = process_prompt("почини баг", model="nonexistent-model-xyz")
    assert improved == ""
    assert "не удалось определить модель" in explanations.lower() or "не найдена" in explanations.lower()

    # При пустом указании модели (None или "") срабатывает автоопределение / дефолт
    imp_def, exp_def = process_prompt("почини баг", model="")
    assert len(exp_def) > 0


def test_format_explanations_clean_prompt():
    """Форматирование отчёта, если промпт уже соответствует всем правилам."""
    report = {
        "target": {
            "model_id": "gpt-5.6",
            "family": "openai",
            "cli": "Codex",
            "generation": "gpt-5.6",
        },
        "shape": "normal",
        "applied": ["r1"],
        "findings": [
            {
                "id": "r1",
                "title": "Добавить тесты",
                "action": "add",
                "why": "Повышает надежность",
                "source": "https://example.com/r1",
            },
            {
                "id": "r2",
                "title": "Совет по архитектуре",
                "action": "warn",
                "why": "Полезно для больших проектов",
                "source": "local_doc",
            },
        ],
        "harness": {"command": "codex", "title": "Codex CLI", "why": "автономный запуск"},
        "metaprompt": "TEST METAPROMPT",
    }
    output = format_explanations(report)
    assert "gpt-5.6" in output
    assert "[+] Добавить" in output
    assert "https://example.com/r1" in output
    assert "`local_doc`" in output
    assert "TEST METAPROMPT" in output

    # Проверка устойчивости к None, не-dict findings, не-iterable applied и вложенным бэктикам
    assert format_explanations(None) == ""
    corrupt_report = {
        "target": {"family": "openai", "model_id": "gpt-5.6"},
        "findings": ["not-a-dict", None],
        "applied": 12345,
        "metaprompt": "```python\ncode\n```",
    }
    safe_out = format_explanations(corrupt_report)
    assert "gpt-5.6" in safe_out
    assert "````text" in safe_out

    # Проверка устойчивости process_prompt к непредвиденным ошибкам build_report
    with mock.patch("nativeprompt.web.build_report", side_effect=RuntimeError("Engine failure")):
        err_imp, err_exp = process_prompt("тестовый промпт", model="gpt-5.6")
        assert err_imp == ""
        assert "Engine failure" in err_exp


def test_cli_web_help():
    """Команда `nativeprompt web --help` выполняется успешно и параметры парсятся."""
    from nativeprompt.__main__ import build_parser

    result = subprocess.run(
        [sys.executable, "-m", "nativeprompt", "web", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    assert "--host" in result.stdout
    assert "--port" in result.stdout
    assert "--share" in result.stdout
    assert "--inbrowser" in result.stdout
    assert "--model" in result.stdout

    # Проверка разбора аргументов CLI для команды web
    parser = build_parser()
    args = parser.parse_args(["web", "--host", "0.0.0.0", "--port", "9000", "--share", "--inbrowser", "-m", "claude-opus-5"])
    assert args.host == "0.0.0.0"
    assert args.port == 9000
    assert args.share is True
    assert args.inbrowser is True
    assert args.model == "claude-opus-5"


def test_cmd_web_missing_gradio(capsys):
    """Если gradio не установлен или сервер падает, cmd_web возвращает 1; Ctrl+C возвращает 0."""
    import gradio as gr
    from nativeprompt.__main__ import cmd_web

    args = mock.MagicMock()
    args.host = "127.0.0.1"
    args.port = 7860
    args.share = False
    args.inbrowser = False
    args.model = None

    # Проверяем, когда пакет gradio отсутствует в системе
    with mock.patch.dict("sys.modules", {"gradio": None}):
        code = cmd_web(args)
        assert code == 1
        captured = capsys.readouterr()
        assert "gradio" in captured.err.lower()

    # Проверяем обработку KeyboardInterrupt
    with mock.patch("nativeprompt.web.launch_web", side_effect=KeyboardInterrupt):
        code_sigint = cmd_web(args)
        assert code_sigint == 0

    # При непредвиденной ошибке запуска сервера cmd_web возвращает код 1 с выводом ошибки в stderr
    with mock.patch("nativeprompt.web.launch_web", side_effect=RuntimeError("Address already in use")):
        code_err = cmd_web(args)
        assert code_err == 1
        captured_err = capsys.readouterr()
        assert "Address already in use" in captured_err.err

    # Если demo.launch падает с ошибкой, launch_web закрывает demo
    with mock.patch.object(gr.Blocks, "launch", side_effect=RuntimeError("Bind error")):
        with mock.patch.object(gr.Blocks, "close") as mock_close:
            with pytest.raises(RuntimeError):
                nativeprompt.launch_web()
            mock_close.assert_called_once()

    # Закрытие demo срабатывает и на BaseException (например KeyboardInterrupt)
    with mock.patch.object(gr.Blocks, "launch", side_effect=KeyboardInterrupt):
        with mock.patch.object(gr.Blocks, "close") as mock_close_base:
            with pytest.raises(KeyboardInterrupt):
                nativeprompt.launch_web()
            mock_close_base.assert_called_once()


def test_launch_web_lifecycle():
    """Проверка запуска сервера, сетевого запроса через client и корректной остановки."""
    import socket
    import urllib.request
    from gradio_client import Client

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    demo = nativeprompt.launch_web(
        host="127.0.0.1",
        port=port,
        share=False,
        inbrowser=False,
        prevent_thread_lock=True,
    )
    assert demo is not None
    actual_port = getattr(demo, "server_port", port)
    client = None
    try:
        # Проверяем доступность HTTP эндпоинта через контекстный менеджер
        with urllib.request.urlopen(f"http://127.0.0.1:{actual_port}/") as resp:
            assert resp.status == 200

        # Проверяем реальный вызов API через gradio_client
        client = Client(f"http://127.0.0.1:{actual_port}/")
        res = client.predict(
            prompt="почини баг, думай пошагово",
            model="gpt-5.6",
            api_name="/process_prompt",
        )
        assert isinstance(res, (list, tuple))
        assert len(res) == 2
        assert "почини баг" in res[0]
        assert len(res[1]) > 0
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
        demo.close()


