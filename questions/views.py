from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count
from questions.models import Question, Tag, Profile
from typing import TYPE_CHECKING
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy

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

def _get_profiles():
    return {"profiles": Profile.objects.all().order_by("nickname")[:20]}

def _get_tags():
    return {"tags": Tag.objects.all().order_by("name")[:20]}

def _render_question_list(request, queryset, template_name, extra_context=None):
    page_object = paginate(request, queryset)
    context = {
        **_get_profiles(),
        **_get_tags(),
        "questions": page_object.object_list,
        "page_obj": page_object
    }
    if extra_context:
        context.update(extra_context)
    return render(request, template_name, context)

@login_required(login_url=reverse_lazy("core:login"))
def index(request):
    return _render_question_list(request, Question.objects.new(), "questions/index.html")

def hot(request):
    return _render_question_list(request, Question.objects.hot(), "questions/hot.html")

def tag(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    return _render_question_list(request, Question.objects.by_tag(tag), "questions/tag.html", {"tag": tag})

def question(request, question_id):
    question = get_object_or_404(Question.objects.annotate(likes_count=Count("likes", distinct=True), answers_count=Count("answers", distinct=True)), pk=question_id)
    if TYPE_CHECKING:
        question: "Question"
    answers = (question.answers.select_related('author').annotate(likes_count=Count('likes')).order_by('-is_correct', "-likes_count", '-created_at'))
    page_object = paginate(request, answers)
    context = {
        "question": question,
        "answers": page_object.object_list,
        "page_obj": page_object
    }
    return render(request, "questions/question.html", context)

def ask(request):
    return render(request, "questions/ask.html")
