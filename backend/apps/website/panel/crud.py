"""A small generator of list / create / edit / delete panel pages, for the
models that need nothing special (categories, pages, announcements...)."""

from dataclasses import dataclass, field
from typing import Callable

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.views.decorators.http import require_POST

from ..permissions import panel_required
from .ui import log, paginate, render_panel


def chip(text, kind=""):
    return format_html('<span class="chip {}">{}</span>', kind, text)


@dataclass
class Section:
    key: str                      # url name prefix: panel:<key>, <key>_new, <key>_edit, <key>_delete
    route: str                    # url path under /panel/
    model: type
    form: type
    title: str
    singular: str
    perm: str
    columns: list                 # [(label, callable(obj) -> str)]
    active: str                   # sidebar key
    search: tuple = ()
    filters: list = field(default_factory=list)   # [(param, label, choices, field_name)]
    ordering: tuple = ()
    can_delete: bool = True
    tabs: list = field(default_factory=list)       # [(label, url name, key)]
    hint: str = ""
    queryset: Callable = None
    on_save: Callable = None
    per_page: int = 25
    new_label: str = ""

    def tab_links(self):
        return [(label, reverse(name), key) for label, name, key in self.tabs]

    # -- views ----------------------------------------------------------------

    def qs(self, request):
        base = self.queryset(request) if self.queryset else self.model.objects.all()
        return base.order_by(*self.ordering) if self.ordering else base

    def list_view(self, request):
        qs = self.qs(request)
        q = (request.GET.get("q") or "").strip()
        if q and self.search:
            cond = Q()
            for f in self.search:
                cond |= Q(**{f"{f}__icontains": q})
            qs = qs.filter(cond)
        active_filters = {}
        for param, _label, _choices, field_name in self.filters:
            value = request.GET.get(param, "")
            if value:
                qs = qs.filter(**{field_name: value})
                active_filters[param] = value
        page = paginate(request, qs, self.per_page)
        rows = [{
            "cells": [col(obj) for _, col in self.columns], "obj": obj,
            "edit": reverse(f"panel:{self.key}_edit", args=[obj.pk]),
            "delete": reverse(f"panel:{self.key}_delete", args=[obj.pk]),
        } for obj in page.object_list]
        return render_panel(request, "panel/list.html", {
            "section": self, "headers": [label for label, _ in self.columns], "rows": rows, "page": page, "q": q,
            "filters": [(p, label, choices, active_filters.get(p, "")) for p, label, choices, _ in self.filters],
            "new_url": reverse(f"panel:{self.key}_new"), "tabs": self.tab_links(),
        }, active=self.active)

    def _form_view(self, request, obj=None):
        form = self.form(request.POST or None, request.FILES or None, instance=obj)
        if request.method == "POST" and form.is_valid():
            saved = form.save()
            if self.on_save:
                self.on_save(request, saved, form)
            log(request, "update" if obj else "create", saved)
            messages.success(request, "ذخیره شد.")
            return redirect(f"panel:{self.key}")
        return render_panel(request, "panel/form.html", {
            "section": self, "form": form, "obj": obj, "tabs": self.tab_links(),
            "heading": f"ویرایش {self.singular}" if obj else f"{self.singular} جدید",
            "back": reverse(f"panel:{self.key}"),
        }, active=self.active)

    def new_view(self, request):
        return self._form_view(request)

    def edit_view(self, request, pk):
        return self._form_view(request, get_object_or_404(self.qs(request), pk=pk))

    def delete_view(self, request, pk):
        obj = get_object_or_404(self.qs(request), pk=pk)
        if self.can_delete:
            log(request, "delete", obj)
            obj.delete()
            messages.success(request, "حذف شد.")
        return redirect(f"panel:{self.key}")

    def urls(self):
        guard = panel_required(self.perm)
        k = self.key
        return [
            path(f"{self.route}/", guard(self.list_view), name=k),
            path(f"{self.route}/new/", guard(self.new_view), name=f"{k}_new"),
            path(f"{self.route}/<int:pk>/", guard(self.edit_view), name=f"{k}_edit"),
            path(f"{self.route}/<int:pk>/delete/", require_POST(guard(self.delete_view)), name=f"{k}_delete"),
        ]
