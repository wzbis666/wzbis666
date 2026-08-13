from __future__ import annotations

import argparse
import hashlib
import io
import json
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


VERSION = "26.2"
CLIENT_SHA1 = "2dc72797acbc1b63fc16a11c4ac393605f453754"
MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"

TEXTURE_PATHS = {
    "obsidian": "assets/minecraft/textures/block/obsidian.png",
    "deepslate": "assets/minecraft/textures/block/deepslate.png",
    "redstone_ore": "assets/minecraft/textures/block/deepslate_redstone_ore.png",
    "redstone_block": "assets/minecraft/textures/block/redstone_block.png",
    "redstone_lamp": "assets/minecraft/textures/block/redstone_lamp_on.png",
    "emerald_block": "assets/minecraft/textures/block/emerald_block.png",
    "blackstone": "assets/minecraft/textures/block/blackstone.png",
    "polished_blackstone": "assets/minecraft/textures/block/polished_blackstone.png",
}

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "assets" / "profile"
FONT_MONO = Path(r"C:\Windows\Fonts\consolab.ttf")
FONT_MONO_REGULAR = Path(r"C:\Windows\Fonts\consola.ttf")
FONT_CJK = Path(r"C:\Windows\Fonts\msyhbd.ttc")
FONT_CJK_REGULAR = Path(r"C:\Windows\Fonts\msyh.ttc")

COLORS = {
    "page": "#090D12",
    "panel": "#0D141A",
    "panel_alt": "#101A1E",
    "text": "#F0F4F8",
    "muted": "#A7B0BA",
    "green": "#4AE168",
    "red": "#F04444",
    "line": "#36414B",
}


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def download_client() -> bytes:
    manifest = fetch_json(MANIFEST_URL)
    entry = next(item for item in manifest["versions"] if item["id"] == VERSION)
    version_data = fetch_json(entry["url"])
    client = version_data["downloads"]["client"]
    with urllib.request.urlopen(client["url"], timeout=180) as response:
        payload = response.read()
    actual = hashlib.sha1(payload).hexdigest()
    if actual != CLIENT_SHA1 or actual != client["sha1"]:
        raise RuntimeError(f"Minecraft client SHA-1 mismatch: {actual}")
    return payload


def load_textures(texture_dir: Path | None) -> dict[str, Image.Image]:
    if texture_dir:
        return {
            name: Image.open(texture_dir / Path(path).name).convert("RGB")
            for name, path in TEXTURE_PATHS.items()
        }

    payload = download_client()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        return {
            name: Image.open(io.BytesIO(archive.read(path))).convert("RGB")
            for name, path in TEXTURE_PATHS.items()
        }


def font(size: int, *, cjk: bool = False, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = []
    if cjk:
        candidates.extend([FONT_CJK if bold else FONT_CJK_REGULAR, FONT_CJK_REGULAR])
    else:
        candidates.extend([FONT_MONO if bold else FONT_MONO_REGULAR, FONT_MONO_REGULAR])
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default(size=size)


def resized(texture: Image.Image, size: int | tuple[int, int]) -> Image.Image:
    if isinstance(size, int):
        size = (size, size)
    return texture.resize(size, Image.Resampling.NEAREST)


def tile(canvas: Image.Image, texture: Image.Image, box: tuple[int, int, int, int], block: int) -> None:
    x0, y0, x1, y1 = box
    patch = resized(texture, block)
    for y in range(y0, y1, block):
        for x in range(x0, x1, block):
            canvas.paste(patch, (x, y))


def textured_border(
    canvas: Image.Image,
    texture: Image.Image,
    box: tuple[int, int, int, int],
    thickness: int,
    block: int = 32,
) -> None:
    x0, y0, x1, y1 = box
    tile(canvas, texture, (x0, y0, x1, y0 + thickness), block)
    tile(canvas, texture, (x0, y1 - thickness, x1, y1), block)
    tile(canvas, texture, (x0, y0, x0 + thickness, y1), block)
    tile(canvas, texture, (x1 - thickness, y0, x1, y1), block)


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, size: int, *,
         color: str = COLORS["text"], cjk: bool = False, bold: bool = False,
         anchor: str | None = None, stroke_width: int = 0) -> None:
    draw.text(
        xy,
        value,
        font=font(size, cjk=cjk, bold=bold),
        fill=color,
        anchor=anchor,
        stroke_width=stroke_width,
        stroke_fill="#050709",
    )


