from django.conf import settings
from django.db import models


class LeagueSeason(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    product_id = models.CharField(max_length=80, default="k_game")
    key = models.CharField(max_length=40)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product_id", "key"],
                name="unique_product_league_season",
            ),
        ]
        indexes = [
            models.Index(fields=["product_id", "key"]),
            models.Index(fields=["product_id", "status"]),
            models.Index(fields=["starts_at", "ends_at"]),
        ]
        ordering = ["-starts_at"]

    def __str__(self):
        return f"{self.product_id}:{self.key}"


class LeagueResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="league_results")
    session = models.OneToOneField("games.GameSession", on_delete=models.CASCADE, related_name="league_result")
    product_id = models.CharField(max_length=80, default="k_game")
    season = models.ForeignKey(
        LeagueSeason,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="results",
    )
    season_key = models.CharField(max_length=40, blank=True)
    topic_key = models.CharField(max_length=50)
    raw_score = models.IntegerField(default=0)
    score_per_question = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    time_remaining_total = models.IntegerField(default=0)
    time_bonus = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    league_rating = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    answered = models.PositiveIntegerField(default=0)
    correct = models.PositiveIntegerField(default=0)
    wrong = models.PositiveIntegerField(default=0)
    percent = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)
    rank_snapshot = models.PositiveIntegerField(null=True, blank=True)
    league_rule_version = models.CharField(max_length=80, default="mvp-weekly-league-v1")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-league_rating", "-raw_score", "-percent", "-time_remaining_total", "created_at"]
        indexes = [
            models.Index(fields=["product_id", "season_key", "topic_key"]),
            models.Index(fields=["user", "created_at"]),
        ]
