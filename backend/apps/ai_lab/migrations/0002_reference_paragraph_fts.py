"""Build the derived lexical index without blocking normal table writes."""
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from django.db import migrations, models


def index_definition():
    return GinIndex(SearchVector("text", config="english"),
                    condition=models.Q(retrieval_number__isnull=False), name="ref_paragraph_fts_idx")


def create_index(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    paragraph = apps.get_model("ai_lab", "ReferenceParagraph")
    # An interrupted concurrent build can leave an invalid index. A retry must
    # repair it, rather than treating its name as proof that indexing succeeded.
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT i.indisvalid FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid "
                       "JOIN pg_namespace n ON n.oid = c.relnamespace "
                       "WHERE c.relname = %s AND n.nspname = current_schema()", ["ref_paragraph_fts_idx"])
        existing = cursor.fetchone()
    if existing and existing[0]:
        return
    if existing:
        schema_editor.execute('DROP INDEX CONCURRENTLY IF EXISTS "ref_paragraph_fts_idx"')
    schema_editor.execute(index_definition().create_sql(paragraph, schema_editor, concurrently=True))


def drop_index(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute('DROP INDEX CONCURRENTLY IF EXISTS "ref_paragraph_fts_idx"')


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("ai_lab", "0001_initial")]
    operations = [migrations.SeparateDatabaseAndState(
        database_operations=[migrations.RunPython(create_index, drop_index)],
        state_operations=[migrations.AddIndex(model_name="referenceparagraph", index=index_definition())],
    )]
