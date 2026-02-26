# 제품 요구사항 문서(PRD) — 4컷 일기 카툰 생성 앱

- 문서 버전: 0.3 (수정)
- 작성일: 2025-10-13
- 문서 상태: Draft

## 1. 제품 개요
- 이미지 생성 모델을 사용하여 사용자의 일기를 기반으로 4컷 카툰 이미지를 자동 생성하는 웹 앱.
- 사용자는 일기를 작성하고 저장하면 생성된 카툰을 캘린더에서 날짜별로 열람/관리.

## 2. 목표와 비범위
- 목표
  - 일기 쓰기 습관 형성에 도움을 주는 즉각적이고 즐거운 보상(4컷 카툰) 제공
  - 1분 내 생성 완료, 간단한 사용 흐름, 낮은 진입 장벽
  - 개인 기록을 바탕으로 한 프라이빗한 경험 우선
- 비범위(초기)
  - 고급 이미지 편집 툴(말풍선/스티커 편집 등)
  - 웹 기반 서비스

## 3. 성공 지표(KPIs)
- 4컷 생성 완료율(생성 성공/요청 비율) ≥ 95%
- 평균 생성 소요시간 T90 ≤ 90초 (프롬프트+이미지 전체)
- 한 달 캘린더 완주율

## 4. 대상 사용자/페르소나
- 가벼운 일기 습관을 만들고 싶은 사용자
- 텍스트 기록을 시각적으로 간직/공유하고 싶은 사용자(사적 공유 중심)

## 5. 사용자 스토리(요구사항 형태)
- “나는 계정을 만들고 간단한 프로필을 설정하고 싶다.”
- “나는 오늘의 일기를 작성하고, 1분 내 4컷 카툰을 받고 싶다.”
- “마음에 들지 않으면 동일 일기에 대해 재생성(프롬프트/시드 변경)하고 싶다.”
- “달력에서 날짜별로 내가 작성한 일기와 카툰을 다시 보고 싶다.”
- “완성된 4컷을 저장(다운로드)하거나 개인적으로 공유하고 싶다(선택).”

## 6. 핵심 기능(MVP)과 수용 기준(AC)
1) 인증/프로필
   - 이메일/비밀번호 기반 로그인/회원가입
   - 프로필(닉네임, 프로필사진) 편집 가능
   - AC: 신규 사용자 1분 이내 온보딩 완료, 세션 유지 7일

2) 일기 작성
   - 날짜별 1개의 일기 작성(텍스트 최소 20자 권장)
   - AC: 저장 즉시 버전 관리 및 자동 임시저장(30초 간격, 선택)

3) 프롬프트 생성(OpenAI GPT 활용)
   - 일기 텍스트를 분석해 4컷 각각의 장면 설명, 등장인물, 스타일, 감정 톤을 포함하는 프롬프트 생성
   - 일관된 캐릭터/스타일을 유지하도록 시스템 지침 포함
   - AC: 프롬프트 생성 3초 내, 구조적 JSON/마크다운 출력

4) 이미지 생성(OpenAI DALL·E 3, 추후 HuggingFace Qwen/Qwen-Image)
   - 4개의 이미지(컷) 생성, 동일 스타일·캐릭터 일관성 유지 시도
   - 해상도 기본 512x512, 최대 768x768(선택)
   - AC: 요청당 4컷 전부 성공 생성 ≥ 95%, 실패 시 자동 재시도 ≤ 1회

5) 4컷 카툰 합성/표시
   - 2x2 그리드 합성
   - 전체 컷 다운로드
   - AC: 합성 이미지와 개별 컷 모두 보기/다운로드 가능

6) 캘린더/히스토리
   - 월 단위 캘린더 UI에서 날짜별 일기/카툰 썸네일 표시
   - 검색/필터: 포함된 단어
   - AC: 월 전환 200ms 내, 썸네일 로딩 지연 최소화(프리패치)

7) 재생성/관리
   - 동일 일기에 대해 프롬프트나 시드 변경 후 재생성
   - AC: 이전 버전 보관, 가장 만족한 버전을 기본 표시

## 7. 기술 스택(초안 근거: prd_draft.md)
- 웹 서버: Django
- 데이터베이스: SQLite
- 프롬프트 생성: OpenAI GPT
- 이미지 생성: OpenAI DALL·E 3 (추후: Hugging Face Hub — `Qwen/Qwen-Image`,`Anime-style-flux-lora-Large`)

## 8. 시스템 아키텍처(개요)
Django 웹 애플리케이션 (단일 구조)
├── Django Views/Templates (웹 UI)
├── Django ORM (데이터베이스)
├── Background Tasks (Celery/Django-RQ)
└── 외부 API 연동
    ├── OpenAI API (GPT로 프롬프트, Images API로 생성)
    └── HuggingFace API (추후 이미지 생성 모델 반영)

- 비동기 작업: Celery를 통한 이미지 생성

## 9. 주요 흐름(파이프라인)
### 일기 작성 → 4컷 생성
0) 로그인/회원가입
1) 사용자가 일기 작성 (Django Form)
2) "생성" 버튼 클릭 → Celery Task 등록
3) Celery Worker 실행:
   - OpenAI GPT-4: 일기 → 4컷 프롬프트 생성 (JSON)
   - OpenAI GPT-4 dall-e-3: 각 프롬프트 → 4개 이미지 생성 (추후: HF-Qwen모델 이용)
   - Pillow: 4컷 → 2x2 그리드 합성
