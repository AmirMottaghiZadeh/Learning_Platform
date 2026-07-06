from apps.games.contracts import ScoringContext, ScoringResult


SCORING_RULE_VERSION = "mvp-scoring-v1"


def calculate_score(context: ScoringContext) -> ScoringResult:
    if not context.is_correct or context.time_expired:
        return ScoringResult(
            score_delta=0,
            xp_delta=0,
            streak_delta=-context.streak,
            rule_version=SCORING_RULE_VERSION,
            bonus={"streak": 0, "time": 0},
        )

    streak_bonus = min(context.streak, 5) * 2
    return ScoringResult(
        score_delta=10 + streak_bonus,
        xp_delta=10,
        streak_delta=1,
        rule_version=SCORING_RULE_VERSION,
        bonus={"streak": streak_bonus, "time": 0},
    )


def calculate_score_delta(*, is_correct: bool, streak: int) -> int:
    context = ScoringContext(
        is_correct=is_correct,
        time_expired=False,
        remaining_seconds=0,
        streak=streak,
    )
    return calculate_score(context).score_delta
