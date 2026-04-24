from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from questions.models import Tag, Profile, Question, Answer, QuestionLike, AnswerLike

admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    class ProfileInline(admin.StackedInline):
        model = Profile
        can_delete = False
        fields = ["bio"]
        extra = 0

    inlines = [ProfileInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "created_at", "get_tags"]
    list_filter = ["created_at", "author", "tags"]
    search_fields = ["title", "text", "author__username"]
    raw_id_fields = ["author"]
    readonly_fields = ["created_at"]
    
    list_select_related = ["author"]
    list_prefetch_related = ["tags"]

    class AnswerInline(admin.TabularInline):
        model = Answer
        fields = ["author", "text", "is_correct", "created_at"]
        readonly_fields = ["created_at"]
        extra = 0
        raw_id_fields = ["author"]

    inlines = [AnswerInline]

    @admin.display(description="Теги")
    def get_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ["question", "author", "is_correct", "created_at"]
    list_filter = ["is_correct", "created_at", "author"]
    search_fields = ["text", "author__username", "question__title"]
    raw_id_fields = ["question", "author"]
    readonly_fields = ["created_at"]
    list_select_related = ["question", "author"]


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ["user", "question", "created_at"]
    list_filter = ["created_at", "question"]
    search_fields = ["user__username", "question__title"]
    raw_id_fields = ["user", "question"]
    readonly_fields = ["created_at"]
    list_select_related = ["user", "question"]


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ["user", "answer", "created_at"]
    list_filter = ["created_at", "answer"]
    search_fields = ["user__username", "answer__text"]
    raw_id_fields = ["user", "answer"]
    readonly_fields = ["created_at"]
    list_select_related = ["user", "answer"]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["nickname", "bio"]
    search_fields = ["nickname", "bio"]
    raw_id_fields = ["user"]
