class FeedbackRouter:
    """Feedback tables live exclusively in their own physical database."""
    def db_for_read(self, model, **hints):
        return "ai_feedback" if model._meta.app_label == "ai_feedback" else None

    db_for_write = db_for_read

    def allow_relation(self, obj1, obj2, **hints):
        labels = {obj1._meta.app_label, obj2._meta.app_label}
        return labels == {"ai_feedback"} if "ai_feedback" in labels else None

    def allow_migrate(self, db, app_label, **hints):
        if app_label == "ai_feedback":
            return db == "ai_feedback"
        return False if db == "ai_feedback" else None
