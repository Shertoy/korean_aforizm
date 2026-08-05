import os
import io
import random
import threading
import requests
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont

from quotes import QUOTES, get_random_quote as get_local_quote

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
TRIGGER_SECRET = os.environ.get("TRIGGER_SECRET")
ADMIN_SECRET = os.environ.get("ADMIN_SECRET")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_KR_BOLD     = os.path.join(BASE_DIR, "Pretendard-Bold.otf")
FONT_KR_SEMI     = os.path.join(BASE_DIR, "Pretendard-SemiBold.otf")
FONT_LATIN       = os.path.join(BASE_DIR, "NotoSans.ttf")
FONT_LATIN_BOLD  = os.path.join(BASE_DIR, "NotoSans-Bold.ttf")

IMG_W = IMG_H = 1080   # 1:1 format

TEXT_MODEL_FALLBACKS = [
    "gemini-2.5-flash-lite", "gemini-flash-latest",
    "gemini-2.5-flash", "gemini-2.0-flash",
]
_text_model = None
_bad_models: set = set()

app = Flask(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI MODEL
# ─────────────────────────────────────────────────────────────────────────────

def _get_text_model(force: bool = False) -> str:
    global _text_model
    if _text_model and not force and _text_model not in _bad_models:
        return _text_model
    r = requests.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        headers={"x-goog-api-key": GEMINI_API_KEY}, timeout=30,
    )
    r.raise_for_status()
    available = {
        m["name"].replace("models/", "")
        for m in r.json().get("models", [])
        if "generateContent" in m.get("supportedGenerationMethods", [])
    } - _bad_models
    for c in TEXT_MODEL_FALLBACKS:
        if c in available:
            _text_model = c
            return c
    _text_model = sorted(n for n in available if "flash" in n)[0]
    return _text_model


def _gemini(prompt: str, search: bool = False, temp: float = 0.5) -> str:
    import time
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 2048, "temperature": temp},
    }
    if search:
        body["tools"] = [{"google_search": {}}]
    for attempt in range(5):
        model = _get_text_model()
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
            json=body, timeout=90,
        )
        if r.status_code == 404:
            _bad_models.add(model); _get_text_model(force=True); continue
        if r.status_code == 429:
            time.sleep(20 * (attempt + 1)); continue
        r.raise_for_status()
        parts = r.json()["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()
    raise RuntimeError("Gemini 5 urinishdan keyin ham muvaffaqiyatsiz")


# ─────────────────────────────────────────────────────────────────────────────
# SUPABASE
# ─────────────────────────────────────────────────────────────────────────────

def _sb_headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}


def _sb_get_used() -> list:
    if not (SUPABASE_URL and SUPABASE_KEY):
        return []
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/quotes",
        params={"select": "korean"}, headers=_sb_headers(), timeout=20,
    )
    return [row["korean"] for row in r.json()] if r.ok else []


def _sb_save(entry: dict, slot: str, theme: str):
    import datetime
    payload = {
        "korean": entry["korean"],
        "translation": entry["translation"],
        "breakdown": entry["breakdown"],
        "grammar_note": entry["grammar_note"],
        "mood": entry["mood"],
        "hashtags": entry["hashtags"],
        "slot": slot,
        "theme": theme,
        "reflection": entry.get("reflection"),
        "reflection_ko": entry.get("reflection_ko"),
        "caption_ko": entry.get("caption_ko"),
        "last_used_at": str(datetime.date.today()),
        "used_count": 1,
    }
    requests.post(
        f"{SUPABASE_URL}/rest/v1/quotes",
        headers={**_sb_headers(), "Content-Type": "application/json", "Prefer": "return=minimal"},
        json=payload, timeout=20,
    )


# ─────────────────────────────────────────────────────────────────────────────
# JONLI GENERATSIYA
# ─────────────────────────────────────────────────────────────────────────────

ERTALAB_THEMES = [
    "harakat va boshlanish — bugun erta turish, birinchi qadam",
    "sabr va izchillik — qiyin damda davom etish",
    "umid — mashaqqatdan keyin kelajak yorqin",
    "kamtarlik — bilsang ham, e'tibor bilan",
    "vaqt — bugun o'tgan kun qaytmaydi",
    "o'z-o'ziga ishonch — o'zing yetarliasan",
]