def fit_text(draw: ImageDraw.ImageDraw, value: str, max_width: int, start_size: int,
             *, cjk: bool = False, bold: bool = False) -> ImageFont.FreeTypeFont:
    size = start_size
    while size > 14:
        candidate = font(size, cjk=cjk, bold=bold)
        if draw.textbbox((0, 0), value, font=candidate)[2] <= max_width:
            return candidate
        size -= 2
    return font(size, cjk=cjk, bold=bold)


def wrap_words(draw: ImageDraw.ImageDraw, value: str, max_width: int, text_font: ImageFont.FreeTypeFont) -> list[str]:
    words = value.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or draw.textbbox((0, 0), candidate, font=text_font)[2] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def textured_text(
    canvas: Image.Image,
    xy: tuple[int, int],
    value: str,
    size: int,
    texture: Image.Image,
    *,
    anchor: str | None = None,
    stroke_width: int = 0,
) -> None:
    display_font = font(size, bold=True)
    mask = Image.new("L", canvas.size)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text(xy, value, font=display_font, fill=255, anchor=anchor, stroke_width=stroke_width)

    outline = ImageDraw.Draw(canvas)
    outline.text(
        xy,
        value,
        font=display_font,
        fill="#050709",
        anchor=anchor,
        stroke_width=max(1, stroke_width),
        stroke_fill="#050709",
    )

    texture_layer = Image.new("RGB", canvas.size)
    tile(texture_layer, texture, (0, 0, canvas.width, canvas.height), max(20, size // 4))
    canvas.paste(texture_layer, (0, 0), mask)


def circuit(canvas: Image.Image, textures: dict[str, Image.Image], points: list[tuple[int, int]], block: int) -> None:
    red = resized(textures["redstone_block"], block)
    lamp = resized(textures["redstone_lamp"], block)
    for index, point in enumerate(points):
        canvas.paste(lamp if index in {0, len(points) - 1} else red, point)


def render_banner(textures: dict[str, Image.Image], language: str, mobile: bool) -> Image.Image:
    width, height = ((760, 460) if mobile else (1280, 320))
    canvas = Image.new("RGB", (width, height), COLORS["page"])
    draw = ImageDraw.Draw(canvas)

    tile(canvas, textures["polished_blackstone"], (0, 0, width, height), 48 if mobile else 56)
    draw.rectangle((0, 0, width, height), fill=(5, 8, 11, 130))

    if mobile:
        tile(canvas, textures["obsidian"], (24, 24, width - 24, 270), 64)
        textured_border(canvas, textures["blackstone"], (12, 12, width - 12, height - 12), 20, 32)
        draw.rectangle((50, 46, width - 50, 244), fill="#070A0D")
        textured_text(canvas, (width // 2, 118), "WZB", 112, textures["deepslate"], anchor="mm", stroke_width=2)
        if language == "cn":
            text(draw, (width // 2, 196), "MC 反作弊系统工程师", 31, cjk=True, bold=True, anchor="mm")
            text(draw, (width // 2, 235), "检测 · 验证 · 守护", 25, cjk=True, color=COLORS["green"], anchor="mm")
        else:
            fitted = fit_text(draw, "ANTI-CHEAT SYSTEMS ENGINEER", width - 100, 32, bold=True)
            draw.text((width // 2, 196), "ANTI-CHEAT SYSTEMS ENGINEER", font=fitted, fill=COLORS["text"], anchor="mm")
            text(draw, (width // 2, 235), "Detect · Verify · Protect", 24, color=COLORS["green"], anchor="mm")

        block = 56
        points = [(56 + i * block, 326) for i in range(9)]
        circuit(canvas, textures, points, block)
        canvas.paste(resized(textures["emerald_block"], 92), (width // 2 - 46, 302))
        text(draw, (width - 42, height - 38), "SYSTEM ONLINE", 21, color=COLORS["green"], anchor="rs")
    else:
        tile(canvas, textures["obsidian"], (34, 42, 685, 258), 64)
        textured_border(canvas, textures["blackstone"], (16, 16, width - 16, height - 16), 20, 32)
        draw.rectangle((66, 66, 652, 232), fill="#070A0D")
        textured_text(canvas, (92, 112), "WZB", 104, textures["deepslate"], stroke_width=2)
        if language == "cn":
            text(draw, (96, 205), "MC 反作弊系统工程师", 30, cjk=True, bold=True)
            text(draw, (96, 242), "检测 · 验证 · 守护", 22, cjk=True, color=COLORS["green"])
        else:
            text(draw, (96, 205), "ANTI-CHEAT SYSTEMS ENGINEER", 29, bold=True)
            text(draw, (96, 242), "Detect · Verify · Protect", 22, color=COLORS["green"])

        block = 48
        points = [
            (748, 82), (796, 82), (844, 82), (844, 130), (844, 178),
            (892, 178), (940, 178), (988, 178), (1036, 178), (1084, 178),
            (1132, 178), (1132, 130), (1132, 82),
        ]
        circuit(canvas, textures, points, block)
        canvas.paste(resized(textures["emerald_block"], 104), (946, 72))
        text(draw, (1218, 264), "SYSTEM ONLINE", 23, color=COLORS["green"], anchor="rs")

    return canvas


def panel(canvas: Image.Image, textures: dict[str, Image.Image], box: tuple[int, int, int, int], *,
          active: bool = False) -> None:
    draw = ImageDraw.Draw(canvas)
    draw.rectangle(box, fill=COLORS["panel_alt"] if active else COLORS["panel"])
    textured_border(canvas, textures["polished_blackstone"], box, 18, 32)
    if active:
        x0, y0, x1, y1 = box
        draw.rectangle((x0 + 16, y0 + 16, x1 - 16, y1 - 16), outline=COLORS["green"], width=4)


def render_mcacs(textures: dict[str, Image.Image], language: str, mobile: bool) -> Image.Image:
    width, height = ((760, 820) if mobile else (1280, 430))
    canvas = Image.new("RGB", (width, height), COLORS["page"])
    draw = ImageDraw.Draw(canvas)
    tile(canvas, textures["blackstone"], (0, 0, width, height), 48)
    draw.rectangle((0, 0, width, height), fill="#090D12")
    textured_border(canvas, textures["polished_blackstone"], (8, 8, width - 8, height - 8), 20, 32)

    if language == "cn":
        title = "MCACS V2.0 · 反作弊运营控制台"
        subtitle = "低误报优先 · 证据可追踪 · Paper 原生执行"
        steps = [
            ("采集", "汇聚玩家行为与检测信号", "deepslate"),
            ("验证", "保留证据并建立调查案件", "emerald_block"),
            ("执行", "通过幂等动作可靠处置", "redstone_ore"),
            ("观察", "实时面板、审计与复盘", "obsidian"),
        ]
        footer = "采集行为 → 汇聚检测 → 保存证据 → 人工复核 → 可靠执行 → 留存审计"
    else:
        title = "MCACS V2.0 · ANTI-CHEAT OPERATIONS CONSOLE"
        subtitle = "Low false positives · Verifiable evidence · Paper-native actions"
        steps = [
            ("ANALYZE", "Collect behavior and detection signals", "deepslate"),
            ("VERIFY", "Preserve evidence and open cases", "emerald_block"),
            ("DISPATCH", "Execute reliable idempotent actions", "redstone_ore"),
            ("OBSERVE", "Operate, audit, and review in real time", "obsidian"),
        ]
        footer = "Collect → Detect → Preserve evidence → Review → Execute → Audit"

    cjk = language == "cn"
    if mobile:
        title_font = fit_text(draw, title, width - 84, 34 if cjk else 30, cjk=cjk, bold=True)
        draw.text((42, 52), title, font=title_font, fill=COLORS["text"])
        text(draw, (42, 101), subtitle, 22 if cjk else 19, cjk=cjk, color=COLORS["green"])
        boxes = [(38, 146, 366, 432), (394, 146, 722, 432), (38, 458, 366, 744), (394, 458, 722, 744)]
        for box, (label, description, texture_name) in zip(boxes, steps):
            panel(canvas, textures, box, active=texture_name == "emerald_block")
            x0, y0, x1, _ = box
            canvas.paste(resized(textures[texture_name], 104), (x0 + (x1 - x0 - 104) // 2, y0 + 42))
            text(draw, ((x0 + x1) // 2, y0 + 176), label, 27, cjk=cjk, bold=True, anchor="mm")
            if cjk:
                text(draw, ((x0 + x1) // 2, y0 + 224), description, 19, cjk=True, color=COLORS["muted"], anchor="mm")
            else:
                description_font = font(16)
                lines = wrap_words(draw, description, x1 - x0 - 34, description_font)
                for line_index, line in enumerate(lines[:2]):
                    draw.text(((x0 + x1) // 2, y0 + 213 + line_index * 25), line, font=description_font, fill=COLORS["muted"], anchor="mm")
        text(draw, (width // 2, 786), footer, 18 if cjk else 16, cjk=cjk, color=COLORS["green"], anchor="mm")
    else:
        title_font = fit_text(draw, title, width - 96, 36 if cjk else 32, cjk=cjk, bold=True)
        draw.text((48, 44), title, font=title_font, fill=COLORS["text"])
        text(draw, (48, 91), subtitle, 22 if cjk else 19, cjk=cjk, color=COLORS["green"])
        gap = 18
        x0 = 36
        y0 = 130
        card_width = (width - x0 * 2 - gap * 3) // 4
        for index, (label, description, texture_name) in enumerate(steps):
            left = x0 + index * (card_width + gap)
            box = (left, y0, left + card_width, 352)
            panel(canvas, textures, box, active=texture_name == "emerald_block")
            center_x = left + card_width // 2
            canvas.paste(resized(textures[texture_name], 82), (center_x - 41, y0 + 30))
            text(draw, (center_x, y0 + 142), label, 25 if cjk else 22, cjk=cjk, bold=True, anchor="mm")
            if cjk:
                split_at = min(9, len(description))
                lines = [description[:split_at], description[split_at:]]
                for line_index, line in enumerate(filter(None, lines)):
                    text(draw, (center_x, y0 + 184 + line_index * 28), line, 18, cjk=True, color=COLORS["muted"], anchor="mm")
            else:
                description_font = font(15)
                lines = wrap_words(draw, description, card_width - 44, description_font)
                for line_index, line in enumerate(lines[:2]):
                    draw.text((center_x, y0 + 168 + line_index * 26), line, font=description_font, fill=COLORS["muted"], anchor="mm")
        text(draw, (width // 2, 392), footer, 19 if cjk else 18, cjk=cjk, color=COLORS["green"], anchor="mm")

    return canvas


def save_asset(image: Image.Image, filename: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT_DIR / filename, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render bilingual GitHub profile assets from vanilla Minecraft textures.")
    parser.add_argument("--textures-dir", type=Path, help="Optional directory containing the eight extracted PNG textures.")
    args = parser.parse_args()
    textures = load_textures(args.textures_dir)

    for language in ("cn", "en"):
        save_asset(render_banner(textures, language, False), f"banner-{language}.png")
        save_asset(render_banner(textures, language, True), f"banner-{language}-mobile.png")
        save_asset(render_mcacs(textures, language, False), f"mcacs-{language}.png")
        save_asset(render_mcacs(textures, language, True), f"mcacs-{language}-mobile.png")

    print(f"Rendered assets to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
