from django.db import migrations


def _table_columns(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def repair_games_schema(apps, schema_editor):
    connection = schema_editor.connection

    GameSession = apps.get_model("games", "GameSession")
    GameQuestion = apps.get_model("games", "GameQuestion")
    GameAnswer = apps.get_model("games", "GameAnswer")
    Mistake = apps.get_model("games", "Mistake")

    session_columns = _table_columns(connection, GameSession._meta.db_table)
    for field_name in [
        "target_category_key",
        "status",
        "paused_at",
        "total_paused_seconds",
    ]:
        field = GameSession._meta.get_field(field_name)
        if field.column not in session_columns:
            schema_editor.add_field(GameSession, field)
            session_columns.add(field.column)

    question_columns = _table_columns(connection, GameQuestion._meta.db_table)
    for field_name in [
        "knowledge_source",
        "paused_seconds",
        "timer_extended_at",
        "timer_extension_seconds",
        "timer_extension_used",
    ]:
        field = GameQuestion._meta.get_field(field_name)
        if field.column not in question_columns:
            schema_editor.add_field(GameQuestion, field)
            question_columns.add(field.column)

    answer_columns = _table_columns(connection, GameAnswer._meta.db_table)
    for field_name in [
        "time_expired",
        "xp_delta",
        "scoring_rule_version",
    ]:
        field = GameAnswer._meta.get_field(field_name)
        if field.column not in answer_columns:
            schema_editor.add_field(GameAnswer, field)
            answer_columns.add(field.column)

    mistake_columns = _table_columns(connection, Mistake._meta.db_table)
    field = Mistake._meta.get_field("knowledge_source")
    if field.column not in mistake_columns:
        schema_editor.add_field(Mistake, field)

    GameSession.objects.filter(is_finished=True, status="").update(status="finished")
    GameSession.objects.filter(is_finished=False, status="").update(status="active")


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0005_gamequestion_timer_extended_at_and_more"),
    ]

    operations = [
        migrations.RunPython(repair_games_schema, migrations.RunPython.noop),
    ]
