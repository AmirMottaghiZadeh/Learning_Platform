from .base import GeneratedQuestion, make_choices


class BrandQuestionGenerator:
    question_type = "BRAND"

    def generate(self, source, distractors) -> GeneratedQuestion:
        correct_answer = source.brand_name
        wrong_answers = [item.brand_name for item in distractors]

        return GeneratedQuestion(
            question_type=self.question_type,
            text=f"برند داروی «{source.generic_name}» کدام است؟",
            choices=make_choices(correct_answer, wrong_answers),
            correct_answer=correct_answer,
            knowledge_source_id=source.id,
        )
