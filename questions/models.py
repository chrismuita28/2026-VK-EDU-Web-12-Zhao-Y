from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models import Count, OuterRef, Exists, Value, BooleanField
from django.core.exceptions import ValidationError
from django.conf import settings
from typing import TYPE_CHECKING

class QuestionManager(models.Manager):
    def _optimized(self, user=None):
        return self.select_related("author").prefetch_related("tags").annotate(
            likes_count=Count("likes", distinct=True), answers_count=Count("answers", distinct=True))

    def new(self, user):
        return self._optimized(user).order_by("-created_at")

    def hot(self, user):
        return self._optimized(user).order_by("-likes_count")
    
    def by_tag(self, tag, user):
        return self._optimized(user).filter(tags=tag).order_by("-created_at")
    
    def _add_has_liked(self, queryset, user):
        if user and user.is_authenticated:
            from .models import QuestionLike
            like_subquery = QuestionLike.objects.filter(
                user=user,
                question=OuterRef('pk')
            )
            return queryset.annotate(has_liked=Exists(like_subquery))
        else:
            return queryset.annotate(has_liked=Value(False, output_field=BooleanField()))


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)
    

class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True, max_length=254)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects: "CustomUserManager" = CustomUserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile", verbose_name="Пользователь")
    nickname = models.CharField(max_length=50, unique=True, blank=True, verbose_name="Никнейм")
    bio = models.CharField(max_length=500, blank=True, verbose_name="О себе")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Аватар")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self) -> str:
        return f"Профиль {self.user.email}"
    
    @property
    def display_name(self):
        return self.nickname or self.user.email or self.user.username


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название тега")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self) -> str:
        return self.name


class Question(models.Model):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    text = models.TextField(verbose_name="Текст вопроса")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="questions", verbose_name="Автор")
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
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="answers", verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_correct = models.BooleanField(default=False, verbose_name="Правильный ответ")

    if TYPE_CHECKING:
        likes: "models.Manager[AnswerLike]"

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"

    def __str__(self):
        return f"Ответ на '{self.question.title}' от {self.author}"


class QuestionLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='question_likes', verbose_name="Пользователь")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="likes", verbose_name="Вопрос")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата лайка")

    class Meta:
        verbose_name = "Лайк к вопросу"
        verbose_name_plural = "Лайки к вопросам"
        constraints = [models.UniqueConstraint(fields=['user', 'question'], name='unique_question_like')]
        indexes = [models.Index(fields=['user', 'question'])]

    def clean(self):
        if QuestionLike.objects.filter(user=self.user, question=self.question).exists():
            raise ValidationError("Вы уже лайкнули этот вопрос")

    def __str__(self):
        return f"Лайк от {self.user} к {self.question}"


class AnswerLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="answer_likes", verbose_name="Пользователь")
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name="likes", verbose_name="Ответ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата лайка")

    class Meta:
        verbose_name = "Лайк к ответу"
        verbose_name_plural = "Лайки к ответам"
        constraints = [models.UniqueConstraint(fields=['user', 'answer'], name='unique_answer_like')]
        indexes = [models.Index(fields=['user', 'answer'])]

    def clean(self):
        if AnswerLike.objects.filter(user=self.user, answer=self.answer).exists():
            raise ValidationError("Вы уже лайкнули этот ответ")

    def __str__(self):
        return f"Лайк от {self.user} к {self.answer}"
    