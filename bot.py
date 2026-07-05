import os
import io
import logging
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import telebot
from telebot import types

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
bot = telebot.TeleBot(BOT_TOKEN)

user_sessions = {}

CARD_W = 1050
CARD_H = 600

THEMES = {
    "Obsidian": {
        "bg":      [(5, 5, 5), (25, 25, 25)],
        "accent":  (0, 255, 180),
        "name":    (255, 255, 255),
        "title":   (0, 255, 180),
        "body":    (180, 180, 180),
        "style":   "neon_line",
    },
    "Arctic": {
        "bg":      [(225, 240, 255), (200, 225, 255)],
        "accent":  (0, 100, 220),
        "name":    (10, 30, 80),
        "title":   (0, 100, 220),
        "body":    (60, 80, 120),
        "style":   "top_bar",
    },
    "Copper": {
        "bg":      [(30, 18, 8), (55, 32, 12)],
        "accent":  (200, 120, 50),
        "name":    (255, 230, 190),
        "title":   (200, 120, 50),
        "body":    (190, 160, 120),
        "style":   "diagonal",
    },
    "Sakura": {
        "bg":      [(255, 240, 245), (250, 220, 235)],
        "accent":  (210, 80, 120),
        "name":    (90, 20, 50),
        "title":   (210, 80, 120),
        "body":    (140, 70, 95),
        "style":   "side_bar",
    },
    "Midnight": {
        "bg":      [(8, 8, 30), (18, 18, 55)],
        "accent":  (120, 100, 255),
        "name":    (230, 225, 255),
        "title":   (120, 100, 255),
        "body":    (170, 165, 220),
        "style":   "diagonal",
    },
    "Sand": {
        "bg":      [(245, 238, 220), (230, 218, 190)],
        "accent":  (160, 110, 40),
        "name":    (60, 40, 10),
        "title":   (160, 110, 40),
        "body":    (100, 75, 35),
        "style":   "top_bar",
    },
    "Glacier": {
        "bg":      [(230, 248, 248), (200, 235, 238)],
        "accent":  (0, 160, 170),
        "name":    (10, 60, 70),
        "title":   (0, 160, 170),
        "body":    (40, 100, 110),
        "style":   "neon_line",
    },
    "Onyx Gold": {
        "bg":      [(12, 10, 5), (28, 22, 8)],
        "accent":  (212, 175, 55),
        "name":    (255, 248, 220),
        "title":   (212, 175, 55),
        "body":    (200, 185, 140),
        "style":   "side_bar",
    },
    "Slate": {
        "bg":      [(38, 50, 56), (55, 71, 79)],
        "accent":  (0, 230, 200),
        "name":    (236, 239, 241),
        "title":   (0, 230, 200),
        "body":    (176, 190, 197),
        "style":   "top_bar",
    },
    "Crimson": {
        "bg":      [(80, 0, 10), (120, 5, 18)],
        "accent":  (255, 180, 50),
        "name":    (255, 240, 230),
        "title":   (255, 180, 50),
        "body":    (240, 190, 180),
        "style":   "diagonal",
    },
}


def load_font(size, bold=False):
    bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    reg_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for p in (bold_paths if bold else reg_paths):
        try:
            return ImageFont.truetype(p, size)
        except:
            continue
    return ImageFont.load_default()


def make_bg(theme):
    c1, c2 = theme["bg"]
    img = Image.new("RGB", (CARD_W, CARD_H))
    draw = ImageDraw.Draw(img)
    for x in range(CARD_W):
        t = x / CARD_W
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        draw.line([(x, 0), (x, CARD_H)], fill=(r, g, b))
    canvas = img.convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    acc = theme["accent"]
    style = theme["style"]

    if style == "neon_line":
        # Glowing bottom line
        for i, width in enumerate([8, 4, 2]):
            alpha = [40, 100, 220][i]
            draw.line(
                [(0, CARD_H - 12 + i), (CARD_W, CARD_H - 12 + i)],
                fill=acc + (alpha,), width=width
            )
        # Top thin line
        draw.line([(0, 0), (CARD_W, 0)], fill=acc + (120,), width=2)

    elif style == "top_bar":
        draw.rectangle([(0, 0), (CARD_W, 10)], fill=acc + (255,))
        draw.rectangle([(0, CARD_H - 10), (CARD_W, CARD_H)], fill=acc + (80,))

    elif style == "diagonal":
        pts1 = [(CARD_W * 0.6, CARD_H), (CARD_W, CARD_H * 0.25), (CARD_W, CARD_H)]
        pts2 = [(CARD_W * 0.75, CARD_H), (CARD_W, CARD_H * 0.5), (CARD_W, CARD_H)]
        draw.polygon(pts1, fill=acc + (20,))
        draw.polygon(pts2, fill=acc + (35,))
        draw.line(
            [(int(CARD_W * 0.6), CARD_H), (CARD_W, int(CARD_H * 0.25))],
            fill=acc + (80,), width=2
        )

    elif style == "side_bar":
        draw.rectangle([(0, 0), (8, CARD_H)], fill=acc + (255,))
        draw.rectangle([(14, 0), (16, CARD_H)], fill=acc + (60,))

    return canvas


