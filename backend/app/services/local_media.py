from __future__ import annotations

import gc
import hashlib
import os
from pathlib import Path
from uuid import uuid4

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from huggingface_hub import snapshot_download

from app.core.config import settings
from app.services.media_plan import MediaPlan, ScenePlan, VideoPlan

OUTPUT_DIRECTORY = Path("app/static/uploads/products/ai")
CACHE_DIRECTORY = Path("data/media-cache")
SIZES = {"square": (1080, 1080), "portrait": (864, 1536), "landscape": (1536, 864)}


def _load_reference_image(url: str | None) -> Image.Image:
    root = Path("app/static/uploads/products").resolve()
    if not url or not url.startswith("/static/uploads/products/"):
        raise ValueError("Une photo originale locale du produit est requise.")
    path = (Path("app") / url.lstrip("/")).resolve()
    if not path.is_relative_to(root) or path.is_relative_to(root / "ai") or not path.is_file():
        raise ValueError("Photo originale introuvable ou chemin non autorisé.")
    with Image.open(path) as source:
        return ImageOps.exif_transpose(source).convert("RGBA")


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _fit_label(text: str, limit: int = 23) -> list[str]:
    words = text.upper().split()
    lines: list[str] = []
    for word in words:
        if not lines or len(lines[-1]) + len(word) + 1 > limit:
            lines.append(word[:limit])
        else:
            lines[-1] += " " + word
    return lines[:3]


