# -*- coding: utf-8 -*-
"""Линейка GPT-6 целиком: Astra, Sol, Luna.

Про саму Astra есть отдельный файл — `test_astra.py`, он про её поведение и
детектор пишущих задач. Здесь про то, что линейка стала семейством из трёх
моделей: у Sol и Luna общий с Astra гайд промптинга (вендор пишет это прямо),
а различия между ними — рантаймовые, к тексту промпта отношения не имеющие.

Отдельный сюжет — переиспользованные имена. Sol и Luna были в GPT-5.6 и
остались в GPT-6, значит одно и то же слово указывает на разные поколения, и
отличает их только версия перед ним.
"""

import json
import os

import pytest

from nativeprompt.analyze import analyze
from nativeprompt.catalog import scopes_for
from nativeprompt.detect import resolve
from nativeprompt.explain import build_report

КОРЕНЬ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ПРАВИЛА = json.load(open(os.path.join(КОРЕНЬ, "nativeprompt", "rules", "openai.json"),
                         encoding="utf-8"))
ЛИНЕЙКА = ("gpt-6-astra", "gpt-6-sol", "gpt-6-luna")


def ids(промпт, модель):
    return {f["id"] for f in analyze(промпт, resolve(модель))}


# ── поколения ───────────────────────────────────────────────────────────
@pytest.mark.parametrize("что_ввели,ожидаем", [
    ("gpt-6-astra", "gpt-6-astra"),
    ("gpt-6-sol", "gpt-6-sol"),
    ("gpt-6-luna", "gpt-6-luna"),
    ("GPT-6-Sol", "gpt-6-sol"),
    ("openai/gpt-6-luna", "gpt-6-luna"),
    ("gpt-6", "gpt-6-astra"),          # без уточнения — старшая модель линейки
])
def test_модель_линейки_опознаётся(что_ввели, ожидаем):
    t = resolve(что_ввели)
    assert t["family"] == "openai", "%s ушло не в openai: %s" % (что_ввели, t)
    assert t["generation"] == ожидаем, (
        "%s опознано как %r, ждали %r" % (что_ввели, t.get("generation"), ожидаем))


def test_sol_и_luna_стоят_выше_astra():
    """Токен «gpt-6» у Astra — подстрока «gpt-6-sol».

    `generation_for` возвращает первое совпадение по порядку файла, поэтому
    порядок здесь и есть вся защита: окажись Astra выше — Sol и Luna молча
    читались бы как Astra, и человек увидел бы в отчёте чужое имя модели.
    """
    ключи = list(ПРАВИЛА["generations"])
    for младшая in ("gpt-6-sol", "gpt-6-luna"):
        assert ключи.index(младшая) < ключи.index("gpt-6-astra"), (
            "%s стоит ниже astra и будет опознаваться как она: %s" % (младшая, ключи))


@pytest.mark.parametrize("версия,ожидаем", [
    ("gpt-6-sol", "gpt-6-sol"),
    ("gpt-5.6-sol", "gpt-5.6"),
    ("gpt-6-luna", "gpt-6-luna"),
    ("gpt-5.6-luna", "gpt-5.6"),
])
def test_переиспользованные_имена_разводятся_по_версии(версия, ожидаем):
    """Sol и Luna есть в обоих поколениях — различает только номер версии."""
    assert resolve(версия)["generation"] == ожидаем, resolve(версия)


def test_поколение_5_6_предупреждает_про_совпадение_имён():
    """Иначе человек напишет «sol» и не узнает, какое поколение ему ответило."""
    note = ПРАВИЛА["generations"]["gpt-5.6"]["note"].lower()
    assert "sol" in note and "версию" in note, note


# ── общий гайд ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("поколение", ["gpt-6-sol", "gpt-6-luna"])
def test_правила_astra_наследуются_младшими(поколение):
    """Вендор пишет: приведённые промпты — отправная точка для всей линейки.

    Это не наша догадка про похожесть моделей, а фраза из гайда, и выражается
    она полем `rules_of`, а не копией правил под каждую модель.
    """
    assert ПРАВИЛА["generations"][поколение]["rules_of"] == "gpt-6-astra"
    assert {поколение, "gpt-6-astra"} <= scopes_for("openai", поколение)


@pytest.mark.parametrize("модель", ЛИНЕЙКА)
def test_правило_про_инициативу_горит_на_всей_линейке(модель):
    assert "astra-bias-to-action" in ids("поправь верстку на главной", модель)


def test_правила_линейки_не_горят_на_прошлом_поколении():
    """Поведение описано вендором для GPT-6. На 5.6 это был бы шум."""
    assert "astra-bias-to-action" not in ids("поправь верстку на главной", "gpt-5.6")


@pytest.mark.parametrize("поколение", ЛИНЕЙКА)
def test_у_каждой_модели_линейки_есть_ссылка_на_гайд(поколение):
    g = ПРАВИЛА["generations"][поколение]
    assert g["doc"].startswith("https://developers.openai.com/"), g
    assert "gpt-6-astra" in g["doc"], (
        "%s: ссылка ведёт не на гайд линейки: %s" % (поколение, g["doc"]))


def test_ссылки_правил_закреплены_за_моделью_а_не_за_словом_latest():
    """Адрес `latest-model` без имени модели переедет на следующий релиз.

    Вместе с ним переедут и якоря разделов, а правило будет ссылаться на текст
    про другую модель — молча, без единой ошибки.
    """
    for r in ПРАВИЛА["rules"]:
        if r.get("scope") != "gpt-6-astra":
            continue
        assert "latest-model/gpt-6-astra" in r["source"], (
            "%s ссылается на скользящий адрес: %s" % (r["id"], r["source"]))


@pytest.mark.parametrize("поколение", ["gpt-6-sol", "gpt-6-luna"])
def test_различие_по_рантайму_названо(поколение):
    """`none` у Astra нет, а у Sol и Luna есть — и это единственное, чем они
    отличаются в настройке. Не сказать об этом значит оставить человека
    переносить с Astra настройку, которая там была невозможна."""
    assert "none" in ПРАВИЛА["generations"][поколение]["note"], (
        ПРАВИЛА["generations"][поколение]["note"])


def test_config_notes_называют_ограничение_astra_по_effort():
    notes = " ".join(ПРАВИЛА["config_notes"])
    assert "none" in notes and "Astra" in notes, notes


# ── отчёт целиком ───────────────────────────────────────────────────────
@pytest.mark.parametrize("модель", ЛИНЕЙКА)
def test_отчёт_собирается_и_называет_модель(модель):
    r = build_report("можешь посмотреть, что не так с логином?", модель)
    assert r["meta"]["generation"] == модель
    assert r["improved"], "пустой результат"
