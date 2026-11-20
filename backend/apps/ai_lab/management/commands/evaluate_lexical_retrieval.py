"""Fixed-plan retrieval diagnostics. No provider calls or generated clinical answers."""
from pathlib import Path
import json
import statistics
import time

from django.core.management.base import BaseCommand, CommandError
from django.test import override_settings

from apps.ai_lab import evaluation, lexical, reference_index, retrieval, selection
from apps.ai_lab.provider import ProviderError


DEFAULT_PLANS = Path(lexical.__file__).parent / "benchmark" / "lexical_cases.json"


def evaluate_plan(case, plan, repeat):
    context = lexical.search_context(case["question"], plan["queries"], lookup_kind=plan.get("lookup_kind", "topic"),
        audience=plan.get("audience", "general"), intent=plan.get("intent", "general"), keywords=plan.get("keywords", []))
    # Candidate retrieval is measured separately from the within-article test.
    # Expected IDs/headings are never supplied to either ranker as query terms.
    candidates = retrieval.search_articles(plan["queries"], None, {})
    ranked = lexical.rank_topics(retrieval.prioritize_topics(candidates, context.lookup_kind, context.audience), context)
    identifiers = [row["id"] for row in ranked]
    evidence, rows = evaluation.SourceEvidence(), []
    bindings = evidence.bind(case)
    for expected in bindings:
        timings, audit, sections = [], {}, []
        for _ in range(repeat):
            before = time.perf_counter()
            audit = {}
            with override_settings(AI_LAB_PREPROCESSED_MODE="require"):
                sections = retrieval.read_sections([expected["article_id"]], None, audit, context=context)
            timings.append(round((time.perf_counter() - before) * 1000, 3))
        headings = [row["heading"] for row in sections]
        passages = [p for section in sections for p in section["passages"]]
        selection_audit = {}
        _, selected = selection.select_evidence(sections, selection_audit)
        selected_headings = {p.section for p in selected}
        first_batch_headings = {p.section for p in selected[:selection.BATCH_SIZE]}
        source_blocks = {block.paragraph_id: block for block in evidence.article(expected["article_id"])[1].blocks}
        anchors_valid = bool(passages) and all(
            (block := source_blocks.get(p.target["params"]["searchAnchor"])) is not None
            and block.text == p.text and block.section_id == p.target["params"]["sectionId"]
            and p.content_hash == expected["content_hash"] for p in passages)
        rows.append({"article_id": expected["article_id"], "canonical_candidate_rank":
            identifiers.index(expected["article_id"]) + 1 if expected["article_id"] in identifiers else None,
            "expected_heading_count": len(expected["headings"]),
            "expected_heading_ranks": [headings.index(heading) + 1 if heading in headings else None for heading in expected["headings"]],
            "any_expected_heading_available": any(heading in headings for heading in expected["headings"]),
            "all_expected_headings_available": all(heading in headings for heading in expected["headings"]),
            "source_anchors_valid": anchors_valid, "selected_sections": len(sections),
            "local_evidence_passages": len(selected), "local_evidence_characters": selection_audit["selected_passage_characters"],
            "local_any_expected_heading_available": any(heading in selected_headings for heading in expected["headings"]),
            "local_all_expected_headings_available": all(heading in selected_headings for heading in expected["headings"]),
            "first_batch_any_expected_heading_available": any(heading in first_batch_headings for heading in expected["headings"]),
            "first_batch_all_expected_headings_available": all(heading in first_batch_headings for heading in expected["headings"]),
            "pooled_passages": len(passages), "menu_characters": sum(len(row["heading"]) + len(row["preview"]) for row in sections),
            "legacy_menu_characters": sum(len(row["heading"]) + len(row["preview"]) for row in retrieval.read_sections([expected["article_id"]], None, {})),
            "read_ms": timings, "median_read_ms": statistics.median(timings), "engine": audit.get("lexical_engine")})
    return {"case_id": case["id"], "sources": rows}


