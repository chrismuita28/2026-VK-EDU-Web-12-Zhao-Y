from django.shortcuts import render
from django.core.paginator import Paginator

QUESTIONS = [
    {
        "title": i,
        "text": f"TEXT {i}",
    }
    for i in range(30)
]

def index(request):
    page_number = int(request.GET.get("page", 1))
    page = Paginator(QUESTIONS, 4)
    page_object = page.page(page_number)
    return render(request, "questions/index.html", context={"questions": page_object.object_list, "page_obj": page_object})

def hot(request):
    return render(request, "questions/hot.html", context={"questions": QUESTIONS[::-1]})
