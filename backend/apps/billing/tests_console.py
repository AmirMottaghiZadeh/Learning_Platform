from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import LearnerProfile

from . import config, services
from . import gateways
from .gateways import ZibalGateway, ZarinpalGateway
from .models import AdminAction, BillingSettings, DiscountCode, Entitlement, Feature, Order, PaymentGateway, Plan, PlanFeature, PlanPrice

User = get_user_model()


class ConsoleTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="root", email="root@example.com", password="pw-123456")
        self.client.force_login(self.admin)
        self.learner = User.objects.create_user(username="learner", email="l@example.com", password="x")
        LearnerProfile.objects.create(user=self.learner, display_name="سارا محمدی", study_field="pharmacy", phone="09120000000")
        self.plan = Plan.objects.create(slug="clinical", name_fa="بالینی", status=Plan.STATUS_ACTIVE)
        PlanFeature.objects.create(plan=self.plan, feature=Feature.objects.get(key="lexicomp"))
        PlanPrice.objects.create(plan=self.plan, duration_days=30, price_toman=150_000)


class AccessTests(ConsoleTestCase):
    def test_only_superusers_get_in(self):
        self.client.logout()
        res = self.client.get(reverse("console:users"))
        self.assertRedirects(res, f"{reverse('console:login')}?next=/ops/users/", fetch_redirect_response=False)
        staff = User.objects.create_user(username="staff", password="pw-123456", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("console:users")).status_code, 302)
        res = self.client.post(reverse("console:login"), {"username": "staff", "password": "pw-123456"})
        self.assertContains(res, "سوپریوزر نیست")

    def test_login(self):
        self.client.logout()
        res = self.client.post(reverse("console:login"), {"username": "root", "password": "pw-123456"})
        self.assertRedirects(res, reverse("console:users"), fetch_redirect_response=False)


class UsersPageTests(ConsoleTestCase):
    def test_list_search_segments_and_drawer(self):
        services.grant(self.learner, self.plan, days=30, source=Entitlement.SOURCE_ADMIN)
        res = self.client.get(reverse("console:users"), {"q": "۰۹۱۲", "u": self.learner.pk})
        self.assertContains(res, "سارا محمدی")
        self.assertContains(res, "بالینی")
        self.assertContains(res, "پرونده‌ی کاربر")
        res = self.client.get(reverse("console:users"), {"seg": "blocked"})
        self.assertNotContains(res, "سارا محمدی")
        res = self.client.get(reverse("console:users"), {"seg": "subscribed"})
        self.assertContains(res, "سارا محمدی")

    def test_detail_page(self):
        res = self.client.get(reverse("console:user", args=[self.learner.pk]))
        self.assertContains(res, "سارا محمدی")
        self.assertContains(res, "دادن پلن یا محصول")

    def test_grant_extend_revoke_are_audited(self):
        res = self.client.post(reverse("console:user_grant", args=[self.learner.pk]), {"plan": self.plan.pk, "days": "30", "note": "هدیه"})
        self.assertEqual(res.status_code, 302)
        ent = Entitlement.objects.get(user=self.learner)
        self.assertEqual(ent.source, Entitlement.SOURCE_ADMIN)
        self.assertEqual(ent.granted_by, self.admin)
        first_end = ent.ends_at

        self.client.post(reverse("console:entitlement_extend", args=[self.learner.pk, ent.pk]), {"days": "۱۰"})
        ent.refresh_from_db()
        self.assertEqual((ent.ends_at - first_end).days, 10)

        self.client.post(reverse("console:entitlement_revoke", args=[self.learner.pk, ent.pk]))
        ent.refresh_from_db()
        self.assertIsNotNone(ent.revoked_at)
        self.assertEqual(
            list(AdminAction.objects.filter(target_user=self.learner).values_list("action", flat=True)),
            ["revoke", "extend", "grant"],
        )

    def test_custom_days_and_permanent_grants(self):
        self.client.post(reverse("console:user_grant", args=[self.learner.pk]), {"plan": self.plan.pk, "days": "30", "custom_days": "45"})
        self.client.post(reverse("console:user_grant", args=[self.learner.pk]), {"plan": self.plan.pk, "days": ""})
        ents = list(Entitlement.objects.filter(user=self.learner).order_by("id"))
        self.assertEqual((ents[0].ends_at - ents[0].starts_at).days, 45)
        self.assertIsNone(ents[1].ends_at)

    def test_block_signs_out_and_unblock(self):
        self.client.post(reverse("console:user_block", args=[self.learner.pk]), {"block": "1"})
        self.learner.refresh_from_db()
        self.assertFalse(self.learner.is_active)
        self.client.post(reverse("console:user_block", args=[self.learner.pk]), {"block": "0"})
        self.learner.refresh_from_db()
        self.assertTrue(self.learner.is_active)
        res = self.client.post(reverse("console:user_block", args=[self.admin.pk]), {"block": "1"}, follow=True)
        self.assertContains(res, "نمی‌توانید حساب خودتان")

    def test_logout_all(self):
        res = self.client.post(reverse("console:user_logout_all", args=[self.learner.pk]))
        self.assertEqual(res.status_code, 302)
        self.assertTrue(AdminAction.objects.filter(action="logout_all").exists())

    def test_export_csv(self):
        res = self.client.get(reverse("console:users_export"))
        body = res.content.decode("utf-8")
        self.assertTrue(body.startswith("﻿"))
        self.assertIn("سارا محمدی", body)
        self.assertIn("09120000000", body)


