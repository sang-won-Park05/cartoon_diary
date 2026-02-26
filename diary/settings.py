"""
Django settings for diary project.

(정리판) 로컬 기본 DB는 SQLite.
환경변수 DATABASE_URL 이 설정되어 있으면 해당 DB로 접속.
Whitenoise로 정적파일 서빙.
"""

import os
from pathlib import Path
import dj_database_url  # 있으면 사용, 없어도 에러 아님(요구사항에 포함 권장)
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# --------------------------------------------------------------------------------------
# 기본 경로
# --------------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------------------
# 보안/디버그
# --------------------------------------------------------------------------------------
SECRET_KEY = 'vp$k^c^z01df9x4ondzp^y(qlqz^0(p^2zft(2n!5e81hxjmcy'  # 실제 배포 시 환경변수로 분리 권장
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']  # 필요 시 추가

# --------------------------------------------------------------------------------------
# 앱
# --------------------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',
    'entry.apps.EntryConfig',
]

# --------------------------------------------------------------------------------------
# 미들웨어
# --------------------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← SecurityMiddleware 다음에 위치
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'diary.urls'

# --------------------------------------------------------------------------------------
# 템플릿
# --------------------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'diary.wsgi.application'

# --------------------------------------------------------------------------------------
# 데이터베이스: 기본은 SQLite, DATABASE_URL 있으면 그걸로 대체
# --------------------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DATABASE_URL = os.getenv('DATABASE_URL', '')
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=False,
    )

# --------------------------------------------------------------------------------------
# 패스워드 검증
# --------------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --------------------------------------------------------------------------------------
# 국제화
# --------------------------------------------------------------------------------------
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# --------------------------------------------------------------------------------------
# 정적/미디어 파일
# --------------------------------------------------------------------------------------
USE_S3 = os.getenv('USE_S3', 'True') == 'True'

if USE_S3:
    # AWS S3 설정
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'ap-northeast-2')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'

    # S3 파일 설정
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = None  # ACL 비활성화 (버킷에서 ACL을 지원하지 않음)
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = False

    # Media 파일은 S3에 저장 (기본값)
    DEFAULT_FILE_STORAGE = 'diary.storages.MediaStorage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

    # 일기 만화 이미지용 (추후 사용)
    CARTOON_STORAGE = 'diary.storages.CartoonStorage'

    # 프로필 이미지용 (추후 사용)
    PROFILE_STORAGE = 'diary.storages.ProfileStorage'

    # 사용자 캐릭터 이미지용 (추후 사용)
    USER_CHARACTER_STORAGE = 'diary.storages.UserCharacterStorage'

    # Static 파일은 Whitenoise로 서빙 (로컬)
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    STATICFILES_DIRS = [
        BASE_DIR / 'diary' / 'static',
    ]
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    # 로컬 파일 시스템 사용
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    STATICFILES_DIRS = [
        BASE_DIR / 'diary' / 'static',
    ]
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# --------------------------------------------------------------------------------------
# 기본 Primary Key 타입 지정 (Django 3.2+ 권장)
# --------------------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --------------------------------------------------------------------------------------
# Heroku 전용 설정 제거 (django_heroku 불필요)
# --------------------------------------------------------------------------------------
# import django_heroku
# django_heroku.settings(locals())
