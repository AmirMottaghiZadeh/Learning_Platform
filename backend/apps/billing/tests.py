import io
import json
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from . import services
from . import config
from .gateways import GatewayError, SepGateway, ZibalGateway, ZarinpalGateway, start_payment
from .jalali import format_date, month_start, to_gregorian, to_jalali
from .models import DiscountCode, Entitlement, Feature, Order, PaymentGateway, Plan, PlanFeature, PlanPrice, UsageRecord

User = get_user_model()


def make_plan(slug, features, *, kind=Plan.KIND_PLAN, status=Plan.STATUS_ACTIVE):
    plan = Plan.objects.create(slug=slug, name_fa=slug, kind=kind, status=status)
    for key, limit, period in features:
        PlanFeature.objects.create(plan=plan, feature=Feature.objects.get(key=key), limit=limit, period=period)
    return plan


def narrow_free_plan(*keys):
    """Leave the seeded free plan with only these features."""
    free = Plan.objects.get(is_free=True)
    free.plan_features.exclude(feature__key__in=keys).delete()
    return free


class JalaliTests(TestCase):
    def test_known_dates(self):
        from datetime import date

        self.assertEqual(to_jalali(date(2026, 10, 14)), (1405, 7, 22))
        self.assertEqual(to_jalali(date(2025, 3, 21)), (1404, 1, 1))
        self.assertEqual(to_jalali(date(2021, 3, 20)), (1399, 12, 30))
        self.assertEqual(to_gregorian(1405, 7, 1), date(2026, 9, 23))
        self.assertEqual(month_start(date(2026, 10, 14)), date(2026, 9, 23))
        self.assertEqual(format_date(date(2026, 10, 14), with_month_name=True), "۲۲ مهر ۱۴۰۵")


class SeedTests(TestCase):
    def test_free_plan_holds_every_builtin_feature_uncapped(self):
        free = Plan.objects.get(is_free=True)
        rows = {pf.feature.key: pf.limit for pf in free.plan_features.select_related("feature")}
        self.assertEqual(set(rows), {"lessons", "uptodate", "lexicomp", "medscape", "calculators", "flashcards", "quiz", "stats"})
        self.assertTrue(all(limit is None for limit in rows.values()))


class AccessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="a@example.com", email="a@example.com", password="x")

    def test_free_plan_and_entitlements_merge_most_generous_wins(self):
        narrow_free_plan("uptodate")
        PlanFeature.objects.filter(plan__is_free=True, feature__key="uptodate").update(limit=3, period="day")
        clinical = make_plan("clinical", [("uptodate", 30, "month"), ("lexicomp", None, "day")])
        services.grant(self.user, clinical, days=30, source=Entitlement.SOURCE_ADMIN)

        have = services.effective_features(self.user)
        # 3/day is 90/month: more generous than 30/month.
        self.assertEqual(have["uptodate"]["limit"], 3)
        self.assertEqual(have["uptodate"]["period"], "day")
        self.assertIsNone(have["lexicomp"]["limit"])
        self.assertNotIn("quiz", have)

    def test_quota_counts_each_item_once_per_period(self):
        narrow_free_plan("uptodate")
        PlanFeature.objects.filter(plan__is_free=True, feature__key="uptodate").update(limit=2, period="day")

        self.assertTrue(services.check_feature(self.user, "uptodate", item="a", consume=True).allowed)
        self.assertTrue(services.check_feature(self.user, "uptodate", item="a", consume=True).allowed)
        self.assertTrue(services.check_feature(self.user, "uptodate", item="b", consume=True).allowed)
        denied = services.check_feature(self.user, "uptodate", item="c", consume=True)
        self.assertFalse(denied.allowed)
        self.assertEqual((denied.reason, denied.limit, denied.used), ("quota", 2, 2))
        # Items already opened today stay open; a call naming no item only
        # needs the feature.
        self.assertTrue(services.check_feature(self.user, "uptodate", item="a", consume=True).allowed)
        self.assertTrue(services.check_feature(self.user, "uptodate").allowed)
        self.assertEqual(UsageRecord.objects.filter(user=self.user).count(), 2)

    def test_feature_outside_every_plan_is_denied_and_inactive_feature_is_open(self):
        narrow_free_plan("lessons")
        self.assertEqual(services.check_feature(self.user, "quiz").reason, "not_in_plan")
        Feature.objects.filter(key="quiz").update(is_active=False)
        self.assertTrue(services.check_feature(self.user, "quiz").allowed)

    def test_entitlement_keeps_the_features_it_was_bought_with(self):
        plan = make_plan("student", [("quiz", 20, "day")])
        services.grant(self.user, plan, days=30, source=Entitlement.SOURCE_ADMIN)
        PlanFeature.objects.filter(plan=plan).update(limit=5)
        PlanFeature.objects.create(plan=plan, feature=Feature.objects.get(key="uptodate"))
        ent = Entitlement.objects.get(user=self.user)
        self.assertEqual(ent.features, {"quiz": {"limit": 20, "period": "day"}})

    def test_renewal_starts_when_the_current_one_ends(self):
        plan = make_plan("clinical", [("lexicomp", None, "day")])
        first = services.grant(self.user, plan, days=30, source=Entitlement.SOURCE_ADMIN)
        second = services.grant(self.user, plan, days=30, source=Entitlement.SOURCE_ADMIN)
        self.assertEqual(second.starts_at, first.ends_at)

    def test_revoked_and_expired_entitlements_give_nothing(self):
        narrow_free_plan()
        plan = make_plan("clinical", [("lexicomp", None, "day")])
        ent = services.grant(self.user, plan, days=30, source=Entitlement.SOURCE_ADMIN)
        self.assertIn("lexicomp", services.effective_features(self.user))
        services.revoke(ent)
        self.assertNotIn("lexicomp", services.effective_features(self.user))
        services.grant(self.user, plan, days=1, source=Entitlement.SOURCE_ADMIN)
        later = timezone.now() + timedelta(days=2)
        self.assertNotIn("lexicomp", services.effective_features(self.user, when=later))

    def test_content_feature_fences_its_scope(self):
        narrow_free_plan("lessons", "flashcards")
        Feature.objects.create(key="cardio-pack", name_fa="بسته قلب", kind=Feature.KIND_CONTENT,
                               scope_type="topic_category", scope_value="cardio-blood")
        Feature.objects.create(key="c09", name_fa="ACE", kind=Feature.KIND_CONTENT,
                               scope_type="atc_prefix", scope_value="C09")
        self.assertEqual([f.key for f in services.content_lock(self.user, "topic_category", "cardio-blood")], ["cardio-pack"])
        self.assertEqual(services.content_lock(self.user, "topic_category", "gi"), [])
        self.assertEqual([f.key for f in services.content_lock(self.user, "atc_prefix", "C09AA")], ["c09"])
        self.assertEqual(services.content_lock(self.user, "atc_prefix", "C08"), [])
        pack = make_plan("pack", [("cardio-pack", None, "day")], kind=Plan.KIND_PRODUCT)
        services.grant(self.user, pack, days=None, source=Entitlement.SOURCE_ADMIN)
        self.assertEqual(services.content_lock(self.user, "topic_category", "cardio-blood"), [])


class DiscountTests(TestCase):
    def setUp(self):
        self.plan = make_plan("clinical", [("lexicomp", None, "day")])
        self.price = PlanPrice.objects.create(plan=self.plan, duration_days=30, price_toman=200_000)

    def test_percent_and_fixed(self):
        pct = DiscountCode.objects.create(code="OFF25", percent=25)
        fixed = DiscountCode.objects.create(code="FIX", amount_toman=500_000)
        self.assertEqual(services.quote(self.price, pct), (200_000, 50_000, 150_000))
        self.assertEqual(services.quote(self.price, fixed), (200_000, 200_000, 0))

    def test_rejections(self):
        cases = {
            "DISCOUNT_INACTIVE": {"percent": 10, "is_active": False},
            "DISCOUNT_EXPIRED": {"percent": 10, "ends_at": timezone.now() - timedelta(hours=1)},
            "DISCOUNT_NOT_STARTED": {"percent": 10, "starts_at": timezone.now() + timedelta(hours=1)},
            "DISCOUNT_USED_UP": {"percent": 10, "max_uses": 2, "used_count": 2},
        }
        for i, (code, fields) in enumerate(cases.items()):
            d = DiscountCode.objects.create(code=f"C{i}", **fields)
            with self.assertRaises(services.BillingError) as ctx:
                services.quote(self.price, d)
            self.assertEqual(ctx.exception.code, code)
        other = make_plan("other", [])
        scoped = DiscountCode.objects.create(code="ONLY", percent=10)
        scoped.plans.add(other)
        with self.assertRaises(services.BillingError):
            services.quote(self.price, scoped)
        with self.assertRaises(services.BillingError):
            services.find_discount("nope")


