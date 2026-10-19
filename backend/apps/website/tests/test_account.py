from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone

from apps.accounts.models import LearnerProfile, OneTimeCode, UserSession
from apps.accounts.services import issue_user_session
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
            res = self.client.post("/account/login/", {"mode": "signup", "phone": phone, "next": f"/checkout/{self.price.pk}/"}, **HOST)
            self.assertEqual(res.status_code, 302)
            res = self.client.post("/account/code/", {"code": "12345"}, **HOST)
            self.assertEqual(res["Location"], "/account/password/")
            res = self.client.post("/account/password/", {
                "name": "سارا احمدی", "new_password": "Kavir7pass", "new_password_confirm": "Kavir7pass",
            }, **HOST)
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
            self.client.post("/account/login/", {"mode": "signup", "phone": "09121112233"}, **HOST)
        self.client.post("/account/code/", {"code": "00000"}, **HOST)
        self.assertEqual(self.client.get("/account/", **HOST).status_code, 302)

    def test_bad_phone_refused(self):
        res = self.client.post("/account/login/", {"mode": "signup", "phone": "123"}, **HOST, follow=True)
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

    def test_checkout_shows_zibal_and_redirects_with_referrer_policy(self):
        from apps.billing.models import PaymentGateway

        PaymentGateway.objects.create(kind="zibal", merchant_id="merchant-1", priority=1)
        billing_config.clear_cache()
        self.addCleanup(billing_config.clear_cache)
        self.sign_in()
        page = self.client.get(f"/checkout/{self.price.pk}/", **HOST)
        self.assertContains(page, 'name="gateway" value="zibal"')
        self.assertContains(page, "zibal-trust-v4.js")
        with mock.patch(
            "apps.billing.gateways.ZibalGateway.start",
            return_value=("https://gateway.zibal.ir/start/123", "123"),
        ) as start:
            res = self.client.post(f"/checkout/{self.price.pk}/", {"action": "pay", "gateway": "zibal"}, **HOST)
        self.assertEqual(res["Location"], "https://gateway.zibal.ir/start/123")
        self.assertEqual(res["Referrer-Policy"], "origin")
        self.assertIn("/pay/callback/zibal/", start.call_args.args[1])
        self.assertEqual((Order.objects.get().gateway, Order.objects.get().authority), ("zibal", "123"))

    def test_checkout_does_not_create_an_order_without_an_active_gateway(self):
        from apps.billing.models import PaymentGateway

        PaymentGateway.objects.create(kind="zibal", merchant_id="merchant-1", is_enabled=False)
        billing_config.clear_cache()
        self.addCleanup(billing_config.clear_cache)
        self.sign_in()
        res = self.client.post(f"/checkout/{self.price.pk}/", {"action": "pay"}, **HOST, follow=True)
        self.assertContains(res, "هیچ درگاه پرداخت فعالی")
        self.assertFalse(Order.objects.exists())

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
            self.client.post("/account/login/", {"mode": "signup", "phone": "09121112233", "next": "https://evil.example/"}, **HOST)
            self.client.post("/account/code/", {"code": "12345"}, **HOST)
        res = self.client.post("/account/password/", {
            "name": "سارا احمدی", "new_password": "Kavir7pass", "new_password_confirm": "Kavir7pass",
        }, **HOST)
        self.assertEqual(res["Location"], "/account/")

    def test_logout(self):
        self.sign_in()
        self.client.post("/account/logout/", **HOST)
        self.assertEqual(self.client.get("/account/", **HOST).status_code, 302)


