import asyncio
import colorsys
import os
import random
import re
import uuid

import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from unidecode import unidecode
from youtubesearchpython.__future__ import VideosSearch

from config import YOUTUBE_IMG_URL

try:  # Pillow >= 9.1
    LANCZOS = Image.Resampling.LANCZOS
except AttributeError:  # older Pillow
    LANCZOS = Image.LANCZOS

WIDTH, HEIGHT = 1280, 720
FONT_BOLD = "ISTKHAR_MUSIC/assets/font.ttf"
FONT_REGULAR = "ISTKHAR_MUSIC/assets/font2.ttf"
CREDIT_TEXT = "ISTKHAR • BLOQUTE OP"


def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    return image.resize((newWidth, newHeight))


def clear(text):
    parts = text.split(" ")
    title = ""
    for i in parts:
        if len(title) + len(i) < 60:
            title += " " + i
    return title.strip()


async def get_qthumb(videoid):
    try:
        return f"https://img.youtube.com/vi/{videoid}/maxresdefault.jpg"
    except Exception:
        return YOUTUBE_IMG_URL


def _random_theme():
    """A new random colour theme for every thumbnail."""
    hue = random.random()
    accent = tuple(
        int(c * 255)
        for c in colorsys.hsv_to_rgb(hue, random.uniform(0.55, 0.85), 1.0)
    )
    tint = tuple(
        int(c * 255)
        for c in colorsys.hsv_to_rgb((hue + random.uniform(-0.08, 0.08)) % 1, 0.8, 0.45)
    )
    return accent, tint


def _wrap(draw, text, font, max_width, max_lines=2):
    words = text.split()
    lines, line = [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and draw.textlength(last + "...", font=font) > max_width:
            last = last[:-1]
        lines[-1] = last.rstrip() + "..."
    return lines


def _render(src_path, out_path, title, duration, views, channel, bot_name):
    accent, tint = _random_theme()

    youtube = Image.open(src_path).convert("RGB")

    # blurred, tinted background (cover-fit to 1280x720)
    bg = ImageOps.fit(youtube, (WIDTH, HEIGHT), method=LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.55).convert("RGBA")
    bg = Image.alpha_composite(bg, Image.new("RGBA", (WIDTH, HEIGHT), tint + (125,)))

    # square cover with rounded corners and coloured border
    size = 500
    cover = ImageOps.fit(youtube, (size, size), method=LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), radius=36, fill=255)
    cover.putalpha(mask)
    border = 14
    frame = Image.new("RGBA", (size + border * 2, size + border * 2), (0, 0, 0, 0))
    ImageDraw.Draw(frame).rounded_rectangle(
        (0, 0, frame.width - 1, frame.height - 1), radius=44, fill=accent + (255,)
    )
    frame.alpha_composite(cover, (border, border))
    cx, cy = 70, (HEIGHT - frame.height) // 2
    bg.alpha_composite(frame, (cx, cy))

    draw = ImageDraw.Draw(bg)
    f_name = ImageFont.truetype(FONT_BOLD, 30)
    f_big = ImageFont.truetype(FONT_REGULAR, 72)
    f_title = ImageFont.truetype(FONT_REGULAR, 44)
    f_info = ImageFont.truetype(FONT_REGULAR, 32)

    tx = cx + frame.width + 60
    max_w = WIDTH - tx - 50

    if bot_name:
        draw.text((24, 16), bot_name, fill="white", font=f_name)

    draw.text(
        (tx, 120), "NOW PLAYING", fill=accent, stroke_width=2, stroke_fill=accent, font=f_big
    )
    draw.rounded_rectangle((tx, 215, tx + 220, 222), radius=4, fill=accent)

    y = 255
    for line in _wrap(draw, title, f_title, max_w, 2):
        draw.text((tx, y), line, fill="white", stroke_width=1, stroke_fill="white", font=f_title)
        y += 62

    y = max(y + 30, 430)
    for label, value in (
        ("Views", views[:23]),
        ("Duration", f"{duration[:23]} Mins"),
        ("Channel", channel),
    ):
        head = f"{label} : "
        draw.text((tx, y), head, fill=accent, font=f_info)
        value_lines = _wrap(draw, value, f_info, max_w - draw.textlength(head, font=f_info), 1)
        draw.text(
            (tx + draw.textlength(head, font=f_info), y),
            value_lines[0] if value_lines else "",
            fill="white",
            font=f_info,
        )
        y += 52

    f_credit = ImageFont.truetype(FONT_BOLD, 30)
    credit_w = draw.textlength(CREDIT_TEXT, font=f_credit)
    draw.text(
        (WIDTH - credit_w - 36, HEIGHT - 62), CREDIT_TEXT, fill=accent, font=f_credit
    )

    bg.convert("RGB").save(out_path, "PNG")


async def get_thumb(videoid):
    os.makedirs("cache", exist_ok=True)
    out_path = f"cache/{videoid}.png"
    tmp_src = f"cache/thumb{videoid}_{uuid.uuid4().hex[:8]}.png"
    tmp_out = f"cache/{videoid}_{uuid.uuid4().hex[:8]}.tmp.png"
    try:
        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        title, duration, views, channel, thumbnail = (
            "Unsupported Title",
            "Unknown",
            "Unknown Views",
            "Unknown Channel",
            None,
        )
        for result in (await results.next())["result"]:
            try:
                title = re.sub(r"\W+", " ", result["title"]).title()
            except Exception:
                pass
            duration = result.get("duration") or duration
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            try:
                views = result["viewCount"]["short"]
            except Exception:
                pass
            try:
                channel = result["channel"]["name"]
            except Exception:
                pass
        if not thumbnail:
            return YOUTUBE_IMG_URL

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status != 200:
                    return YOUTUBE_IMG_URL
                async with aiofiles.open(tmp_src, mode="wb") as f:
                    await f.write(await resp.read())

        try:
            from ISTKHAR_MUSIC import app

            bot_name = unidecode(app.name)
        except Exception:
            bot_name = ""

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, _render, tmp_src, tmp_out, title, duration, views, channel, bot_name
        )
        os.replace(tmp_out, out_path)  # new random colours every time it is generated
        return out_path
    except Exception as e:
        print(e)
        return YOUTUBE_IMG_URL
    finally:
        for p in (tmp_src, tmp_out):
            try:
                os.remove(p)
            except OSError:
                pass
