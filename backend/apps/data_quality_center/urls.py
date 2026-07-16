from django.urls import path

from . import views

app_name = "data_quality_center"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("health/", views.health_center, name="health"),
    path("batches/", views.batch_list, name="batch_list"),
    path("batches/<int:batch_id>/", views.batch_detail, name="batch_detail"),
    path("batches/<int:batch_id>/generate-report/", views.batch_generate_report, name="batch_generate_report"),
    path("batches/<int:batch_id>/compare/", views.batch_compare, name="batch_compare"),
    path("jobs/", views.job_list, name="job_list"),
    path("suggestions/", views.suggestion_list, name="suggestion_list"),
    path("suggestions/<int:suggestion_id>/", views.suggestion_detail, name="suggestion_detail"),
    path("reports/", views.report_list, name="report_list"),
    path("reports/<int:report_id>/", views.report_detail, name="report_detail"),
    path("reports/<int:report_id>/download/<str:format>/", views.report_download, name="report_download"),
    path("database/", views.drug_database_list, name="drug_database_list"),
    path("database/new/", views.drug_database_create, name="drug_database_create"),
    path("database/<int:drug_id>/", views.drug_database_edit, name="drug_database_edit"),
    path("records/<str:table_name>/<str:record_id>/", views.record_inspector, name="record_inspector"),
]
