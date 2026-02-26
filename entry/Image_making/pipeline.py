"""
OpenAI 기반 일기 → 프롬프트 변환 → 이미지 생성 파이프라인 (URL 우선, 2x2 강제, '하찮은 그림' 스타일).

요구사항 반영:
- 반드시 2x2(정확히 4컷) 레이아웃으로 출력되도록 프롬프트 설계 강화
- 프롬프트도 최대 4개의 패널로 요약(초과 시 4개로 강제)
- 스타일은 '하찮은 그림(초간단 흑백 선 드로잉)' 고정
- 이미지 생성은 OpenAI 임시 URL 우선 사용 (현재 S3 사용 안 함)

사용 예시(로컬 테스트):
    python -m entry.Image_making.pipeline --diary sample_diary.txt --style sample_prompt.txt
"""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

try:
    # OpenAI Python SDK v1
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional import
    OpenAI = None  # type: ignore

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    load_dotenv = None  # type: ignore


BASE_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BASE_DIR
MEDIA_DIR = PROJECT_ROOT / "media" / "generated"


def _ensure_env_loaded() -> None:
    """.env를 로드하고 OPENAI_API 키를 환경변수로 노출한다."""
    if load_dotenv is not None:
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)

    api_key = (
        os.getenv("OPENAI_API")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENAI_API_TOKEN")
    )
    if api_key:
        os.environ.setdefault("OPENAI_API_KEY", api_key)


# ───────────────────────────
# 스타일 / 레이아웃 / 네거티브
# ───────────────────────────

def _doodle_global_style_block() -> str:
    # '하찮은 그림' 고정 스타일 (말풍선/톤/음영 등 제거)
    return (
        "[GLOBAL STYLE]\n"
        "Ultra-simple black-and-white doodle, childlike and amateurish.\n"
        "Single-weight clean line art, minimal detail, white background.\n"
        "Stick-figure-like proportions, naive faces, thin black frames.\n"
        "Short caption under each panel; no speech balloons.\n"
        "No color, no shading, no hatching, no gradients, no photorealism.\n"
    )


def _force_2x2_layout_block() -> str:
    # 2x2 고정 및 '정확히 4컷' 강조
    return (
        "[LAYOUT]\n"
        "A comic strip with EXACTLY four panels in a 2x2 grid (no more than four).\n"
        "Top-left: Panel 1, top-right: Panel 2, bottom-left: Panel 3, bottom-right: Panel 4.\n"
        "Equal panel sizes, clear white gutters, thin visible borders.\n"
        "Do NOT draw 3x2, 1x6, 3x3, collage, storyboard, or any extra frames.\n"
    )


def _ensure_negative_prompt(text: str) -> str:
    multi_panel_block = (
        "6-panel, 9-panel, 3x2 grid, 3x3 grid, storyboard, collage, thumbnail sheet, "
        "comic page layout, more than four panels, extra frames, split panels, "
        "speech balloons, manga tones, shading, gradients, color, photorealism"
    )
    if "[NEGATIVE PROMPT]" not in text:
        return text.rstrip() + "\n\n[NEGATIVE PROMPT]\n" + multi_panel_block + "\n"
    neg_re = re.compile(r"(\[NEGATIVE PROMPT\]\s*)([\s\S]*)\Z")
    return neg_re.sub(lambda m: m.group(1) + (m.group(2).strip() + ", " if m.group(2).strip() else "") + multi_panel_block + "\n", text)


def _normalize_layout_to_2x2(prompt_text: str) -> str:
    """[LAYOUT] 섹션을 2x2 고정 블록으로 대체/추가"""
    layout_re = re.compile(r"\[LAYOUT\][\s\S]*?(?=\n\[PANEL|\n\[NEGATIVE PROMPT|\Z)")
    if layout_re.search(prompt_text):
        prompt_text = layout_re.sub(_force_2x2_layout_block(), prompt_text)
    else:
        prompt_text = _force_2x2_layout_block() + "\n" + prompt_text
    return prompt_text


def _clamp_to_four_panels(prompt_text: str) -> str:
    """[PANEL N] 블록을 최대 4개로 제한(5번째 이상 제거)"""
    panel_re = re.compile(r"\n\[PANEL\s*\d+[^\]]*\][\s\S]*?(?=\n\[PANEL|\n\[NEGATIVE PROMPT|\Z)")
    panels = panel_re.findall("\n" + prompt_text)
    if not panels:
        return prompt_text
    kept = panels[:4]
    prompt_wo_panels = panel_re.sub("", "\n" + prompt_text)
    neg_re = re.compile(r"\n\[NEGATIVE PROMPT\]")
    m = neg_re.search(prompt_wo_panels)
    joined_panels = "".join(kept)
    if m:
        idx = m.start()
        prompt_text = prompt_wo_panels[:idx] + joined_panels + prompt_wo_panels[idx:]
    else:
        prompt_text = prompt_wo_panels + joined_panels
    return prompt_text.strip()


