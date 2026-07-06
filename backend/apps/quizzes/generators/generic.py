from .base import GeneratedQuestion, make_choices


class GenericQuestionGenerator:
    question_type = "GENERIC"

    def generate(self, source, distractors) -> GeneratedQuestion:
        correct_answer = source.generic_name
        wrong_answers = [item.generic_name for item in distractors]

        return GeneratedQuestion(
            question_type=self.question_type,
            text=f"نام ژنریک برند «{source.brand_name}» کدام است؟",
            choices=make_choices(correct_answer, wrong_answers),
            correct_answer=correct_answer,
            knowledge_source_id=source.id,
        )
