"""Posts in the panel: list with bulk actions, the editor, revisions."""

from django.contrib import messages
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import Category, Media, Post, PostRevision, unique_slug
from ..permissions import can, panel_required
from . import forms
from .ui import log, paginate, render_panel

MAX_REVISIONS = 30
BULK = {
    "publish": ("منتشر شود", "post.publish"), "draft": ("به پیش‌نویس برگردد", "post.publish"),
    "archive": ("بایگانی شود", "post.publish"), "feature": ("ویژه شود", "post.publish"),
    "delete": ("حذف شود", "post.delete"),
}


def _scope(request):
    qs = Post.objects.select_related("category", "author", "cover")
    return qs if can(request.user, "post.view_all") else qs.filter(author=request.user)


def _editable(request, post):
    if can(request.user, "post.edit_all"):
        return True
    return post.author_id == request.user.id and post.status in (Post.DRAFT, Post.REVIEW) and can(request.user, "post.edit_own")


@panel_required("post.create")
def posts(request):
    base = _scope(request)
    if request.method == "POST":
        return _bulk(request, base)
    qs = base
    status = request.GET.get("status", "")
    if status:
        qs = qs.filter(status=status)
    if request.GET.get("category"):
        qs = qs.filter(category_id=request.GET["category"])
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(slug__icontains=q))
    counts = dict(base.values_list("status").annotate(n=Count("id")))
    tabs = [("", "همه", sum(counts.values()))] + [(k, label, counts.get(k, 0)) for k, label in Post.STATUS_CHOICES]
    return render_panel(request, "panel/posts.html", {
        "page": paginate(request, qs.order_by("-updated_at"), 20), "q": q, "status": status, "tabs": tabs,
        "categories": Category.objects.all(), "category": request.GET.get("category", ""),
        "bulk": [(k, label) for k, (label, perm) in BULK.items() if can(request.user, perm)],
    }, active="posts")


def _bulk(request, base):
    action = request.POST.get("bulk")
    ids = [i for i in request.POST.getlist("ids") if i.isdigit()]
    if action not in BULK or not ids or not can(request.user, BULK[action][1]):
        messages.error(request, "کاری انتخاب نشده یا اجازه ندارید.")
        return redirect(request.get_full_path())
    rows = base.filter(pk__in=ids)
    n = rows.count()
    now = timezone.now()
    if action == "publish":
        rows.filter(published_at__isnull=True).update(published_at=now)
        rows.update(status=Post.PUBLISHED)
    elif action == "draft":
        rows.update(status=Post.DRAFT)
    elif action == "archive":
        rows.update(status=Post.ARCHIVED)
    elif action == "feature":
        rows.update(featured=True)
    elif action == "delete":
        rows.delete()
    log(request, f"bulk_{action}", detail=f"{n} مطلب")
    messages.success(request, f"{n} مطلب به‌روزرسانی شد.")
    return redirect(reverse("panel:posts"))


def _snapshot(post, user):
    last = post.revisions.first()
    if last and (last.title, last.excerpt, last.body_html) == (post.title, post.excerpt, post.body_html):
        return
    PostRevision.objects.create(post=post, title=post.title, excerpt=post.excerpt, body_html=post.body_html, saved_by=user)
    for old in post.revisions.all()[MAX_REVISIONS:]:
        old.delete()


@panel_required("post.create")
def post_edit(request, pk=None):
    post = get_object_or_404(_scope(request), pk=pk) if pk else None
    if post and not _editable(request, post):
        return render_panel(request, "panel/forbidden.html", active="posts", status=403)
    allow_publish = can(request.user, "post.publish")
    form = forms.PostForm(request.POST or None, instance=post, allow_publish=allow_publish)
    if request.method == "POST" and form.is_valid():
        intent = request.POST.get("intent", "save")
        saved = form.save(commit=False)
        if intent == "publish" and allow_publish and saved.status in (Post.DRAFT, Post.REVIEW, Post.ARCHIVED):
            saved.status = Post.PUBLISHED
            saved.published_at = saved.published_at or timezone.now()
        elif intent == "review" and not allow_publish:
            saved.status = Post.REVIEW
        if not allow_publish and saved.status not in (Post.DRAFT, Post.REVIEW):
            saved.status = Post.DRAFT
        if saved.author_id is None:
            saved.author = request.user
        saved.save()
        form.save_tags(saved)
        _snapshot(saved, request.user)
        log(request, "update" if post else "create", saved)
        messages.success(request, "مطلب ذخیره شد." if saved.status != Post.PUBLISHED else "مطلب منتشر شد.")
        return redirect("panel:post_edit", pk=saved.pk)
    return render_panel(request, "panel/post_form.html", {
        "form": form, "post": post, "allow_publish": allow_publish,
        "revision_count": post.revisions.count() if post else 0,
        "preview_url": post.get_absolute_url() if post else "",
        "heading": "ویرایش مطلب" if post else "مطلب جدید",
    }, active="posts")


@require_POST
@panel_required("post.create")
def post_delete(request, pk):
    post = get_object_or_404(_scope(request), pk=pk)
    if not (can(request.user, "post.delete") or (post.author_id == request.user.id and post.status == Post.DRAFT)):
        return render_panel(request, "panel/forbidden.html", active="posts", status=403)
    log(request, "delete", post)
    post.delete()
    messages.success(request, "مطلب حذف شد.")
    return redirect("panel:posts")


@require_POST
@panel_required("post.create")
def post_duplicate(request, pk):
    post = get_object_or_404(_scope(request), pk=pk)
    copy = Post.objects.create(
        title=f"{post.title} (کپی)", slug=unique_slug(Post, post.slug), excerpt=post.excerpt, body_html=post.body_html, cover=post.cover,
        category=post.category, author=request.user, status=Post.DRAFT, seo_title=post.seo_title, seo_description=post.seo_description,
    )
    copy.tags.set(post.tags.all())
    log(request, "duplicate", copy)
    messages.success(request, "نسخهٔ کپی به‌عنوان پیش‌نویس ساخته شد.")
    return redirect("panel:post_edit", pk=copy.pk)


@panel_required("post.create")
def post_revisions(request, pk):
    post = get_object_or_404(_scope(request), pk=pk)
    if not _editable(request, post):
        return render_panel(request, "panel/forbidden.html", active="posts", status=403)
    return render_panel(request, "panel/revisions.html", {"post": post, "revisions": post.revisions.select_related("saved_by")}, active="posts")


@require_POST
@panel_required("post.create")
def revision_restore(request, pk, rid):
    post = get_object_or_404(_scope(request), pk=pk)
    if not _editable(request, post):
        raise Http404
    rev = get_object_or_404(post.revisions, pk=rid)
    _snapshot(post, request.user)
    post.title, post.excerpt, post.body_html = rev.title, rev.excerpt, rev.body_html
    post.save()
    _snapshot(post, request.user)
    log(request, "restore", post, detail=f"نسخهٔ {rev.pk}")
    messages.success(request, "نسخهٔ انتخاب‌شده بازگردانده شد.")
    return redirect("panel:post_edit", pk=post.pk)