def _agent_packaging(product_name: str, brand: str, category: str, packaging_hint: str = "") -> Image.Image:
    """Build an original local packaging mockup when no physical product photo exists."""
    canvas = Image.new("RGBA", (760, 980), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    label = _fit_label(product_name)
    text = f"{packaging_hint} {category} {product_name}".lower()
    amber, dark, cream = "#E59C25", "#171713", "#FFF9EA"
    if any(term in text for term in ("tube", "tubulaire")):
        draw.rounded_rectangle((185, 150, 575, 800), radius=72, fill=cream, outline=dark, width=9)
        draw.polygon([(185, 250), (575, 250), (530, 830), (230, 830)], fill=cream, outline=dark)
        draw.rounded_rectangle((250, 795, 510, 900), radius=28, fill=dark)
        body = (225, 370, 535, 700)
    elif any(term in text for term in ("pot", "jar", "baume")):
        draw.rounded_rectangle((130, 360, 630, 820), radius=85, fill=cream, outline=dark, width=9)
        draw.rounded_rectangle((110, 275, 650, 425), radius=42, fill=dark)
        body = (175, 475, 585, 735)
    elif any(term in text for term in ("airless", "pompe", "flacon", "bottle", "shampoo", "lotion", "huile", "sérum", "serum")):
        draw.rounded_rectangle((190, 175, 570, 850), radius=95, fill=cream, outline=dark, width=9)
        draw.rounded_rectangle((240, 80, 520, 220), radius=35, fill=dark)
        draw.rectangle((315, 25, 445, 105), fill=dark)
        body = (225, 390, 535, 700)
    else:
        draw.rounded_rectangle((155, 170, 605, 850), radius=48, fill=dark, outline=amber, width=10)
        draw.rectangle((180, 120, 580, 225), fill=amber)
        body = (205, 370, 555, 710)
        cream, dark = dark, cream
    draw.rounded_rectangle(body, radius=34, fill=amber)
    brand_font = _font(42, True)
    name_font = _font(36, True)
    small_font = _font(23)
    brand_text = (brand or "MIELMAR").upper()
    box = draw.textbbox((0, 0), brand_text, font=brand_font)
    draw.text(((760 - (box[2] - box[0])) / 2, body[1] + 35), brand_text, fill="#171713", font=brand_font)
    y = body[1] + 115
    for line in label:
        box = draw.textbbox((0, 0), line, font=name_font)
        draw.text(((760 - (box[2] - box[0])) / 2, y), line, fill="#171713", font=name_font)
        y += 47
    category_text = (category or "COSMÉTIQUE").upper()
    box = draw.textbbox((0, 0), category_text, font=small_font)
    draw.text(((760 - (box[2] - box[0])) / 2, body[3] - 65), category_text, fill="#171713", font=small_font)
    return canvas


def _cutout(source: Image.Image) -> Image.Image:
    """Keep original RGB pixels; segmentation changes only alpha, cached by source bytes."""
    fingerprint = hashlib.sha256(source.tobytes() + str(source.size).encode()).hexdigest()
    CACHE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    cached = CACHE_DIRECTORY / f"cutout-v1-{fingerprint}.png"
    if cached.exists():
        with Image.open(cached) as saved:
            return saved.convert("RGBA")
    if source.getchannel("A").getextrema()[0] < 255:
        result = source.copy()
    else:
        os.environ.setdefault("U2NET_HOME", "/app/data/media-models/rembg")
        from rembg import new_session, remove
        session = new_session("u2net", providers=["CPUExecutionProvider"])
        mask = remove(source.convert("RGB"), session=session, only_mask=True)
        result = source.copy()
        result.putalpha(mask.convert("L"))
        del session
        gc.collect()
    alpha = result.getchannel("A")
    box = alpha.point(lambda value: 255 if value > 20 else 0).getbbox()
    coverage = np.count_nonzero(np.asarray(alpha) > 128) / (source.width * source.height)
    if not box or not 0.02 < coverage < 0.97:
        raise ValueError("Le détourage n’est pas fiable. Fournissez une photo avec un fond plus distinct du produit.")
    result = result.crop(box)
    result.save(cached)
    return result


def _generate_background(prompt: str, size: tuple[int, int]) -> Image.Image:
    if not prompt.strip():
        raise ValueError("L’agent n’a pas décrit le décor demandé. Précisez le décor et relancez.")
    import openvino_genai
    model_path = Path(settings.local_media_model_dir)
    if not (model_path / "model_index.json").exists():
        snapshot_download(repo_id=settings.local_media_model_id, local_dir=model_path)
    pipeline = openvino_genai.Text2ImagePipeline(str(model_path), settings.local_media_device)
    try:
        result = pipeline.generate(
            "Professional commercial photography empty background, free space for a product in foreground. " + prompt,
            negative_prompt="product, packaging, bottle, jar, pouch, person, hands, text, letters, logo, watermark, blurry",
            guidance_scale=7.5, num_inference_steps=max(12, min(settings.local_media_steps, 30)),
            width=512, height=512,
        )
        return ImageOps.fit(Image.fromarray(np.asarray(result.data[0]).astype(np.uint8)).convert("RGB"), size, Image.Resampling.LANCZOS)
    finally:
        del pipeline
        gc.collect()


def _background(scene: ScenePlan) -> Image.Image:
    size = SIZES[scene.format]
    if scene.background == "generated":
        canvas = _generate_background(scene.background_prompt, size)
    else:
        canvas = Image.new("RGB", size, scene.background_color)
    if scene.background != "solid" and scene.light_strength > 0:
        w, h = size
        cx, cy = {"left": (0.1, 0.35), "right": (0.9, 0.35), "top": (0.5, 0.12), "center": (0.5, 0.5)}[scene.light_direction]
        y, x = np.ogrid[:h, :w]
        glow = np.exp(-(((x / w - cx) / 0.5) ** 2 + ((y / h - cy) / 0.5) ** 2))
        alpha = Image.fromarray((glow * scene.light_strength * 255).astype(np.uint8))
        canvas.paste(Image.new("RGB", size, scene.light_color), (0, 0), alpha)
    return canvas


def _compose(cutout: Image.Image, scene: ScenePlan, background: Image.Image) -> Image.Image:
    canvas = background.copy()
    width, height = canvas.size
    product = ImageOps.contain(cutout, (int(width * 0.65), int(height * scene.product_height)), Image.Resampling.LANCZOS)
    center_x = {"left": 0.34, "center": 0.5, "right": 0.66}[scene.product_position]
    left = max(12, min(width - product.width - 12, round(width * center_x - product.width / 2)))
    top = round((height - product.height) / 2 - height * 0.035)
    alpha = product.getchannel("A")
    if scene.reflection:
        reflected = ImageOps.flip(product)
        fade = np.linspace(scene.reflection, 0, reflected.height, dtype=np.float32)[:, None]
        reflected.putalpha(Image.fromarray((np.asarray(reflected.getchannel("A")) * fade).astype(np.uint8)))
        canvas.paste(reflected, (left, top + product.height + 2), reflected.getchannel("A"))
    if scene.shadow:
        mask = Image.new("L", canvas.size)
        mask.paste(alpha, (left + round(width * 0.014), top + round(height * 0.018)))
        mask = mask.filter(ImageFilter.GaussianBlur(width * 0.014)).point(lambda v: round(v * scene.shadow))
        canvas.paste(Image.new("RGB", canvas.size, "black"), (0, 0), mask)
    canvas.paste(product, (left, top), alpha)
    return canvas


def _video_frame(source: Image.Image, plan: VideoPlan, progress: float) -> Image.Image:
    width, height = source.size
    p = progress * progress * (3 - 2 * progress)
    amount = plan.motion_amount
    if plan.motion == "static":
        return source
    zoom = 1 + amount * (p if plan.motion == "zoom_in" else 1 - p if plan.motion == "zoom_out" else 1)
    scaled = source.resize((round(width * zoom), round(height * zoom)), Image.Resampling.LANCZOS)
    dx, dy = scaled.width - width, scaled.height - height
    left = round(dx * (p if plan.motion == "pan_right" else 1 - p if plan.motion == "pan_left" else 0.5))
    return scaled.crop((left, dy // 2, left + width, dy // 2 + height))


def _create_product_video(source: Image.Image, output: Path, plan: VideoPlan) -> None:
    fps = 24
    with imageio.get_writer(output, fps=fps, codec="libx264", quality=8, macro_block_size=2, ffmpeg_params=["-movflags", "+faststart"]) as writer:
        frames = fps * plan.duration_seconds
        for index in range(frames):
            writer.append_data(np.asarray(_video_frame(source, plan, index / (frames - 1))))


def generate_local_product_media(
    plan: MediaPlan,
    requested_media: list[str],
    source_image_url: str | None,
    source_mode: str = "upload",
    product_name: str = "Produit sur mesure",
    brand: str = "MIELMAR",
    category: str = "Cosmétique",
    packaging_hint: str = "",
) -> tuple[str | None, str | None]:
    if plan.unsupported:
        raise ValueError("Consignes non réalisables en local : " + "; ".join(plan.unsupported))
    cutout = _agent_packaging(product_name, brand, category, packaging_hint) if source_mode == "agent" and not source_image_url else _cutout(_load_reference_image(source_image_url))
    if min(cutout.size) < 180:
        raise ValueError("Le produit est trop petit dans la photo pour un rendu net. Ajoutez une photo plus rapprochée.")
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    stem = uuid4().hex
    scenes: dict[str, Image.Image] = {}

    def render(scene: ScenePlan) -> Image.Image:
        key = scene.model_dump_json()
        if key not in scenes:
            scenes[key] = _compose(cutout, scene, _background(scene))
        return scenes[key]

    image_url = video_url = None
    if "image" in requested_media:
        path = OUTPUT_DIRECTORY / f"{stem}.webp"
        render(plan.photo).save(path, format="WEBP", lossless=True, method=4)
        image_url = f"/static/uploads/products/ai/{path.name}"
    if "video" in requested_media:
        path = OUTPUT_DIRECTORY / f"{stem}.mp4"
        _create_product_video(render(plan.video.scene), path, plan.video)
        video_url = f"/static/uploads/products/ai/{path.name}"
    return image_url, video_url
