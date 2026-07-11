from django.contrib import admin
from .models import Drug, DrugDatasetDocument, DrugTopic, DrugQuestionSource

admin.site.register(DrugDatasetDocument)
admin.site.register(DrugTopic)
admin.site.register(Drug)
admin.site.register(DrugQuestionSource)
