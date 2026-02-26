from django.urls import path
from . import views

urlpatterns = [
    path('', views.entry, name='entry'),
    path('show/', views.show, name='show'),
    path('show/<int:diary_id>', views.detail, name='detail'),
    
    path('detail/<str:date>/', views.detail_view, name='detail_by_date'),  # ✅ name 변경
    path('diary/<int:diary_id>/', views.detail, name='detail'),  # ✅ 경로 변경
   
    # API
    path('api/diary/dates/', views.diary_dates_api, name='diary_dates_api'),
    path('api/diary/<str:date>/', views.diary_by_date_api, name='diary_by_date_api'),
    path('api/diary/detail/<int:diary_id>/', views.get_diary_detail, name='get_diary_detail'),
    
    path('productivity/', views.productivity, name='productivity'),
    path('generate-image/<int:diary_id>/', views.generate_image, name='generate_image'),
    path('save-image/<int:diary_id>/', views.save_image, name='save_image'),
    path('download/<int:diary_id>/', views.download_image, name='download'),  # ← views.py에 없는 함수!

    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('accounts/signup/', views.signup, name='signup'),  # ← signup_view를 signup으로 수정!
    path('accounts/profile/', views.profile_view, name='profile'),
    path('accounts/settings/', views.settings_view, name='settings'),
    
    path('api/diary/dates/', views.diary_dates_api, name='diary_dates_api'),
    path('api/diary/<str:date>/', views.diary_by_date_api, name='diary_by_date_api'),
]
