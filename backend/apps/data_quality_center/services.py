"""The review workflow: every state change of a `SectionEditRequest`, each in
one transaction with the request (and, when applying, the section) locked,
each writing its `ReviewEvent`. Views only translate HTTP into these calls.

Who may do what:
- any staff operator drafts, submits, withdraws and discards their own
  requests;
- only a superuser approves (which applies the change), rejects, sends a
  request back for changes, or starts a revert of an applied edit.
"""

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.drugs.models import IngredientProfileSection

from .checks import run_checks
from .models import ReviewEvent, SectionEdit, SectionEditRequest


class WorkflowError(ValueError):
    """An action the request's current state, or the actor, doesn't allow.
    The message is Persian and shown to the user as is."""


def _client_ip(http_request):
    """The caller's address. Behind the platform's proxy REMOTE_ADDR is the
    proxy itself; the proxy appends the address it saw to X-Forwarded-For, so
    the LAST entry is the one a client cannot forge (anything before it is
    whatever the client sent)."""
    if http_request is None:
        return None
    forwarded = [part.strip() for part in http_request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")]
    forwarded = [part for part in forwarded if part]
    return (forwarded[-1] if forwarded else http_request.META.get("REMOTE_ADDR")) or None


def _event(req, actor, action, *, note="", metadata=None, http_request=None):
    return ReviewEvent.objects.create(
        request=req,
        actor=actor,
        actor_username=actor.get_username() if actor else "",
        action=action,
        note=note,
        metadata=metadata or {},
        ip_address=_client_ip(http_request),
    )


def _require_superuser(user):
    if not user.is_superuser:
        raise WorkflowError("فقط سوپریوزر می‌تواند این کار را انجام دهد.")


def _clean(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def min_reason_length():
    return getattr(settings, "DATA_QUALITY_MIN_REASON_LENGTH", 12)


def open_request(section):
    """The section's pending or sent-back request, if any."""
    return (
        SectionEditRequest.objects.filter(section=section, status__in=SectionEditRequest.OPEN_STATUSES)
        .select_related("requested_by")
        .first()
    )


def editable_request(section, user):
    """The request `user` would be editing on this section: their own
    sent-back request, else their own draft."""
    return (
        SectionEditRequest.objects.filter(
            section=section, requested_by=user, status=SectionEditRequest.STATUS_CHANGES_REQUESTED
        ).first()
        or SectionEditRequest.objects.filter(
            section=section, requested_by=user, status=SectionEditRequest.STATUS_DRAFT
        ).first()
    )


def save_draft(section, user, *, summary_fa, summary_en, reason):
    """Creates or updates `user`'s editable request on the section (the
    autosave). Refused while someone else's request holds the section."""
    with transaction.atomic():
        section = IngredientProfileSection.objects.select_for_update().get(pk=section.pk)
        held = open_request(section)
        if held and held.requested_by_id != user.id:
            raise WorkflowError(
                f"این بخش در دست درخواست #{held.pk} از {held.requested_by_username} است."
            )
        if held and held.status == SectionEditRequest.STATUS_PENDING:
            raise WorkflowError("درخواست شما در انتظار تأیید است؛ برای ویرایش، اول آن را پس بگیرید.")

        req = editable_request(section, user)
        if req is None:
            req = SectionEditRequest(
                section=section,
                requested_by=user,
                requested_by_username=user.get_username(),
                ingredient_name=section.ingredient.name,
                field=section.field,
                before_fa=section.summary_fa,
                before_en=section.summary_en,
                status=SectionEditRequest.STATUS_DRAFT,
            )
        # Browsers submit textarea line breaks as CRLF; the live summaries
        # (and the app's line parser) use plain LF.
        req.after_fa = _clean(summary_fa)
        req.after_en = _clean(summary_en)
        req.reason = " ".join(reason.split())
        req.save()
        return req


def submit(req, user, *, http_request=None):
    """Sends a draft, or a request sent back for changes, to the superuser."""
    with transaction.atomic():
        req = SectionEditRequest.objects.select_for_update().select_related("section").get(pk=req.pk)
        if req.requested_by_id != user.id:
            raise WorkflowError("فقط نویسندهٔ درخواست می‌تواند آن را ارسال کند.")
        if not req.is_editable:
            raise WorkflowError("این درخواست قابل ارسال نیست.")
        if len(req.reason) < min_reason_length():
            raise WorkflowError(f"دلیل تغییر را دست‌کم در {min_reason_length()} نویسه بنویسید.")

        section = IngredientProfileSection.objects.select_for_update().get(pk=req.section_id)
        if req.after_fa == section.summary_fa and req.after_en == section.summary_en:
            raise WorkflowError("متن پیشنهادی با متن فعلی فرقی ندارد.")
        held = open_request(section)
        if held and held.pk != req.pk:
            raise WorkflowError(f"درخواست #{held.pk} برای همین بخش هنوز باز است.")

        drifted = section.summary_fa != req.before_fa or section.summary_en != req.before_en
        req.before_fa = section.summary_fa
        req.before_en = section.summary_en
        req.checks = run_checks(section.raw_text, req.before_fa, req.after_fa, req.before_en, req.after_en)
        if drifted:
            req.checks.insert(0, {
                "key": "drift",
                "level": "warn",
                "label": "متن فعلی بخش از زمان شروع این پیش‌نویس تغییر کرده",
            })
        resubmitting = req.status == SectionEditRequest.STATUS_CHANGES_REQUESTED
        req.status = SectionEditRequest.STATUS_PENDING
        req.submitted_at = timezone.now()
        req.save()
        _event(
            req,
            user,
            ReviewEvent.RESUBMITTED if resubmitting else ReviewEvent.SUBMITTED,
            note=req.reason,
            metadata={"checks": req.checks},
            http_request=http_request,
        )
        return req


def withdraw(req, user, *, http_request=None):
    """Takes a pending request back to draft, so its author can change it."""
    with transaction.atomic():
        req = SectionEditRequest.objects.select_for_update().get(pk=req.pk)
        if req.requested_by_id != user.id:
            raise WorkflowError("فقط نویسندهٔ درخواست می‌تواند آن را پس بگیرد.")
        if not req.is_pending:
            raise WorkflowError("فقط درخواست در انتظار تأیید را می‌شود پس گرفت.")
        if SectionEditRequest.objects.filter(
            section_id=req.section_id, requested_by=user, status=SectionEditRequest.STATUS_DRAFT
        ).exclude(pk=req.pk).exists():
            raise WorkflowError("برای این بخش پیش‌نویس دیگری دارید؛ اول آن را کنار بگذارید.")
        req.status = SectionEditRequest.STATUS_DRAFT
        req.save(update_fields=["status", "updated_at"])
        _event(req, user, ReviewEvent.WITHDRAWN, http_request=http_request)
        return req


def discard(req, user, *, http_request=None):
    """Drops a draft (or sent-back request). One never submitted has no
    history and is deleted; otherwise it is closed as discarded."""
    with transaction.atomic():
        req = SectionEditRequest.objects.select_for_update().get(pk=req.pk)
        if req.requested_by_id != user.id:
            raise WorkflowError("فقط نویسندهٔ درخواست می‌تواند آن را کنار بگذارد.")
        if not req.is_editable:
            raise WorkflowError("این درخواست دیگر قابل کنار گذاشتن نیست.")
        if not req.events.exists():
            req.delete()
            return None
        req.status = SectionEditRequest.STATUS_DISCARDED
        req.save(update_fields=["status", "updated_at"])
        _event(req, user, ReviewEvent.DISCARDED, http_request=http_request)
        return req


def _close(req, reviewer, status, note):
    req.status = status
    req.reviewed_by = reviewer
    req.reviewed_by_username = reviewer.get_username()
    req.review_note = note
    req.reviewed_at = timezone.now()
    req.save(update_fields=[
        "status", "reviewed_by", "reviewed_by_username", "review_note", "reviewed_at", "updated_at",
    ])


def approve(req, reviewer, note="", *, http_request=None):
    """Applies the proposed summaries to the live section and writes the
    permanent `SectionEdit`. Refuses if the section changed since the
    request was submitted -- the reviewer sends it back instead of silently
    overwriting someone else's applied change."""
    _require_superuser(reviewer)
    with transaction.atomic():
        req = SectionEditRequest.objects.select_for_update().get(pk=req.pk)
        if not req.is_pending:
            raise WorkflowError("فقط درخواست در انتظار تأیید را می‌شود تأیید کرد.")
        section = IngredientProfileSection.objects.select_for_update().get(pk=req.section_id)
        if section.summary_fa != req.before_fa or section.summary_en != req.before_en:
            raise WorkflowError(
                "متن این بخش پس از ارسال درخواست تغییر کرده؛ آن را برای اصلاح برگردانید."
            )

        section.summary_fa = req.after_fa
        section.summary_en = req.after_en
        section.save(update_fields=["summary_fa", "summary_en", "updated_at"])
        edit = SectionEdit.objects.create(
            section=section,
            request=req,
            editor=req.requested_by,
            editor_username=req.requested_by_username,
            approved_by=reviewer,
            approved_by_username=reviewer.get_username(),
            ingredient_name=req.ingredient_name,
            field=req.field,
            before_fa=req.before_fa,
            after_fa=req.after_fa,
            before_en=req.before_en,
            after_en=req.after_en,
            reason=req.reason,
        )
        _close(req, reviewer, SectionEditRequest.STATUS_APPROVED, note)
        _event(req, reviewer, ReviewEvent.APPROVED, note=note, metadata={"edit_id": edit.pk}, http_request=http_request)
        return edit


def reject(req, reviewer, note="", *, http_request=None):
    _require_superuser(reviewer)
    with transaction.atomic():
        req = SectionEditRequest.objects.select_for_update().get(pk=req.pk)
        if not req.is_pending:
            raise WorkflowError("فقط درخواست در انتظار تأیید را می‌شود رد کرد.")
        _close(req, reviewer, SectionEditRequest.STATUS_REJECTED, note)
        _event(req, reviewer, ReviewEvent.REJECTED, note=note, http_request=http_request)
        return req


def request_changes(req, reviewer, note, *, http_request=None):
    """Sends a pending request back to its author with what to fix."""
    _require_superuser(reviewer)
    if not note.strip():
        raise WorkflowError("بنویسید چه چیزی باید اصلاح شود.")
    with transaction.atomic():
        req = SectionEditRequest.objects.select_for_update().get(pk=req.pk)
        if not req.is_pending:
            raise WorkflowError("فقط درخواست در انتظار تأیید را می‌شود برای اصلاح برگرداند.")
        req.status = SectionEditRequest.STATUS_CHANGES_REQUESTED
        req.reviewed_by = reviewer
        req.reviewed_by_username = reviewer.get_username()
        req.review_note = note.strip()
        req.reviewed_at = timezone.now()
        req.save(update_fields=[
            "status", "reviewed_by", "reviewed_by_username", "review_note", "reviewed_at", "updated_at",
        ])
        _event(req, reviewer, ReviewEvent.CHANGES_REQUESTED, note=note.strip(), http_request=http_request)
        return req


def start_revert(edit, user, reason, *, http_request=None):
    """Opens a pending request that puts back the text `edit` replaced. It
    goes through the same approval as any change -- and refuses while the
    section has another open request."""
    _require_superuser(user)
    reason = reason.strip()
    if len(reason) < min_reason_length():
        raise WorkflowError(f"دلیل بازگردانی را دست‌کم در {min_reason_length()} نویسه بنویسید.")
    with transaction.atomic():
        section = IngredientProfileSection.objects.select_for_update().get(pk=edit.section_id)
        held = open_request(section)
        if held:
            raise WorkflowError(f"درخواست #{held.pk} برای همین بخش هنوز باز است.")
        if section.summary_fa == edit.before_fa and section.summary_en == edit.before_en:
            raise WorkflowError("متن این بخش همین حالا همان متن قبل از این ویرایش است.")
        req = SectionEditRequest.objects.create(
            section=section,
            requested_by=user,
            requested_by_username=user.get_username(),
            ingredient_name=edit.ingredient_name,
            field=edit.field,
            before_fa=section.summary_fa,
            before_en=section.summary_en,
            after_fa=edit.before_fa,
            after_en=edit.before_en,
            reason=reason,
            reverts=edit,
            status=SectionEditRequest.STATUS_PENDING,
            submitted_at=timezone.now(),
        )
        req.checks = run_checks(section.raw_text, req.before_fa, req.after_fa, req.before_en, req.after_en)
        req.save(update_fields=["checks"])
        _event(req, user, ReviewEvent.REVERT_REQUESTED, note=reason, metadata={"edit_id": edit.pk}, http_request=http_request)
        return req