KECHQURUN_THEMES = [
    "minnatdorchilik — bugun qiyinchilikka qaramay tiriksan, bu yetarli",
    "yaqinlar — ota-onang tirikmi? qo'ng'iroq qil",
    "o'sish — kitob o'qi, davra kengay, ichkilik yechim emas",
    "empatsiya — seniki katta ko'rinadi, lekin dunyo kattaroq",
    "amaliy qadam — biror to'garakka kir, to'xtama",
    "o'z qadringni bil — kim bo'lsang ham eng zo'ri bo'l",
    "dam — bugungi mehnatga rahmat, erta yangi kun",
]


def _extract_json(text: str) -> dict:
    import json
    t = text.strip()
    if "```" in t:
        t = t.split("```")[1]
        if t.startswith("json"): t = t[4:]
    return json.loads(t.strip())


def generate_live_quote(slot: str) -> dict:
    used = _sb_get_used()
    themes = ERTALAB_THEMES if slot == "ertalab" else KECHQURUN_THEMES
    random.shuffle(themes)

    reflection_field = ""
    if slot == "kechqurun":
        reflection_field = """
  "reflection_ko": "kechqurun o'quvchini mulohazaga undaydigan, xulosasi oldindan belgilanmagan ochiq savol — KOREYS TILIDA (한국어). Bugun o'zingizga yaxshilik qildingizmi? kabi samimiy savol.",
  "caption_ko": "koreyscha 3-5 qatorli chuqur, dalda beruvchi, mulohazaga undaydigan matn — KOREYS TILIDA. Odam o'qiganda ko'ngli yumshaydigan, ulashgisi keladigan darajada. Bugun ham tiriksan, bu sovg'a. Ota-onangga qo'ng'iroq qil. kabi mazmunga yaqin.","""

    for theme in themes:
        try:
            prompt = f"""
Senga "{theme}" mavzusida, "{slot}" vaqti uchun mos HAQIQIY va KENG TARQALGAN
koreys xalq maqoli, 속담 yoki 한자성어 top.

MUHIM: Faqat haqiqiy, keng tarqalgan maqollarni yoz. To'qima, fabrikatsiya qilma.
Quyidagilar allaqachon ishlatilgan, ularni TAKRORLAMA: {used[:20]}

Faqat JSON qaytar, boshqa hech narsa yozma:
{{
  "korean": "koreyscha asl matn",
  "translation": "o'zbekcha tabiiy, ravon tarjima",
  "breakdown": [["so'z (talaffuz)", "o'zbekcha ma'nosi"], ...],
  "grammar_note": "eng muhim grammatik qo'shimcha yoki qolip haqida o'zbekcha izoh (2-3 jumla)",
  "mood": "rasm foni uchun inglizcha kayfiyat va sahna tavsifi — 20-30 so'z, hi-tech futuristik uslub",
  "hashtags": ["#tag1", "#tag2", "#tag3"]{reflection_field}
}}
"""
            raw = _gemini(prompt, search=False, temp=0.6)
            entry = _extract_json(raw)
            if entry.get("korean") and entry["korean"] not in used:
                entry["slot"] = slot
                entry["theme"] = theme
                return entry
        except Exception as e:
            print(f"[generate_live_quote] {theme} — xato: {e}", flush=True)
            continue

    raise RuntimeError("Barcha mavzular uchun generatsiya muvaffaqiyatsiz")


# ─────────────────────────────────────────────────────────────────────────────
# QUOTE TANLASH (3 bosqichli: jonli -> baza -> mahalliy)
# ─────────────────────────────────────────────────────────────────────────────

def get_quote_for_slot(slot: str) -> dict:
    import datetime

    # 1-BOSQICH: jonli generatsiya
    if GEMINI_API_KEY:
        try:
            entry = generate_live_quote(slot)
            if SUPABASE_URL and SUPABASE_KEY:
                _sb_save(entry, slot, entry.get("theme", ""))
            print(f"[quote] YANGI: {entry['korean']}", flush=True)
            return entry
        except Exception as e:
            print(f"[quote] Jonli generatsiya muvaffaqiyatsiz: {e}", flush=True)

    # 2-BOSQICH: Supabase bazasidan eng kam ishlatilgan
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            r = requests.get(
                f"{SUPABASE_URL}/rest/v1/quotes",
                params={"slot": f"eq.{slot}", "select": "*",
                        "order": "used_count.asc,last_used_at.asc.nullsfirst", "limit": "1"},
                headers=_sb_headers(), timeout=20,
            )
            rows = r.json() if r.ok else []
            if rows:
                row = rows[0]
                requests.patch(
                    f"{SUPABASE_URL}/rest/v1/quotes",
                    params={"id": f"eq.{row['id']}"},
                    headers={**_sb_headers(), "Content-Type": "application/json", "Prefer": "return=minimal"},
                    json={"used_count": (row.get("used_count") or 0) + 1,
                          "last_used_at": str(datetime.date.today())},
                    timeout=20,
                )
                print(f"[quote] BAZA: {row['korean']}", flush=True)
                return row
        except Exception as e:
            print(f"[quote] Baza xato: {e}", flush=True)

    # 3-BOSQICH: mahalliy
    print("[quote] Mahalliy ro'yxatga (fallback) o'tildi", flush=True)
    return get_local_quote(slot)


