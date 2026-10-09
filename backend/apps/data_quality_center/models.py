from django.conf import settings
from django.db import models

from apps.drugs.models import CLINICAL_FIELDS


class SectionEdit(models.Model):
    """Append-only ledger of one edit actually APPLIED to an ingredient
    section's summaries -- written only when a `SectionEditRequest` clears
    superuser review (see below), never at submission time.

    The Data Quality Center only edits `summary_fa` / `summary_en` on
    `drugs.IngredientProfileSection`; the raw label text stays read-only.
    """

    section = models.ForeignKey(
        "drugs.IngredientProfileSection",
        on_delete=models.CASCADE,
        related_name="edits",
    )
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="section_edits",
    )
    editor_username = models.CharField(max_length=150, blank=True)
    # The superuser whose approval applied this edit -- null only for rows
    # written before approval existed, never for a new one.
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="section_edit_approvals",
    )
    approved_by_username = models.CharField(max_length=150, blank=True)

    ingredient_name = models.CharField(max_length=255)
    field = models.CharField(max_length=40, choices=CLINICAL_FIELDS)
    before_fa = models.TextField(blank=True)
    after_fa = models.TextField(blank=True)
    before_en = models.TextField(blank=True)
    after_en = models.TextField(blank=True)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at"], name="dqc_edit_recent_idx")]

    def __str__(self):
        return f"{self.ingredient_name}.{self.field} by {self.editor_username}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("SectionEdit rows are append-only.")
        return super().save(*args, **kwargs)


class SectionEditRequest(models.Model):
    """One operator's proposed edit, awaiting (or resolved by) superuser
    review -- the two-step gate in front of `SectionEdit`. Nothing here
    touches the live `IngredientProfileSection` until `approve()` runs;
    `reject()` just closes the request out. Unlike `SectionEdit` this row
    *is* mutable -- `status`/`reviewed_*` are the whole point of it -- but
    the proposed content (`before_*`/`after_*`/`reason`) is only ever set
    once, at creation.
    """

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    section = models.ForeignKey(
        "drugs.IngredientProfileSection",
        on_delete=models.CASCADE,
        related_name="edit_requests",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="section_edit_requests",
    )
    requested_by_username = models.CharField(max_length=150, blank=True)

    ingredient_name = models.CharField(max_length=255)
    field = models.CharField(max_length=40, choices=CLINICAL_FIELDS)
    before_fa = models.TextField(blank=True)
    after_fa = models.TextField(blank=True)
    before_en = models.TextField(blank=True)
    after_en = models.TextField(blank=True)
    reason = models.TextField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="section_edit_reviews",
    )
    reviewed_by_username = models.CharField(max_length=150, blank=True)
    review_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"], name="dqc_request_status_idx"),
            models.Index(fields=["section", "status"], name="dqc_request_section_idx"),
        ]

    def __str__(self):
        return f"{self.ingredient_name}.{self.field} [{self.status}] by {self.requested_by_username}"

    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING

    def approve(self, reviewer, note=""):
        """Applies the proposed summaries to the live section and writes the
        permanent `SectionEdit` ledger row. Refuses if the section has
        drifted from the snapshot this request was built from (someone else
        applied a different change in the meantime) -- the reviewer re-opens
        the ingredient and re-reviews against current content instead of
        silently clobbering it."""
        if not self.is_pending:
            raise ValueError("Only a pending request can be approved.")
        section = self.section
        if section.summary_fa != self.before_fa or section.summary_en != self.before_en:
            raise ValueError(
                "This section changed since the request was submitted -- re-check it before approving."
            )

        from django.utils import timezone

        section.summary_fa = self.after_fa
        section.summary_en = self.after_en
        section.save(update_fields=["summary_fa", "summary_en", "updated_at"])

        SectionEdit.objects.create(
            section=section,
            editor=self.requested_by,
            editor_username=self.requested_by_username,
            approved_by=reviewer,
            approved_by_username=reviewer.get_username(),
            ingredient_name=self.ingredient_name,
            field=self.field,
            before_fa=self.before_fa,
            after_fa=self.after_fa,
            before_en=self.before_en,
            after_en=self.after_en,
            reason=self.reason,
        )

        self.status = self.STATUS_APPROVED
        self.reviewed_by = reviewer
        self.reviewed_by_username = reviewer.get_username()
        self.review_note = note
        self.reviewed_at = timezone.now()
        self.save(update_fields=[
            "status", "reviewed_by", "reviewed_by_username", "review_note", "reviewed_at",
        ])

    def reject(self, reviewer, note=""):
        if not self.is_pending:
            raise ValueError("Only a pending request can be rejected.")

        from django.utils import timezone

        self.status = self.STATUS_REJECTED
        self.reviewed_by = reviewer
        self.reviewed_by_username = reviewer.get_username()
        self.review_note = note
        self.reviewed_at = timezone.now()
        self.save(update_fields=[
            "status", "reviewed_by", "reviewed_by_username", "review_note", "reviewed_at",
        ])
