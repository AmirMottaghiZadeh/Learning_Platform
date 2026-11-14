from django.db import models


class SearchAnswer(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)  # Server job UUID.
    user_key = models.CharField(max_length=64, db_index=True)  # HMAC, no cross-database foreign key.
    question = models.TextField()
    question_types = models.JSONField(default=list)
    result = models.JSONField()
    model = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)


class SearchFeedback(models.Model):
    answer = models.OneToOneField(SearchAnswer, primary_key=True, on_delete=models.CASCADE, related_name="feedback")
    value = models.SmallIntegerField(choices=[(1, "positive"), (-1, "negative")])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(value__in=[1, -1]), name="ai_feedback_valid_vote")]