# ─────────────────────────────────────────────────────────────────────────────
# RASM GENERATSIYASI (Pollinations.ai — bepul, API kalit shart emas)
# ─────────────────────────────────────────────────────────────────────────────

def generate_background(mood: str) -> bytes:
    prompt = (
        f"{mood}, hyper-detailed cinematic digital art, futuristic sci-fi atmosphere, "
        "dramatic volumetric lighting, ultra realistic 8k octane render, "
        "square 1:1 composition, dark cinematic color grading, "
        "open empty center for text overlay, no text no letters, breathtaking concept art"
    )
    seed = random.randint(1, 1_000_000)
    url = (
        f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
        f"?width={IMG_W}&height={IMG_H}&seed={seed}&nologo=true"
    )
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    if "image" not in r.headers.get("Content-Type", ""):
        raise RuntimeError(f"Rasm kelmadi: {r.text[:200]}")
    return r.content


# ─────────────────────────────────────────────────────────────────────────────
# MATNNI RASMGA CHIZISH (Pillow — to'liq nazorat)
# ─────────────────────────────────────────────────────────────────────────────

def _wrap(draw, text, font, max_w, stroke=0):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textbbox((0,0), test, font=font, stroke_width=stroke)[2] <= max_w or not cur:
            cur = test
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def _draw_lines(draw, lines, font, y, img_w, fill, lh, stroke=3):
    for line in lines:
        bb = draw.textbbox((0,0), line, font=font, stroke_width=stroke)
        x = (img_w - (bb[2]-bb[0])) / 2
        draw.text((x, y), line, font=font, fill=fill,
                  stroke_width=stroke, stroke_fill=(0,0,0,220))
        y += lh
    return y


def render_image(bg_bytes: bytes, quote: dict) -> bytes:
    img = Image.open(io.BytesIO(bg_bytes)).convert("RGB").resize((IMG_W, IMG_H))

    # Pastki qora gradient (matn joyi uchun)
    ov = Image.new("RGBA", img.size, (0,0,0,0))
    d  = ImageDraw.Draw(ov)
    h2 = IMG_H // 2
    for i in range(h2):
        alpha = int(200 * (i/h2)**1.8)
        d.line([(0, IMG_H-h2+i),(IMG_W, IMG_H-h2+i)], fill=(0,0,0,alpha))
    img = Image.alpha_composite(img.convert("RGBA"), ov)
    draw = ImageDraw.Draw(img, "RGBA")

    margin = 60
    max_w  = IMG_W - margin * 2

    # @korean_aforizm — yuqori markazda
    wf = ImageFont.truetype(FONT_LATIN_BOLD, 26)
    wt = "@korean_aforizm"
    wb = draw.textbbox((0,0), wt, font=wf)
    ww, wh = wb[2]-wb[0], wb[3]-wb[1]
    wx = (IMG_W - ww) / 2
    wy = 48
    draw.rounded_rectangle([wx-22,wy-12,wx+ww+22,wy+wh+16],
                           radius=24, fill=(0,0,0,150))
    draw.text((wx, wy-wb[1]), wt, font=wf, fill=(255,255,255,240))

    # Koreyscha matn — pastki yarida, markazda, KATTA
    fnt = ImageFont.truetype(FONT_KR_BOLD, 80)
    lines = _wrap(draw, quote["korean"], fnt, max_w, stroke=3)
    lh = int(80 * 1.4)
    total_h = len(lines) * lh
    y = IMG_H - total_h - 110
    _draw_lines(draw, lines, fnt, y, IMG_W, fill=(255,255,255,255), lh=lh, stroke=3)

    out = io.BytesIO()
    img.convert("RGB").save(out, format="JPEG", quality=93)
    return out.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# CAPTION YARATISH