@override_settings(SMS_BACKEND="console")
class WebsiteAuthTests(SiteTestCase):
    phone = "09121112233"
    password = "Kavir7pass"

    def request_code(self, mode="signup", phone=None, target="/account/"):
        with mock.patch("apps.accounts.otp._new_code", return_value="12345"):
            return self.client.post("/account/login/", {
                "mode": mode, "phone": phone or self.phone, "next": target,
            }, **HOST)

    def verify_code(self):
        return self.client.post("/account/code/", {"code": "۱۲۳۴۵"}, **HOST)

    def save_password(self, **overrides):
        data = {"name": "سارا  احمدی", "new_password": self.password, "new_password_confirm": self.password}
        data.update(overrides)
        return self.client.post("/account/password/", data, **HOST)

    def existing_user(self):
        user = User.objects.create_user(username="sara", email="sara@example.com", password="Old-pass8")
        LearnerProfile.objects.create(user=user, phone=self.phone)
        return user

    def test_header_and_login_offer_both_flows(self):
        self.assertContains(self.client.get("/", **HOST), "ثبت‌نام / ورود")
        page = self.client.get("/account/login/", **HOST)
        self.assertContains(page, 'name="password"')
        self.assertContains(page, "mode=signup")
        self.assertContains(page, "mode=reset")
        self.assertIn("no-store", page["Cache-Control"])
        signup = self.client.get("/account/login/?mode=signup", **HOST)
        self.assertNotContains(signup, 'name="password"')
        self.assertContains(signup, "ارسال کد تأیید")

    def test_signup_requires_verified_phone_then_name_and_valid_password(self):
        self.assertEqual(self.request_code(phone="۰۹۱۲۱۱۱۲۲۳۳")["Location"], "/account/code/")
        self.assertFalse(LearnerProfile.objects.filter(phone=self.phone).exists())
        self.assertEqual(self.verify_code()["Location"], "/account/password/")
        user = LearnerProfile.objects.get(phone=self.phone).user
        self.assertFalse(user.has_usable_password())
        self.assertNotIn("_auth_user_id", self.client.session)
        for invalid in ({"name": ""}, {"new_password_confirm": "Other-pass8"}, {"new_password": "123", "new_password_confirm": "123"}):
            with self.subTest(invalid=invalid):
                page = self.save_password(**invalid)
                self.assertEqual(page.status_code, 200)
                self.assertTrue(page.context["form"].errors)
                self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.save_password()["Location"], "/account/")
        user.refresh_from_db()
        self.assertTrue(user.check_password(self.password))
        self.assertEqual((user.first_name, user.last_name), ("سارا", "احمدی"))
        self.assertEqual(user.learner_profile.display_name, "سارا احمدی")
        self.assertNotIn("site_password", self.client.session)
        self.assertEqual(self.client.get("/account/", **HOST).status_code, 200)

    def test_new_site_account_can_log_in_to_app(self):
        self.request_code()
        self.verify_code()
        self.save_password()
        response = self.client.post("/api/v1/auth/login/", {
            "username": self.phone, "password": self.password,
        }, HTTP_HOST="testserver")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["id"], LearnerProfile.objects.get(phone=self.phone).user_id)

    def test_existing_app_account_logs_in_by_phone_or_email_without_sms(self):
        user = self.existing_user()
        for identifier in ("+989121112233", "sara@example.com"):
            with self.subTest(identifier=identifier):
                response = self.client.post("/account/login/", {
                    "phone": identifier, "password": "Old-pass8", "next": "/plans/?duration=30&offer=yes",
                }, **HOST)
                self.assertEqual(response["Location"], "/plans/?duration=30&offer=yes")
                self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
                self.client.logout()
        self.assertFalse(OneTimeCode.objects.exists())

    def test_wrong_or_missing_password_does_not_send_sms(self):
        self.existing_user()
        for password in ("incorrect", ""):
            response = self.client.post("/account/login/", {"phone": self.phone, "password": password}, **HOST)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
            self.assertNotIn("_auth_user_id", self.client.session)
        self.assertFalse(OneTimeCode.objects.exists())

    def test_registered_signup_and_unregistered_reset_are_refused(self):
        self.existing_user()
        response = self.request_code()
        self.assertContains(response, "این شماره قبلاً ثبت‌نام کرده")
        response = self.request_code(mode="reset", phone="09124445566")
        self.assertContains(response, "حسابی با این شماره پیدا نشد")
        self.assertFalse(OneTimeCode.objects.exists())

    def test_reset_requires_code_and_revokes_app_sessions(self):
        user = self.existing_user()
        session = issue_user_session(user).session
        self.request_code(mode="reset", target="/plans/")
        self.assertEqual(OneTimeCode.objects.get().purpose, OneTimeCode.RESET)
        self.verify_code()
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotContains(self.client.get("/account/password/", **HOST), 'name="name"')
        self.assertEqual(self.save_password(name="")["Location"], "/plans/")
        user.refresh_from_db()
        self.assertTrue(user.check_password(self.password))
        self.assertFalse(user.check_password("Old-pass8"))
        self.assertTrue(UserSession.objects.filter(pk=session.pk, revoked_at__isnull=False).exists())

    def test_password_cannot_be_changed_without_recent_sms_proof(self):
        user = self.existing_user()
        self.assertEqual(self.save_password()["Location"], "/account/login/")
        self.request_code(mode="reset")
        self.verify_code()
        session = self.client.session
        pending = session["site_password"]
        pending["verified_at"] = (timezone.now() - timedelta(hours=1)).timestamp()
        session["site_password"] = pending
        session.save()
        self.assertEqual(self.save_password().status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.check_password("Old-pass8"))
        self.assertNotIn("site_password", self.client.session)

    def test_wrong_and_expired_codes_do_not_grant_password_access(self):
        self.request_code()
        self.assertEqual(self.client.post("/account/code/", {"code": "00000"}, **HOST).status_code, 200)
        self.assertNotIn("site_password", self.client.session)
        OneTimeCode.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertContains(self.verify_code(), "کد منقضی شده")
        self.assertFalse(LearnerProfile.objects.filter(phone=self.phone).exists())

    def test_resend_cooldown_and_existing_code_are_preserved(self):
        self.request_code(target="/plans/?duration=30&offer=yes")
        self.assertEqual(self.request_code(target="/plans/?duration=30&offer=yes")["Location"], "/account/code/")
        response = self.client.post("/account/code/", {"action": "resend"}, **HOST, follow=True)
        self.assertContains(response, "کمی صبر کن")
        self.assertEqual(OneTimeCode.objects.count(), 1)
        OneTimeCode.objects.update(created_at=timezone.now() - timedelta(minutes=2))
        with mock.patch("apps.accounts.otp._new_code", return_value="54321"):
            response = self.client.post("/account/code/", {"action": "resend"}, **HOST)
        self.assertEqual(response["Location"], "/account/code/")
        self.assertContains(self.verify_code(), "کد درست نیست")
        self.client.post("/account/code/", {"code": "54321"}, **HOST)
        self.assertEqual(self.save_password()["Location"], "/plans/?duration=30&offer=yes")

    def test_signup_rejects_external_redirects_even_after_verification(self):
        self.request_code(target="https://evil.example/")
        self.verify_code()
        session = self.client.session
        pending = session["site_password"]
        pending["next"] = "//evil.example/"
        session["site_password"] = pending
        session.save()
        self.assertEqual(self.save_password()["Location"], "/account/")