class PlanBuilderTests(ConsoleTestCase):
    def test_wizard_end_to_end(self):
        res = self.client.post(reverse("console:plan_new") + "?kind=plan", {
            "kind": "plan", "name_fa": "دانشجویی", "name_en": "Student", "slug": "", "tagline_fa": "", "audience": "pharmacy", "order": "5",
        })
        plan = Plan.objects.get(slug="student")
        self.assertRedirects(res, reverse("console:plan_features", args=[plan.pk]), fetch_redirect_response=False)
        self.assertEqual(plan.status, Plan.STATUS_HIDDEN)

        flash = Feature.objects.get(key="flashcards")
        lessons = Feature.objects.get(key="lessons")
        self.assertContains(self.client.get(reverse("console:plan_features", args=[plan.pk])), "امکان کاملاً جدید")
        self.client.post(reverse("console:plan_features", args=[plan.pk]), {
            f"f_{flash.pk}": "on", f"limit_{flash.pk}": "۵۰", f"period_{flash.pk}": "day",
            f"f_{lessons.pk}": "on",
        })
        rows = {pf.feature.key: (pf.limit, pf.period) for pf in plan.plan_features.select_related("feature")}
        self.assertEqual(rows, {"flashcards": (50, "day"), "lessons": (None, "day")})

        res = self.client.post(reverse("console:plan_prices", args=[plan.pk]), {"new_days": "90", "new_price": "۳۰۰٬۰۰۰"})
        self.assertRedirects(res, reverse("console:plan_review", args=[plan.pk]), fetch_redirect_response=False)
        price = plan.prices.get()
        self.assertEqual((price.duration_days, price.price_toman), (90, 300_000))

        self.assertContains(self.client.get(reverse("console:plan_review", args=[plan.pk])), "۳ ماهه")
        self.client.post(reverse("console:plan_review", args=[plan.pk]), {"status": "active"})
        plan.refresh_from_db()
        self.assertEqual(plan.status, Plan.STATUS_ACTIVE)
        self.assertContains(self.client.get(reverse("console:plans")), "دانشجویی")

    def test_cannot_publish_without_a_price(self):
        plan = Plan.objects.create(slug="empty", name_fa="خالی", status=Plan.STATUS_HIDDEN)
        self.client.post(reverse("console:plan_review", args=[plan.pk]), {"status": "active"})
        plan.refresh_from_db()
        self.assertEqual(plan.status, Plan.STATUS_HIDDEN)

    def test_free_plan_skips_prices(self):
        free = Plan.objects.get(is_free=True)
        res = self.client.get(reverse("console:plan_prices", args=[free.pk]))
        self.assertRedirects(res, reverse("console:plan_review", args=[free.pk]), fetch_redirect_response=False)

    def test_copy(self):
        self.client.post(reverse("console:plan_copy", args=[self.plan.pk]))
        copy = Plan.objects.exclude(pk=self.plan.pk).get(name_fa="بالینی (کپی)")
        self.assertEqual(copy.status, Plan.STATUS_HIDDEN)
        self.assertEqual(copy.plan_features.count(), 1)
        self.assertEqual(copy.prices.count(), 1)

    def test_price_with_orders_is_retired_not_deleted(self):
        price = self.plan.prices.get()
        Order.objects.create(user=self.learner, plan=self.plan, price=price, amount_toman=1, payable_toman=1)
        self.client.post(reverse("console:plan_prices", args=[self.plan.pk]), {f"delete_{price.pk}": "on"})
        price.refresh_from_db()
        self.assertFalse(price.is_active)


