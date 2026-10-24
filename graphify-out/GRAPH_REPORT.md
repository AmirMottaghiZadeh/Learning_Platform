# Graph Report - Learning Platform  (2026-10-24)

## Corpus Check
- 499 files · ~398,129 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 32 file(s) not represented in the graph (top: (none) 11, .ttf 7, .woff2 4)

## Summary
- 4760 nodes · 13376 edges · 195 communities (116 shown, 79 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1215 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a5440308`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- api/types.ts
- django_db
- test_panel.py
- console/views.py
- react
- Post
- useTheme
- views_public.py
- .reverse
- package.json
- flashcards/views.py
- calculators/reference_db.py
- billing/views.py
- Navigator.tsx
- GatewayError
- ImportOpenfdaTests
- billing/services.py
- Page
- views_drugs.py
- data_quality_center/forms.py
- accounts/views.py
- import_calculators.py
- data_quality_center/views.py
- calculatorEngine.ts
- accounts/checks.py
- quiz/views.py
- MedscapeArticleScreen.tsx
- lexicomp/services.py
- .request_code
- progress/tests.py
- core/views.py
- lessons/views.py
- VisitorDay
- store.ts
- Calculator
- SectionEditRequest
- re
- CalculatorDetailScreen.tsx
- offline/views.py
- common.tsx
- calculatorModel.ts
- AtcCategory
- QuizApiTests
- sources.ts
- progress/views.py
- SecurityAuditEvent
- config.py
- pack.py
- drugs/serializers.py
- FlashcardApiTests
- LessonTaxonomyTests
- expo
- planning.py
- import_medscape_articles.py
- ResultCard
- data_quality_center/tests.py
- django_conf
- Article
- test_phone_auth.py
- ۶. پیکربندی و متغیرهای محیطی
- billing/tests.py
- 6. Lesson study topics (52)
- ApiTests
- throttling.py
- django_core_management_base
- WebsiteAuthTests
- logging
- ۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین
- uptodate/services.py
- dependencies
- medscape/tests.py
- crypto.web.ts
- panel.js
- Post
- اپ‌ها (`backend/apps/`)
- django_core_management
- SectionEdit
- views_account.py
- maintenance_urls.py
- ConsoleTestCase
- StudyTopicsCoverageTests
- LessonDetailScreen.tsx
- IngredientProfileSection
- UptodateTests
- RoleAssignment
- website_extras.py
- clean_profile_boilerplate.py
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- porter.ts
- storage.py
- downloader.ts
- uptodate/views.py
- MedscapeApiTests
- Media
- offline/reader.ts
- docs/README.md
- files.ts
- django_core_management_base
- site.js
- drugs/reference_db.py
- downloader.web.ts
- dqc_extras.py
- Section
- ImportCalculatorsTests
- ReferenceDbTests
- Repository Guidelines
- Media
- ۲. راه‌اندازی محیط توسعه
- bidi.ts
- accounts/services.py
- ۵. قرارداد API (نسخهٔ ۱)
- bootstrap_superuser.py
- ۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی
- tsconfig.json
- ۱۲. سایت `pharmenta.ir` و پنل محتوا
- django_apps
- sw.js
- Command
- pagination.py
- settings/base.py
- otp.py
- jalali.ts
- docker-start.sh
- billing/apps.py
- FlashcardFact
- .claude/CLAUDE.md
- OfflinePackageCard.tsx
- app.config.js
- .mcp.json
- ۳. بک‌اند (Django)
- 0005_atccode_name_fa.py
- data_quality_center/apps.py
- drugs/apps.py
- flashcards/apps.py
- lessons/apps.py
- lexicomp/apps.py
- offline/apps.py
- progress/apps.py
- quiz/apps.py
- uptodate/apps.py
- website/apps.py
- ۸. دیپلوی
- ۱. معرفی و معماری
- ۱۰. مرجع سریع دستورها
- کنسول فروش (`/ops/`)
- مستندات فارمنتا
- فارمنتا (Pharmenta)

## God Nodes (most connected - your core abstractions)
1. `useTheme()` - 163 edges
2. `AppText()` - 157 edges
3. `useLang()` - 143 edges
4. `PlatformAPIError` - 79 edges
5. `react` - 78 edges
6. `Ingredient` - 72 edges
7. `react-native` - 67 edges
8. `useNav` - 60 edges
9. `SiteSettings` - 54 edges
10. `Post` - 54 edges

## Surprising Connections (you probably didn't know these)
- `فاز ۰.۵ — حذف زیرساخت رهاشده ✅` --references--> `UserSession`  [INFERRED]
  PHASES.md → backend/apps/accounts/models.py
- `۳d — بازنویسی `data_quality_center` ✅` --references--> `SectionEdit`  [INFERRED]
  PHASES.md → backend/apps/data_quality_center/models.py
- `دستورهای خودکار هنگام شروع` --references--> `AtcCategory`  [INFERRED]
  docs/07-data.md → backend/apps/drugs/models.py
- `۳a — جدول مرجع ATC + `apps.lessons` ✅` --references--> `AtcCategory`  [INFERRED]
  PHASES.md → backend/apps/drugs/models.py
- `فلش‌کارت — `/flashcards/` (ویژگی `flashcards`؛ پرچم `FLASHCARDS_API_ENABLED`)` --references--> `next_topic()`  [INFERRED]
  docs/05-api.md → backend/apps/flashcards/decks.py

## Import Cycles
- None detected.

## Communities (195 total, 79 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.03
Nodes (96): حساب و احراز هویت — `/auth/`, API_BASE_URL, apiClient, ApiError, ApiErrorBody, AuthController, configureAuth(), RetryableConfig (+88 more)

### Community 1 - "django_db"
Cohesion: 0.02
Nodes (52): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+44 more)

### Community 2 - "test_panel.py"
Cohesion: 0.07
Nodes (15): StaffRole, Meta, AdminTests, AuthorTests, AuthTests, CommercePagesTests, InboxTests, make_user() (+7 more)

### Community 3 - "console/views.py"
Cohesion: 0.05
Nodes (71): DiscountForm, FeatureEditForm, Meta, FeatureForm, Meta, latin_digits(), parse_amount(), parse_jalali() (+63 more)

### Community 4 - "react"
Cohesion: 0.08
Nodes (65): calculatorsApi, meApi, medscapeApi, MedscapeKind, ALPHABET, AlphabeticalArticleList(), buildOffsets(), groupAlphabetically() (+57 more)

### Community 5 - "Post"
Cohesion: 0.06
Nodes (59): ActivityLog, Meta, Comment, Meta, ContactMessage, Meta, PostRevision, Meta (+51 more)

### Community 6 - "useTheme"
Cohesion: 0.11
Nodes (61): SectionTone, NumberedHeading(), AuthLayout(), BottomNav(), CardsFlow(), ChecklistFlow(), LiveScore(), Choices() (+53 more)

### Community 7 - "views_public.py"
Cohesion: 0.05
Nodes (47): site(), SiteMaintenanceMiddleware, Announcement, Meta, DailyStat, Meta, PostQuerySet, SiteSettings (+39 more)

### Community 8 - ".reverse"
Cohesion: 0.04
Nodes (18): AuthenticationSecurityTests, OnboardingTests, enabled_gateways(), wrapper(), AccessTests, ConsoleTestCase, DeleteUserTests, DiscountAndReportTests (+10 more)

### Community 9 - "package.json"
Cohesion: 0.04
Nodes (75): ارتباط با API و کش, دانلود آفلاین (`src/offline/`), زبان، جهت و تم, ساختار `frontend/src/`, شروع اپ, وب‌اپ و PWA, پیکربندی اپ بومی, ۴. اپ (Expo — اندروید، iOS و وب) (+67 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.04
Nodes (44): Ingredient, Meta, all_decks(), _carded_slugs(), deck_slugs(), next_topic(), progress_map(), topic_meta() (+36 more)

### Community 11 - "calculators/reference_db.py"
Cohesion: 0.08
Nodes (14): export(), Command, dumps(), expected_count(), loads(), record_counts(), rows(), writing() (+6 more)

### Community 12 - "billing/views.py"
Cohesion: 0.07
Nodes (33): is_guest(), Order, Meta, CatalogSerializer, CheckoutSerializer, MyAccessSerializer, MyEntitlementSerializer, Meta (+25 more)

### Community 13 - "Navigator.tsx"
Cohesion: 0.19
Nodes (41): قابلیت‌ها, افزودن صفحهٔ تازه, قواعد کدنویسی اپ, ناوبری, LoadingState(), Screen(), ScreenChrome(), CurrentScreen() (+33 more)

### Community 14 - "GatewayError"
Cohesion: 0.06
Nodes (14): FakeGateway, GatewayError, get_gateway(), _post_json(), SepGateway, start_payment(), Verification, ZarinpalGateway (+6 more)

### Community 15 - "ImportOpenfdaTests"
Cohesion: 0.06
Nodes (8): AtcSupplementTests, CleanBoilerplateInPipelineTests, DrugApiTests, ImportOpenfdaTests, LoadAtcReferenceTests, _make_source_db(), ModelTests, StandardizePipelineUnitsTests

### Community 16 - "billing/services.py"
Cohesion: 0.04
Nodes (33): UsageRecord, Meta, Access, active_entitlements(), BillingError, check_feature(), content_lock(), create_order() (+25 more)

### Community 17 - "Page"
Cohesion: 0.08
Nodes (6): clean_html(), _Cleaner, plain_text(), safe_url(), _Text, SanitizeTests

### Community 18 - "views_drugs.py"
Cohesion: 0.06
Nodes (26): Command, Migration, Migration, article(), breadcrumbs(), editorial_team(), home_graph(), _id() (+18 more)

### Community 20 - "accounts/views.py"
Cohesion: 0.05
Nodes (48): AuthTokenResponseSerializer, LearnerProfileSerializer, Meta, LoginSerializer, OnboardingSerializer, OtpRequestResponseSerializer, OtpRequestSerializer, PasswordResetConfirmSerializer (+40 more)

### Community 21 - "import_calculators.py"
Cohesion: 0.05
Nodes (31): _fa_keys_standardized(), fix_questions(), fix_results(), fix_strings_fa(), renumber_from_one(), standardize_fa_units(), _title_formula_as_result(), _with_choices() (+23 more)

### Community 22 - "data_quality_center/views.py"
Cohesion: 0.11
Nodes (25): warning_count(), section_state(), _diffs(), discard(), history(), _login_key(), login_view(), logout_view() (+17 more)

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.08
Nodes (54): CalculatorErrorCheck, useLiveScore(), buildHeuristicSeeds(), cartesian(), classifyResultTone(), computeCalculator(), ComputeOptions, computeResultRanges() (+46 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.05
Nodes (43): slugs_for_topic(), BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, ingredient_ids_for_selection(), preview_selection(), sample_bank_questions(), _sample_rows() (+35 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.06
Nodes (71): MedscapeBlock, MedscapeSection, useBleedTop(), countMatches(), FindState, highlight(), ListMarker(), LTR (+63 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.09
Nodes (18): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, _categories_for_generics(), check_interactions(), close_all(), _conn(), _dir() (+10 more)

### Community 28 - ".request_code"
Cohesion: 0.08
Nodes (21): CodeRuleTests, PhoneAuthTestCase, ResetTests, SignUpTests, برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی, روش تبدیل پیشنهادها به کلمات کلیدی معتبر, ساخت Analytics از ابتدا (+13 more)

### Community 29 - "progress/tests.py"
Cohesion: 0.06
Nodes (22): DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin, DailyStudy, Meta, LearnerProgress, StudyPlan (+14 more)

### Community 30 - "core/views.py"
Cohesion: 0.13
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 31 - "lessons/views.py"
Cohesion: 0.07
Nodes (30): _applies(), require_atc_content(), _require_content(), require_feature(), require_topic_content(), _first_message(), _message_from_data(), _normalize_code() (+22 more)

### Community 32 - "VisitorDay"
Cohesion: 0.24
Nodes (4): VisitorDay, Meta, UniqueVisitorTests, visit()

### Community 33 - "store.ts"
Cohesion: 0.14
Nodes (36): closeReaders(), bootOffline(), cancel(), currentUserId(), DatasetState, download(), empty(), events (+28 more)

### Community 34 - "Calculator"
Cohesion: 0.07
Nodes (18): Calculator, Meta, CalculatorCategory, Meta, CalculatorTag, Meta, CalculatorCategorySerializer, Meta (+10 more)

### Community 35 - "SectionEditRequest"
Cohesion: 0.10
Nodes (21): ReviewEvent, Meta, SectionEditRequest, Meta, approve(), _clean(), _client_ip(), _close() (+13 more)

### Community 36 - "re"
Cohesion: 0.07
Nodes (16): _stage_names_without_prefix(), StandardizeUnitsTests, _adjective(), _chain(), _key(), _latin_quantity(), _spelling(), standardize_in() (+8 more)

### Community 37 - "CalculatorDetailScreen.tsx"
Cohesion: 0.12
Nodes (25): describeInputs(), flowLayout, QuestionFlow(), canGoBack(), goBackInApp(), installWebBackGuard(), Interceptor, interceptors (+17 more)

### Community 38 - "offline/views.py"
Cohesion: 0.08
Nodes (23): build_matches_dataset(), LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer, PackageFileUrlSerializer, PackageManifestSerializer, PackageUrlsRequestSerializer (+15 more)

### Community 39 - "common.tsx"
Cohesion: 0.13
Nodes (32): bandFor(), Chip(), Collapse(), Extra, Extras(), fmt(), hasPersian(), LEVEL_TONES (+24 more)

### Community 40 - "calculatorModel.ts"
Cohesion: 0.10
Nodes (34): CalculatorDetail, CalculatorQuestion, CalculatorResultDef, ResultProps, LIST_FROM, FieldProps, FlowProps, StagingResult() (+26 more)

### Community 41 - "AtcCategory"
Cohesion: 0.11
Nodes (10): AtcCategoryAdmin, AtcCodeAdmin, IngredientAdmin, IngredientProfileSectionAdmin, Command, AtcCategory, Meta, fold() (+2 more)

### Community 42 - "QuizApiTests"
Cohesion: 0.10
Nodes (3): QuizAccessTests, QuizApiTests, QuizLockedTests

### Community 43 - "sources.ts"
Cohesion: 0.08
Nodes (30): Coding Style & Naming Conventions, پایهٔ Django, lexicompApi, uptodateApi, LexicompDrug, LexicompInteraction, UptodateImage, cache (+22 more)

### Community 44 - "progress/views.py"
Cohesion: 0.08
Nodes (34): due_card_count(), Mistake, Meta, dashboard(), _display_name(), _leitner_focus_row(), _mastery_pct(), _next_chapter() (+26 more)

### Community 45 - "SecurityAuditEvent"
Cohesion: 0.12
Nodes (20): SecurityAuditEvent, Meta, CanManagePlatformRoles, CanViewSecurityAudit, HasPlatformPermission, HasRecentStepUp, PasswordSetSerializer, assign_platform_role() (+12 more)

### Community 46 - "config.py"
Cohesion: 0.10
Nodes (3): clear_cache(), _settings_changed(), PurchaseFlowTests

### Community 47 - "pack.py"
Cohesion: 0.07
Nodes (23): build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections(), _varints(), Command (+15 more)

### Community 48 - "drugs/serializers.py"
Cohesion: 0.09
Nodes (13): Command, AtcCode, Meta, AtcCodeSerializer, Meta, IngredientDetailSerializer, Meta, IngredientListSerializer (+5 more)

### Community 49 - "FlashcardApiTests"
Cohesion: 0.11
Nodes (5): FlashcardApiTests, FlashcardLockedTests, _refresh_facts(), _rich_ingredient(), TopicDeckTests

### Community 50 - "LessonTaxonomyTests"
Cohesion: 0.08
Nodes (4): DrugSearchTests, _ingredient(), LessonTaxonomyFallbackTests, LessonTaxonomyTests

### Community 51 - "expo"
Cohesion: 0.06
Nodes (31): backgroundColor, foregroundImage, adaptiveIcon, package, versionCode, projectId, typedRoutes, expo (+23 more)

### Community 52 - "planning.py"
Cohesion: 0.06
Nodes (32): ChapterProgress, Meta, lesson_groups(), mark_drug_read(), _subgroup(), topic_chapters(), topic_progress(), StudyPlanItem (+24 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.15
Nodes (7): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label()

### Community 54 - "ResultCard"
Cohesion: 0.34
Nodes (21): Explain(), Hero(), Interpretation(), ResultCard(), showTierBar(), toneOf(), useShown(), useTier() (+13 more)

### Community 55 - "data_quality_center/tests.py"
Cohesion: 0.22
Nodes (6): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), word_diff(), CheckTests

### Community 56 - "django_conf"
Cohesion: 0.10
Nodes (4): Command, rewrite_summaries(), _make_snapshot(), _make_snapshot()

### Community 57 - "Article"
Cohesion: 0.09
Nodes (15): Command, Command, Article, Meta, ArticleImage, ArticleDetailSerializer, Meta, ArticleImageSerializer (+7 more)

### Community 58 - "test_phone_auth.py"
Cohesion: 0.11
Nodes (8): EmailOrUsernameBackend, LearnerProfile, InvalidPhone, looks_like_phone(), normalize_phone(), PhoneField, NormalizePhoneTests, _find_user()

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.12
Nodes (16): HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت, دادهٔ مرجع (UpToDate و Lexicomp), دیتابیس، کش و آمادگی, سایت (+8 more)

### Community 60 - "billing/tests.py"
Cohesion: 0.18
Nodes (16): _div(), fa_digits(), format_date(), _jal_cal(), _mod(), month_start(), to_gregorian(), to_jalali() (+8 more)

### Community 61 - "6. Lesson study topics (52)"
Cohesion: 0.06
Nodes (34): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 6. Lesson study topics (52), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups (+26 more)

### Community 62 - "ApiTests"
Cohesion: 0.13
Nodes (3): ApiTests, BuildTests, DownloadHostTests

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "django_core_management_base"
Cohesion: 0.12
Nodes (5): Command, _DryRun, ReferenceImportCommand, open_for_import(), Command

### Community 66 - "logging"
Cohesion: 0.06
Nodes (11): password_reset_url_for_user(), send_password_reset_email(), send_password_reset_emails_for_email(), send_password_reset_email_task(), PlatformTask, retry_delay_seconds(), get_request_id(), JsonFormatter (+3 more)

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (26): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+18 more)

### Community 68 - "uptodate/services.py"
Cohesion: 0.09
Nodes (18): Command, article_from_row(), _dir(), get_image(), get_topic(), is_available(), mysql_config(), _mysql_conn() (+10 more)

### Community 69 - "dependencies"
Cohesion: 0.05
Nodes (36): dependencies, axios, expo, expo-crypto, expo-file-system, expo-font, @expo-google-fonts/vazirmatn, expo-linear-gradient (+28 more)

### Community 70 - "medscape/tests.py"
Cohesion: 0.25
Nodes (5): _disease_record(), _guideline_record(), ImportMedscapeArticlesTests, _write_diseases_tree(), _write_guidelines()

### Community 71 - "crypto.web.ts"
Cohesion: 0.21
Nodes (10): اجرای کامل با Docker, OfflineLicense, db(), idb(), keyring, openRecord(), openRecordBase64(), PackageKey (+2 more)

### Community 72 - "panel.js"
Cohesion: 0.16
Nodes (14): buildEditor(), align(), block(), exec(), sync(), toggleSource(), wrapBlock(), filterNav() (+6 more)

### Community 73 - "Post"
Cohesion: 0.04
Nodes (19): Page, Meta, Post, Meta, Subscriber, Meta, SiteTestCase, CommentTests (+11 more)

### Community 74 - "اپ‌ها (`backend/apps/`)"
Cohesion: 0.05
Nodes (33): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, BillingConfig, current() (+25 more)

### Community 75 - "django_core_management"
Cohesion: 0.15
Nodes (3): HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests

### Community 76 - "SectionEdit"
Cohesion: 0.16
Nodes (6): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin, SectionEdit, Meta

### Community 77 - "views_account.py"
Cohesion: 0.12
Nodes (16): AccountForm, CodeForm, LoginForm, PasswordForm, PhoneForm, account(), login_code(), login_phone() (+8 more)

### Community 79 - "ConsoleTestCase"
Cohesion: 0.16
Nodes (3): ConsoleTestCase, DraftAndSubmitTests, ReviewTests

### Community 81 - "LessonDetailScreen.tsx"
Cohesion: 0.29
Nodes (11): LessonSection, Badge(), joinOpenParens(), LessonBlock, LessonLine, parenDepth(), parseLessonText(), sectionText() (+3 more)

### Community 82 - "IngredientProfileSection"
Cohesion: 0.15
Nodes (7): IngredientProfileSectionInline, IngredientProfileSection, Meta, LessonDrugSectionSerializer, Meta, ProfileSectionSerializer, Meta

### Community 84 - "RoleAssignment"
Cohesion: 0.20
Nodes (8): RoleAssignment, Meta, RoleAssignmentCreateSerializer, RoleAssignmentRevokeSerializer, RoleAssignmentSerializer, Meta, RoleAssignmentListCreateView, RoleAssignmentRevokeView

### Community 85 - "website_extras.py"
Cohesion: 0.15
Nodes (8): atc_groups(), feature_icon(), nav_on(), oneline(), person(), split_highlight(), split_lines(), آنچه کد انجام می‌دهد

### Community 86 - "clean_profile_boilerplate.py"
Cohesion: 0.14
Nodes (13): clean_text(), Command, cleaned(), is_hypersensitivity_boilerplate(), is_hypersensitivity_boilerplate_en(), is_negative_indication_en(), is_negative_indication_fa(), is_null_placeholder() (+5 more)

### Community 87 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.10
Nodes (15): validate_production_broker(), validate_production_cache(), validate_production_secret_key(), CorsPreflightTests, ProductionSecretKeyTests, PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa, 🎉 بازنویسی کامل شد, فاز ۰.۵ — حذف زیرساخت رهاشده ✅ (+7 more)

### Community 88 - "porter.ts"
Cohesion: 0.23
Nodes (8): firstRule(), isVowelLetter(), porterStem(), Rule, STEP2, STEP3, STEP4, Word

### Community 89 - "storage.py"
Cohesion: 0.09
Nodes (15): Command, cors_rule(), _request(), clear_cache(), file_urls(), is_configured(), latest_manifest(), local_dir() (+7 more)

### Community 90 - "downloader.ts"
Cohesion: 0.20
Nodes (6): downloader, DownloadEvents, PartJob, PartRef, tasks, @kesha-antonov/react-native-background-downloader

### Community 91 - "uptodate/views.py"
Cohesion: 0.30
Nodes (8): UptodateArticleSerializer, UptodateImageSerializer, UptodateSearchResultSerializer, UptodateTopicSerializer, ImageDetailView, _require_available(), TopicDetailView, TopicSearchView

### Community 94 - "offline/reader.ts"
Cohesion: 0.22
Nodes (10): OfflineDataset, OfflineManifest, keyring, openRecord(), openRecordBase64(), PackageKey, sealed(), open (+2 more)

### Community 97 - "files.ts"
Cohesion: 0.26
Nodes (13): buildDir(), closeHandles(), ensureBuildDir(), handles, partFile(), partPath(), partSize(), readRange() (+5 more)

### Community 98 - "django_core_management_base"
Cohesion: 0.11
Nodes (5): Command, ensure_title_search_index(), _has_title_search_index(), MysqlTitleIndexTests, MysqlTitleSearchTests

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

### Community 100 - "drugs/reference_db.py"
Cohesion: 0.07
Nodes (11): Command, Command, _DryRun, _checked(), _digest(), export(), load(), open_parts() (+3 more)

### Community 102 - "downloader.web.ts"
Cohesion: 0.20
Nodes (9): downloader, DownloadEvents, newWorker(), PartJob, PartRef, Run, runFor(), runs (+1 more)

### Community 103 - "dqc_extras.py"
Cohesion: 0.22
Nodes (9): action_label(), action_tone(), ago(), dict_get(), fa_digits(), percent(), status_label(), status_tone() (+1 more)

### Community 105 - "ImportCalculatorsTests"
Cohesion: 0.32
Nodes (3): _build_sqlite(), ImportCalculatorsTests, _one_calculator()

### Community 107 - "Repository Guidelines"
Cohesion: 0.29
Nodes (6): Build, Test, and Development Commands, Commit & Pull Request Guidelines, Project Structure & Module Organization, Repository Guidelines, Security & Configuration Tips, Testing Guidelines

### Community 109 - "Media"
Cohesion: 0.03
Nodes (49): Command, AppRelease, Meta, Category, Meta, ContentBlock, Meta, DownloadLink (+41 more)

### Community 110 - "۲. راه‌اندازی محیط توسعه"
Cohesion: 0.17
Nodes (12): اندروید و iOS, اپ (Expo), بک‌اند, تست بستهٔ آفلاین بدون باکت, تست و بررسی, روال کار با مخزن, ساخت دیتابیس و اجرای سرور, نسخهٔ وب (+4 more)

### Community 111 - "bidi.ts"
Cohesion: 0.25
Nodes (7): isolated(), ENGLISH_RUN, hasPersianLetters(), isolateEnglish(), LRI, PDI, RLM

### Community 112 - "accounts/services.py"
Cohesion: 0.07
Nodes (21): SessionTokenAuthentication, SessionTokenAuthenticationScheme, Role, Meta, SessionRefreshToken, Meta, UserSession, Meta (+13 more)

### Community 113 - "۵. قرارداد API (نسخهٔ ۱)"
Cohesion: 0.11
Nodes (18): Lexicomp — `/lexicomp/` (ویژگی `lexicomp`), Medscape — `/medscape/` (ویژگی `medscape`), UpToDate — `/uptodate/` (ویژگی `uptodate`), آزمون — `/quiz/` (ویژگی `quiz`؛ پرچم `QUIZ_API_ENABLED`), تغییر دادن API, داروها — `/drugs/` و `/atc/`, دانلود آفلاین — `/offline/`, درس‌نامه — `/lessons/` (ویژگی `lessons`) (+10 more)

### Community 115 - "۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی"
Cohesion: 0.12
Nodes (17): اطلاعات غیرمحرمانه‌ای که باید جایی ثبت باشد, بازیابی, بکاپ و بازیابی, حساب‌های سرویس, رازها و چیزهایی که باید امن نگه داشته شوند, رازهای فنی, شاخص‌هایی که مرتب دیده شوند, عیب‌یابی (+9 more)

### Community 116 - "tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, paths, strict, extends, include, expo/tsconfig.base

### Community 117 - "۱۲. سایت `pharmenta.ir` و پنل محتوا"
Cohesion: 0.14
Nodes (14): not_found(), آمار بازدید, حساب و خرید روی سایت, دارونامهٔ عمومی (`/drugs/`), رسانه, سئو, ساختار کد, صفحه‌های عمومی (+6 more)

### Community 120 - "sw.js"
Cohesion: 0.38
Nodes (4): inScope(), referencedFiles(), SCOPE, storeShell()

### Community 125 - "settings/base.py"
Cohesion: 0.11
Nodes (3): build.sh script, DJANGO_SETTINGS_MODULE, release.sh script

### Community 126 - "otp.py"
Cohesion: 0.08
Nodes (20): OneTimeCode, Meta, account_for_signup(), _hash(), _new_code(), OtpError, request_code(), user_for_phone() (+12 more)

### Community 127 - "jalali.ts"
Cohesion: 0.26
Nodes (20): DateInput(), DaysInput(), Field(), QuestionTitle(), BREAKS, d2g(), d2j(), dateToMs() (+12 more)

### Community 132 - "FlashcardFact"
Cohesion: 0.20
Nodes (5): FlashcardFactAdmin, LeitnerCardAdmin, FlashcardFact, Meta, Command

### Community 134 - "OfflinePackageCard.tsx"
Cohesion: 0.21
Nodes (19): OfflineDownloadButton(), OfflineSheet(), ERROR_TEXT, LOGO, NAME, OfflinePackageCard(), PHASE_TEXT, SUPPORTS_BACKGROUND (+11 more)

### Community 182 - "۳. بک‌اند (Django)"
Cohesion: 0.12
Nodes (13): RequestIdMiddleware, SiteHostMiddleware, UpToDate و Lexicomp, افزودن یک قابلیت فروشی تازه, بستهٔ آفلاین (`apps.offline`), زنجیرهٔ middleware, صورتحساب و دسترسی (`apps.billing`), قواعد مشترک API (+5 more)

### Community 204 - "۸. دیپلوی"
Cohesion: 0.18
Nodes (11): CI, اپ اندروید و iOS, برگرداندن یک دیپلوی خراب, بک‌اند, جریان دیپلوی, راه‌اندازی از صفر (یک بار), سرویس‌های رانفلر, وب‌اپ (+3 more)

### Community 211 - "۱. معرفی و معماری"
Cohesion: 0.25
Nodes (8): دامنه‌ها و سرویس‌ها, ذخیره‌گاه‌های داده, ساختار مخزن, سرویس‌های بیرونی, فناوری‌ها, محصول, معماری, ۱. معرفی و معماری

### Community 212 - "۱۰. مرجع سریع دستورها"
Cohesion: 0.25
Nodes (8): اپ موبایل (EAS), تست و بررسی, توسعهٔ محلی, دستورهای مدیریتی Django (همه), دیپلوی و گیت, عیب‌یابی, پایپلاین study_content (بیرون از مخزن), ۱۰. مرجع سریع دستورها

### Community 213 - "کنسول فروش (`/ops/`)"
Cohesion: 0.22
Nodes (9): ادمین Django (`/admin/`), درگاه پرداخت و کلیدهای فروش, دسترسی مهمان, مرکز کیفیت داده (`/ops/data-quality/`), ویژگی‌ها, پلن‌ها و محصول‌ها, کاربران, کنسول فروش (`/ops/`) (+1 more)

### Community 226 - "مستندات فارمنتا"
Cohesion: 0.50
Nodes (4): سندهای دیگر مخزن, فهرست, قرارداد نگهداری این مستندات, مستندات فارمنتا

### Community 230 - "فارمنتا (Pharmenta)"
Cohesion: 0.67
Nodes (3): شروع سریع, فارمنتا (Pharmenta), مستندات

## Knowledge Gaps
- **8 isolated node(s):** `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-splash-screen`, `react-dom`, `react-native-web` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1550 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **79 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UserSession` connect `accounts/services.py` to `WebsiteAuthTests`, `console/views.py`, `useTheme`, `اپ‌ها (`backend/apps/`)`, `SecurityAuditEvent`, `accounts/views.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.149) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `AppText()` (e.g. with `زبان، جهت و تم` and `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅`) actually correct?**
  _`AppText()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-splash-screen` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.03076923076923077 - nodes in this community are weakly interconnected._
- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `useTheme` to `accounts/services.py`, `package.json`, `Navigator.tsx`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `PlatformAPIError` (e.g. with `LoginView` and `OtpVerifyView`) actually correct?**
  _`PlatformAPIError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.022123893805309734 - nodes in this community are weakly interconnected._