@override_settings(BILLING_GATEWAY="fake", BILLING_RETURN_URL="https://app.example.com")
class PurchaseApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="b@example.com", email="b@example.com", password="x")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.plan = make_plan("clinical", [("lexicomp", None, "day"), ("uptodate", 30, "month")])
        self.price = PlanPrice.objects.create(plan=self.plan, duration_days=90, price_toman=300_000)

    def test_catalog_lists_plans_and_products_on_sale(self):
        make_plan("hidden", [], status=Plan.STATUS_HIDDEN)
        product = make_plan("exam-pack", [], kind=Plan.KIND_PRODUCT)
        PlanPrice.objects.create(plan=product, duration_days=None, price_toman=90_000)
        body = self.client.get("/api/v1/billing/catalog/").json()
        self.assertEqual([p["slug"] for p in body["plans"]], ["clinical"])
        self.assertEqual([p["slug"] for p in body["products"]], ["exam-pack"])
        self.assertEqual(body["products"][0]["prices"][0]["duration_label"], "دائمی")
        self.assertEqual(body["free"]["slug"], "free")
        uptodate = next(f for f in body["plans"][0]["features"] if f["key"] == "uptodate")
        self.assertEqual((uptodate["limit"], uptodate["period"]), (30, "month"))

    def test_checkout_then_callback_grants_once(self):
        res = self.client.post("/api/v1/billing/checkout/", {"price_id": self.price.pk}, format="json")
        self.assertEqual(res.status_code, 201)
        order = Order.objects.get(pk=res.json()["order_id"])
        self.assertEqual(order.status, Order.STATUS_PENDING)
        self.assertIn("/api/v1/billing/callback/fake/?Authority=FAKE-", res.json()["payment_url"])

        callback = f"/api/v1/billing/callback/fake/?Authority={order.authority}&Status=OK"
        back = self.client.get(callback)
        self.assertEqual(back.status_code, 302)
        self.assertIn("/api/v1/billing/result/", back["Location"])
        page = self.client.get(back["Location"])
        self.assertContains(page, "پرداخت موفق بود")
        self.assertContains(page, "https://app.example.com")
        self.assertContains(page, f"FAKE{order.pk}")
        self.client.get(callback)  # a retried callback
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PAID)
        ent = Entitlement.objects.get(user=self.user)
        self.assertEqual(ent.order, order)
        self.assertEqual((ent.ends_at - ent.starts_at).days, 90)

        me = self.client.get("/api/v1/billing/me/").json()
        self.assertEqual(me["entitlements"][0]["plan_name_fa"], "clinical")
        self.assertIn("lexicomp", [f["key"] for f in me["features"]])

    def test_cancelled_payment_grants_nothing(self):
        res = self.client.post("/api/v1/billing/checkout/", {"price_id": self.price.pk}, format="json")
        order = Order.objects.get(pk=res.json()["order_id"])
        page = self.client.get(f"/api/v1/billing/callback/fake/?Authority={order.authority}&Status=NOK", follow=True)
        self.assertContains(page, "پرداخت انجام نشد")
        self.assertContains(page, "لغو شد")
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_FAILED)
        self.assertFalse(Entitlement.objects.exists())

    def test_the_callback_from_before_per_gateway_paths_still_works(self):
        res = self.client.post("/api/v1/billing/checkout/", {"price_id": self.price.pk}, format="json")
        order = Order.objects.get(pk=res.json()["order_id"])
        page = self.client.get(f"/api/v1/billing/callback/?Authority={order.authority}&Status=OK", follow=True)
        self.assertContains(page, "پرداخت موفق بود")

    def test_a_result_link_cannot_be_forged(self):
        res = self.client.post("/api/v1/billing/checkout/", {"price_id": self.price.pk}, format="json")
        self.assertEqual(self.client.get(f"/api/v1/billing/result/{res.json()['order_id']}/").status_code, 404)

    def test_a_payment_whose_verify_did_not_answer_is_shown_as_unknown(self):
        res = self.client.post("/api/v1/billing/checkout/", {"price_id": self.price.pk}, format="json")
        order = Order.objects.get(pk=res.json()["order_id"])
        with mock.patch("apps.billing.gateways.FakeGateway.verify", side_effect=GatewayError("down")):
            page = self.client.get(f"/api/v1/billing/callback/fake/?Authority={order.authority}&Status=OK", follow=True)
        self.assertContains(page, "وضعیت پرداخت هنوز روشن نیست")
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PENDING)

    def test_full_discount_skips_the_gateway_and_counts_the_use(self):
        code = DiscountCode.objects.create(code="GIFT", percent=100, max_uses=1)
        res = self.client.post("/api/v1/billing/checkout/", {"price_id": self.price.pk, "discount_code": "gift"}, format="json")
        self.assertEqual(res.json()["status"], "paid")
        code.refresh_from_db()
        self.assertEqual(code.used_count, 1)
        again = self.client.post("/api/v1/billing/checkout/", {"price_id": self.price.pk, "discount_code": "GIFT"}, format="json")
        self.assertEqual(again.status_code, 400)
        self.assertEqual(again.json()["code"], "DISCOUNT_USED_UP")

    def test_quote_and_unavailable_price(self):
        DiscountCode.objects.create(code="TEN", percent=10)
        res = self.client.post("/api/v1/billing/quote/", {"price_id": self.price.pk, "discount_code": "TEN"}, format="json")
        self.assertEqual(res.json(), {"amount_toman": 300_000, "discount_toman": 30_000, "payable_toman": 270_000})
        self.plan.status = Plan.STATUS_HIDDEN
        self.plan.save()
        res = self.client.post("/api/v1/billing/quote/", {"price_id": self.price.pk}, format="json")
        self.assertEqual(res.json()["code"], "PRICE_NOT_AVAILABLE")

    def test_unknown_authority_and_gateway(self):
        self.assertEqual(self.client.get("/api/v1/billing/callback/?Authority=nope&Status=OK").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/billing/callback/fake/?Authority=nope&Status=OK").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/billing/callback/paypal/").status_code, 404)


