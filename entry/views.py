from datetime import datetime

from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404

from .forms import AddForm
from .models import DiaryModel


def entry(request):
    form = AddForm(request.POST or None)

    if request.method == 'POST':

        if form.is_valid():
            note = request.POST['note']
            content = request.POST['content']
            posted_date = datetime.now()
            productivity = request.POST['productivity']
            image_url = request.POST.get('image_url', '').strip()

            todays_diary = DiaryModel()
            todays_diary.note = note
            todays_diary.posted_date = posted_date
            todays_diary.content = content
            todays_diary.productivity = productivity
            if image_url:
                todays_diary.image_url = image_url

            todays_diary.save()

            # 저장 직후 동일 페이지에서 이미지 생성 트리거를 위해 id 전달
            form = AddForm()  # 새 폼으로 초기화
            return render(
                request,
                'entry/add.html',
                {
                    'title': 'Add Entry',
                    'subtitle': "Add what you feel and we'll store it for you.",
                    'add_highlight': True,
                    'addform': form,
                    'new_diary_id': todays_diary.id,
                }
            )

        # 유효하지 않으면 그대로 다시 렌더
        return render(
            request,
            'entry/add.html',
            {
                'title': 'Add Entry',
                'subtitle': "Add what you feel and we'll store it for you.",
                'add_highlight': True,
                'addform': form,
            }
        )

    return render(
        request,
        'entry/add.html',
        {
            'title': 'Add Entry',
            'subtitle': 'Add what you feel and we\'ll store it for you.',
            'add_highlight': True,
            'addform': form,
        }
    )


def show(request):
    """
        We need to show the diaries sorted by date posted in descending order
        5:32 PM 10/19/19 by Arjun Adhikari
    """
    diaries = DiaryModel.objects.order_by('posted_date')
    icon = True if len(diaries) == 0 else None

    return render(
        request,
        'entry/show.html',
        {
            'show_highlight': True,
            'title': 'All Entries',
            'subtitle': 'It\'s all you\'ve written.',
            'diaries': reversed(diaries),
            'icon': icon
        }
    )


def detail(request, diary_id):
    diary = get_object_or_404(DiaryModel, pk=diary_id)

    return render(
        request,
        'entry/detail.html',
        {
            'show_highlight': True,
            'title': diary.note,
            'subtitle': diary.posted_date,
            'diary': diary
        }
    )


def productivity(request):
    
    """
        At max, draw chart for last 10 data.
        11:24 PM 10/19/19 by Arjun Adhikari
    """
    data = DiaryModel.objects.order_by('posted_date')[:10]
    icon = True if len(data) == 0 else None

    return render(
        request,
        'entry/productivity.html',
        {
            'title': 'Productivity Chart',
            'subtitle': 'Keep the line heading up always.',
            'data': data,
            'icon': icon
        }
    )


def generate_image(request, diary_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    # OpenAI 파이프라인 실행 후 URL을 모델에 저장
    try:
        from .Image_making.pipeline import generate_and_attach_image_to_diary

        generate_and_attach_image_to_diary(diary_id, language='en')
        diary = get_object_or_404(DiaryModel, pk=diary_id)
        return JsonResponse({'status': 'ok', 'image_url': diary.image_url})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
