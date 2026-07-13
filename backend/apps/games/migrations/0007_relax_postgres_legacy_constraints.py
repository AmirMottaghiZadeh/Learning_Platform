from django.db import migrations


def _table_columns(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def relax_legacy_constraints(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != "postgresql":
        return

    existing_tables = set(connection.introspection.table_names())

    def drop_not_null(table_name, column_name):
        if table_name not in existing_tables:
            return
        if column_name not in _table_columns(connection, table_name):
            return
        schema_editor.execute(
            f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" DROP NOT NULL'
        )

    drop_not_null("games_gamequestion", "question_started_at")
    drop_not_null("games_gamequestion", "source_id")
    drop_not_null("games_gamequestion", "knowledge_source_id")
    drop_not_null("games_mistake", "source_id")
    drop_not_null("games_mistake", "knowledge_source_id")


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0006_repair_postgres_schema_drift"),
    ]

    operations = [
        migrations.RunPython(relax_legacy_constraints, migrations.RunPython.noop),
    ]
