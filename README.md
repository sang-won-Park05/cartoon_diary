**일기 4컷 생성 다이어리 (SKN16-4th-1Team)**

- 하루의 기록을 작성하면 OpenAI DALL·E 3를 사용해 2x2(총 4컷) 만화 이미지를 생성합니다.
- 생성 이미지는 임시 URL로 미리보기 후, 원하면 S3에 저장해 영구 URL로 관리합니다.
- 생산성 점수(0~10) 기록, 리스트/상세 보기, 캘린더 탐색, 생산성 차트 등 기본 다이어리 기능을 지원합니다.

----------------------------------------

**주요 기능**

- 다이어리 작성/수정: 제목, 본문, 날짜 선택, 생산성 점수 기록
- 4컷 이미지 생성: 일기 내용을 4개의 장면으로 요약해 2x2 그리드로 강제 생성
- 스타일 선택: `simple`(낙서풍), `ani`(애니풍), `real`(보다 사실적) 프롬프트 템플릿 제공
- 미리보기와 저장: 임시 URL로 미리보기 → S3 저장 시 영구 URL로 전환
- 리스트/상세 보기: 날짜별/항목별 조회, 상세 화면에서 이미지 다운로드
- 생산성 차트: 최근 기록을 기반으로 라인 차트 표시
- 사용자 계정: 회원가입/로그인/로그아웃, 프로필(로컬 아바타), 설정 화면

----------------------------------------
**아키 텍처**
<img width="3668" height="1157" alt="Untitled_diagram-2025-10-20-034225" src="https://github.com/user-attachments/assets/9fe373c2-2cca-46d7-b4f1-143141ee009f" />
----------------------------------------

**기술 스택**

- Backend: `Python 3.x`, `Django 4.2`
- AI/이미지: `openai (Images/DALL·E 3)`, 커스텀 프롬프트 파이프라인
- Storage/배포 보조: `django-storages`, `boto3`(AWS S3), `whitenoise`
- DB: 기본 `SQLite`(로컬), 환경변수 `DATABASE_URL` 지정 시 Postgres 등으로 전환 (`dj-database-url`)
- Frontend: `Bootstrap 4`, `jQuery`, `Quill` 에디터, `Chart.js`, `Lucide Icons`, Google Fonts
- 기타: `python-dotenv`, `requests`, `Pillow`, `gunicorn`(배포 환경)

----------------------------------------

**프로젝트 구조(요약)**

- `diary/` Django 프로젝트 설정, URL, S3 스토리지 백엔드(`storages.py`)
- `entry/` 앱: 모델/뷰/폼/템플릿, 이미지 파이프라인(`Image_making/pipeline.py`)
- `entry/templates/entry/` 화면 템플릿들 (`add.html`, `show.html`, `detail.html`, `login.html`, `signup.html` 등)
- `entry/static/entry/` 정적 리소스(`css/main.css`, `js/ui.js` 등)
- 루트: `requirements.txt`, 샘플 프롬프트(`sample_prompt_*.txt`), 샘플 일기(`sample_diary.txt`)

----------------------------------------

**로컬 실행 방법**

1) 가상환경 및 의존성 설치 (Windows PowerShell 예시)

```
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

2) 환경변수(.env) 설정 — 프로젝트 루트에 `.env` 파일 생성

```
# OpenAI
OPENAI_API=YOUR_OPENAI_KEY              # 또는 OPENAI_API_KEY/OPENAI_API_TOKEN

# AWS S3 (USE_S3=true일 때 사용)
USE_S3=True
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...
AWS_S3_REGION_NAME=ap-northeast-2

# 데이터베이스(선택)
# DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/DBNAME
```

3) 마이그레이션/관리자 생성/서버 실행

```
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

관리자 계정은 실행 중 프롬프트에 따라 직접 입력해 생성합니다.

----------------------------------------

**이미지 생성 동작 개요**

- 경로: `entry/Image_making/pipeline.py`
- 일기 본문을 4개의 장면으로 요약하고, 2x2 레이아웃(정확히 4컷)과 낙서풍 기본 스타일을 강제 적용합니다.
- 스타일 템플릿 파일: 루트의 `sample_prompt_simple.txt`, `sample_prompt_ani.txt`, `sample_prompt_real.txt`
- UI 흐름: 일기 저장 → 생성 요청 → 임시 이미지 URL 미리보기(`temp_image_url`) → 저장 시 S3 업로드(`image_url`)
- 상세 화면에서 이미지 다운로드 버튼 제공

참고 API 엔드포인트
- `POST /generate-image/<diary_id>/` 4컷 이미지 임시 생성(스타일 선택 가능)
- `POST /save-image/<diary_id>/` 임시 이미지를 S3로 저장하고 영구 URL 반영
- `GET  /download/<diary_id>/` 생성 이미지를 파일로 다운로드

----------------------------------------

**주요 화면(이미지는 직접 추가 예정)**
<img width="1899" height="906" alt="2025-10-20_151311" src="https://github.com/user-attachments/assets/28a3629f-f169-48a5-87fa-ef19d20c9f9c" />

- 메인 작성 화면: 일기 작성, 테마/날짜 선택, 이미지 생성/저장
- 목록 화면: 작성한 일기 카드 리스트
- 상세 화면: 4컷 이미지 + 본문 + 같은 날 항목 리스트, 다운로드
- 생산성 차트: 최근 기록 라인 차트
- 인증/프로필/설정: 로그인, 회원가입, 프로필(로컬 아바타), 설정

----------------------------------------

**유의 사항**

- OpenAI 이미지 생성은 비용이 발생할 수 있습니다. 키/과금 정책을 확인하세요.
- S3 사용 시 버킷 공개 범위/정책을 점검하세요. 로컬 개발은 `USE_S3=False`로 파일시스템 사용 가능.
- 기본 DB는 SQLite입니다. 운영환경에서는 `DATABASE_URL`로 외부 DB 사용을 권장합니다.

----------------------------------------

**라이선스/저작권**

- 저장소 내 아이콘, 폰트, CDN 스크립트는 각 라이선스 정책을 따릅니다.
- 본 애플리케이션 코드는 팀/내부 정책에 따릅니다.

