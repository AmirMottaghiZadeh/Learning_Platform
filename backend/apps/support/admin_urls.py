from django.urls import path
from . import admin_views

app_name = "support_admin"
urlpatterns = [
    path("", admin_views.inbox, name="inbox"),
    path("<uuid:conversation_id>/", admin_views.inbox, name="conversation"),
    path("<uuid:conversation_id>/messages/", admin_views.message_list, name="messages"),
    path("<uuid:conversation_id>/reply/", admin_views.reply, name="reply"),
    path("<uuid:conversation_id>/read/", admin_views.read, name="read"),
    path("<uuid:conversation_id>/status/", admin_views.close, name="status"),
]