class FeatureTests(ConsoleTestCase):
    def test_new_content_and_custom_features(self):
        self.client.post(reverse("console:feature_new"), {
            "name_fa": "بسته قلب", "key": "Cardio Pack", "kind": "content", "scope_type": "topic_category", "scope_category": "cardio-blood",
        })
        cardio = Feature.objects.get(key="cardio_pack")
        self.assertEqual((cardio.kind, cardio.scope_value), ("content", "cardio-blood"))
        self.assertTrue(cardio.is_wired)

        self.client.post(reverse("console:feature_new"), {
            "name_fa": "جزوه PDF", "key": "pdf_notes", "kind": "custom", "countable": "on", "unit_fa": "جزوه",
        })
        pdf = Feature.objects.get(key="pdf_notes")
        self.assertFalse(pdf.is_wired)
        self.assertTrue(pdf.countable)
        self.assertContains(self.client.get(reverse("console:features")), "در انتظار اتصال در کد")

        res = self.client.post(reverse("console:feature_new"), {"name_fa": "بی‌محتوا", "key": "x1", "kind": "content", "scope_type": "atc_prefix"}, follow=True)
        self.assertContains(res, "محتوای آن را مشخص کنید")

    def test_builtin_cannot_be_deleted_but_can_be_switched_off(self):
        quiz = Feature.objects.get(key="quiz")
        self.client.post(reverse("console:feature_edit", args=[quiz.pk]), {"op": "delete"})
        self.assertTrue(Feature.objects.filter(key="quiz").exists())
        self.client.post(reverse("console:feature_edit", args=[quiz.pk]), {"op": "toggle"})
        quiz.refresh_from_db()
        self.assertFalse(quiz.is_active)


class DiscountAndReportTests(ConsoleTestCase):
    def test_create_discount_with_jalali_dates(self):
        res = self.client.post(reverse("console:discounts"), {
            "code": "nowruz", "kind": "percent", "value": "۲۰", "max_uses": "100",
            "starts": "۱۴۰۵/۰۱/۰۱", "ends": "1405/01/13", "plans": [self.plan.pk], "note": "",
        })
        self.assertEqual(res.status_code, 302)
        code = DiscountCode.objects.get(code="NOWRUZ")
        self.assertEqual(code.percent, 20)
        self.assertEqual(timezone.localtime(code.starts_at, services.TEHRAN).date().isoformat(), "2026-03-21")
        self.assertEqual(list(code.plans.all()), [self.plan])
        res = self.client.post(reverse("console:discounts"), {"code": "BAD", "kind": "percent", "value": "150"})
        self.assertContains(res, "حداکثر ۱۰۰")

    def test_sales_and_audit_pages(self):
        order = services.create_order(self.learner, self.plan.prices.get())
        services.mark_paid(order.pk, gateway="fake", ref_id="R1")
        res = self.client.get(reverse("console:sales"))
        self.assertContains(res, "۱۵۰٬۰۰۰ تومان")
        self.assertContains(res, "سارا محمدی")
        self.client.post(reverse("console:user_logout_all", args=[self.learner.pk]))
        self.assertContains(self.client.get(reverse("console:audit")), "خروج از همه‌ی دستگاه‌ها")


