from functools import lru_cache

from django.conf import settings
from django.utils.module_loading import import_string

from apps.learning.contracts import LearningProductAdapter


@lru_cache(maxsize=1)
def get_learning_adapter() -> LearningProductAdapter:
    adapter_class = import_string(settings.LEARNING_PRODUCT_ADAPTER)
    return adapter_class()
