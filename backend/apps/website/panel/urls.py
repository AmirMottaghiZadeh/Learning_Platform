from django.urls import path

from . import commerce, inbox, media, posts, sections, views

app_name = "panel"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("search/", views.search, name="search"),
    path("posts/", posts.posts, name="posts"),
    path("posts/new/", posts.post_edit, name="post_new"),
    path("posts/<int:pk>/", posts.post_edit, name="post_edit"),
    path("posts/<int:pk>/delete/", posts.post_delete, name="post_delete"),
    path("posts/<int:pk>/duplicate/", posts.post_duplicate, name="post_duplicate"),
    path("posts/<int:pk>/revisions/", posts.post_revisions, name="post_revisions"),
    path("posts/<int:pk>/revisions/<int:rid>/restore/", posts.revision_restore, name="revision_restore"),
    path("media/", media.media_list, name="media"),
    path("media/upload/", media.media_upload, name="media_upload"),
    path("media/picker/", media.media_picker, name="media_picker"),
    path("media/<int:pk>/", media.media_edit, name="media_edit"),
    path("media/<int:pk>/delete/", media.media_delete, name="media_delete"),
    path("comments/", inbox.comments, name="comments"),
    path("comments/action/", inbox.comment_action, name="comment_action"),
    path("contact/", inbox.contact, name="contact"),
    path("contact/<int:pk>/", inbox.contact_action, name="contact_action"),
    path("subscribers/", inbox.subscribers, name="subscribers"),
    path("subscribers/export.csv", inbox.subscribers_export, name="subscribers_export"),
    path("subscribers/<int:pk>/", inbox.subscriber_action, name="subscriber_action"),
    path("plans/", commerce.plans, name="plans"),
    path("orders/", commerce.orders, name="orders"),
    path("subscriptions/", commerce.subscriptions, name="subscriptions"),
    path("stats/", views.stats, name="stats"),
    path("seo/", views.seo, name="seo"),
    path("settings/", views.settings_view, name="settings"),
    path("staff/", views.staff, name="staff"),
    path("staff/<int:pk>/", views.staff_update, name="staff_update"),
    path("activity/", views.activity, name="activity"),
]
for section in sections.ALL:
    urlpatterns += section.urls()
