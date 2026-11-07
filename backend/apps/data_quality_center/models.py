from django.conf import settings
from django.db import models
from django.db.models import Q

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
    # The request this edit applied -- null only for rows written before
    # requests were linked.
    request = models.ForeignKey(
        "SectionEditRequest",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="applied_edits",
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
    """One operator's proposed change to a section's summaries, carried
    through review -- the gate in front of `SectionEdit`:

        draft --submit--> pending --approve--> approved (applied)
          ^                  |  \\--reject---> rejected
          |                  |   \\--request changes--> changes_requested
          +----withdraw------+                          (edited, resubmitted)
        draft / changes_requested --discard--> discarded

    The proposed content (`after_*`, `reason`) is editable only while the
    request is a draft or has been sent back for changes; once pending it is
    frozen until a reviewer acts. `before_*` is the live text the proposal
    was made against -- taken when the draft starts and refreshed at each
    submission, so approval can refuse to overwrite a section that changed
    in the meantime. Nothing touches the live section until approval.

    Every transition after the first submission is written to
    `ReviewEvent`; a draft that was never submitted has no history and can
    simply be deleted.
    """

    STATUS_DRAFT = "draft"
    STATUS_PENDING = "pending"
    STATUS_CHANGES_REQUESTED = "changes_requested"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_DISCARDED = "discarded"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PENDING, "Pending"),
        (STATUS_CHANGES_REQUESTED, "Changes requested"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_DISCARDED, "Discarded"),
    ]
    EDITABLE_STATUSES = (STATUS_DRAFT, STATUS_CHANGES_REQUESTED)
    # At most one of these per section: the section is locked to its author.
    OPEN_STATUSES = (STATUS_PENDING, STATUS_CHANGES_REQUESTED)

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
    reason = models.TextField(blank=True)
    # Results of the automatic checks at the last submission (see checks.py).
    checks = models.JSONField(default=list, blank=True)
    # Set when this request puts back the text an applied edit replaced.
    reverts = models.ForeignKey(
        SectionEdit,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="revert_requests",
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
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
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"], name="dqc_request_status_idx"),
            models.Index(fields=["section", "status"], name="dqc_request_section_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["section"],
                condition=Q(status__in=["pending", "changes_requested"]),
                name="dqc_one_open_request_per_section",
            ),
            models.UniqueConstraint(
                fields=["section", "requested_by"],
                condition=Q(status="draft"),
                name="dqc_one_draft_per_editor",
            ),
        ]

    def __str__(self):
        return f"{self.ingredient_name}.{self.field} [{self.status}] by {self.requested_by_username}"

    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING

    @property
    def is_editable(self):
        return self.status in self.EDITABLE_STATUSES


class ReviewEvent(models.Model):
    """Append-only audit trail: one row per action taken on a request --
    who did what, when, from where, with what note. The request history in
    the console and the history page read from here."""

    SUBMITTED = "submitted"
    RESUBMITTED = "resubmitted"
    WITHDRAWN = "withdrawn"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISCARDED = "discarded"
    REVERT_REQUESTED = "revert_requested"
    ACTION_CHOICES = [
        (SUBMITTED, "Submitted"),
        (RESUBMITTED, "Resubmitted"),
        (WITHDRAWN, "Withdrawn"),
        (CHANGES_REQUESTED, "Changes requested"),
        (APPROVED, "Approved and applied"),
        (REJECTED, "Rejected"),
        (DISCARDED, "Discarded"),
        (REVERT_REQUESTED, "Revert requested"),
    ]

    request = models.ForeignKey(
        SectionEditRequest,
        on_delete=models.PROTECT,
        related_name="events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="dqc_review_events",
    )
    actor_username = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=24, choices=ACTION_CHOICES)
    note = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["-created_at"], name="dqc_event_recent_idx"),
            models.Index(fields=["actor", "-created_at"], name="dqc_event_actor_idx"),
        ]

    def __str__(self):
        return f"{self.action} on #{self.request_id} by {self.actor_username}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("ReviewEvent rows are append-only.")
        return super().save(*args, **kwargs)
