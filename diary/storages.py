"""
AWS S3 Storage 설정
업로드되는 파일들을 S3의 media 폴더 내에서 용도별로 분류하여 저장
"""
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    기본 Media 파일 Storage
    location: media/ 폴더에 저장
    """
    location = 'media'
    file_overwrite = False


class CartoonStorage(S3Boto3Storage):
    """
    일기 만화 이미지 Storage
    location: media/cartoon/ 폴더에 저장
    """
    location = 'media/cartoon'
    file_overwrite = False

# 추후 작업 사항

# class ProfileStorage(S3Boto3Storage):
#     """
#     사용자 프로필 이미지 Storage
#     location: media/profile/ 폴더에 저장
#     """
#     location = 'media/profile'
#     file_overwrite = False


# class UserCharacterStorage(S3Boto3Storage):
#     """
#     사용자 캐릭터 이미지 Storage
#     location: media/user_character/ 폴더에 저장
#     """
#     location = 'media/user_character'
#     file_overwrite = False
