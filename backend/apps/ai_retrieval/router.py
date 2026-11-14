from django.conf import settings


class RetrievalRouter:
    def db_for_read(self, model, **hints):
        return settings.AI_RETRIEVAL_DATABASE_ALIAS if model._meta.app_label == "ai_retrieval" else None

    db_for_write = db_for_read

    def allow_relation(self, obj1, obj2, **hints):
        labels = {obj1._meta.app_label, obj2._meta.app_label}
        return labels == {"ai_retrieval"} if "ai_retrieval" in labels else None

    def allow_migrate(self, db, app_label, **hints):
        if app_label == "ai_retrieval":
            return db == settings.AI_RETRIEVAL_DATABASE_ALIAS
        return False if db == "reference_search" else None
