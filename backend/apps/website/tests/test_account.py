from unittest import mock

from django.contrib.auth import get_user_model
from django.test import override_settings

from apps.accounts.models import LearnerProfile
from apps.billing import config as billing_config
from apps.billing.models import DiscountCode, Entitlement, Order, Plan, PlanPrice

from .base import SiteTestCase

HOST = {"HTTP_HOST": "site.localhost"}
User = get_user_model()


@override_settings(BILLING_GATEWAY="fake")
class PurchaseFlowTests(SiteTestCase):
    def setUp(self):
        super().setUp()
        billing_config._cached.update(loaded=False)
        self.plan = Plan.objects.create(slug="pro", name_fa="حرفه‌ای", kind="plan", status="active")
        self.price = PlanPrice.objects.create(plan=self.plan, duration_days=30, price_toman=200000)

    def sign_in(self, phone="09121112233"):
        with mock.patch("apps.accounts.otp._new_code", return_value="12345"):
            res = self.client.post("/account/login/", {"phone": phone, "next": f"/checkout/{self.price.pk}/"}, **HOST)
            self.assertEqual(res.status_code, 302)
            res = self.client.post("/account/code/", {"code": "12345"}, **HOST)
        return res

    def test_pricing_page_shows_plan_and_buy_link(self):
        res = self.client.get("/plans/", **HOST)
        self.assertContains(res, "حرفه‌ای")
        self.assertContains(res, f"/checkout/{self.price.pk}/")

    def test_checkout_requires_login(self):
        res = self.client.get(f"/checkout/{self.price.pk}/", **HOST)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/account/login/", res["Location"])

    def test_sms_login_creates_account_and_returns_to_checkout(self):
        res = self.sign_in()
        self.assertEqual(res["Location"], f"/checkout/{self.price.pk}/")
        profile = LearnerProfile.objects.get(phone="09121112233")
        self.assertTrue(profile.user.is_active)
        self.assertEqual(self.client.get("/account/", **HOST).status_code, 200)

    def test_wrong_code_is_refused(self):
        with mock.patch("apps.accounts.otp._new_code", return_value="12345"):
            self.client.post("/account/login/", {"phone": "09121112233"}, **HOST)
        self.client.post("/account/code/", {"code": "00000"}, **HOST)
        self.assertEqual(self.client.get("/account/", **HOST).status_code, 302)

    def test_bad_phone_refused(self):
        res = self.client.post("/account/login/", {"phone": "123"}, **HOST, follow=True)
        self.assertContains(res, "شمارهٔ موبایل معتبر نیست")

    def test_password_login(self):
        user = User.objects.create_user(username="09125556677", password="s3cret-pass")
        LearnerProfile.objects.create(user=user, phone="09125556677")
        res = self.client.post("/account/login/", {"phone": "09125556677", "password": "s3cret-pass"}, **HOST)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.client.get("/account/", **HOST).status_code, 200)

    def test_full_purchase_with_fake_gateway(self):
        self.sign_in()
        res = self.client.get(f"/checkout/{self.price.pk}/", **HOST)
        self.assertContains(res, "قابل پرداخت")
        res = self.client.post(f"/checkout/{self.price.pk}/", {"action": "pay"}, **HOST)
        self.assertEqual(res.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.status, Order.STATUS_PENDING)
        self.assertEqual(order.payable_toman, 200000)
        self.assertIn("/pay/callback/fake/", res["Location"])
        # the gateway sends the buyer back to the callback, which moves on to the result page
        back = self.client.get(res["Location"].split("localhost")[-1], **HOST)
        self.assertEqual(back.status_code, 302)
        self.assertIn("/pay/result/", back["Location"])
        page = self.client.get(back["Location"], **HOST)
        self.assertContains(page, "پرداخت موفق بود")
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PAID)
        self.assertTrue(Entitlement.objects.filter(user=order.user, plan=self.plan).exists())
        self.assertContains(self.client.get("/account/", **HOST), "حرفه‌ای")

    def test_a_failed_payment_offers_to_try_again(self):
        self.sign_in()
        res = self.client.post(f"/checkout/{self.price.pk}/", {"action": "pay"}, **HOST)
        order = Order.objects.get()
        page = self.client.get(f"/pay/callback/fake/?Authority={order.authority}&Status=NOK", **HOST, follow=True)
        self.assertContains(page, "پرداخت انجام نشد")
        self.assertContains(page, f"/checkout/{self.price.pk}/")
        self.assertContains(page, 'href="/contact/"')

    def test_the_buyer_picks_a_gateway_when_there_are_several(self):
        from apps.billing.models import PaymentGateway

        PaymentGateway.objects.create(kind="zarinpal", merchant_id="m" * 36, priority=1)
        PaymentGateway.objects.create(kind="sep", merchant_id="21009876", priority=2, title="بانک سامان")
        billing_config.clear_cache()
        self.addCleanup(billing_config.clear_cache)
        self.sign_in()
        page = self.client.get(f"/checkout/{self.price.pk}/", **HOST)
        self.assertContains(page, 'name="gateway" value="sep"')
        self.assertContains(page, "بانک سامان")
        with mock.patch("apps.billing.gateways.SepGateway.start", return_value=("https://sep.shaparak.ir/OnlinePG/SendToken?token=T1", "T1")) as start:
            res = self.client.post(f"/checkout/{self.price.pk}/", {"action": "pay", "gateway": "sep"}, **HOST)
        self.assertEqual(res["Location"], "https://sep.shaparak.ir/OnlinePG/SendToken?token=T1")
        self.assertIn("/pay/callback/sep/", start.call_args.args[1])
        self.assertEqual((Order.objects.get().gateway, Order.objects.get().authority), ("sep", "T1"))

    def test_discount_code_is_applied(self):
        DiscountCode.objects.create(code="OFF50", percent=50)
        self.sign_in()
        res = self.client.post(f"/checkout/{self.price.pk}/", {"action": "quote", "discount_code": "off50"}, **HOST)
        self.assertContains(res, "۱۰۰٬۰۰۰")
        self.client.post(f"/checkout/{self.price.pk}/", {"action": "pay", "discount_code": "OFF50"}, **HOST)
        self.assertEqual(Order.objects.get().payable_toman, 100000)

    def test_bad_discount_code_blocks_payment(self):
        self.sign_in()
        res = self.client.post(f"/checkout/{self.price.pk}/", {"action": "pay", "discount_code": "NOPE"}, **HOST)
        self.assertContains(res, "این کد تخفیف وجود ندارد")
        self.assertEqual(Order.objects.count(), 0)

    def test_inactive_price_cannot_be_bought(self):
        self.price.is_active = False
        self.price.save()
        self.sign_in()
        res = self.client.get(f"/checkout/{self.price.pk}/", **HOST)
        self.assertEqual(res.status_code, 302)

    def test_next_cannot_leave_the_site(self):
        with mock.patch("apps.accounts.otp._new_code", return_value="12345"):
            self.client.post("/account/login/", {"phone": "09121112233", "next": "https://evil.example/"}, **HOST)
            res = self.client.post("/account/code/", {"code": "12345"}, **HOST)
        self.assertEqual(res["Location"], "/account/")

    def test_logout(self):
        self.sign_in()
        self.client.post("/account/logout/", **HOST)
        self.assertEqual(self.client.get("/account/", **HOST).status_code, 302)