def _fake_urlopen(responses):
    calls = []

    def urlopen(request, timeout):
        calls.append((request.full_url, json.loads(request.data)))
        return io.BytesIO(json.dumps(responses.pop(0)).encode())

    return urlopen, calls


@override_settings(ZARINPAL_MERCHANT_ID="m-123", ZARINPAL_SANDBOX=True)
class ZarinpalTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="z@example.com", password="x")
        plan = make_plan("p", [])
        self.order = Order.objects.create(user=user, plan=plan, amount_toman=150_000, payable_toman=150_000, authority="A00012")

    def test_start_sends_rials_and_returns_the_pay_url(self):
        urlopen, calls = _fake_urlopen([{"data": {"code": 100, "authority": "A00012"}, "errors": []}])
        with mock.patch("urllib.request.urlopen", urlopen):
            url, authority = ZarinpalGateway().start(self.order, "https://api/cb", description="خرید")
        self.assertEqual(authority, "A00012")
        self.assertEqual(url, "https://sandbox.zarinpal.com/pg/StartPay/A00012")
        self.assertEqual(calls[0][1]["amount"], 1_500_000)
        self.assertEqual(calls[0][1]["merchant_id"], "m-123")

    def test_verify_accepts_100_and_101_only(self):
        for code, ok in ((100, True), (101, True), (-51, False)):
            urlopen, _ = _fake_urlopen([{"data": {"code": code, "ref_id": 777, "card_pan": "6037**1234"}, "errors": []}])
            with mock.patch("urllib.request.urlopen", urlopen):
                result = ZarinpalGateway().verify(self.order, {"Status": "OK"})
            self.assertEqual(result.ok, ok)
        self.assertFalse(ZarinpalGateway().verify(self.order, {"Status": "NOK"}).ok)

    def test_refused_request_raises(self):
        urlopen, _ = _fake_urlopen([{"data": [], "errors": {"code": -9, "message": "validation"}}])
        with mock.patch("urllib.request.urlopen", urlopen), self.assertRaises(GatewayError):
            ZarinpalGateway().start(self.order, "https://api/cb", description="x")


