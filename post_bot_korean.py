import os
import io
import random
import textwrap
import threading
import requests
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from quotes import QUOTES, get_random_quote as get_local_quote


def get_quote_for_slot(slot: str) -> dict:
    """Avval Supabase'dan urinadi (agar sozlangan bo'lsa), aks holda
    quotes.py'dagi mahalliy ro'yxatga qaytadi. Ikkalasida ham sana asosida
    aylanma tanlaydi, shu sabab ketma-ket kunlar takrorlanmaydi."""
    import datetime
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/quotes",
                params={"slot": f"eq.{slot}", "select": "*", "order": "id.asc"},
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
                timeout=20,
            )
            response.raise_for_status()
            rows = response.json()
            if rows:
                idx = datetime.date.today().toordinal() % len(rows)
                row = rows[idx]
                return {
                    "korean": row["korean"],
                    "translation": row["translation"],
                    "breakdown": row["breakdown"],
                    "grammar_note": row["grammar_note"],
                    "reflection": row.get("reflection"),
                    "reflection_ko": row.get("reflection_ko"),
                    "mood": row["mood"],
                    "hashtags": row["hashtags"],
                }
        except Exception as e:
            print(f"Supabase'dan o'qishda xato, mahalliy ro'yxatga o'tildi: {e}")
    return get_local_quote(slot)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")  # @korean_aforizm
TRIGGER_SECRET = os.environ.get("TRIGGER_SECRET")
ADMIN_SECRET = os.environ.get("ADMIN_SECRET")  # /discover_quote, /generate_quotes uchun
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

SIGNATURE = "\n\nAlisher Asqad Ali\n@korean_aforizm"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_KOREAN = os.path.join(BASE_DIR, "Pretendard-Bold.otf")  # Koreyada eng ko'p ishlatiladigan zamonaviy shrift
FONT_KOREAN_SEMIBOLD = os.path.join(BASE_DIR, "Pretendard-SemiBold.otf")
FONT_LATIN = os.path.join(BASE_DIR, "NotoSans.ttf")
FONT_LATIN_BOLD = os.path.join(BASE_DIR, "NotoSans-Bold.ttf")

# 9:16 hajm (Instagram/Telegram story formatiga mos)
IMG_W, IMG_H = 1080, 1920

app = Flask(__name__)

TEXT_MODEL_FALLBACKS = [
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]
_cached_text_model = None
_known_bad_models = set()


def get_working_text_model() -> str:
    global _cached_text_model
    if _cached_text_model and _cached_text_model not in _known_bad_models:
        return _cached_text_model
    response = requests.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        headers={"x-goog-api-key": GEMINI_API_KEY},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    available = {
        m.get("name", "").replace("models/", "")
        for m in data.get("models", [])
        if "generateContent" in m.get("supportedGenerationMethods", [])
    } - _known_bad_models
    for candidate in TEXT_MODEL_FALLBACKS:
        if candidate in available:
            _cached_text_model = candidate
            return candidate
    flash = sorted(n for n in available if "flash" in n)
    if flash:
        _cached_text_model = flash[0]
        return flash[0]
    if available:
        _cached_text_model = sorted(available)[0]
        return _cached_text_model
    raise RuntimeError("Hech qanday ishlaydigan Gemini modeli topilmadi.")


# ---------------------------------------------------------------------------
# RASM FONI GENERATSIYASI (matn AI orqali chizilmaydi - faqat fon)
# ---------------------------------------------------------------------------

def generate_background_image(mood: str) -> bytes:
    prompt = (
        f"{mood}, hyper-detailed cinematic digital art, futuristic "
        "sci-fi atmosphere, dramatic volumetric lighting, ultra realistic "
        "render, 8k octane render quality, awe-inspiring epic scale, "
        "vertical portrait composition, dark cinematic color grading, "
        "clear open negative space in the upper third and center for text "
        "overlay, no text or letters in the image, breathtaking concept art"
    )
    encoded = requests.utils.quote(prompt)
    seed = random.randint(1, 1_000_000)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={IMG_W}&height={IMG_H}&seed={seed}&nologo=true"
    )
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    if "image" not in response.headers.get("Content-Type", ""):
        raise RuntimeError(f"Rasm o'rniga boshqa javob keldi: {response.text[:200]}")
    return response.content


