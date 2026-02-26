from django.contrib import admin
from .models import DiaryModel

# Register your models here.
class DiaryModelAdmin(admin.ModelAdmin):
    list_display = ['note', 'posted_date', 'temp_image_url', 'image_url']

admin.site.register(DiaryModel, DiaryModelAdmin)