@override_settings(ZIBAL_MERCHANT="merchant-1")
class ZibalTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="zb@example.com", password="x")
        plan = make_plan("zibal-plan", [])
        self.order = Order.objects.create(
            user=user, plan=plan, amount_toman=150_000, payable_toman=150_000,
            gateway="zibal", authority="987654",
        )

    def test_start_sends_rials_and_returns_the_pay_url(self):
        urlopen, calls = _fake_urlopen([{"result": 100, "trackId": 987654, "message": "موفق"}])
        with mock.patch("urllib.request.urlopen", urlopen):
            url, track_id = ZibalGateway().start(self.order, "https://api/cb", description="خرید", mobile="09120000000")
        self.assertEqual((track_id, url), ("987654", "https://gateway.zibal.ir/start/987654"))
        self.assertEqual(calls[0][1], {
            "merchant": "merchant-1", "amount": 1_500_000, "callbackUrl": "https://api/cb",
            "orderId": str(self.order.pk), "description": "خرید", "mobile": "09120000000",
        })

    def test_verify_checks_callback_and_amount(self):
        urlopen, calls = _fake_urlopen([{
            "result": "100", "trackId": 987654, "amount": 1_500_000,
            "cardNumber": "6037****1234", "refNumber": "REF-1",
        }])
        with mock.patch("urllib.request.urlopen", urlopen):
            result = ZibalGateway().verify(self.order, {"trackId": "987654", "success": "1"})
        self.assertTrue(result.ok)
        self.assertEqual((result.ref_id, result.card_pan, result.gateway_ref), ("REF-1", "6037****1234", "987654"))
        self.assertEqual(calls[0][1], {"merchant": "merchant-1", "trackId": "987654"})
        self.assertFalse(ZibalGateway().verify(self.order, {"trackId": "987654", "success": "0"}).ok)

    def test_verify_rejects_an_amount_mismatch(self):
        urlopen, _ = _fake_urlopen([{"result": 100, "trackId": 987654, "amount": 100}])
        with mock.patch("urllib.request.urlopen", urlopen):
            result = ZibalGateway().verify(self.order, {"trackId": "987654", "success": "1"})
        self.assertFalse(result.ok)
        self.assertIn("مبلغ", result.message)


