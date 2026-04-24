from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count
from django.core.exceptions import ValidationError
from typing import TYPE_CHECKING

class QuestionManager(models.Manager):
    def _optimized(self):
        return self.select_related("author").prefetch_related("tags").annotate(likes_count=Count("likes"))

    def new(self):
        return self._optimized().order_by("-created_at")

    def hot(self):
        return self._optimized().order_by("-likes_count")
    
    def by_tag(self, tag):
        return self._optimized().filter(tags=tag).order_by("-created_at")


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название тега")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self) -> str:
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile", verbose_name="Пользователь")
    nickname = models.CharField(max_length=50, unique=True, blank=True, verbose_name="Никнейм")
    bio = models.CharField(max_length=500, blank=True, verbose_name="О себе")
    # avatar = models.ImageField(blank=True, null=True, verbose_name="Аватар")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self) -> str:
        return f"Профиль {self.user.username}"
    
    @property
    def display_name(self):
        return self.nickname or self.user.username
    
    def save(self, *args, **kwargs):
        if not self.nickname and self.user:
            self.nickname = self.user.username
        super().save(*args, **kwargs)


class Question(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    text = models.TextField(verbose_name="Текст вопроса")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="questions", verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    tags = models.ManyToManyField(Tag, related_name="questions", verbose_name="Теги")

    objects = QuestionManager()

    if TYPE_CHECKING:
        objects: "QuestionManager"
        answers: "models.Manager[Answer]"

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"

    def __str__(self):
        return self.title
    
    def get_best_answers(self):
        return self.answers.select_related("author").order_by("is_correct", "-created_at")


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers", verbose_name="Вопрос")
    text = models.TextField(verbose_name="Текст ответа")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="answers", verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_correct = models.BooleanField(default=False, verbose_name="Правильный ответ")

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

    def __str__(self):
        return f"Ответ на '{self.question.title}' от {self.author}"


class QuestionLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_likes', verbose_name="Пользователь")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="likes", verbose_name="Вопрос")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата лайка")

    class Meta:
        verbose_name = "Лайк к вопросу"
        verbose_name_plural = "Лайки к вопросам"

    def clean(self):
        if QuestionLike.objects.filter(user=self.user, question=self.question).exists():
            raise ValidationError("Вы уже лайкнули этот вопрос")

    def __str__(self):
        return f"Лайк от {self.user} к {self.question}"


class AnswerLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="answer_likes", verbose_name="Пользователь")
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name="likes", verbose_name="Ответ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата лайка")

    class Meta:
        verbose_name = "Лайк к ответу"
        verbose_name_plural = "Лайки к ответам"

    def clean(self):
        if AnswerLike.objects.filter(user=self.user, answer=self.answer).exists():
            raise ValidationError("Вы уже лайкнули этот ответ")

    def __str__(self):
        return f"Лайк от {self.user} к {self.answer}"
    