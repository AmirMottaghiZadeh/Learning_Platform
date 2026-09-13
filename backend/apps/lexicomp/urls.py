from django.urls import path

from .views import DrugSearchView, InteractionCheckView

urlpatterns = [
    path("lexicomp/drugs/", DrugSearchView.as_view(), name="lexicomp-drugs"),
    path("lexicomp/interactions/", InteractionCheckView.as_view(), name="lexicomp-interactions"),
]