# ---------------------------------------------------------------------------
# MATNNI RASMGA DASTURIY CHIZISH (Pillow) - to'liq nazorat, xato yo'q
# ---------------------------------------------------------------------------

def _fit_font(draw, text, font_path, max_width, start_size, min_size=28):
    """Matn max_width'ga sig'guncha shrift o'lchamini kamaytiradi."""
    size = start_size
    while size > min_size:
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(font_path, min_size)


def _add_gradient_scrim(img):
    """Fon qanday bo'lishidan qat'i nazar matn o'qilishi uchun yuqori va pastki
    qismga qorong'ulashtiruvchi gradient qatlam qo'shadi."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    grad = ImageDraw.Draw(overlay)
    top_h = int(IMG_H * 0.42)
    for i in range(top_h):
        alpha = int(190 * (1 - i / top_h) ** 1.4)
        grad.line([(0, i), (IMG_W, i)], fill=(0, 0, 0, alpha))
    bottom_h = int(IMG_H * 0.35)
    for i in range(bottom_h):
        alpha = int(190 * (1 - i / bottom_h) ** 1.4)
        y = IMG_H - i
        grad.line([(0, y), (IMG_W, y)], fill=(0, 0, 0, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def _wrap_lines(draw, text, font_path, size, max_width, stroke_width=0):
    font = ImageFont.truetype(font_path, size)
    words = text.split(" ")
    lines, current = [], ""
    for w in words:
        test = (current + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=font, stroke_width=stroke_width)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines, font


def _draw_lines_centered(draw, lines, font, y, fill, img_w, line_h, stroke_width=3):
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        w = bbox[2] - bbox[0]
        x = (img_w - w) / 2
        draw.text(
            (x, y), line, font=font, fill=fill,
            stroke_width=stroke_width, stroke_fill=(0, 0, 0, 235),
        )
        y += line_h
    return y


def _draw_centered_wrapped(draw, text, font_path, size, max_width, y, fill,
                            img_w, line_spacing=1.35, stroke_width=3):
    font = ImageFont.truetype(font_path, size)
    words = text.split(" ")
    lines, current = [], ""
    for w in words:
        test = (current + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)

    line_h = int(size * line_spacing)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        w = bbox[2] - bbox[0]
        x = (img_w - w) / 2
        # Qora kontur - fon rangidan qat'i nazar matn har doim o'qiladigan bo'lishi uchun
        draw.text(
            (x, y), line, font=font, fill=fill,
            stroke_width=stroke_width, stroke_fill=(0, 0, 0, 235),
        )
        y += line_h
    return y


def render_quote_image(background_bytes: bytes, quote: dict) -> bytes:
    img = Image.open(io.BytesIO(background_bytes)).convert("RGB")
    if img.size != (IMG_W, IMG_H):
        img = img.resize((IMG_W, IMG_H))

    # Kontrast uchun qorong'ulashtiruvchi gradient
    img = _add_gradient_scrim(img)
    draw = ImageDraw.Draw(img, "RGBA")

    margin = 80
    max_w = IMG_W - margin * 2

    # 1) Kanal nomi - YUQORI MARKAZDA, kichik badge ko'rinishida
    #    (Instagram Reels/Stories'da pastki-chekka UI elementlar bilan
    #    qoplanib qolmasligi uchun)
    wm_font = ImageFont.truetype(FONT_LATIN_BOLD, 36)
    wm_text = "@korean_aforizm"
    bbox = draw.textbbox((0, 0), wm_text, font=wm_font)
    wm_w, wm_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    wx = (IMG_W - wm_w) / 2
    wy = int(IMG_H * 0.045)
    draw.rounded_rectangle(
        [wx - 28, wy - 16, wx + wm_w + 28, wy + wm_h + 24],
        radius=30, fill=(0, 0, 0, 150),
    )
    draw.text((wx, wy - bbox[1]), wm_text, font=wm_font, fill=(255, 255, 255, 245))

    y = int(IMG_H * 0.14)

    # 2) Koreyscha asl matn (Noto Serif KR - Batang uslubiga yaqin)
    y = _draw_centered_wrapped(
        draw, quote["korean"], FONT_KOREAN, 66, max_w, y,
        fill=(255, 255, 255, 255), img_w=IMG_W,
    )
    y += 34

    # 3) O'zbekcha tarjima
    y = _draw_centered_wrapped(
        draw, quote["translation"], FONT_LATIN, 44, max_w, y,
        fill=(255, 214, 130, 255), img_w=IMG_W, stroke_width=2,
    )

    # 4) Kechqurungi post uchun - mulohaza savoli KOREYS TILIDA, pastda ramkada
    #    (auditoriyaning 97% koreys millatiga mansub bo'lgani uchun)
    reflection_text = quote.get("reflection_ko") or quote.get("reflection")
    if reflection_text:
        box_font_size = 42
        box_max_w = max_w - 60
        stroke_w = 2
        lines, rfont = _wrap_lines(
            draw, reflection_text, FONT_KOREAN_SEMIBOLD, box_font_size,
            box_max_w, stroke_width=stroke_w,
        )
        line_h = int(box_font_size * 1.4)
        pad_v = 40
        text_block_h = len(lines) * line_h
        box_h = text_block_h + pad_v * 2
        box_top = int(IMG_H * 0.78) - box_h // 2
        box_bottom = box_top + box_h
        draw.rounded_rectangle(
            [margin - 20, box_top, IMG_W - margin + 20, box_bottom],
            radius=18, fill=(0, 0, 0, 175),
            outline=(255, 214, 130, 210), width=2,
        )
        text_y = box_top + pad_v
        _draw_lines_centered(
            draw, lines, rfont, text_y, fill=(255, 255, 255, 255),
            img_w=IMG_W, line_h=line_h, stroke_width=stroke_w,
        )

    output = io.BytesIO()
    img.convert("RGB").save(output, format="JPEG", quality=92)
    return output.getvalue()


def generate_post_image(quote: dict) -> bytes:
    background = generate_background_image(quote["mood"])
    return render_quote_image(background, quote)


# ---------------------------------------------------------------------------
# CAPTION - FAQAT TILSHUNOSLIK QISMI (so'zma-so'z tarjima + grammatika)
# ---------------------------------------------------------------------------

def build_caption(quote: dict) -> str:
    lines = ["So'zma-so'z tarjima:"]
    for korean_part, meaning in quote["breakdown"]:
        lines.append(f"- {korean_part} — {meaning}")
    lines.append("")
    lines.append("Grammatika izohi:")
    lines.append(quote["grammar_note"])
    lines.append("")
    lines.append(" ".join(quote["hashtags"]))
    caption = "\n".join(lines) + SIGNATURE
    return caption[:1024]  # Telegram caption limiti


# ---------------------------------------------------------------------------
# TELEGRAM'GA YUBORISH
# ---------------------------------------------------------------------------

def send_photo_to_telegram(image_bytes: bytes, caption: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    files = {"photo": ("post.jpg", io.BytesIO(image_bytes), "image/jpeg")}
    data = {"chat_id": TELEGRAM_CHANNEL_ID, "caption": caption}
    response = requests.post(url, data=data, files=files, timeout=60)
    if not response.ok:
        raise RuntimeError(f"Telegram xatosi: {response.status_code} {response.text}")


# ---------------------------------------------------------------------------
# ASOSIY POST JARAYONI
# ---------------------------------------------------------------------------

def do_post(slot: str):
    try:
        quote = get_quote_for_slot(slot)
        image_bytes = generate_post_image(quote)
        caption = build_caption(quote)
        send_photo_to_telegram(image_bytes, caption)
        print(f"[{slot}] Post yuborildi: {quote['korean']}")
    except Exception as e:
        print(f"[{slot}] XATO: {e}")


@app.route("/")
def home():
    return "Koreys iqtiboslar boti ishlayapti. /trigger/<slot>?key=... dan foydalaning."


@app.route("/trigger/<slot>")
def trigger(slot):
    secret = request.args.get("key")
    if TRIGGER_SECRET and secret != TRIGGER_SECRET:
        return jsonify({"error": "Noto'g'ri yoki yo'q kalit"}), 403
    if slot not in ("ertalab", "kechqurun"):
        return jsonify({"error": "slot 'ertalab' yoki 'kechqurun' bo'lishi kerak"}), 400

    missing = [n for n, v in [
        ("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN),
        ("TELEGRAM_CHANNEL_ID", TELEGRAM_CHANNEL_ID),
    ] if not v]
    if missing:
        return jsonify({"error": f"Environment variable topilmadi: {', '.join(missing)}"}), 500

    thread = threading.Thread(target=do_post, args=(slot,), daemon=True)
    thread.start()
    return jsonify({"status": "started", "message": "Post orqa fonda tayyorlanmoqda."})


# ---------------------------------------------------------------------------
# ADMIN: YANGI MAQOL TOPISH (avtomatik post qilinmaydi - faqat taklif beradi,
# siz tekshirib quotes.py ga qo'lda qo'shasiz)
# ---------------------------------------------------------------------------

@app.route("/discover_quote")
def discover_quote():
    secret = request.args.get("key")
    if not ADMIN_SECRET or secret != ADMIN_SECRET:
        return jsonify({"error": "Noto'g'ri yoki yo'q admin kaliti"}), 403

    existing = [q["korean"] for q in QUOTES]
    prompt = (
        "Menga bitta haqiqiy, keng tarqalgan koreys xalq maqoli yoki "
        "한자성어 (xitoycha-koreyscha idioma) top. Quyidagilar allaqachon "
        f"ishlatilgan, ularni TAKRORLAMA: {existing}. "
        "Google qidiruv orqali maqolning haqiqiyligini tekshir. "
        "Faqat JSON qaytar, boshqa hech narsa yozma: "
        '{"korean": "...", "translation_uzbek": "...", "meaning_note": "..."}'
    )
    text_model = get_working_text_model()
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{text_model}:generateContent",
        headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
        json={
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.7},
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        raw_text = "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError):
        raw_text = ""

    return jsonify({
        "status": "review_needed",
        "note": "Bu taklif AVTOMATIK post qilinmaydi. Tekshirib, o'zingiz quotes.py ga qo'shing.",
        "raw_suggestion": raw_text,
    })


def do_generate_quotes(count: int):
    from generate_quotes import generate_new_quotes
    try:
        results = generate_new_quotes(count=count)
        for r in results:
            print(f"[generate_quotes] {r}")
    except Exception as e:
        print(f"[generate_quotes] XATO: {e}")


@app.route("/generate_quotes")
def generate_quotes_route():
    secret = request.args.get("key")
    if not ADMIN_SECRET or secret != ADMIN_SECRET:
        return jsonify({"error": "Noto'g'ri yoki yo'q admin kaliti"}), 403
    if not (SUPABASE_URL and SUPABASE_KEY):
        return jsonify({"error": "SUPABASE_URL / SUPABASE_KEY sozlanmagan"}), 500

    count = int(request.args.get("count", 3))
    thread = threading.Thread(target=do_generate_quotes, args=(count,), daemon=True)
    thread.start()
    return jsonify({
        "status": "started",
        "message": "Yangi maqollar orqa fonda tayyorlanmoqda (bir necha daqiqa vaqt olishi mumkin). Natijani Render Logs bo'limidan yoki Supabase jadvalidan tekshiring.",
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