4) "재생성" 버튼 클릭 → 이미지 생성 다시 시도(S3 저장 안됨)
5) "저장" 버튼 클릭 → AWS S3: 이미지 저장, Django: 날짜/일기본문/S3 URL 저장
6) Cartoon status = 'succeeded'
7) 캘린더: 해당 날짜 일기/이미지 불러오기 및 다운로드


## 9. 주요 흐름(파이프라인)
### 일기 작성 → 4컷 생성
0) 로그인/회원가입
1) 사용자가 일기 작성 (Django Form)
2) "생성" 버튼 클릭 → Celery Task 등록
3) Celery Worker 실행:
   - OpenAI GPT-4: 일기 → 4컷 프롬프트 생성 (JSON)
   - OpenAI GPT-4 dall-e-3: 각 프롬프트 → 4개 이미지 생성 (추후: HF-Qwen모델 이용)
   - Pillow: 4컷 → 2x2 그리드 합성
4) "재생성" 버튼 클릭 → 이미지 생성 다시 시도(S3 저장 안됨)
5) "저장" 버튼 클릭 → AWS S3: 이미지 저장, Django: 날짜/일기본문/S3 URL 저장
6) Cartoon status = 'succeeded'
7) 캘린더: 해당 날짜 일기/이미지 불러오기 및 다운로드

일기 작성 → "이미지 생성" 클릭 → 이미지 생성(미리보기 화면) 및 DB temp_url 저장 → "저장" 클릭 → S3 업로드, DB image_url저장
														  → "재생성" 클릭 → 이미지 다시 생성, DB temp_url 추가 



### 캘린더 조회
1) /calendar 접속
2) Django가 해당 월 DiaryEntry 조회
3) 날짜별 일기 + 카툰 썸네일 표시

## 10. 데이터 모델(최종)

1. user table
| 컬럼              | 타입           | 설명           |
| --------------- | ------------ | -------------    |
| `seq_id`        | SERIAL / INT | PK, 사용자 고유 ID, 자동 증가     |
| `email_id`      | VARCHAR      | 로그인 ID(UNIQUE, NOT NULL)         |
| `password_hash` | VARCHAR      | 비밀번호 해시(NOT NULL)       |
| `username`      | VARCHAR      | 사용자 이름                 |
| `nickname`      | VARCHAR      | 사용자 닉네임(미설정 시 username 사용)        |
| `created_at`    | TIMESTAMP    | 계정 생성 시각               |
| `last_login_at`    | TIMESTAMP    | 마지막 로그인 시간         |



2. diary table
| 컬럼           | 타입            | 설명                               |
| ------------  | ------------- | --------------------------------------- |
| `seq_id`     | SERIAL / INT  | PK, 일기 고유 ID, 자동 증가        |
| `user_id`    | INT / VARCHAR | user.seq_id FK, 작성자(User) 참조      |
| `content`    | TEXT          | 일기 본문 내용 (NOT NULL)              |
| `diary_date` | DATE          | 일기 작성 날짜 (UNIQUE, NOT NULL)         |
| `image_url`  | VARCHAR       | 생성한 네컷 이미지 URL                  |
| `is_deleted`   | VARCHAR       | 삭제 여부 관리 [Y/N]    |



## 11. Django Template 기반 웹앱 -> (🔒 = 로그인 필요, 🟢 = 공개)

### 인증/회원
- GET/POST /accounts/signup 🟢
- GET/POST /accounts/login 🟢
- POST /accounts/logout 🔒
- GET/POST /accounts/profile 🔒

### 일기
- GET /diaries 🔒
- GET/POST /diaries/new 🔒
- GET /diaries/{id} 🔒
- GET/POST /diaries/{id}/edit 🔒
- POST /diaries/{id}/delete 🔒

### 카툰 생성
- POST /diaries/{id}/generate 🔒 — Celery Task 시작
- GET /diaries/{id}/generating 🔒 — 대기 페이지
- GET /diaries/{id}/result 🔒 — 결과 페이지
- POST /diaries/{id}/regenerate 🔒
- POST /diaries/{id}/save 🔒
- GET /diaries/{id}/download 🔒

### 캘린더
- GET /calendar 🔒 (쿼리: ?month=YYYY-MM)

### 기타
- GET / 🟢
- GET /admin/ 🔒

## 12. UX 화면(핵심)
- 회원가입: 이메일, 비밀번호, 닉네임
- 로그인: 이메일, 비밀번호
- 프로필: 닉네임/프로필 이미지 편집
- 일기 작성 화면(날짜, 본문 텍스트, 테마)
- 생성 대기/진행 표시(큐 상태, 남은 예상 시간)
- 결과 화면(카툰 4컷 그리드, 저장, 다운로드, 재생성)
- 캘린더 화면(저장된 일기,카툰 불러오기)

## 13. MVP 개발 시 주의사항
1. 에러 처리: AI 생성 실패 시 사용자에게 알림
2. 보안: 내 일기는 나만 볼 수 있게
3. 비용 관리: OpenAI/HuggingFace API는 유료
   - 개발 중에는 Mock 데이터 사용
   - 무한 루프나 대량 호출 조심
   - API 호출 실패 시 최대 1회만 재시도