class DeleteUserTests(ConsoleTestCase):
    def delete(self, user, confirm="09120000000", password="pw-123456"):
        return self.client.post(reverse("console:user_delete", args=[user.pk]), {"confirm": confirm, "password": password}, follow=True)

    def test_detail_page_offers_deletion(self):
        res = self.client.get(reverse("console:user", args=[self.learner.pk]))
        self.assertContains(res, "حذف همیشگی کاربر")

    def test_deletes_everything_but_keeps_paid_orders_for_sales(self):
        paid = services.create_order(self.learner, self.plan.prices.get())
        services.mark_paid(paid.pk, gateway="fake", ref_id="R1")
        pending = services.create_order(self.learner, self.plan.prices.get())
        pk = self.learner.pk

        res = self.delete(self.learner, confirm="۰۹۱۲۰۰۰۰۰۰۰")  # Persian digits are fine
        self.assertContains(res, "حذف شد")
        self.assertFalse(User.objects.filter(pk=pk).exists())
        self.assertFalse(LearnerProfile.objects.filter(user_id=pk).exists())
        self.assertFalse(Entitlement.objects.filter(user_id=pk).exists())
        self.assertFalse(Order.objects.filter(pk=pending.pk).exists())
        paid.refresh_from_db()
        self.assertIsNone(paid.user)
        self.assertIn("سارا محمدی", paid.deleted_user_label)

        sales = self.client.get(reverse("console:sales"))
        self.assertContains(sales, "کاربر حذف‌شده")
        self.assertContains(sales, "۱۵۰٬۰۰۰ تومان")
        action = AdminAction.objects.get(action="user_delete")
        self.assertEqual(action.details["phone"], "09120000000")
        self.assertIn("سارا محمدی", action.summary)

    def test_wrong_confirmation_or_password_deletes_nothing(self):
        self.assertContains(self.delete(self.learner, confirm="09129999999"), "دقیق وارد کنید")
        self.assertContains(self.delete(self.learner, password="nope"), "رمز حساب درست نیست")
        self.assertTrue(User.objects.filter(pk=self.learner.pk).exists())

    def test_superusers_and_yourself_cannot_be_deleted(self):
        other = User.objects.create_superuser(username="boss", email="boss@example.com", password="x")
        self.assertContains(self.delete(other, confirm="boss@example.com"), "سوپریوزر از پنل حذف نمی‌شوند")
        self.assertContains(self.delete(self.admin, confirm="root@example.com"), "سوپریوزر از پنل حذف نمی‌شوند")
        self.assertTrue(User.objects.filter(pk=other.pk).exists())


