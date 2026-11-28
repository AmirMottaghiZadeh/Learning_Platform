from django.contrib.postgres.indexes import GinIndex
from django.db import migrations


def create_index(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT i.indisvalid FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid "
                       "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relname=%s AND n.nspname=current_schema()",
                       ["hybrid_chunk_fts_idx"])
        row = cursor.fetchone()
    if row and row[0]:
        return
    if row:
        schema_editor.execute('DROP INDEX CONCURRENTLY "hybrid_chunk_fts_idx"')
    schema_editor.execute(GinIndex(fields=["search_document"], name="hybrid_chunk_fts_idx").create_sql(
        apps.get_model("ai_retrieval", "SearchChunk"), schema_editor, concurrently=True))


def drop_index(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute('DROP INDEX CONCURRENTLY IF EXISTS "hybrid_chunk_fts_idx"')


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("ai_retrieval", "0002_retrievalgeneration_article_ids")]
    operations = [migrations.SeparateDatabaseAndState(
        database_operations=[migrations.RunPython(create_index, drop_index)],
        state_operations=[migrations.AddIndex(model_name="searchchunk", index=GinIndex(
            fields=["search_document"], name="hybrid_chunk_fts_idx"))])]
