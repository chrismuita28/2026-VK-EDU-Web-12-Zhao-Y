from django.shortcuts import render
from django.core.paginator import Paginator

QUESTIONS = [
    {
        "id": i,
        "title": i,
        "text": f"TEXT {i}",
    }
    for i in range(30)
]

ANSWERS = [
    {
        "user": i,
        "text": f"TEXT {i}",
    }
    for i in range(10)
]

TAGS = ['python', 'javascript', 'css', 'html', 'bootstrap']

def paginate(request, pagination_list, per_list=4):
    if not pagination_list:
        return Paginator([], per_list).get_page(1)
    
    try:
        per_list = int(per_list)
        if per_list <= 0:
            per_list = 4
    except (ValueError, TypeError):
        per_list = 4
    
    paginator = Paginator(pagination_list, per_list)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)
    return page_object

def index(request):
    page_object = paginate(request, QUESTIONS)
    return render(request, "questions/index.html", context={"questions": page_object.object_list, "page_obj": page_object, "tags": TAGS})

def hot(request):
    page_object = paginate(request, QUESTIONS)
    return render(request, "questions/hot.html", context={"questions": page_object.object_list, "page_obj": page_object, "tags": TAGS})

def tag(request, tag_name):
    page_object = paginate(request, QUESTIONS)
    return render(request, "questions/tag.html", context={"questions": page_object.object_list, "page_obj": page_object, "tag_name": tag_name, "tags": TAGS})

def question(request, question_num):
    page_object = paginate(request, ANSWERS)
    return render(request, "questions/question.html", context={"answers": page_object.object_list, "page_obj": page_object, "question_num": question_num, "tags": TAGS})

def ask(request):
    return render(request, "questions/ask.html")
