from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.ai_lab import telemetry
from apps.ai_lab.models import SearchRun
from apps.ai_lab.provider import ProviderError
from apps.billing.gateways import FakeGateway
from apps.billing.models import BillingSettings, Entitlement, Order
from apps.billing.services import mark_paid
from apps.core.exceptions import PlatformAPIError
from . import services, fx
from .models import CreditAttempt, CreditEntry, CreditPackage, CreditReservation, CreditSettings


TEST_CACHES = {key:{"BACKEND":"django.core.cache.backends.locmem.LocMemCache","LOCATION":"credit-tests-"+key}
               for key in ["default","throttle","ai_lab"]}


@override_settings(CACHES=TEST_CACHES, AI_LAB_ENABLED=True, AI_LAB_SEARCH_ENGINE="hybrid",
    AI_LAB_MODEL="fixture-model", AI_LAB_BASE_URL="https://fixture.invalid/v1", BILLING_GATEWAY="fake",
    ENVIRONMENT="local", SITE_HOSTS=[], SITE_PUBLIC_URL="http://testserver", BILLING_SALES_ENABLED=True)
class WalletTests(TestCase):
    def setUp(self):
        from django.core.cache import caches
        for key in TEST_CACHES:caches[key].clear()
        self.alice=get_user_model().objects.create_user("credit-alice")
        self.bob=get_user_model().objects.create_user("credit-bob")
        self.admin=get_user_model().objects.create_user("credit-admin",is_staff=True,is_superuser=True)
        setting=self.settings(AI_LAB_USER_IDS={str(self.alice.pk),str(self.bob.pk)})
        setting.enable();self.addCleanup(setting.disable)
        self.config,_=CreditSettings.objects.update_or_create(pk=1,defaults=dict(enabled=True,initial_credits=100,
            input_per_million=1000000,cached_input_per_million=500000,output_per_million=2000000,
            embedding_per_million=500000,model_signature=services.model_signature(),fx_mode="manual"))
        self.api=APIClient();self.api.force_authenticate(self.alice)
        BillingSettings.objects.update_or_create(pk=1,defaults={"sales_enabled":True})

    def reserve(self,user=None):
        return services.start_search(user or self.alice,uuid.uuid4())

    def attempt(self,reservation,sequence=1,kind="chat",usage=None):
        ticket=services.start_attempt(reservation.pk,sequence,kind)
        services.finish_attempt(ticket,{"usage":usage if usage is not None else {"prompt_tokens":4,"completion_tokens":2,"total_tokens":6},"cached_prompt_tokens":2})
        return ticket

    def test_initial_credit_is_awarded_once_and_can_be_enabled_after_first_visit(self):
        self.config.initial_credits=0;self.config.save()
        self.assertEqual(services.get_wallet(self.alice).balance,0)
        self.config.initial_credits=100;self.config.save()
        self.assertEqual(services.get_wallet(self.alice).balance,100)
        self.config.initial_credits=200;self.config.save()
        self.assertEqual(services.get_wallet(self.alice).balance,100)
        self.assertEqual(CreditEntry.objects.filter(kind="initial").count(),1)

    def test_start_does_not_debit_or_cross_accounts(self):
        res=self.reserve()
        services.start_search(self.alice,res.pk)
        self.assertEqual(services.get_wallet(self.alice).balance,100)
        with self.assertRaises(PlatformAPIError):services.start_search(self.bob,res.pk)

    def test_known_chat_embedding_and_cached_usage_settle_once(self):
        res=self.reserve();self.attempt(res)
        self.attempt(res,2,"embedding",{"prompt_tokens":2,"total_tokens":2})
        services.settle(res.pk,outcome="complete");services.settle(res.pk,outcome="complete")
        wallet=services.get_wallet(self.alice)
        self.assertEqual(wallet.balance,92)
        res.refresh_from_db()
        self.assertEqual((res.prompt_tokens,res.completion_tokens,res.embedding_tokens,res.cached_tokens),(4,2,2,2))
        self.assertEqual(res.charged,8)
        self.assertEqual(CreditEntry.objects.filter(kind="search").count(),1)

    def test_pricing_changes_do_not_change_a_running_search_tariff(self):
        res=self.reserve()
        self.config.input_per_million=999000000;self.config.save()
        self.attempt(res);services.settle(res.pk)
        res.refresh_from_db();self.assertEqual(res.charged,7)

    def test_search_finishes_with_negative_balance_then_blocks_until_funded(self):
        self.config.initial_credits=3;self.config.save()
        summary=services.summary(self.alice)
        self.assertTrue(summary["can_search"])
        res=self.reserve();self.assertEqual(services.get_wallet(self.alice).balance,3)
        self.attempt(res);services.settle(res.pk)
        self.assertEqual(services.get_wallet(self.alice).balance,-4)
        self.assertFalse(services.summary(self.alice)["can_search"])
        with self.assertRaises(PlatformAPIError):self.reserve()
        services.adjust(self.alice,3,actor=self.admin,note="شارژ ناکافی",key=uuid.uuid4())
        self.assertFalse(services.summary(self.alice)["can_search"])
        services.adjust(self.alice,2,actor=self.admin,note="شارژ کافی",key=uuid.uuid4())
        self.assertTrue(services.summary(self.alice)["can_search"])

    def test_token_accounting_is_not_exposed_by_wallet_endpoints(self):
        res=self.reserve();self.attempt(res);services.settle(res.pk)
        for url in ["ai-credit-wallet","ai-credit-history"]:
            response=self.api.get(reverse(url))
            self.assertEqual(response.status_code,200)
            self.assertNotIn("tokens",str(response.data))

    def test_explicit_cache_writes_are_billed_as_a_subset_of_input_once(self):
        self.config.input_per_million=1000;self.config.output_per_million=1000
        self.config.cached_input_per_million=100
        self.config.cache_write_per_million=1250;self.config.cache_write_12h_per_million=2500
        self.config.save()
        res=self.reserve();ticket=services.start_attempt(res.pk,1,"chat")
        services.finish_attempt(ticket,{"usage":{"prompt_tokens":1000,"completion_tokens":100},
            "cached_prompt_tokens":200,"cache_write_prompt_tokens":300,"cache_write_12h_prompt_tokens":100})
        services.settle(res.pk);res.refresh_from_db()
        # 500 normal + 200 read + 200 short writes + 100 long writes + 100 output.
        self.assertEqual(res.charged,Decimal("1.12"))
        self.assertEqual(res.cache_write_tokens,300)

    def test_dollar_packages_reprice_and_existing_orders_keep_their_quote(self):
        package=CreditPackage.objects.create(name="بستهٔ دلاری",credits=1000,price_toman=162000,dollar_priced=True)
        response=self.checkout(package)
        self.assertEqual(response.status_code,201)
        order=Order.objects.get(pk=response.data["order_id"])
        self.assertEqual(order.payable_toman,162000)
        self.config.usd_to_toman=300000;self.config.save();fx.reprice_packages(self.config)
        package.refresh_from_db();self.assertEqual(package.price_toman,180000)
        order.refresh_from_db();self.assertEqual(order.payable_toman,162000)
        mark_paid(order.pk,gateway="fake")
        self.assertEqual(services.get_wallet(self.alice).balance,1100)

    def test_price_change_is_rejected_before_a_payment_order_is_created(self):
        package=CreditPackage.objects.create(name="بستهٔ دلاری",credits=1000,price_toman=162000,dollar_priced=True)
        response=self.api.post(reverse("ai-credit-topup"),{"package_id":package.pk,"request_id":"changed-price",
            "expected_price_toman":150000},format="json")
        self.assertEqual(response.status_code,409)
        self.assertEqual(response.data["code"],"AI_CREDIT_PRICE_CHANGED")
        self.assertFalse(Order.objects.exists())

    def test_stale_automatic_currency_rate_blocks_new_dollar_orders(self):
        self.config.fx_mode="tgju";self.config.fx_source="tgju"
        self.config.fx_quoted_at=timezone.now()-timedelta(days=4);self.config.fx_checked_at=timezone.now();self.config.save()
        package=CreditPackage.objects.create(name="بستهٔ دلاری",credits=1000,price_toman=162000,dollar_priced=True)
        response=self.checkout(package)
        self.assertEqual(response.status_code,503)
        self.assertFalse(Order.objects.exists())

    def test_valid_quote_converts_rial_to_toman_and_reprices_dollar_packages(self):
        self.config.fx_mode="tgju";self.config.save()
        package=CreditPackage.objects.create(name="بستهٔ دلاری",credits=1000,price_toman=162000,dollar_priced=True)
        with patch.object(fx,"fetch_quote",return_value=(300000,timezone.now())):
            updated=fx.refresh(self.config)
        self.assertEqual(updated.usd_to_toman,300000)
        package.refresh_from_db();self.assertEqual(package.price_toman,180000)

    def test_currency_failure_does_not_overwrite_the_managers_rate(self):
        self.config.fx_mode="tgju";self.config.save()
        with patch.object(fx,"fetch_quote",side_effect=fx.QuoteUnavailable):
            updated=fx.refresh(self.config)
        self.assertEqual(updated.usd_to_toman,270000)

    def test_explicit_refresh_enables_tgju_only_after_a_valid_quote(self):
        self.config.fx_mode="manual";self.config.save()
        with patch.object(fx,"fetch_quote",side_effect=fx.QuoteUnavailable):
            with self.assertRaises(fx.QuoteUnavailable):fx.refresh(self.config,force=True,enable=True)
        self.config.refresh_from_db();self.assertEqual(self.config.fx_mode,"manual")
        with self.assertRaises(fx.QuoteUnavailable):fx.refresh(self.config,force=True,enable=True)
        from django.core.cache import caches
        caches["throttle"].delete("ai-credit:fx-refresh")  # Expire the failed fetch's cooldown.
        with patch.object(fx,"fetch_quote",return_value=(300000,timezone.now())):
            fx.refresh(self.config,force=True,enable=True)
        self.config.refresh_from_db()
        self.assertEqual((self.config.fx_mode,self.config.usd_to_toman),("tgju",300000))

    def test_public_quote_rejects_old_or_wrong_units_and_parses_market_timestamp(self):
        stamp=timezone.now().astimezone(fx.ZoneInfo("Asia/Tehran")).strftime("%Y-%m-%d %H:%M:%S")
        data={"current":{"price_dollar_rl":{"p":"2,700,000","ts":stamp}}}
        rate,_=fx.parse_quote(data)
        self.assertEqual(rate,270000)
        data["current"]["price_dollar_rl"]["ts"]="2020-01-01 00:00:00"
        with self.assertRaises(fx.QuoteUnavailable):fx.parse_quote(data)

    def test_cache_hit_and_failure_before_provider_request_release_all_credit(self):
        res=self.reserve();services.settle(res.pk,outcome="complete")
        self.assertEqual(services.get_wallet(self.alice).available,100)
        other=self.reserve();services.settle(other.pk,outcome="failed")
        self.assertEqual(services.get_wallet(self.alice).balance,100)

    def test_unknown_usage_never_locks_balance_and_can_be_reviewed_later(self):
        res=self.reserve();self.attempt(res,usage={})
        services.settle(res.pk,outcome="failed")
        wallet=services.get_wallet(self.alice)
        self.assertEqual((wallet.balance,wallet.available),(100,100))
        self.assertTrue(services.summary(self.alice)["can_search"])
        res.refresh_from_db();self.assertEqual(res.status,"pending")
        services.settle(res.pk,reviewed_charge=5,actor=self.admin,note="بررسی مصرف")
        services.settle(res.pk,reviewed_charge=5,actor=self.admin,note="تکرار")
        self.assertEqual(services.get_wallet(self.alice).balance,95)
        self.assertEqual(services.get_wallet(self.alice).available,95)

    def test_customer_cannot_adjust_or_review_credit(self):
        with self.assertRaises(PlatformAPIError):services.adjust(self.alice,100,actor=self.alice,note="x",key=uuid.uuid4())
        res=self.reserve();self.attempt(res,usage={});services.settle(res.pk)
        with self.assertRaises(PlatformAPIError):services.settle(res.pk,reviewed_charge=0,actor=self.alice,note="x")

    def test_a_started_search_continues_and_bills_full_cost_without_a_hold_cap(self):
        res=self.reserve();self.attempt(res,usage={"prompt_tokens":100,"completion_tokens":100})
        self.attempt(res,2,usage={"prompt_tokens":4,"completion_tokens":2})
        services.settle(res.pk)
        self.assertEqual(services.get_wallet(self.alice).balance,-206)
        self.assertFalse(services.summary(self.alice)["can_search"])

    def test_known_usage_is_charged_once_while_unknown_portion_waits_without_hold(self):
        res=self.reserve();self.attempt(res);self.attempt(res,2,usage={})
        services.settle(res.pk);services.settle(res.pk)
        self.assertEqual(services.get_wallet(self.alice).balance,93)
        services.settle(res.pk,reviewed_charge=9,actor=self.admin,note="کل مصرف تأیید شد")
        services.settle(res.pk,reviewed_charge=9,actor=self.admin,note="تکرار")
        self.assertEqual(services.get_wallet(self.alice).balance,91)

    def test_replayed_attempt_cannot_send_another_paid_request(self):
        res=self.reserve();services.start_attempt(res.pk,1,"chat")
        with self.assertRaisesMessage(ProviderError,"AI_CREDIT_ATTEMPT_REPLAY"):services.start_attempt(res.pk,1,"chat")

    def test_terminal_search_is_reconciled_before_admitting_the_next_request(self):
        self.config.initial_credits=3;self.config.save()
        res=self.reserve();self.attempt(res)
        SearchRun.objects.create(id=res.pk,owner=self.alice,client_id="lost-settlement",payload_digest="x"*64,
            encrypted_payload="fixture",status="complete")
        with self.assertRaises(PlatformAPIError):self.reserve()
        # Admission rolls back with the caller's failed transaction; the next
        # normal wallet refresh settles the terminal search independently.
        services.reconcile(services.get_wallet(self.alice))
        self.assertEqual(services.get_wallet(self.alice).balance,-4)

    def test_model_change_requires_tariff_review_before_reservation(self):
        with override_settings(AI_LAB_MODEL="another-model"):
            with self.assertRaises(PlatformAPIError):self.reserve()

    def test_disabled_billing_records_usage_without_debit(self):
        self.config.enabled=False;self.config.initial_credits=0;self.config.save()
        res=self.reserve();self.attempt(res);services.settle(res.pk)
        res.refresh_from_db()
        self.assertEqual((res.charged,res.prompt_tokens,res.completion_tokens),(0,4,2))

    def test_wallet_and_history_are_private_to_authenticated_owner(self):
        services.adjust(self.alice,10,actor=self.admin,note="هدیهٔ شخصی",key=uuid.uuid4())
        self.api.force_authenticate(self.bob)
        response=self.api.get(reverse("ai-credit-wallet"),{"user_id":self.alice.pk})
        self.assertEqual(response.status_code,200)
        self.assertEqual(Decimal(response.data["available"]),100)
        response=self.api.get(reverse("ai-credit-history"))
        self.assertNotIn("هدیهٔ شخصی",str(response.data))
        self.assertIn("no-store",response["Cache-Control"])
        self.api.force_authenticate(None)
        self.assertEqual(self.api.get(reverse("ai-credit-wallet")).status_code,401)

    def test_insufficient_credit_rejects_admission_before_queue_or_provider(self):
        self.config.initial_credits=0;self.config.save()
        with patch("apps.ai_lab.events.last_sequence",return_value=0),patch("apps.ai_lab.jobs.active",return_value=None),patch("apps.ai_lab.tasks.enqueue_search") as queued:
            response=self.api.post(reverse("ai-lab-ask"),{"question":"سؤال مرجع آزمایشی","model":"luna","sources":["uptodate"],"request_id":"not-funded"},format="json")
        self.assertEqual(response.status_code,402)
        self.assertEqual(SearchRun.objects.count(),0)
        queued.assert_not_called()

    def test_provider_telemetry_persists_usage_without_provider_bodies(self):
        res=self.reserve();trace=telemetry.Trace(credit_reservation_id=str(res.pk))
        with trace.activate(),telemetry.operation("answering"),telemetry.model_attempt():
            telemetry.provider_request_sent()
            telemetry.provider_usage({"usage":{"prompt_tokens":4,"completion_tokens":2,"total_tokens":6,
                "prompt_tokens_details":{"cached_tokens":2},"private":"must-not-store"}})
        services.settle(res.pk)
        attempt=CreditAttempt.objects.get(reservation=res)
        self.assertNotIn("must-not-store",str(attempt.usage))
        self.assertNotIn("_credit_ticket",str(trace.snapshot()))
        res.refresh_from_db();self.assertEqual(res.charged,7)

    def package(self):
        return CreditPackage.objects.create(name="بستهٔ آزمایشی",credits=10,price_toman=10000)

    def checkout(self,package,key="package-once"):
        return self.api.post(reverse("ai-credit-topup"),{"package_id":package.pk,"request_id":key,"client":"web"},format="json")

    def test_checkout_is_idempotent_and_package_values_are_server_owned(self):
        pack=self.package();first=self.checkout(pack);second=self.checkout(pack)
        self.assertEqual(first.status_code,201)
        self.assertEqual(first.data["order_id"],second.data["order_id"])
        self.assertEqual(Order.objects.count(),1)
        other=self.package()
        self.assertEqual(self.checkout(other).status_code,409)
        self.assertEqual(services.get_wallet(self.alice).balance,100)

    def test_verified_topup_credits_once_and_never_grants_a_subscription(self):
        pack=self.package();response=self.checkout(pack)
        order=Order.objects.get(pk=response.data["order_id"])
        self.api.get(response.data["payment_url"])
        order.refresh_from_db()
        self.assertEqual(order.gateway,"fake")
        callback=reverse("billing-callback-gateway",args=["fake"])
        params={"Authority":order.authority,"Status":"OK"}
        self.assertEqual(self.api.get(callback,params).status_code,302)
        self.assertEqual(self.api.get(callback,params).status_code,302)
        self.assertEqual(services.get_wallet(self.alice).balance,110)
        self.assertEqual(Entitlement.objects.filter(user=self.alice).count(),0)
        self.assertEqual(CreditEntry.objects.filter(kind="topup").count(),1)

    def test_reload_payment_start_reuses_the_existing_gateway_invoice(self):
        response=self.checkout(self.package())
        gateway=FakeGateway()
        with patch("apps.billing.gateways.get_gateway",return_value=gateway),patch.object(gateway,"start",wraps=gateway.start) as start:
            self.api.get(response.data["payment_url"]);self.api.get(response.data["payment_url"])
        self.assertEqual(start.call_count,1)

    def test_pending_order_keeps_its_original_credit_amount_when_package_is_edited(self):
        package=self.package();response=self.checkout(package)
        package.credits=100;package.save()
        mark_paid(response.data["order_id"],gateway="fake")
        self.assertEqual(services.get_wallet(self.alice).balance,110)

    def test_disabled_pricing_keeps_wallet_visible_and_blocks_topup_sales(self):
        package=self.package();self.config.enabled=False;self.config.initial_credits=0;self.config.save()
        response=self.api.get(reverse("ai-credit-wallet"))
        self.assertFalse(response.data["billing_enabled"])
        self.assertTrue(response.data["can_search"])
        self.assertEqual(self.checkout(package).status_code,503)

    def test_admin_pages_require_billing_permission(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(reverse("ai_wallet_admin:dashboard")).status_code,403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("ai_wallet_admin:dashboard")).status_code,200)
        self.assertEqual(self.client.get(reverse("ai_wallet_admin:user",args=[self.alice.pk])).status_code,200)

    def test_admin_cannot_enable_unpriced_billing(self):
        self.client.force_login(self.admin)
        body={"enabled":"on","initial_credits":"0","input_per_million":"0","output_per_million":"0",
              "embedding_per_million":"0","cached_input_per_million":""}
        response=self.client.post(reverse("ai_wallet_admin:dashboard"),body)
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.context["form"].errors)
