from django.db import migrations


def _table_columns(connection, table_name):
    with connection.cursor() as cursor:
        description = connection.introspection.get_table_description(cursor, table_name)
    return {column.name for column in description}


def repair_drugs_schema(apps, schema_editor):
    connection = schema_editor.connection
    existing_tables = set(connection.introspection.table_names())

    Drug = apps.get_model("drugs", "Drug")
    DrugDatasetDocument = apps.get_model("drugs", "DrugDatasetDocument")

    if DrugDatasetDocument._meta.db_table not in existing_tables:
        schema_editor.create_model(DrugDatasetDocument)
        existing_tables.add(DrugDatasetDocument._meta.db_table)

    dataset_columns = _table_columns(connection, DrugDatasetDocument._meta.db_table)
    for field_name in [
        "schema_version",
        "source_file",
        "source_path",
        "source_format",
        "source_size_bytes",
        "source_sha256",
        "source_metadata",
        "extraction_metadata",
        "warnings",
        "enrichment_metadata",
        "imported_at",
        "updated_at",
    ]:
        field = DrugDatasetDocument._meta.get_field(field_name)
        if field.column not in dataset_columns:
            schema_editor.add_field(DrugDatasetDocument, field)
            dataset_columns.add(field.column)

    drug_columns = _table_columns(connection, Drug._meta.db_table)
    for field_name in [
        "atc_categories",
        "atc_classes",
        "atc_codes",
        "atc_subclasses",
        "breastfeeding",
        "clinical_notes",
        "dataset_document",
        "dose_adjustment",
        "dosing_and_administration",
        "extra_attributes",
        "pregnancy",
        "source_row",
        "source_table",
        "category",
    ]:
        field = Drug._meta.get_field(field_name)
        if field.column not in drug_columns:
            schema_editor.add_field(Drug, field)
            drug_columns.add(field.column)


class Migration(migrations.Migration):

    dependencies = [
        ("drugs", "0005_drug_category"),
    ]

    operations = [
        migrations.RunPython(repair_drugs_schema, migrations.RunPython.noop),
    ]