class Command(BaseCommand):
    help = "Measure fixed-plan article ordering and within-article lexical recall without any model requests."

    def add_arguments(self, parser):
        parser.add_argument("--dataset", default=str(evaluation.DEFAULT_DATASET))
        parser.add_argument("--plans", default=str(DEFAULT_PLANS))
        parser.add_argument("--repeat", type=int, default=3)
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        try:
            if not 1 <= options["repeat"] <= 10:
                raise evaluation.EvaluationError("INVALID_REPEAT")
            data = evaluation.load_dataset(options["dataset"])
            cases = {case["id"]: case for case in data["cases"]}
            plan_data = json.loads(Path(options["plans"]).read_text())
            if not isinstance(plan_data, dict):
                raise evaluation.EvaluationError("INVALID_PLANS")
            plans = plan_data.get("plans")
            if plan_data.get("schema") != 1 or not isinstance(plans, list) or not 1 <= len(plans) <= 100:
                raise evaluation.EvaluationError("INVALID_PLANS")
            seen = set()
            for plan in plans:
                if (not isinstance(plan, dict) or not isinstance(plan.get("case_id"), str)
                        or plan["case_id"] not in cases or plan["case_id"] in seen
                        or cases[plan["case_id"]]["expect"] != "answerable"
                        or len(cases[plan["case_id"]]["expected"]) != 1
                        or not isinstance(plan.get("queries"), list) or not 1 <= len(plan["queries"]) <= 2
                        or any(not isinstance(q, str) or not 1 <= len(q) <= 140 for q in plan["queries"])
                        or plan.get("intent", "general") not in lexical.INTENTS
                        or plan.get("lookup_kind", "topic") not in {"topic", "drug"}
                        or plan.get("audience", "general") not in {"general", "adult", "pediatric", "patient"}
                        or not isinstance(plan.get("keywords", []), list)
                        or len(plan.get("keywords", [])) > 8
                        or any(not isinstance(word, str) or len(word) > 100 for word in plan.get("keywords", []))):
                    raise evaluation.EvaluationError("INVALID_PLAN")
                seen.add(plan["case_id"])
            stamp = reference_index.source_stamp()
            generation = reference_index.active_generation(stamp)
            if generation is None:
                raise ProviderError("REFERENCE_INDEX_NOT_READY")
            rows = []
            for plan in plans:
                rows.append(evaluate_plan(cases[plan["case_id"]], plan, options["repeat"]))
                self.stdout.write(f"Checked {plan['case_id']}")
            sources = [source for row in rows for source in row["sources"]]
            report = {"schema": 1, "kind": "fixed_plan_lexical_retrieval", "lexical_version": lexical.LEXICAL_VERSION,
                "selection_version": selection.SELECTION_VERSION,
                "scope": "fixed_authored_plans_and_expected_articles_not_end_to_end_answers",
                "generation": str(generation), "provider_requests": 0, "clinical_quality_assessed": False,
                "source_unchanged": reference_index.source_stamp() == stamp,
                "dataset_digest": evaluation.digest(data), "plans_digest": evaluation.digest(plan_data),
                "pipeline_code_digest": evaluation.digest({Path(module.__file__).name: Path(module.__file__).read_text()
                    for module in [lexical, retrieval, reference_index, selection]}),
                "cases": rows, "summary": {"cases": len(rows),
                    "any_expected_heading_available": sum(row["any_expected_heading_available"] for row in sources),
                    "all_expected_headings_available": sum(row["all_expected_headings_available"] for row in sources),
                    "all_source_anchors_valid": all(row["source_anchors_valid"] for row in sources),
                    "local_any_expected_heading_available": sum(row["local_any_expected_heading_available"] for row in sources),
                    "local_all_expected_headings_available": sum(row["local_all_expected_headings_available"] for row in sources),
                    "first_batch_any_expected_heading_available": sum(row["first_batch_any_expected_heading_available"] for row in sources),
                    "first_batch_all_expected_headings_available": sum(row["first_batch_all_expected_headings_available"] for row in sources),
                    "within_article_read_median_ms": statistics.median(row["median_read_ms"] for row in sources)}}
            evaluation.write_private_json(options["output"], report)
        except (evaluation.EvaluationError, ProviderError) as exc:
            raise CommandError(str(exc)) from None
        except (OSError, ValueError, TypeError):
            raise CommandError("LEXICAL_EVALUATION_FAILED") from None
        if not report["source_unchanged"] or not report["summary"]["all_source_anchors_valid"]:
            raise CommandError("LEXICAL_SOURCE_VERIFICATION_FAILED")
        self.stdout.write(f"Checked {len(rows)} fixed plans; no model requests. Report: {options['output']}")