# ───────────────────────────
# 일기 → 4패널 구조화 (JSON)  → 프롬프트 렌더
# ───────────────────────────

def _outline_diary_into_4_panels(diary_text: str, language: str = "en") -> List[Dict[str, Any]]:
    """
    일기를 정확히 4개의 장면으로 압축 (Hook / Complication / HighPoint / Resolution).
    OpenAI 사용; 실패 시 간단 폴백.
    """
    text = (diary_text or "").strip()
    if not text:
        return [{"scene":"", "caption":"", "emotion":""} for _ in range(4)]

    if OpenAI is None:
        # 폴백: 텍스트 4등분
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        chunks = [" ".join(lines[i::4]) for i in range(4)] or ["", "", "", ""]
        return [{"scene": c[:120], "caption": c[:40], "emotion": ""} for c in chunks]

    client = OpenAI()
    lang = "English" if language.lower().startswith("en") else "Korean"

    system = (
        "You are a story editor. Read the diary and compress it into EXACTLY 4 story beats "
        "(Hook, Complication, HighPoint, Resolution). Output STRICT JSON only."
    )
    user = f"""
Return JSON with schema:
{{
  "panels": [
    {{"role":"Hook|Complication|HighPoint|Resolution", "scene": "<concise scene>", "caption": "<short {lang} caption>", "emotion":"<one word>"}}
  ]
}}

Rules:
- EXACTLY 4 items in "panels".
- One main action per panel; merge minor events.
- Keep captions short (<= 12 words). Use {lang}.
DIARY:
{text}
"""
    import json
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    try:
        data = json.loads(resp.choices[0].message.content or "{}")
        panels = (data.get("panels") or [])[:4]
        while len(panels) < 4:
            panels.append({"scene": "", "caption": "", "emotion": ""})
        return [{"scene": p.get("scene",""), "caption": p.get("caption",""), "emotion": p.get("emotion","")} for p in panels]
    except Exception:
        return [{"scene":"", "caption":"", "emotion":""} for _ in range(4)]


def _render_prompt(style_template: str, panels: List[Dict[str, Any]]) -> str:
    """선택된 스타일 템플릿과 4패널 데이터를 결합해 최종 프롬프트를 생성."""
    style_template = (style_template or "").strip()
    # 스타일 템플릿이 주어지면 그대로 사용, 없으면 기본 '하찮은 그림' 스타일과 2x2 레이아웃 사용
    if style_template:
        header = style_template.rstrip() + "\n\n"
    else:
        header = _doodle_global_style_block() + "\n" + _force_2x2_layout_block() + "\n\n"

    def ptext(idx: int, p: Dict[str, Any]) -> str:
        scene = (p.get("scene") or "").strip()
        emo   = (p.get("emotion") or "").strip()
        cap   = (p.get("caption") or "").strip()
        body = f"Scene: {scene}\n"
        if emo:
            body += f"Emotion: {emo}\n"
        if cap:
            body += f"Caption: {cap}\n"
        return f"[PANEL {idx}]\n{body}"

    # 정확히 4개만
    p1 = ptext(1, panels[0] if len(panels) > 0 else {})
    p2 = ptext(2, panels[1] if len(panels) > 1 else {})
    p3 = ptext(3, panels[2] if len(panels) > 2 else {})
    p4 = ptext(4, panels[3] if len(panels) > 3 else {})

    prompt = header + "\n".join([p1, p2, p3, p4]) + "\n"
    prompt = _ensure_negative_prompt(prompt)
    prompt = _normalize_layout_to_2x2(prompt)
    prompt = _clamp_to_four_panels(prompt)
    return prompt


def build_prompt_from_diary(diary_text: str, style_template: str, language: str = "en") -> str:
    """
    일기를 sample_prompt 스타일로 변환하되, 반드시 2x2(4패널)만 생성되도록 강제.
    - style_template 인자로 뭐가 오든, 내부 '하찮은 그림' 스타일+2x2 레이아웃로 통일.
    """
    _ensure_env_loaded()
    panels = _outline_diary_into_4_panels(diary_text, language=language)
    prompt = _render_prompt(style_template=style_template, panels=panels)
    return prompt


# ───────────────────────────
# 이미지 생성 (URL 우선 반환)
# ───────────────────────────

def generate_image(prompt: str, size: str = "1024x1024") -> Tuple[Optional[str], Optional[Path]]:
    """
    DALL·E 3로 이미지를 생성한다.
    반환: (url, local_path)
      - url: OpenAI가 제공하는 임시 URL(제공 시)
      - local_path: base64 응답일 경우 저장한 로컬 파일 경로
    """
    _ensure_env_loaded()

    if OpenAI is None:
        return None, None

    client = OpenAI()

    # size는 1024x1024 고정
    resp = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        n=1,
    )

    data = resp.data[0]
    url = getattr(data, "url", None)
    b64 = getattr(data, "b64_json", None)

    if url:
        return url, None

    if b64:
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        file_path = MEDIA_DIR / "diary_4cut_1024.png"
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(b64))
        return None, file_path

    return None, None