# ─────────────────────────────────────────────────────────────────────────────

def build_caption(quote: dict, slot: str) -> str:
    lines = []

    if slot == "ertalab":
        # Ertalab: tarjima + grammatika + hashtag
        lines.append(f"🇰🇷 {quote['korean']}")
        lines.append(f"🇺🇿 {quote['translation']}")
        lines.append("")
        lines.append("📖 So'zma-so'z:")
        bd = quote.get("breakdown", [])
        if isinstance(bd, list):
            for item in bd:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    lines.append(f"  • {item[0]} — {item[1]}")
        lines.append("")
        lines.append("📌 Grammatika:")
        lines.append(quote.get("grammar_note", ""))
    else:
        # Kechqurun: koreyscha chuqur matn (caption_ko) + tarjima + grammatika
        caption_ko = quote.get("caption_ko") or quote.get("reflection_ko") or ""
        if caption_ko:
            lines.append(caption_ko)
            lines.append("")
        lines.append("─" * 20)
        lines.append(f"🇰🇷 {quote['korean']}")
        lines.append(f"🇺🇿 {quote['translation']}")
        lines.append("")
        lines.append("📖 So'zma-so'z:")
        bd = quote.get("breakdown", [])
        if isinstance(bd, list):
            for item in bd:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    lines.append(f"  • {item[0]} — {item[1]}")
        lines.append("")
        lines.append("📌 Grammatika:")
        lines.append(quote.get("grammar_note", ""))

    lines.append("")
    hashtags = quote.get("hashtags", [])
    if isinstance(hashtags, list):
        lines.append(" ".join(hashtags))

    lines.append("")
    lines.append("Alisher Asqad Ali\n@korean_aforizm")

    caption = "\n".join(lines)
    return caption[:1024]


# ─────────────────────────────────────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────────────────────────────────────

def send_to_telegram(image_bytes: bytes, caption: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    r = requests.post(
        url,
        data={"chat_id": TELEGRAM_CHANNEL_ID, "caption": caption},
        files={"photo": ("post.jpg", io.BytesIO(image_bytes), "image/jpeg")},
        timeout=60,
    )
    if not r.ok:
        raise RuntimeError(f"Telegram xato: {r.status_code} {r.text}")


# ─────────────────────────────────────────────────────────────────────────────
# ASOSIY JARAYON
# ─────────────────────────────────────────────────────────────────────────────

def do_post(slot: str):
    try:
        quote   = get_quote_for_slot(slot)
        bg      = generate_background(quote.get("mood", "beautiful landscape"))
        image   = render_image(bg, quote)
        caption = build_caption(quote, slot)
        send_to_telegram(image, caption)
        print(f"[{slot}] Post yuborildi: {quote['korean']}", flush=True)
    except Exception as e:
        print(f"[{slot}] XATO: {e}", flush=True)


def do_generate(count: int):
    from generate_quotes import generate_new_quotes
    print(f"[generate] BOSHLANDI (count={count})", flush=True)
    try:
        generate_new_quotes(count=count)
    except Exception as e:
        print(f"[generate] XATO: {e}", flush=True)
    print("[generate] TUGADI", flush=True)


# ─────────────────────────────────────────────────────────────────────────────
# FLASK ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return "Korean Aforizm bot ishlayapti."


@app.route("/trigger/<slot>")
def trigger(slot):
    if TRIGGER_SECRET and request.args.get("key") != TRIGGER_SECRET:
        return jsonify({"error": "Noto'g'ri kalit"}), 403
    if slot not in ("ertalab", "kechqurun"):
        return jsonify({"error": "slot 'ertalab' yoki 'kechqurun' bo'lishi kerak"}), 400
    threading.Thread(target=do_post, args=(slot,), daemon=True).start()
    return jsonify({"status": "started", "slot": slot})


@app.route("/generate_quotes")
def generate_quotes_route():
    if not ADMIN_SECRET or request.args.get("key") != ADMIN_SECRET:
        return jsonify({"error": "Noto'g'ri admin kalit"}), 403
    count = int(request.args.get("count", 3))
    threading.Thread(target=do_generate, args=(count,), daemon=True).start()
    return jsonify({"status": "started", "message": "Orqa fonda ishlamoqda. Render Logs'dan tekshiring."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
