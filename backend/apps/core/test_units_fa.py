from django.test import SimpleTestCase

from apps.core.units_fa import standardize_in, standardize_units


class StandardizeUnitsTests(SimpleTestCase):
    def assertBecomes(self, text, expected):
        self.assertEqual(standardize_units(text), expected, text)

    def test_simple_and_compound_units(self):
        self.assertBecomes("۱۰ میلی‌گرم", "10 mg")
        self.assertBecomes("۱۰ میلی گرم بر کیلوگرم در روز", "10 mg/kg/day")
        self.assertBecomes("۵ میلی‌گرم بر متر مربع سطح بدن", "5 mg/m² سطح بدن")
        self.assertBecomes("۲۵۰ میلی‌گرم/میلی‌لیتر", "250 mg/mL")
        self.assertBecomes("۰٫۵ میکروگرم بر کیلوگرم در دقیقه", "0.5 mcg/kg/min")
        self.assertBecomes("۱۴۰ میلی‌اکی‌والان در لیتر", "140 mEq/L")
        self.assertBecomes("فشار ۱۴۰ میلی‌متر جیوه", "فشار 140 mmHg")
        self.assertBecomes("۲۰ واحد بین‌المللی", "20 IU")
        self.assertBecomes("۳ میلی‌گرم در هر میلی‌لیتر", "3 mg/mL")
        self.assertBecomes("۱۰۰ واحد به ازای هر کیلوگرم در روز", "100 units/kg/day")

    def test_kidney_function_per_body_surface(self):
        self.assertBecomes("۳۰ میلی‌لیتر در دقیقه/۱.۷۳ متر مربع", "30 mL/min/1.73 m²")
        self.assertBecomes("۴۰ میلی‌لیتر در دقیقه بر ۱٫۷۳ مترمربع", "40 mL/min/1.73 m²")

    def test_counts_per_volume(self):
        self.assertBecomes("۷۵×۱۰⁹ در لیتر یا بیشتر", "75×10⁹/L یا بیشتر")
        self.assertBecomes("۵۰۰ سلول در میکرولیتر", "۵۰۰ سلول/µL")
        self.assertBecomes("کمتر از ۱۵۰۰ در میلی‌متر مکعب", "کمتر از 1500/mm³")
        # a number after «در» is an amount, not a denominator
        self.assertBecomes("۵۰۰ میلی‌گرم در ۱۰۰ میلی‌لیتر", "500 mg در 100 mL")

    def test_a_point_in_time_is_not_a_rate(self):
        self.assertBecomes("۱۰ میلی‌گرم در روز اول", "10 mg در روز اول")
        self.assertBecomes("۱۰ میلی‌گرم در هفته دوم", "10 mg در هفته دوم")
        self.assertBecomes("۵ میلی‌گرم در ساعت ۸ صبح", "5 mg در ساعت ۸ صبح")
        self.assertBecomes("۱۰ میلی‌گرم در ساعت های اول", "10 mg در ساعت های اول")
        self.assertBecomes("۱۰ میلی‌گرم در روز، سپس", "10 mg/day، سپس")
        self.assertBecomes("۱۰ میلی‌گرم در روز در روز", "10 mg/day در روز")

    def test_durations_on_their_own_stay_persian(self):
        self.assertBecomes("به مدت ۷ روز هر ۸ ساعت", "به مدت ۷ روز هر ۸ ساعت")

    def test_words_that_are_also_ordinary_persian_need_a_number(self):
        self.assertBecomes("کمپرس گرم روی محل", "کمپرس گرم روی محل")
        self.assertBecomes("۲ گرم وریدی", "2 g وریدی")
        self.assertBecomes("به‌صورت دوز واحد روزانه", "به‌صورت دوز واحد روزانه")
        self.assertBecomes("پیشگیری در مول هیداتیدیفرم", "پیشگیری در مول هیداتیدیفرم")
        self.assertBecomes("دندان مولار", "دندان مولار")
        self.assertBecomes("کالری دریافتی", "کالری دریافتی")
        self.assertBecomes("۵۰۰۰ واحد/میلی‌لیتر", "5000 units/mL")

    def test_one_unit_is_singular(self):
        self.assertBecomes("۱ واحد انسولین", "1 unit انسولین")
        self.assertBecomes("۱۱ واحد", "11 units")
        self.assertBecomes("۰٫۱ واحد", "0.1 units")

    def test_adjective_form_after_a_number(self):
        self.assertBecomes("قرص ۵۰۰ میلی‌گرمی", "قرص 500 mg")
        self.assertBecomes("وسیلهٔ اندازه‌گیری میلی‌لیتری", "وسیلهٔ اندازه‌گیری میلی‌لیتری")
        self.assertBecomes("در غلظت‌های نانومولار", "در غلظت‌های nM")

    def test_rates_named_in_words(self):
        self.assertBecomes("نبض (ضربان در دقیقه)", "نبض (beats/min)")
        self.assertBecomes("تعداد تنفس (تنفس در دقیقه)", "تعداد تنفس (breaths/min)")

    def test_latin_spellings_are_normalized(self):
        self.assertBecomes("۵ ml و ۲ mg/dl", "5 mL و 2 mg/dL")
        self.assertBecomes("۱۰ mg/m2 و ۵ ug", "10 mg/m² و 5 mcg")
        self.assertBecomes("html و drug", "html و drug")

    def test_templates_and_spacing(self):
        self.assertBecomes("$result0 میلی‌گرم", "$result0 mg")
        self.assertBecomes("۱۰میلی‌گرم", "10 mg")

    def test_the_numbers_of_a_quantity_get_latin_digits(self):
        self.assertBecomes("۲۵ تا ۵۰ میلی‌گرم", "25 تا 50 mg")
        self.assertBecomes("قرص: ۰٫۲۵، ۰٫۵ و ۱ میلی‌گرم", "قرص: 0.25، 0.5 و 1 mg")
        self.assertBecomes("۵۰۰٬۰۰۰ واحد", "500,000 units")
        self.assertBecomes("۱۰۰ میلی‌گرم/۵ میلی‌لیتر", "100 mg/5 mL")
        self.assertBecomes("≥۳۰ کیلوگرم", "≥30 kg")
        # other numbers keep their Persian digits
        self.assertBecomes("به مدت ۷ روز", "به مدت ۷ روز")
        self.assertBecomes("۱۲۵ mg روز ۱ و ۸۰ mg", "125 mg روز ۱ و 80 mg")

    def test_json_values(self):
        value = {"title_fa": "۲ گرم", "choices": [{"title_primary_fa": "۵ میلی‌لیتر"}], "n": 3}
        self.assertEqual(standardize_in(value), {"title_fa": "2 g", "choices": [{"title_primary_fa": "5 mL"}], "n": 3})
        self.assertEqual(value["title_fa"], "۲ گرم")  # input untouched
        self.assertIsNone(standardize_units(None))
