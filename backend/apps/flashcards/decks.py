"""Flashcard decks: one per clinical study topic (the lessons taxonomy's
topics are the sub-categories, its CATEGORIES the categories), holding the
topic's drugs that have card facts, in a fixed study order -- a learner
picks a category, then a topic, and works through its drugs one card at a
time until the deck is done, rather than getting cards at random.
"""

from apps.drugs.models import Ingredient
from apps.lessons.data.study_topics import CATEGORIES, STUDY_TOPICS
from apps.lessons.selectors import l2_slug_index, ordered_topic_slugs

from .models import TopicProgress

_TOPIC_BY_KEY = {t["key"]: t for t in STUDY_TOPICS}
_CATEGORY_BY_KEY = {c["key"]: c for c in CATEGORIES}


def _carded_slugs() -> set[str]:
    """Drugs build_flashcards gave at least one Persian fact -- a card."""
    return set(
        Ingredient.objects.filter(flashcard_facts__lang="fa")
        .values_list("slug", flat=True)
        .distinct()
    )


def all_decks() -> list[dict]:
    """[{category, topics: [{topic, slugs}]}] in taxonomy order, leaving out
    topics with no carded drug and categories with no such topic."""
    index = l2_slug_index()
    carded = _carded_slugs()
    out = []
    for category in CATEGORIES:
        topics = []
        for topic in STUDY_TOPICS:
            if topic["category"] != category["key"]:
                continue
            slugs = [s for s in ordered_topic_slugs(topic["key"], index) if s in carded]
            if slugs:
                topics.append({"topic": topic, "slugs": slugs})
        if topics:
            out.append({"category": category, "topics": topics})
    return out


def deck_slugs(topic_key: str) -> list[str] | None:
    """This topic's carded drugs in order, or None for an unknown topic."""
    if topic_key not in _TOPIC_BY_KEY:
        return None
    carded = _carded_slugs()
    return [s for s in ordered_topic_slugs(topic_key) if s in carded]


def next_topic(topic_key: str, decks: list[dict] | None = None) -> dict | None:
    """The deck after this one: the next topic in the same category, else the
    first topic of the next category; None after the very last."""
    flat = [t["topic"] for d in (decks or all_decks()) for t in d["topics"]]
    keys = [t["key"] for t in flat]
    if topic_key not in keys:
        return None
    i = keys.index(topic_key)
    if i + 1 >= len(flat):
        return None
    nxt = flat[i + 1]
    category = _CATEGORY_BY_KEY[nxt["category"]]
    return {
        "key": nxt["key"],
        "name_fa": nxt["name_fa"],
        "name_en": nxt["name_en"],
        "category_key": category["key"],
        "category_name_fa": category["name_fa"],
        "category_name_en": category["name_en"],
    }


def topic_meta(topic_key: str) -> tuple[dict, dict]:
    topic = _TOPIC_BY_KEY[topic_key]
    return topic, _CATEGORY_BY_KEY[topic["category"]]


def progress_map(user) -> dict[str, TopicProgress]:
    return {p.topic_key: p for p in TopicProgress.objects.filter(user=user)}
