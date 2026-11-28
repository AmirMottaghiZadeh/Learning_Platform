from django.db import migrations


def seed(apps,schema_editor):
    preset=apps.get_model("data_quality_center","AIPromptPreset")
    rows=[
        ("structure","ویرایش ساختاری جملات","ساختار و جمله‌بندی ستون‌های انتخاب‌شده را روان و منظم کن؛ همهٔ حقایق بالینی، اعداد، دوزها، هشدارها و محدودیت‌ها را دقیقاً حفظ کن. اطلاعات جدید اضافه نکن."),
        ("align","تطبیق با متن خام OpenFDA","خلاصه‌های انتخاب‌شده را با متن خام OpenFDA همین بخش مقایسه کن. ناسازگاری‌های قطعی با منبع را اصلاح کن و موارد نامطمئن یا اطلاعاتی که در منبع نیست را در notes توضیح بده؛ اطلاعات پزشکی بیرونی اضافه نکن."),
        ("fa_to_en","ترجمه فارسی به انگلیسی","فقط خلاصهٔ فارسی را به انگلیسی پزشکی دقیق ترجمه و در ستون summary_en قرار بده؛ summary_fa را تغییر نده. تمام اعداد، واحدها، هشدارها، قیود و ترتیب توصیه‌ها حفظ شوند."),
        ("en_to_fa","ترجمه انگلیسی به فارسی","فقط خلاصهٔ انگلیسی را به فارسی پزشکی روان و دقیق ترجمه و در summary_fa قرار بده؛ summary_en را تغییر نده. دوزها، واحدها، هشدارها و محدودیت‌ها کامل حفظ شوند."),
    ]
    for order,(action,name,instruction) in enumerate(rows):
        if not preset.objects.using(schema_editor.connection.alias).filter(action=action).exists():
            preset.objects.using(schema_editor.connection.alias).create(action=action,name=name,instruction=instruction,order=order)


class Migration(migrations.Migration):
    dependencies=[("data_quality_center","0008_ai_editing")]
    operations=[migrations.RunPython(seed,migrations.RunPython.noop)]