class GatewayPageTests(ConsoleTestCase):
    MERCHANT = "11111111-2222-3333-4444-555555555555"

    def setUp(self):
        super().setUp()
        config.clear_cache()
        self.addCleanup(config.clear_cache)

    def save(self, **fields):
        data = {"password": "pw-123456", "enforcement": "env", "sales_enabled": "on", "return_url": ""}
        data.update(fields)
        return self.client.post(reverse("console:gateway"), data, follow=True)

    def add(self, kind, **fields):
        data = {"password": "pw-123456", "kind": kind, "priority": "10", "is_enabled": "on"}
        data.update(fields)
        return self.client.post(f"{reverse('console:gateway_new')}?kind={kind}", data, follow=True)

    def test_page_falls_back_to_the_environment_and_lists_what_a_gateway_asks_for(self):
        with self.settings(BILLING_GATEWAY="zarinpal", ZARINPAL_MERCHANT_ID="", SITE_PUBLIC_URL="https://pharmenta.ir"):
            config.clear_cache()
            res = self.client.get(reverse("console:gateway"))
        self.assertContains(res, "از تنظیمات سرور")
        self.assertContains(res, "https://pharmenta.ir/pay/callback/sep/")
        self.assertContains(res, "https://pharmenta.ir/pay/callback/zarinpal/")
        self.assertContains(res, "443")
        self.assertContains(res, "افزودن سامان (سپ)")

    def test_adding_a_gateway_needs_the_password_and_a_valid_id(self):
        res = self.add("sep", password="nope", merchant_id="21009876")
        self.assertContains(res, "رمز حساب درست نیست")
        self.assertContains(self.add("sep", merchant_id="abc"), "فقط رقم")
        self.assertContains(self.add("zarinpal", merchant_id="short"), "۳۶ کاراکتری")
        self.assertFalse(PaymentGateway.objects.exists())

        res = self.add("sep", merchant_id="۲۱۰۰۹۸۷۶", title="بانک سامان")
        gw = PaymentGateway.objects.get()
        self.assertEqual((gw.kind, gw.merchant_id, gw.title, gw.is_enabled), ("sep", "21009876", "بانک سامان", True))
        self.assertContains(res, "••••••••9876")
        self.assertNotContains(res, "21009876")
        self.assertEqual(AdminAction.objects.get(action="gateway_edit").details["after"]["merchant"], "••••••••9876")
        self.assertEqual([g.kind for g in config.enabled_gateways()], ["sep"])
        # one of each kind
        self.add("sep", merchant_id="21009999")
        self.assertEqual(PaymentGateway.objects.count(), 1)

    def test_zibal_can_be_added_and_tested(self):
        res = self.add("zibal", merchant_id="merchant-1")
        gw = PaymentGateway.objects.get()
        self.assertEqual((gw.kind, gw.merchant_id), ("zibal", "merchant-1"))
        self.assertContains(res, "مرچنت زیبال")
        with mock.patch.object(ZibalGateway, "test", return_value="زیبال درخواست را پذیرفت؛ مرچنت درست است."):
            res = self.client.post(reverse("console:gateway_test", args=[gw.pk]), follow=True)
        self.assertContains(res, "مرچنت درست است")
        gw.refresh_from_db()
        self.assertTrue(gw.last_test_ok)

    def test_editing_keeps_the_saved_id_when_left_empty_and_toggling_switches_it(self):
        self.add("zarinpal", merchant_id=self.MERCHANT, sandbox="on")
        gw = PaymentGateway.objects.get()
        self.assertTrue(gw.sandbox)
        self.client.post(reverse("console:gateway_edit", args=[gw.pk]), {"password": "pw-123456", "priority": "5", "is_enabled": "on"})
        gw.refresh_from_db()
        self.assertEqual((gw.merchant_id, gw.priority, gw.sandbox), (self.MERCHANT, 5, False))
        res = self.client.post(reverse("console:gateway_toggle", args=[gw.pk]), follow=True)
        self.assertContains(res, "هیچ درگاهی فعال نیست")
        self.assertEqual(config.enabled_gateways(), [])

    def test_general_settings_are_saved_and_audited(self):
        with self.settings(BILLING_ENFORCEMENT_ENABLED=False):
            self.save(enforcement="on", return_url="https://app.pharmenta.ir")
            cfg = config.current()
            self.assertTrue(cfg.enforcement)
            self.assertEqual(cfg.return_url, "https://app.pharmenta.ir")
            self.assertEqual(AdminAction.objects.get(action="gateway_settings").details["after"]["enforcement"], True)
            self.save()
            self.assertFalse(config.current().enforcement)
        self.assertContains(self.save(return_url="ftp://x"), "https://")
        self.assertContains(self.save(password="nope"), "رمز حساب درست نیست")

    def test_paused_sales_refuse_checkout(self):
        self.save(sales_enabled="")
        from rest_framework.test import APIClient

        api = APIClient()
        api.force_authenticate(self.learner)
        res = api.post("/api/v1/billing/checkout/", {"price_id": self.plan.prices.get().pk}, format="json")
        self.assertEqual(res.status_code, 503)
        self.assertEqual(res.json()["code"], "SALES_PAUSED")

    def test_connection_test_records_the_result_on_the_gateway(self):
        self.add("zarinpal", merchant_id=self.MERCHANT)
        gw = PaymentGateway.objects.get()
        with mock.patch.object(ZarinpalGateway, "_post", return_value={"data": {"code": 100, "authority": "A1"}, "errors": []}):
            res = self.client.post(reverse("console:gateway_test", args=[gw.pk]), follow=True)
        self.assertContains(res, "مرچنت‌کد درست است")
        gw.refresh_from_db()
        self.assertTrue(gw.last_test_ok)
        with mock.patch.object(ZarinpalGateway, "_post", return_value={"data": [], "errors": {"code": -9, "message": "merchant invalid"}}):
            res = self.client.post(reverse("console:gateway_test", args=[gw.pk]), follow=True)
        self.assertContains(res, "اتصال ناموفق")
        gw.refresh_from_db()
        self.assertFalse(gw.last_test_ok)

    def test_sep_connection_test_names_an_unregistered_ip(self):
        self.add("sep", merchant_id="21009876")
        gw = PaymentGateway.objects.get()
        with mock.patch.object(gateways, "_post_json", return_value={"status": -1, "errorCode": "-106", "errorDesc": "ip not allowed"}):
            res = self.client.post(reverse("console:gateway_test", args=[gw.pk]), follow=True)
        self.assertContains(res, "ip not allowed")
        with mock.patch.object(gateways, "_post_json", return_value={"status": 1, "token": "T"}):
            res = self.client.post(reverse("console:gateway_test", args=[gw.pk]), follow=True)
        self.assertContains(res, "IP سرور درست است")

    def test_outbound_ip_is_looked_up_and_remembered(self):
        import io

        with mock.patch("urllib.request.urlopen", return_value=io.BytesIO(b'{"ip": "185.1.2.3"}')):
            res = self.client.post(reverse("console:gateway_outbound_ip"), follow=True)
        self.assertContains(res, "185.1.2.3", count=2)

