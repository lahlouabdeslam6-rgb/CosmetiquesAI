import json
from unittest.mock import AsyncMock

import imageio.v2 as imageio
import numpy as np
import pytest
from PIL import Image

from app.services import local_media
from app.services.media_plan import MediaPlan, ScenePlan, VideoPlan, plan_media, apply_explicit_constraints


def test_executed_plan_changes_background_layout_without_redrawing_product():
    product = Image.new("RGBA", (60, 100), (20, 40, 180, 255))
    scene_a = ScenePlan(background="solid", background_color="#ffffff", shadow=0)
    scene_b = ScenePlan(background="solid", background_color="#dd9933", format="portrait", product_height=0.8, shadow=0)
    a = local_media._compose(product, scene_a, local_media._background(scene_a))
    b = local_media._compose(product, scene_b, local_media._background(scene_b))
    assert a.size == (1080, 1080)
    assert b.size == (864, 1536)
    assert a.getpixel((0, 0)) == (255, 255, 255)
    assert b.getpixel((0, 0)) == (221, 153, 51)
    for image in (a, b):
        assert image.getpixel((image.width // 2, image.height // 2)) == (20, 40, 180)


def test_agent_enforces_literal_instructions_when_model_proposes_other_values():
    plan = MediaPlan(summary="", photo=ScenePlan(shadow=0.5, reflection=0.4), video=VideoPlan(motion="static"))
    apply_explicit_constraints({"image_description": "Fond orange uni #dd9933, sans ombre ni reflet, 9:16", "video_description": "Même décor, zoom arrière, 8 secondes"}, plan)
    for scene in (plan.photo, plan.video.scene):
        assert scene.background_color == "#dd9933"
        assert scene.format == "portrait"
        assert scene.shadow == scene.reflection == 0
    assert plan.video.duration_seconds == 8
    assert plan.video.motion == "zoom_out"


def test_video_obeys_motion_duration_aspect_and_has_no_black_start(tmp_path):
    source = Image.new("RGB", (64, 96), "white")
    source.paste(Image.new("RGB", (24, 40), "red"), (20, 28))
    plan = VideoPlan(motion="zoom_out", duration_seconds=3, motion_amount=0.12)
    path = tmp_path / "motion.mp4"
    local_media._create_product_video(source, path, plan)
    reader = imageio.get_reader(path)
    try:
        assert reader.get_meta_data()["size"] == source.size
        assert reader.get_meta_data()["duration"] == pytest.approx(3, abs=0.1)
        first = reader.get_data(0)
        last = reader.get_data(71)
        assert first.mean() > 150
        assert np.count_nonzero(first[:, :, 1] < 80) > np.count_nonzero(last[:, :, 1] < 80)
    finally:
        reader.close()
    static = VideoPlan(motion="static")
    assert np.array_equal(local_media._video_frame(source, static, 0), local_media._video_frame(source, static, 1))


@pytest.mark.parametrize("url", ["https://other/image.png", "/static/uploads/products/../../../../etc/passwd", "/static/uploads/products/ai/result.png"])
def test_reference_rejects_traversal_remote_and_generated_images(url):
    with pytest.raises(ValueError):
        local_media._load_reference_image(url)


def test_unsupported_request_does_not_render(monkeypatch):
    cutout = AsyncMock()
    monkeypatch.setattr(local_media, "_cutout", cutout)
    with pytest.raises(ValueError, match="360"):
        local_media.generate_local_product_media(MediaPlan(summary="", limitations=[{"request_quote": "360°", "reason": "360°"}]), ["video"], "/static/x.png")
    cutout.assert_not_called()


@pytest.mark.asyncio
async def test_planner_receives_separate_current_descriptions_and_previous_feedback(monkeypatch):
    captured = {}
    class Response:
        def raise_for_status(self): pass
        def json(self): return {"message": {"content": MediaPlan(summary="Fond orange", video=VideoPlan(duration_seconds=8)).model_dump_json()}}
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, json):
            captured.update(json)
            return Response()
    monkeypatch.setattr("app.services.media_plan.httpx.AsyncClient", Client)
    request = {"image_description": "fond orange", "video_description": "zoom arrière 8 secondes", "feedback": "plus grand"}
    previous = {"photo": {"background_color": "#ffffff"}}
    await plan_media(request, previous)
    sent = json.loads(captured["messages"][1]["content"])
    assert sent == {"request": request, "previous_plan": previous}
    assert captured["keep_alive"] == 0
    assert set(captured["format"]["$defs"]["ScenePlan"]["required"]) == set(captured["format"]["$defs"]["ScenePlan"]["properties"])
