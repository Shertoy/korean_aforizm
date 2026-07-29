# -*- coding: utf-8 -*-
"""
Har hafta (yoki admin chaqirganda) yangi, tasdiqlangan koreys ibora/iqtibos
qidiradi, ikki bosqichda tekshiradi (haqiqiylik + imlo), va Supabase'ga
qo'shadi. Hech qachon avtomatik ravishda kanalga to'g'ridan-to'g'ri
post qilmaydi -- faqat bazani to'ldiradi, botning asosiy oqimi (post_bot_korean.py)
keyin shu bazadan foydalanadi.
"""
import os
import json
import requests

import time
import random

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

TEXT_MODEL_FALLBACKS = [
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]
_bad_models = set()


def _get_model(force_refresh: bool = False) -> str:
    global _cached_model
    if _cached_model and not force_refresh and _cached_model not in _bad_models:
        return _cached_model
    response = requests.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        headers={"x-goog-api-key": GEMINI_API_KEY},
        timeout=30,
    )
    response.raise_for_status()
    available = {
        m.get("name", "").replace("models/", "")
        for m in response.json().get("models", [])
        if "generateContent" in m.get("supportedGenerationMethods", [])
    } - _bad_models
    for candidate in TEXT_MODEL_FALLBACKS:
        if candidate in available:
            _cached_model = candidate
            return candidate
    flash = sorted(n for n in available if "flash" in n)
    _cached_model = flash[0] if flash else sorted(available)[0]
    return _cached_model

THEMES = [
    ("ertalab", "harakat va boshlanish"),
    ("ertalab", "sabr va izchillik"),
    ("ertalab", "umid va yaxshilikka ishonch"),
    ("kechqurun", "o'z-o'ziga mehr va dam olish"),
    ("kechqurun", "vaqt va o'tkinchilik haqida mulohaza"),
    ("kechqurun", "insoniy munosabatlar va minnatdorchilik"),
]


def _call_gemini(prompt: str, use_search: bool = False, temperature: float = 0.4) -> str:
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 1024, "temperature": temperature},
    }
    if use_search:
        body["tools"] = [{"google_search": {}}]

    for attempt in range(4):
        model = _get_model()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        response = requests.post(
            url,
            headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
            json=body,
            timeout=60,
        )
        if response.status_code == 404:
            _bad_models.add(model)
            global _cached_model
            _cached_model = None
            _get_model(force_refresh=True)
            continue
        if response.status_code == 429:
            time.sleep(15 * (attempt + 1))  # bepul tarif chegarasiga hurmat - kutib, qayta urinish
            continue
        response.raise_for_status()
        data = response.json()
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()

    raise RuntimeError("Gemini so'rov 4 urinishdan keyin ham muvaffaqiyatsiz (model yoki rate limit muammosi)")


def _get_existing_korean_texts() -> list:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/quotes?select=korean",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
        timeout=30,
    )
    response.raise_for_status()
    return [row["korean"] for row in response.json()]


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


# ---------------------------------------------------------------------------
# 1-BOSQICH: HAQIQIY IBORA QIDIRISH (Google Search bilan tasdiqlangan)
# ---------------------------------------------------------------------------

def find_candidate(slot: str, theme: str, existing: list) -> dict:
    reflection_instruction = ""
    if slot == "kechqurun":
        reflection_instruction = (
            '\n"reflection_uzbek": "o\'quvchini mulohaza qilishga undaydigan, '
            'xulosasi oldindan belgilanmagan ochiq savol (o\'zbekcha)",'
            '\n"reflection_ko": "xuddi shu savolning tabiiy, to\'g\'ri koreyscha tarjimasi (한국어)",'
        )
    prompt = f"""
Menga "{theme}" mavzusida, {slot} vaqti uchun mos, HAQIQIY va KENG TARQALGAN
koreys xalq maqoli, 한자성어 (idioma) yoki keng qo'llaniladigan hikmatli ibora top.

Google qidiruv orqali uning haqiqatan koreys tilida keng ishlatilishini
TEKSHIR. Fabrikatsiya qilma, o'zing to'qima.

Quyidagilar ALLAQACHON ishlatilgan, ularni TAKRORLAMA:
{existing}

Faqat quyidagi JSON formatda javob ber, boshqa hech narsa yozma:
{{
  "korean": "koreyscha asl matn",
  "translation_uzbek": "o'zbekcha tabiiy tarjima",
  "breakdown": [["koreyscha bo'lak (talaffuz)", "o'zbekcha ma'no"], ...],
  "grammar_note": "eng muhim grammatik qo'shimcha yoki qolip haqida o'zbekcha izoh",
  "mood": "rasm foni uchun inglizcha kayfiyat tavsifi, 15-25 so'z",
  "hashtags": ["#mavzu1", "#mavzu2", "#mavzu3"]{reflection_instruction}
}}
"""
    raw = _call_gemini(prompt, use_search=True, temperature=0.5)
    return _extract_json(raw)


