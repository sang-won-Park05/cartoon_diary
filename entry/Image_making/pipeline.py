"""
OpenAI 기반 일기 → 프롬프트 변환 → 이미지 생성 파이프라인.

요구사항 반영
- 반드시 2x2(4컷) 레이아웃으로 출력
- 프롬프트도 최대 4개의 패널로 요약(초과 시 4개로 강제)

사용 예시(로컬 테스트):
    python -m entry.Image_making.pipeline --diary sample_diary.txt --style sample_prompt.txt
"""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path
from typing import Optional, Tuple

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


def _force_2x2_layout_block() -> str:
    return (
        "[LAYOUT]\n"
        "A 4-panel comic strip arranged in a 2x2 grid.\n"
        "Top-left: Panel 1, top-right: Panel 2, bottom-left: Panel 3, bottom-right: Panel 4.\n"
        "Each panel has equal size, clear white space between them, and visible frame lines.\n"
    )


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


def build_prompt_from_diary(diary_text: str, style_template: str, language: str = "en") -> str:
    """
    일기를 sample_prompt 스타일로 변환하되, 반드시 2x2(4패널)만 생성되도록 강제.
    """

    _ensure_env_loaded()

    if OpenAI is None:
        header = "\n[DIARY SUMMARY]\n" + diary_text.strip() + "\n"
        rough = style_template.strip() + "\n\n" + _force_2x2_layout_block() + header
        return _clamp_to_four_panels(_normalize_layout_to_2x2(rough))

    client = OpenAI()

    system = (
        "You are a prompt-writer for DALL·E 3. "
        "Rewrite the user's diary into a structured 4-panel comic prompt. "
        "Strictly preserve the section headers from the provided STYLE TEMPLATE: "
        "[GLOBAL STYLE], [LAYOUT], [PANEL 1 ... 4], [NEGATIVE PROMPT]. "
        "Fill in concrete scene details based on the diary. "
        "Keep captions short and natural. "
        "Respond only with the final prompt text. "
        "Hard constraints: exactly 4 panels only; a 2x2 grid; no extra panels."
    )

    lang_hint = (
        "Write all output in English." if language.lower().startswith("en") else "Write all output in Korean."
    )

    user = (
        "STYLE TEMPLATE:\n" + style_template.strip() +
        "\n\nUSER DIARY:\n" + diary_text.strip() +
        f"\n\nRequirements:\n"
        f"- EXACTLY 4 panels arranged in a 2x2 grid.\n"
        f"- {lang_hint}\n"
        f"- Keep the [NEGATIVE PROMPT] section.\n"
        f"- Replace panel scenes and captions to match the diary.\n"
        f"- Do not add any extra sections or panels beyond 1..4.\n"
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = resp.choices[0].message.content or ""
    content = content.strip()
    content = _normalize_layout_to_2x2(content)
    content = _clamp_to_four_panels(content)
    return content


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

    if b64:
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        file_path = MEDIA_DIR / "diary_4cut_1024.png"
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(b64))
        return None, file_path

    return url, None


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
    style_text = Path(style_path).read_text(encoding="utf-8")

    diary_text = f"Title: {diary.note}\nDate: {diary.posted_date}\n\n{diary.content}"
    prompt = build_prompt_from_diary(diary_text, style_text, language=language)

    url, local_path = generate_image(prompt, size="1024x1024")

    if url:
        diary.image_url = url
    elif local_path:
        try:
            from django.conf import settings  # type: ignore

            rel_path = local_path.relative_to(settings.MEDIA_ROOT)
            diary.image_url = settings.MEDIA_URL.rstrip("/") + "/" + str(rel_path).replace("\\", "/")
        except Exception:
            diary.image_url = str(local_path)

    diary.save(update_fields=["image_url"])
    return prompt, url, local_path


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
    style_text = style_path.read_text(encoding="utf-8")
    prompt = build_prompt_from_diary(diary_text, style_text, language=language)
    url, local_path = generate_image(prompt, size="1024x1024")
    return prompt, url, local_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Diary → Prompt → DALL·E3 pipeline")
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

