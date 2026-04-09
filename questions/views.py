from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

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

def paginate(request, objects_list, per_page=4):
    if not objects_list:
        objects_list = []
    
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get("page")
    
    try:
        page_object = paginator.page(page_number)
    except PageNotAnInteger:
        page_object = paginator.page(1)
    except EmptyPage:
        page_object = paginator.page(paginator.num_pages)
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