class SepTests(TestCase):
    def setUp(self):
        config.clear_cache()
        self.addCleanup(config.clear_cache)
        PaymentGateway.objects.create(kind="sep", merchant_id="21009876")
        user = User.objects.create_user(username="s@example.com", password="x")
        plan = make_plan("p", [])
        self.order = Order.objects.create(
            user=user, plan=plan, amount_toman=150_000, payable_toman=150_000, gateway="sep", authority="TOKEN-1",
        )
        self.back = {"State": "OK", "Status": "2", "RefNum": "REF-9", "ResNum": str(self.order.pk), "Token": "TOKEN-1"}

    @staticmethod
    def verified(amount=1_500_000, code=0, success=True):
        return {
            "TransactionDetail": {"RRN": "14000123", "RefNum": "REF-9", "MaskedPan": "621986****8080", "OrginalAmount": amount, "AffectiveAmount": amount},
            "ResultCode": code, "ResultDescription": "", "Success": success,
        }

    def test_start_asks_for_a_token_in_rials_and_sends_the_buyer_to_sep(self):
        urlopen, calls = _fake_urlopen([{"status": 1, "token": "TOKEN-1"}])
        with mock.patch("urllib.request.urlopen", urlopen):
            url, token = SepGateway().start(self.order, "https://pharmenta.ir/pay/callback/sep/", description="خرید", mobile="09120000000")
        self.assertEqual(token, "TOKEN-1")
        self.assertEqual(url, "https://sep.shaparak.ir/OnlinePG/SendToken?token=TOKEN-1")
        sent = calls[0][1]
        self.assertEqual((sent["TerminalId"], sent["Amount"], sent["ResNum"]), ("21009876", 1_500_000, str(self.order.pk)))
        self.assertEqual(sent["RedirectUrl"], "https://pharmenta.ir/pay/callback/sep/")

    def test_a_refused_token_raises(self):
        urlopen, _ = _fake_urlopen([{"status": -1, "errorCode": "5", "errorDesc": "invalid terminal"}])
        with mock.patch("urllib.request.urlopen", urlopen), self.assertRaises(GatewayError):
            SepGateway().start(self.order, "https://x/cb", description="x")

    def test_the_order_is_found_only_with_its_own_token(self):
        orders = Order.objects.all()
        self.assertEqual(SepGateway.find_order(orders, self.back), self.order)
        self.assertIsNone(SepGateway.find_order(orders, {**self.back, "Token": "OTHER"}))
        self.assertIsNone(SepGateway.find_order(orders, {**self.back, "ResNum": "abc"}))

    def test_verify_checks_result_and_amount(self):
        urlopen, calls = _fake_urlopen([self.verified()])
        with mock.patch("urllib.request.urlopen", urlopen):
            result = SepGateway().verify(self.order, self.back)
        self.assertTrue(result.ok)
        self.assertEqual((result.ref_id, result.card_pan, result.gateway_ref), ("14000123", "621986****8080", "REF-9"))
        self.assertEqual(calls[0][1], {"RefNum": "REF-9", "TerminalNumber": 21009876})

    def test_a_short_payment_is_reversed(self):
        urlopen, calls = _fake_urlopen([self.verified(amount=10_000), {"ResultCode": 0, "Success": True}])
        with mock.patch("urllib.request.urlopen", urlopen):
            result = SepGateway().verify(self.order, self.back)
        self.assertFalse(result.ok)
        self.assertIn("برگشت داده شد", result.message)
        self.assertIn("ReverseTransaction", calls[1][0])

    def test_rejections_explain_themselves(self):
        urlopen, _ = _fake_urlopen([{"ResultCode": -106, "ResultDescription": "ip", "Success": False}])
        with mock.patch("urllib.request.urlopen", urlopen):
            self.assertIn("IP سرور", SepGateway().verify(self.order, self.back).message)
        cancelled = SepGateway().verify(self.order, {**self.back, "State": "CanceledByUser", "Status": "1"})
        self.assertEqual((cancelled.ok, cancelled.message), (False, "پرداخت را لغو کردید."))

    def test_a_receipt_settles_one_order_only(self):
        Order.objects.create(
            user=self.order.user, plan=self.order.plan, amount_toman=1, payable_toman=1, gateway="sep",
            authority="TOKEN-0", status=Order.STATUS_PAID, gateway_ref="REF-9",
        )
        self.assertIn("سفارش دیگری", SepGateway().verify(self.order, self.back).message)

    def test_sep_posts_back_and_the_order_is_paid(self):
        urlopen, _ = _fake_urlopen([self.verified()])
        with mock.patch("urllib.request.urlopen", urlopen):
            back = self.client.post("/api/v1/billing/callback/sep/", self.back)
        self.assertEqual(back.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual((self.order.status, self.order.ref_id, self.order.gateway_ref), (Order.STATUS_PAID, "14000123", "REF-9"))
        self.assertContains(self.client.get(back["Location"]), "14000123")


class GatewayChoiceTests(TestCase):
    def setUp(self):
        config.clear_cache()
        self.addCleanup(config.clear_cache)
        user = User.objects.create_user(username="c@example.com", password="x")
        self.order = Order.objects.create(user=user, plan=make_plan("p", []), amount_toman=1000, payable_toman=1000)

    def start(self, **kw):
        return start_payment(self.order, lambda kind: f"https://pharmenta.ir/pay/callback/{kind}/", description="x", **kw)

    def test_the_next_gateway_takes_over_when_the_first_refuses(self):
        PaymentGateway.objects.create(kind="sep", merchant_id="21009876", priority=1)
        PaymentGateway.objects.create(kind="zarinpal", merchant_id="m" * 36, priority=2)
        urlopen, calls = _fake_urlopen([{"status": -1, "errorCode": "-106"}, {"data": {"code": 100, "authority": "A9"}, "errors": []}])
        with mock.patch("urllib.request.urlopen", urlopen):
            url = self.start()
        self.assertIn("zarinpal.com/pg/StartPay/A9", url)
        self.order.refresh_from_db()
        self.assertEqual((self.order.gateway, self.order.authority), ("zarinpal", "A9"))
        self.assertIn("/pay/callback/zarinpal/", calls[1][1]["callback_url"])

    def test_disabled_gateways_are_skipped_and_a_chosen_one_is_used_alone(self):
        PaymentGateway.objects.create(kind="sep", merchant_id="21009876", priority=1, is_enabled=False)
        PaymentGateway.objects.create(kind="zarinpal", merchant_id="m" * 36, priority=2)
        self.assertEqual([g.kind for g in config.enabled_gateways()], ["zarinpal"])
        urlopen, _ = _fake_urlopen([{"status": -1}])
        with mock.patch("urllib.request.urlopen", urlopen), self.assertRaises(GatewayError):
            self.start(kind="sep")

    def test_with_no_gateway_set_up_the_environment_applies(self):
        with self.settings(BILLING_GATEWAY="zarinpal", ZARINPAL_MERCHANT_ID="env-m", ZARINPAL_SANDBOX=False):
            config.clear_cache()
            (spec,) = config.current().gateways
            self.assertEqual((spec.kind, spec.merchant_id, spec.source), ("zarinpal", "env-m", "env"))


@override_settings(BILLING_ENFORCEMENT_ENABLED=True)
class EnforcementTests(TestCase):
    def test_console_switch_overrides_the_environment(self):
        from . import config
        from .models import BillingSettings

        narrow_free_plan("lessons")
        BillingSettings.objects.create(enforcement_enabled=False)
        try:
            self.assertEqual(self.client.get("/api/v1/me/statistics/").status_code, 200)
        finally:
            config.clear_cache()

    def setUp(self):
        self.user = User.objects.create_user(username="c@example.com", email="c@example.com", password="x")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_feature_outside_the_plan_answers_402(self):
        narrow_free_plan("lessons")
        res = self.client.get("/api/v1/me/statistics/")
        self.assertEqual(res.status_code, 402)
        self.assertEqual(res.json()["code"], "PREMIUM_REQUIRED")

    def test_staff_are_never_locked(self):
        narrow_free_plan()
        self.user.is_staff = True
        self.user.save()
        self.assertEqual(self.client.get("/api/v1/me/statistics/").status_code, 200)

    @override_settings(BILLING_ENFORCEMENT_ENABLED=False)
    def test_switched_off_changes_nothing(self):
        narrow_free_plan()
        self.assertEqual(self.client.get("/api/v1/me/statistics/").status_code, 200)

    def test_quota_on_calculators(self):
        from apps.calculators.models import Calculator

        narrow_free_plan("calculators")
        PlanFeature.objects.filter(plan__is_free=True).update(limit=1, period="day")
        for i in range(2):
            Calculator.objects.create(uid=f"u{i}", calculator_id=str(i), slug=f"calc-{i}", name=f"Calc {i}")
        self.assertEqual(self.client.get("/api/v1/calculators/calc-0/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/calculators/calc-0/").status_code, 200)
        res = self.client.get("/api/v1/calculators/calc-1/")
        self.assertEqual(res.status_code, 402)
        self.assertEqual(res.json()["code"], "QUOTA_EXCEEDED")
