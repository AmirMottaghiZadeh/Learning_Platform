from django.contrib import admin
from .models import Drug, DrugTopic, DrugQuestionSource
admin.site.register(DrugTopic)
admin.site.register(Drug)
admin.site.register(DrugQuestionSource)
