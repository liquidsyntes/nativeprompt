"""nativeprompt — перепиши промпт на РОДНОЙ диалект той модели/CLI, которой ты
реально пользуешься (Claude Code, Codex, Gemini CLI, Grok, Kimi, Qwen), строго по ОФИЦИАЛЬНЫМ правилам вендора,
и объясни почему.

Zero-deps, stdlib-only, детерминированное ядро. См. README.md.
"""

__version__ = "0.8.1"

from .catalog import load_family, available_families, RulesError
from .detect import detect_model
from .analyze import analyze, task_shape
from .harness import recommend_harness
from .rewrite import rewrite, build_metaprompt
from .explain import build_report, render_report


def create_app(*args, **kwargs):
    from .web import create_app as _create_app
    return _create_app(*args, **kwargs)


def create_ui(*args, **kwargs):
    from .web import create_ui as _create_ui
    return _create_ui(*args, **kwargs)


def process_prompt(*args, **kwargs):
    from .web import process_prompt as _process_prompt
    return _process_prompt(*args, **kwargs)


def launch_web(*args, **kwargs):
    from .web import launch_web as _launch_web
    return _launch_web(*args, **kwargs)


__all__ = [
    "__version__",
    "load_family",
    "available_families",
    "RulesError",
    "detect_model",
    "analyze",
    "task_shape",
    "recommend_harness",
    "rewrite",
    "build_metaprompt",
    "build_report",
    "render_report",
    "create_app",
    "create_ui",
    "process_prompt",
    "launch_web",
]

