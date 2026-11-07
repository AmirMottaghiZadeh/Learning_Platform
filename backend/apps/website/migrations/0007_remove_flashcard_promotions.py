from django.db import migrations

REPLACEMENTS = {'در فارمنتا پنج جعبه با فاصله\u200cهای تقریبی صفر، ۳، ۷، ۱۶ و ۳۵ روز استفاده می\u200cشود.': 'برای '
                                                                                             'مرور '
                                                                                             'شخصی '
                                                                                             'می\u200cتوانید '
                                                                                             'فاصلهٔ '
                                                                                             'جعبه\u200cها '
                                                                                             'را '
                                                                                             'با '
                                                                                             'زمان '
                                                                                             'مطالعهٔ '
                                                                                             'خود '
                                                                                             'تنظیم '
                                                                                             'کنید.',
 '<h2>فلش\u200cکارت\u200cهای آمادهٔ فارمنتا</h2>': '<h2>خودآزمایی در فارمنتا</h2>',
 '<p>در اپ فارمنتا فلش\u200cکارت هر دارو از پیش ساخته شده است: موارد مصرف، عوارض شایع و جدی، اشکال دارویی و منع مصرف و هشدار جعبه\u200cای، به\u200cصورت عبارت\u200cهای کوتاه. زمان\u200cبندی جعبه\u200cها خودکار است و کارت\u200cهای موعدرسیدهٔ هر روز در داشبورد نشان داده می\u200cشوند.</p>': '<p>در '
                                                                                                                                                                                                                                                                                                'اپ '
                                                                                                                                                                                                                                                                                                'فارمنتا '
                                                                                                                                                                                                                                                                                                'پس '
                                                                                                                                                                                                                                                                                                'از '
                                                                                                                                                                                                                                                                                                'خواندن '
                                                                                                                                                                                                                                                                                                'دارونامه '
                                                                                                                                                                                                                                                                                                'می\u200cتوانید '
                                                                                                                                                                                                                                                                                                'از '
                                                                                                                                                                                                                                                                                                'دسته '
                                                                                                                                                                                                                                                                                                'و '
                                                                                                                                                                                                                                                                                                'زیردستهٔ '
                                                                                                                                                                                                                                                                                                'دلخواه '
                                                                                                                                                                                                                                                                                                'آزمون '
                                                                                                                                                                                                                                                                                                'بدهید '
                                                                                                                                                                                                                                                                                                'و '
                                                                                                                                                                                                                                                                                                'پاسخ\u200cهای '
                                                                                                                                                                                                                                                                                                'اشتباه '
                                                                                                                                                                                                                                                                                                'را '
                                                                                                                                                                                                                                                                                                'مرور '
                                                                                                                                                                                                                                                                                                'کنید.</p>',
 'درس\u200cنامهٔ کامل، فلش\u200cکارت و آزمون همین داروها': 'دارونامهٔ کامل و آزمون همین داروها',
 'همراه با فلش\u200cکارت و آزمون در اپ فارمنتا': 'همراه با آزمون در اپ فارمنتا',
 '، فلش\u200cکارت لایتنر با مرور خودکار، آزمون': '، آزمون'}


def remove_retired_promotions(apps, schema_editor):
    db = schema_editor.connection.alias
    for post in apps.get_model("website", "Post").objects.using(db).all().iterator():
        body = post.body_html
        for old, new in REPLACEMENTS.items():
            body = body.replace(old, new)
        if body != post.body_html:
            post.body_html = body
            post.save(using=db, update_fields=["body_html"])


class Migration(migrations.Migration):
    dependencies = [("website", "0006_alter_contentblock_screen_and_more")]
    operations = [migrations.RunPython(remove_retired_promotions, migrations.RunPython.noop)]