# ---------------------------------------------------------------------------
# 2-BOSQICH: IMLO VA GRAMMATIKA TEKSHIRUVI (alohida, mustaqil so'rov)
# ---------------------------------------------------------------------------

def spellcheck_korean(korean_text: str) -> dict:
    prompt = f"""
Quyidagi koreyscha matnni 맞춤법 (imlo) va grammatika jihatidan tekshir:

"{korean_text}"

Faqat JSON qaytar:
{{"is_correct": true yoki false, "corrected": "agar xato bo'lsa to'g'irlangan matn, aks holda asl matn", "note": "qisqa izoh"}}
"""
    raw = _call_gemini(prompt, use_search=False, temperature=0.0)
    return _extract_json(raw)


# ---------------------------------------------------------------------------
# 3-BOSQICH: SUPABASE'GA SAQLASH
# ---------------------------------------------------------------------------

def save_to_supabase(entry: dict, slot: str, theme: str) -> None:
    payload = {
        "korean": entry["korean"],
        "translation": entry["translation_uzbek"],
        "breakdown": entry["breakdown"],
        "grammar_note": entry["grammar_note"],
        "mood": entry["mood"],
        "hashtags": entry["hashtags"],
        "slot": slot,
        "theme": theme,
        "reflection": entry.get("reflection_uzbek"),
        "reflection_ko": entry.get("reflection_ko"),
    }
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/quotes",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        json=payload,
        timeout=30,
    )
    response.raise_for_status()


# ---------------------------------------------------------------------------
# ASOSIY JARAYON
# ---------------------------------------------------------------------------

def generate_live_quote(slot: str) -> dict:
    """Har bir /trigger chaqirilganda ISHGA TUSHADI: yangi mavzu tanlaydi,
    haqiqiy va tasdiqlangan koreys ibora/iqtibos qidiradi, imlosini
    tekshiradi. Faqat ikkala tekshiruvdan o'tgan matn qaytariladi."""
    existing = _get_existing_korean_texts() if (SUPABASE_URL and SUPABASE_KEY) else []
    themes = [t for s, t in THEMES if s == slot]
    random.shuffle(themes)
    last_error = None
    for theme in themes:
        for _ in range(2):
            try:
                candidate = find_candidate(slot, theme, existing)
                korean_text = candidate["korean"]
                if korean_text in existing:
                    continue
                check = spellcheck_korean(korean_text)
                if not check.get("is_correct", False):
                    print(f"[generate_live_quote] Imlo xatosi tufayli rad etildi: {korean_text}", flush=True)
                    continue
                candidate["theme"] = theme
                return candidate
            except Exception as e:
                last_error = e
                time.sleep(2)
                continue
    raise RuntimeError(f"Jonli generatsiya muvaffaqiyatsiz bo'ldi: {last_error}")


def generate_new_quotes(count: int = 3) -> list:
    """count ta yangi, tasdiqlangan, imlosi to'g'ri yozuvni bazaga qo'shadi.
    Har biri natijasini (muvaffaqiyatli/xato) ro'yxat qilib qaytaradi."""
    results = []
    existing = _get_existing_korean_texts()
    theme_cycle = THEMES * 3  # yetarlicha urinish imkoniyati

    added = 0
    consecutive_errors = 0
    for slot, theme in theme_cycle:
        if added >= count:
            break
        if consecutive_errors >= 4:
            entry = {"status": "stopped", "note": "Ketma-ket xatolar ko'p, to'xtatildi. Birozdan keyin qayta urinib ko'ring."}
            results.append(entry)
            print(f"[generate_quotes] {entry}", flush=True)
            break
        try:
            candidate = find_candidate(slot, theme, existing)
            korean_text = candidate["korean"]

            if korean_text in existing:
                entry = {"status": "skipped_duplicate", "korean": korean_text}
                results.append(entry)
                print(f"[generate_quotes] {entry}", flush=True)
                consecutive_errors = 0
                time.sleep(3)
                continue

            check = spellcheck_korean(korean_text)
            if not check.get("is_correct", False):
                entry = {
                    "status": "rejected_spelling",
                    "korean": korean_text,
                    "note": check.get("note"),
                }
                results.append(entry)
                print(f"[generate_quotes] {entry}", flush=True)
                consecutive_errors = 0
                time.sleep(3)
                continue

            save_to_supabase(candidate, slot, theme)
            existing.append(korean_text)
            added += 1
            consecutive_errors = 0
            entry = {"status": "added", "korean": korean_text, "slot": slot, "theme": theme}
            results.append(entry)
            print(f"[generate_quotes] {entry}", flush=True)
            time.sleep(3)  # Gemini bepul tarif chegarasiga hurmat
        except Exception as e:
            consecutive_errors += 1
            entry = {"status": "error", "error": str(e)}
            results.append(entry)
            print(f"[generate_quotes] {entry}", flush=True)
            time.sleep(5)

    return results
