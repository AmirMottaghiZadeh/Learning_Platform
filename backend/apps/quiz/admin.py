from django.contrib import admin

from .models import QuizAnswer, QuizQuestion, QuizSession


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 0


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ["user", "category", "score", "question_count", "started_at", "finished_at"]
    list_filter = ["category", "finished_at"]
    search_fields = ["user__username"]
    inlines = [QuizQuestionInline]


admin.site.register(QuizAnswer)
