# Quiz and flashcard content (study_content)

The app's old rule-based question bank and flashcard facts were retired (see PHASES / README).
The new content is written by language models from the drug profiles and kept in a database of
its own, outside this repository:

    /home/amir/Documents/openfda/study_content/study_content.db      (schema.sql, README.md next to it)

`pipeline_v2.db` is only read from there. The app will load from `study_content.db` when the
content is ready (a loader like `import_openfda` is the next step, with the models for the new
shape: questions with explanations and evidence, flashcards as lists of very short phrases).

What is decided:

- Questions are generated only from a drug's own profile text, bilingual, four options, one right,
  with an explanation and the quoted passage it rests on; the quote is checked against the text.
- Flashcards are telegraphic (2-6 phrases of at most 8 words) and cover only indications, the
  common and serious side effects particular to the drug, important interactions and warnings
  (with absolute contraindications), the boxed warning, and briefly the mechanism.
- A second model verifies what the first wrote; people grade a sample. Until the loader exists the
  quiz answers 422 `INSUFFICIENT_QUESTIONS` and the flashcard deck seeds empty.
