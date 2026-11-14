"""Offline indexing queue. Paid embedding remains an explicitly budgeted CLI."""
from celery import shared_task
from django.core.management import call_command


@shared_task(name="ai_retrieval.build_index", queue="ai_indexing", max_retries=0,
             soft_time_limit=0, time_limit=0, acks_late=True)
def build_index(resume=None):
    options = {"resume": resume} if resume else {}
    call_command("build_hybrid_index", **options)