def generate_and_attach_image_to_diary(
    diary_id: int,
    style_path: Path = PROJECT_ROOT / "sample_prompt.txt",
    language: str = "en",
) -> Tuple[str, Optional[str], Optional[Path]]:
    """
    특정 DiaryModel(id)에 대해 프롬프트 생성 및 이미지 생성 후
    diary.image_url에 URL(또는 로컬 파일 경로)을 저장한다.
    """
    from entry.models import DiaryModel  # 지연 import

    diary = DiaryModel.objects.get(pk=diary_id)
    diary_text = f"Title: {diary.note}\nDate: {diary.posted_date}\n\n{diary.content}"

    style_text = ""
    try:
        if style_path and Path(style_path).exists():
            style_text = Path(style_path).read_text(encoding="utf-8")
    except Exception:
        style_text = ""

    prompt = build_prompt_from_diary(diary_text, style_template=style_text, language=language)

    url, local_path = generate_image(prompt, size="1024x1024")

    if url:
        diary.temp_image_url = url
    elif local_path:
        try:
            from django.conf import settings  # type: ignore
            rel_path = local_path.relative_to(settings.MEDIA_ROOT)
            diary.temp_image_url = settings.MEDIA_URL.rstrip("/") + "/" + str(rel_path).replace("\\", "/")
        except Exception:
            diary.temp_image_url = str(local_path)
    # 최종 프롬프트 저장
    diary.final_prompt = prompt
    diary.save(update_fields=["temp_image_url", "final_prompt"])
    return prompt, url, local_path


def save_temp_image_to_s3(diary_id: int) -> Optional[str]:
    """
    DiaryModel의 temp_image_url에서 이미지를 다운로드하고
    S3에 업로드한 후 image_url에 저장
    반환: S3 URL (성공 시)
    """
    import requests
    from io import BytesIO
    from datetime import datetime
    from entry.models import DiaryModel

    try:
        # 1. DiaryModel 조회
        diary = DiaryModel.objects.get(pk=diary_id)

        if not diary.temp_image_url:
            return None

        # 2. temp_image_url에서 이미지 다운로드
        response = requests.get(diary.temp_image_url, timeout=30)
        response.raise_for_status()
        image_data = BytesIO(response.content)

        # 3. S3에 업로드
        try:
            from django.conf import settings
            from diary.storages import CartoonStorage

            # 파일명 생성: diary_{id}_{timestamp}.png
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"diary_{diary_id}_{timestamp}.png"

            # CartoonStorage 사용 (media/cartoon/ 폴더에 저장)
            storage = CartoonStorage()
            saved_path = storage.save(file_name, image_data)

            # S3 URL 생성
            s3_url = storage.url(saved_path)

            # 4. image_url에 저장
            diary.image_url = s3_url
            diary.save(update_fields=["image_url"])

            return s3_url

        except Exception as e:
            print(f"S3 upload failed: {e}")
            return None

    except DiaryModel.DoesNotExist:
        return None
    except requests.RequestException as e:
        print(f"Image download failed: {e}")
        return None


def run_sample(
    diary_path: Path = PROJECT_ROOT / "sample_diary.txt",
    style_path: Path = PROJECT_ROOT / "sample_prompt.txt",
    language: str = "en",
) -> Tuple[str, Optional[str], Optional[Path]]:
    """
    샘플 파일을 사용해 전체 파이프라인 실행.
    반환: (prompt_text, url, local_path)
    """
    diary_text = diary_path.read_text(encoding="utf-8")
    style_text = ""
    try:
        if style_path and Path(style_path).exists():
            style_text = Path(style_path).read_text(encoding="utf-8")
    except Exception:
        style_text = ""
    prompt = build_prompt_from_diary(diary_text, style_template=style_text, language=language)
    url, local_path = generate_image(prompt, size="1024x1024")
    return prompt, url, local_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Diary → Prompt → DALL·E3 pipeline (2x2 enforced, doodle style, URL-first)")
    parser.add_argument("--diary", type=str, default=str(PROJECT_ROOT / "sample_diary.txt"))
    parser.add_argument("--style", type=str, default=str(PROJECT_ROOT / "sample_prompt.txt"))
    parser.add_argument("--lang", type=str, default="en", help="en or ko")
    args = parser.parse_args()

    prompt_text, url, local_path = run_sample(
        diary_path=Path(args.diary), style_path=Path(args.style), language=args.lang
    )

    print("===== GENERATED PROMPT =====\n")
    print(prompt_text)
    print("\n===== IMAGE RESULT =====")
    if url:
        print("URL:", url)
    if local_path:
        print("Saved:", local_path)
