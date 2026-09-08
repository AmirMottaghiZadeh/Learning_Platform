from django.contrib import admin

from .models import DailyStudy, LearnerProgress, Mistake, StudyPlan


@admin.register(LearnerProgress)
class LearnerProgressAdmin(admin.ModelAdmin):
    list_display = ["user", "xp", "streak_days", "last_study_date",
                    "total_quizzes", "total_reviews", "total_minutes"]
    search_fields = ["user__username", "user__email"]


@admin.register(DailyStudy)
class DailyStudyAdmin(admin.ModelAdmin):
    list_display = ["user", "day", "minutes"]
    list_filter = ["day"]
    search_fields = ["user__username"]


@admin.register(Mistake)
class MistakeAdmin(admin.ModelAdmin):
    list_display = ["user", "topic_key", "count", "resolved", "last_seen"]
    list_filter = ["resolved", "topic_key"]
    search_fields = ["user__username", "topic_key"]


@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ["user", "days", "reminders_enabled"]
    search_fields = ["user__username"]
