from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class LearningTopicRef:
    key: str
    label: str = ""


@dataclass(frozen=True)
class LearningObjectRef:
    id: int
    display_name: str
    subtitle: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeSourceRef:
    id: int
    source_type: str
    prompt: str
    correct_answer: str
    topic: LearningTopicRef
    learning_object: LearningObjectRef
    explanation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class LearningProductAdapter(Protocol):
    product_id: str

    def list_knowledge_sources(
        self,
        context: Any,
    ) -> list[KnowledgeSourceRef]:
        ...

    def get_source_instance(self, knowledge_source_id: int):
        ...
