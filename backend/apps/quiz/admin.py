from django.contrib import admin

from .models import BankQuestion, QuizAnswer, QuizQuestion, QuizSession


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 0


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ["user", "category", "atc_code", "score", "question_count", "started_at", "finished_at"]
    list_filter = ["category", "finished_at"]
    search_fields = ["user__username"]
    inlines = [QuizQuestionInline]


@admin.register(BankQuestion)
class BankQuestionAdmin(admin.ModelAdmin):
    list_display = ["ingredient", "field", "prompt_fa"]
    list_filter = ["field"]
    search_fields = ["ingredient__name", "prompt_fa"]
    autocomplete_fields = ["ingredient"]


admin.site.register(QuizAnswer)
