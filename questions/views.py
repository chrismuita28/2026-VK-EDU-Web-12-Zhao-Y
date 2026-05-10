from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.db.models import Count, OuterRef, Exists, Value, BooleanField
from questions.models import Question, Tag, Profile, Answer, QuestionLike, AnswerLike
from typing import TYPE_CHECKING
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from questions.forms import AskForm, AnswerForm

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
    profiles = Profile.objects.select_related('user').annotate(answers_count=Count('user__answers')).order_by('-answers_count')[:5]
    return {"profiles": profiles}

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


def index(request):
    questions = Question.objects.new(user=request.user)
    return _render_question_list(request, questions, "questions/index.html")

def hot(request):
    questions = Question.objects.new(user=request.user)
    return _render_question_list(request, questions, "questions/hot.html")

def tag(request, tag_name):
    tag = get_object_or_404(Tag, name=tag_name)
    questions = Question.objects.by_tag(tag, user=request.user)
    return _render_question_list(request, questions, "questions/tag.html", {"tag": tag})


def question(request, question_id):
    question_query = Question.objects.select_related('author').prefetch_related('tags')
    question_query = question_query.annotate(likes_count=Count("likes", distinct=True), answers_count=Count("answers", distinct=True))
    if request.user.is_authenticated:
        like_subquery = QuestionLike.objects.filter(user=request.user, question=OuterRef('pk'))
        question_query = question_query.annotate(has_liked=Exists(like_subquery))
    else:
        question_query = question_query.annotate(has_liked=Value(False, output_field=BooleanField()))

    question_obj = get_object_or_404(question_query, pk=question_id)

    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(question=question_obj, author=request.user)
            return redirect(f'{request.path}?new_answer={answer.pk}#answer-{answer.pk}')
    else:
        form = AnswerForm()

    answers_query = question_obj.answers.select_related('author').annotate(likes_count=Count('likes', distinct=True))
    if request.user.is_authenticated:    
        like_subquery = AnswerLike.objects.filter(user=request.user, answer=OuterRef('pk'))
        answers_query = answers_query.annotate(has_liked=Exists(like_subquery))
    else:
        answers_query = answers_query.annotate(has_liked=Value(False, output_field=BooleanField()))

    page_object = paginate(request, answers_query)
    
    context = {
        "question": question_obj,
        "answers": page_object.object_list,
        "page_obj": page_object,
        "form": form,
        "new_answer_id": request.GET.get('new_answer'),
    }
    return render(request, "questions/question.html", context)


@login_required(login_url=reverse_lazy("core:login"))
def ask(request):
    if request.method == 'POST':
        form = AskForm(request.POST)
        if form.is_valid():
            question = form.save(author=request.user)
            return redirect("questions:question", question_id=question.id)
    else:
        form = AskForm()
    return render(request, "questions/ask.html", {'form': form})


def like_question(request, question_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Question not found'}, status=404)

    like_obj, created = QuestionLike.objects.get_or_create(user=request.user, question=question)

    if created:
        action = 'liked'
    else:
        like_obj.delete()
        action = 'unliked'

    return JsonResponse({'status': 'success', 'likes_count': question.likes.count(), 'action': action})


def like_answer(request, answer_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    try:
        answer = Answer.objects.get(id=answer_id)
    except Answer.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Answer not found'}, status=404)

    like_obj, created = AnswerLike.objects.get_or_create(user=request.user, answer=answer)

    if created:
        action = 'liked'
    else:
        like_obj.delete()
        action = 'unliked'

    return JsonResponse({'status': 'success', 'likes_count': answer.likes.count(), 'action': action})


@login_required(login_url=reverse_lazy("core:login"))
def mark_best_answer(request, answer_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    try:
        answer = Answer.objects.select_related('question').get(id=answer_id)
    except Answer.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Answer not found'}, status=404)

    if request.user != answer.question.author:
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

    Answer.objects.filter(question=answer.question).update(is_correct=False)
    answer.is_correct = True
    answer.save(update_fields=['is_correct'])
    return JsonResponse({'status': 'success', 'message': 'Best answer marked', 'answer_id': answer.pk})
