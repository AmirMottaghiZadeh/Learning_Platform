"""Bounded, source-derived search milestones. Never stores model reasoning."""
from copy import deepcopy


def apply_event(workflow, event):
    parts = deepcopy(workflow)
    index = event["part_index"]
    if not 0 <= index < 3:
        raise ValueError("Invalid question index")
    part = next((item for item in parts if item["part_index"] == index), None)
    if part is None:
        part = {"part_index": index, "question_fa": event["question_fa"], "queries": [], "titles": [], "articles": []}
        parts.append(part)
    kind = event["type"]
    if kind == "titles":
        if event["query"] not in part["queries"]:
            part["queries"] = [*part["queries"], event["query"]][:4]
        seen = {item["id"] for item in part["titles"]}
        for article in event["articles"]:
            if article["id"] not in seen and len(part["titles"]) < 120:
                part["titles"].append({"id": article["id"], "title": article["title"]})
                seen.add(article["id"])
    elif kind == "related_topics":
        existing = {item["id"] for item in part["titles"]}
        additions = [{"id": item["id"], "title": item["title"], "related_to": event["article_id"]}
                     for item in event["articles"] if item["id"] not in existing]
        position = next((i + 1 for i, item in enumerate(part["titles"]) if item["id"] == event["article_id"]), len(part["titles"]))
        part["titles"] = (part["titles"][:position] + additions + part["titles"][position:])[:120]
    elif kind == "article":
        part["current_article_id"] = event["article_id"]
        if not any(item["id"] == event["article_id"] for item in part["articles"]) and len(part["articles"]) < 8:
            part["articles"].append({"id": event["article_id"], "title": event["title"], "phase": "reading",
                                     "reviewed_passages": 0, "reviewing_count": 0})
    elif kind in {"sections", "paragraphs", "article_done"}:
        article = next((item for item in part["articles"] if item["id"] == event["article_id"]), None)
        if article is None:
            raise ValueError("Missing current article")
        if kind == "sections":
            article.update(phase="sections", paragraph_count=event["paragraph_count"],
                           sections=[{"id": item["id"], "heading": item["heading"]} for item in event["sections"][:60]])
        elif kind == "paragraphs":
            article.update(phase="paragraphs", reviewed_passages=event["reviewed_passages"],
                           reviewing_count=min(6, event["reviewing_count"]))
        else:
            article.update(phase=event["outcome"], reviewing_count=0)
    elif kind != "question":
        raise ValueError("Unknown search milestone")
    return parts