def circle_crop(img_bytes, size):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([(0, 0), (size - 1, size - 1)], fill=255)
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)
    return result


def draw_text_line(draw, x, y, text, font, color, max_w=None):
    if max_w:
        while len(text) > 3:
            bb = draw.textbbox((0, 0), text, font=font)
            if bb[2] - bb[0] <= max_w:
                break
            text = text[:-2] + "…"
    draw.text((x, y), text, font=font, fill=color)
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]


def make_card_front(data):
    theme = THEMES[data["theme"]]
    canvas = make_bg(theme)
    draw = ImageDraw.Draw(canvas)

    style = theme["style"]
    left = 28 if style == "side_bar" else 50
    has_logo = bool(data.get("logo_bytes"))

    # Logo or avatar — top right
    logo_size = 120
    lx = CARD_W - logo_size - 45
    ly = 35
    if has_logo:
        avatar = circle_crop(data["logo_bytes"], logo_size)
        # Glow ring
        ring = Image.new("RGBA", (logo_size + 10, logo_size + 10), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse(
            [(0, 0), (logo_size + 9, logo_size + 9)],
            outline=theme["accent"] + (180,), width=3
        )
        canvas.alpha_composite(ring, dest=(lx - 5, ly - 5))
        canvas.alpha_composite(avatar, dest=(lx, ly))
        draw = ImageDraw.Draw(canvas)

    max_w = (lx - left - 20) if has_logo else (CARD_W - left - 50)
    y = 48

    # Name
    name_font = load_font(60, bold=True)
    h = draw_text_line(draw, left, y, data.get("name", "Your Name"),
                       name_font, theme["name"], max_w)
    y += h + 10

    # Title
    if data.get("title"):
        tf = load_font(28)
        h = draw_text_line(draw, left, y, data["title"], tf, theme["title"], max_w)
        y += h + 5

    # Company
    if data.get("company"):
        cf = load_font(24, bold=True)
        h = draw_text_line(draw, left, y, data["company"], cf, theme["body"], max_w)
        y += h + 5

    # Divider
    y += 14
    acc = theme["accent"]
    draw.line([(left, y), (left + 260, y)], fill=acc + (180,), width=2)
    # Small diamond on divider
    mid = left + 130
    draw.polygon(
        [(mid - 5, y), (mid, y - 5), (mid + 5, y), (mid, y + 5)],
        fill=acc + (220,)
    )
    y += 22

    # Contact rows
    cf = load_font(23)
    gap = 33

    contacts = [
        ("✉", "email"),
        ("☎", "phone"),
        ("🌐", "website"),
        ("📍", "address"),
    ]
    for icon, key in contacts:
        val = data.get(key, "")
        if val:
            draw_text_line(draw, left, y, f"{icon}  {val}", cf, theme["body"],
                           max_w=CARD_W - left - 50)
            y += gap

    # Tagline
    if data.get("tagline"):
        tg_f = load_font(21)
        draw.text(
            (left, CARD_H - 52),
            f'"{data["tagline"]}"',
            font=tg_f,
            fill=acc + (190,)
        )

    out = io.BytesIO()
    canvas.convert("RGB").save(out, format="PNG", optimize=True, dpi=(300, 300))
    out.seek(0)
    return out.read()


def make_card_back(data):
    theme = THEMES[data["theme"]]
    canvas = make_bg(theme)
    draw = ImageDraw.Draw(canvas)
    acc = theme["accent"]

    has_logo = bool(data.get("logo_bytes"))

    if has_logo:
        size = 200
        avatar = circle_crop(data["logo_bytes"], size)
        ring = Image.new("RGBA", (size + 12, size + 12), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse(
            [(0, 0), (size + 11, size + 11)],
            outline=acc + (200,), width=4
        )
        lx = CARD_W // 2 - size // 2
        ly = CARD_H // 2 - size // 2 - 20
        canvas.alpha_composite(ring, dest=(lx - 6, ly - 6))
        canvas.alpha_composite(avatar, dest=(lx, ly))
        draw = ImageDraw.Draw(canvas)
    else:
        # Large monogram
        name = data.get("name", "?")
        parts = name.strip().split()
        monogram = "".join(p[0].upper() for p in parts[:2])
        mf = load_font(180, bold=True)
        bb = draw.textbbox((0, 0), monogram, font=mf)
        mw = bb[2] - bb[0]
        mh = bb[3] - bb[1]
        mx = (CARD_W - mw) // 2
        my = (CARD_H - mh) // 2 - 30
        # Shadow
        draw.text((mx + 5, my + 5), monogram, font=mf, fill=(0, 0, 0, 50))
        draw.text((mx, my), monogram, font=mf, fill=acc + (210,))

    # Company bottom center
    if data.get("company"):
        co_f = load_font(30, bold=True)
        bb = draw.textbbox((0, 0), data["company"], font=co_f)
        cw = bb[2] - bb[0]
        cx = (CARD_W - cw) // 2
        draw.text((cx, CARD_H - 68), data["company"], font=co_f,
                  fill=theme["body"])

    # Website small bottom
    if data.get("website"):
        wf = load_font(22)
        bb = draw.textbbox((0, 0), data["website"], font=wf)
        ww = bb[2] - bb[0]
        wx = (CARD_W - ww) // 2
        draw.text((wx, CARD_H - 36), data["website"], font=wf,
                  fill=acc + (180,))

    out = io.BytesIO()
    canvas.convert("RGB").save(out, format="PNG", optimize=True, dpi=(300, 300))
    out.seek(0)
    return out.read()


# ---- Bot flow ----

def send_theme_picker(cid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚫ Obsidian", callback_data="theme:Obsidian"),
        types.InlineKeyboardButton("🔵 Arctic", callback_data="theme:Arctic"),
        types.InlineKeyboardButton("🟠 Copper", callback_data="theme:Copper"),
        types.InlineKeyboardButton("🌸 Sakura", callback_data="theme:Sakura"),
        types.InlineKeyboardButton("🌌 Midnight", callback_data="theme:Midnight"),
        types.InlineKeyboardButton("🟤 Sand", callback_data="theme:Sand"),
        types.InlineKeyboardButton("🩵 Glacier", callback_data="theme:Glacier"),
        types.InlineKeyboardButton("✨ Onyx Gold", callback_data="theme:Onyx Gold"),
        types.InlineKeyboardButton("🩶 Slate", callback_data="theme:Slate"),
        types.InlineKeyboardButton("🔴 Crimson", callback_data="theme:Crimson"),
    )
    bot.send_message(
        cid,
        "🎨 *Step 1 — Choose a theme:*",
        parse_mode="Markdown",
        reply_markup=markup,
    )


@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    cid = message.chat.id
    bot.send_message(
        cid,
        "👋 *Business Card Maker Bot*\n\n"
        "Create a stunning professional business card!\n\n"
        "🎨 10 premium themes\n"
        "📇 Front + back card\n"
        "🖼 Optional logo\n"
        "📐 Print-ready 300 DPI\n\n"
        "Send /make to start!",
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["make"])
def cmd_make(message):
    cid = message.chat.id
    user_sessions[cid] = {"step": "theme"}
    send_theme_picker(cid)


@bot.callback_query_handler(func=lambda call: call.data.startswith("theme:"))
def handle_theme(call):
    cid = call.message.chat.id
    theme = call.data.split(":", 1)[1]
    session = user_sessions.setdefault(cid, {})
    session["theme"] = theme
    session["step"] = "name"
    bot.answer_callback_query(call.id, f"{theme} selected!")
    bot.edit_message_text(
        f"✅ Theme: *{theme}*",
        cid, call.message.message_id, parse_mode="Markdown",
    )
    bot.send_message(
        cid,
        "✏️ *Step 2 — Full name:*\n_(e.g. James Carter)_",
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda m: user_sessions.get(m.chat.id, {}).get("step") == "name")
def handle_name(message):
    cid = message.chat.id
    user_sessions[cid]["name"] = message.text.strip()
    user_sessions[cid]["step"] = "title"
    bot.send_message(
        cid,
        "💼 *Step 3 — Job title:*\n_(e.g. Creative Director)_\n/skip to leave blank.",
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda m: user_sessions.get(m.chat.id, {}).get("step") == "title")
def handle_title(message):
    cid = message.chat.id
    user_sessions[cid]["title"] = "" if message.text.strip() == "/skip" else message.text.strip()
    user_sessions[cid]["step"] = "company"
    bot.send_message(
        cid,
        "🏢 *Step 4 — Company:*\n_(e.g. Nova Studios)_\n/skip to leave blank.",
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda m: user_sessions.get(m.chat.id, {}).get("step") == "company")
def handle_company(message):
    cid = message.chat.id
    user_sessions[cid]["company"] = "" if message.text.strip() == "/skip" else message.text.strip()
    user_sessions[cid]["step"] = "email"
    bot.send_message(
        cid,
        "✉️ *Step 5 — Email:*\n_(e.g. james@novastudios.com)_\n/skip to leave blank.",
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda m: user_sessions.get(m.chat.id, {}).get("step") == "email")
def handle_email(message):
    cid = message.chat.id
    user_sessions[cid]["email"] = "" if message.text.strip() == "/skip" else message.text.strip()
    user_sessions[cid]["step"] = "phone"
    bot.send_message(
        cid,
        "📞 *Step 6 — Phone:*\n_(e.g. +1 555 123 4567)_\n/skip to leave blank.",
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda m: user_sessions.get(m.chat.id, {}).get("step") == "phone")
def handle_phone(message):
    cid = message.chat.id
    user_sessions[cid]["phone"] = "" if message.text.strip() == "/skip" else message.text.strip()
    user_sessions[cid]["step"] = "website"
    bot.send_message(
        cid,
        "🌐 *Step 7 — Website:*\n_(e.g. www.novastudios.com)_\n/skip to leave blank.",
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda m: user_sessions.get(m.chat.id, {}).get("step") == "website")
def handle_website(message):
    cid = message.chat.id
    user_sessions[cid]["website"] = "" if message.text.strip() == "/skip" else message.text.strip()
    user_sessions[cid]["step"] = "address"
    bot.send_message(
        cid,
        "📍 *Step 8 — Address:*\n_(e.g. 42 Park Ave, New York)_\n/skip to leave blank.",
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda m: user_sessions.get(m.chat.id, {}).get("step") == "address")
def handle_address(message):
    cid = message.chat.id
    user_sessions[cid]["address"] = "" if message.text.strip() == "/skip" else message.text.strip()
    user_sessions[cid]["step"] = "tagline"
    bot.send_message(
        cid,
        "💬 *Step 9 — Tagline:*\n_(e.g. Building brands that matter)_\n/skip to leave blank.",
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda m: user_sessions.get(m.chat.id, {}).get("step") == "tagline")
def handle_tagline(message):
    cid = message.chat.id
    user_sessions[cid]["tagline"] = "" if message.text.strip() == "/skip" else message.text.strip()
    user_sessions[cid]["step"] = "logo"
    bot.send_message(
        cid,
        "🖼 *Step 10 — Logo:*\n_(send a photo — square works best)_\n/skip to use monogram instead.",
        parse_mode="Markdown",
    )


@bot.message_handler(commands=["skip"])
def handle_skip(message):
    cid = message.chat.id
    session = user_sessions.get(cid, {})
    if session.get("step") == "logo":
        session["logo_bytes"] = None
        generate_cards(cid)


@bot.message_handler(
    content_types=["photo", "document"],
    func=lambda m: user_sessions.get(m.chat.id, {}).get("step") == "logo",
)
def handle_logo(message):
    cid = message.chat.id
    session = user_sessions.get(cid, {})
    try:
        if message.content_type == "photo":
            file_id = message.photo[-1].file_id
        else:
            if not message.document.mime_type.startswith("image/"):
                bot.send_message(cid, "⚠️ Please send an image.")
                return
            file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        session["logo_bytes"] = bot.download_file(file_info.file_path)
        generate_cards(cid)
    except Exception as e:
        logger.exception("Logo error")
        bot.send_message(cid, f"❌ Error: {e}")


def generate_cards(cid):
    session = user_sessions.get(cid, {})
    msg = bot.send_message(cid, "⏳ Designing your cards…")
    try:
        front = make_card_front(session)
        back = make_card_back(session)
        bot.send_photo(cid, front, caption="📇 *Front*", parse_mode="Markdown")
        bot.send_photo(
            cid, back,
            caption=(
                "📇 *Back*\n\n"
                "✅ Print-ready at 300 DPI!\n"
                "Send /make to create another."
            ),
            parse_mode="Markdown",
        )
        bot.delete_message(cid, msg.message_id)
    except Exception as e:
        logger.exception("Generation error")
        bot.send_message(cid, f"❌ Failed: {e}")


@bot.message_handler(commands=["cancel"])
def cmd_cancel(message):
    cid = message.chat.id
    user_sessions.pop(cid, None)
    bot.send_message(cid, "❌ Cancelled. Send /make to start over.")


if __name__ == "__main__":
    logger.info("Business card bot v2 starting…")
    bot.infinity_polling()
