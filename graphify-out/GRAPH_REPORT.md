# Graph Report - Learning Platform  (2026-10-24)

## Corpus Check
- 495 files · ~394,638 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 32 file(s) not represented in the graph (top: (none) 11, .ttf 7, .woff2 4)

## Summary
- 4709 nodes · 13253 edges · 197 communities (114 shown, 83 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1207 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `81921b23`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- api/types.ts
- django_db
- test_panel.py
- console/views.py
- react
- Post
- useLang
- views_public.py
- .reverse
- package.json
- flashcards/views.py
- calculators/reference_db.py
- billing/views.py
- website/models.py
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
- progress/views.py
- core/views.py
- lessons/views.py
- DailyStat
- store.ts
- Calculator
- SectionEditRequest
- re
- CalculatorDetailScreen.tsx
- offline/views.py
- common.tsx
- calculatorModel.ts
- Ingredient
- QuizApiTests
- sources.ts
- billing/tests.py
- guest.py
- PurchaseFlowTests
- pack.py
- drugs/serializers.py
- FlashcardApiTests
- LessonTaxonomyTests
- expo
- planning.py
- import_medscape_articles.py
- ResultCard
- data_quality_center/tests.py
- فاز ۳ — اپ‌های بک‌اند (زیرفازی)
- Article
- test_phone_auth.py
- ۶. پیکربندی و متغیرهای محیطی
- RegisterSerializer
- 6. Lesson study topics (52)
- ApiTests
- throttling.py
- billing/models.py
- WebsiteAuthTests
- logging
- ۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین
- uptodate/services.py
- dependencies
- medscape/tests.py
- crypto.web.ts
- panel.js
- DownloadAndMachineTests
- اپ‌ها (`backend/apps/`)
- django_core_management
- SectionEdit
- sms.py
- maintenance_urls.py
- ConsoleTestCase
- StudyTopicsCoverageTests
- LessonDetailScreen.tsx
- drugs/admin.py
- UptodateTests
- ResultProps
- website_extras.py
- clean_profile_boilerplate.py
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- porter.ts
- storage.py
- downloader.ts
- uptodate/views.py
- DrugPageTests
- LexicompApiTests
- offline/reader.ts
- docs/README.md
- 0003_about_contact_text.py
- files.ts
- django_core_management_base
- site.js
- BuildTests
- ۴. اپ (Expo — اندروید، iOS و وب)
- downloader.web.ts
- dqc_extras.py
- Section
- calculators/tests.py
- DateResult.tsx
- Repository Guidelines
- ReviewTests
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
- scripts
- Command
- pagination.py
- views_account.py
- docker-start.sh
- billing/apps.py
- .claude/CLAUDE.md
- OfflinePackageCard.tsx
- app.config.js
- .mcp.json
- ۳. بک‌اند (Django)
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
6. `Ingredient` - 68 edges
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
- `ایمپورت از منبع خام (روی لپ‌تاپ)` --references--> `ArticleImage`  [INFERRED]
  docs/07-data.md → backend/apps/medscape/models.py

## Import Cycles
- None detected.

## Communities (197 total, 83 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.04
Nodes (84): حساب و احراز هویت — `/auth/`, flashcardsApi, quizApi, AtcCode, AtcGroup, AuthTokenResponse, BoxSummary, CalculatorCategoryRef (+76 more)

### Community 1 - "django_db"
Cohesion: 0.02
Nodes (49): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+41 more)

### Community 2 - "test_panel.py"
Cohesion: 0.07
Nodes (12): AdminTests, AuthorTests, AuthTests, CommercePagesTests, InboxTests, make_user(), MediaTests, PanelCase (+4 more)

### Community 3 - "console/views.py"
Cohesion: 0.05
Nodes (76): DiscountForm, FeatureEditForm, Meta, FeatureForm, Meta, latin_digits(), parse_amount(), parse_jalali() (+68 more)

### Community 4 - "react"
Cohesion: 0.08
Nodes (63): calculatorsApi, meApi, medscapeApi, MedscapeKind, ALPHABET, AlphabeticalArticleList(), buildOffsets(), groupAlphabetically() (+55 more)

### Community 5 - "Post"
Cohesion: 0.07
Nodes (51): Comment, Meta, Post, Meta, StaffRole, Meta, Subscriber, Meta (+43 more)

### Community 6 - "useLang"
Cohesion: 0.13
Nodes (80): قابلیت‌ها, ساختار `frontend/src/`, شروع اپ, قواعد کدنویسی اپ, Gate(), AppShell(), AuthLayout(), BottomNav() (+72 more)

### Community 7 - "views_public.py"
Cohesion: 0.06
Nodes (40): site(), SiteMaintenanceMiddleware, SiteSettings, Meta, login_view(), _safe_next(), add_toc(), blocks() (+32 more)

### Community 8 - ".reverse"
Cohesion: 0.04
Nodes (15): AuthenticationSecurityTests, OnboardingTests, wrapper(), AccessTests, ConsoleTestCase, DeleteUserTests, DiscountAndReportTests, FeatureTests (+7 more)

### Community 9 - "package.json"
Cohesion: 0.03
Nodes (70): زبان، جهت و تم, App(), ThemedStatusBar(), main, name, private, version, API_BASE_URL (+62 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.05
Nodes (37): FlashcardFactAdmin, LeitnerCardAdmin, all_decks(), _carded_slugs(), deck_slugs(), next_topic(), progress_map(), topic_meta() (+29 more)

### Community 11 - "calculators/reference_db.py"
Cohesion: 0.05
Nodes (22): Command, export(), load(), Command, _DryRun, dumps(), expected_count(), loads() (+14 more)

### Community 12 - "billing/views.py"
Cohesion: 0.05
Nodes (43): enabled_gateways(), get_gateway(), start_payment(), is_guest(), CatalogSerializer, CheckoutSerializer, MyAccessSerializer, MyEntitlementSerializer (+35 more)

### Community 13 - "website/models.py"
Cohesion: 0.04
Nodes (36): Command, ActivityLog, Meta, Announcement, Meta, AppRelease, Meta, Category (+28 more)

### Community 14 - "GatewayError"
Cohesion: 0.06
Nodes (12): FakeGateway, GatewayError, _post_json(), SepGateway, Verification, ZarinpalGateway, ZibalGateway, _fake_urlopen() (+4 more)

### Community 15 - "ImportOpenfdaTests"
Cohesion: 0.06
Nodes (11): IngredientProfileSection, Meta, AtcSupplementTests, CleanBoilerplateInPipelineTests, DrugApiTests, ImportOpenfdaTests, LoadAtcReferenceTests, _make_source_db() (+3 more)

### Community 16 - "billing/services.py"
Cohesion: 0.08
Nodes (20): Feature, Meta, UsageRecord, Meta, Access, active_entitlements(), check_feature(), content_lock() (+12 more)

### Community 17 - "Page"
Cohesion: 0.07
Nodes (6): clean_html(), _Cleaner, plain_text(), safe_url(), _Text, SanitizeTests

### Community 18 - "views_drugs.py"
Cohesion: 0.07
Nodes (26): Command, article(), breadcrumbs(), editorial_team(), home_graph(), _id(), organization(), page_graph() (+18 more)

### Community 20 - "accounts/views.py"
Cohesion: 0.05
Nodes (49): CanManagePlatformRoles, CanViewSecurityAudit, HasPlatformPermission, HasRecentStepUp, LearnerProfileSerializer, Meta, LoginSerializer, OtpRequestResponseSerializer (+41 more)

### Community 21 - "import_calculators.py"
Cohesion: 0.06
Nodes (27): _fa_keys_standardized(), fix_questions(), fix_results(), fix_strings_fa(), renumber_from_one(), standardize_fa_units(), _title_formula_as_result(), _with_choices() (+19 more)

### Community 22 - "data_quality_center/views.py"
Cohesion: 0.12
Nodes (25): warning_count(), section_state(), _diffs(), discard(), history(), _login_key(), login_view(), logout_view() (+17 more)

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.08
Nodes (56): CalculatorErrorCheck, useLiveScore(), buildHeuristicSeeds(), cartesian(), classifyResultTone(), computeCalculator(), ComputeOptions, computeResultRanges() (+48 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.07
Nodes (36): record_quiz_answers(), BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, best_score_pct_for_topic(), _finished_sessions(), _finished_topic_sessions(), topic_mastery_map() (+28 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.10
Nodes (43): MedscapeBlock, MedscapeSection, countMatches(), FindState, highlight(), ListMarker(), LTR, NumberedHeading() (+35 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.11
Nodes (16): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, _categories_for_generics(), check_interactions(), _conn(), _dir(), _exceptions_for_monographs() (+8 more)

### Community 28 - ".request_code"
Cohesion: 0.08
Nodes (21): CodeRuleTests, PhoneAuthTestCase, ResetTests, SignUpTests, برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی, روش تبدیل پیشنهادها به کلمات کلیدی معتبر, ساخت Analytics از ابتدا (+13 more)

### Community 29 - "progress/views.py"
Cohesion: 0.04
Nodes (53): DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin, DailyStudy, Meta, LearnerProgress, Mistake (+45 more)

### Community 30 - "core/views.py"
Cohesion: 0.12
Nodes (13): Migration, check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer (+5 more)

### Community 31 - "lessons/views.py"
Cohesion: 0.08
Nodes (26): _applies(), require_atc_content(), _require_content(), require_feature(), require_topic_content(), LessonDrugSerializer, get_chapter(), get_lesson_drug() (+18 more)

### Community 32 - "DailyStat"
Cohesion: 0.11
Nodes (14): DailyStat, Meta, VisitorDay, Meta, jalali_format(), dashboard(), _delta(), _paths() (+6 more)

### Community 33 - "store.ts"
Cohesion: 0.12
Nodes (38): offlineApi, OfflinePackageInfo, useOfflineBoot(), closeReaders(), bootOffline(), cancel(), currentUserId(), DATASETS (+30 more)

### Community 34 - "Calculator"
Cohesion: 0.08
Nodes (19): Calculator, Meta, CalculatorCategory, Meta, CalculatorTag, Meta, CalculatorCategorySerializer, Meta (+11 more)

### Community 35 - "SectionEditRequest"
Cohesion: 0.10
Nodes (21): ReviewEvent, Meta, SectionEditRequest, Meta, approve(), _clean(), _client_ip(), _close() (+13 more)

### Community 36 - "re"
Cohesion: 0.11
Nodes (12): _stage_names_without_prefix(), StandardizeUnitsTests, _adjective(), _chain(), _key(), _latin_quantity(), _spelling(), standardize_in() (+4 more)

### Community 37 - "CalculatorDetailScreen.tsx"
Cohesion: 0.09
Nodes (38): describeInputs(), CardsFlow(), ChecklistFlow(), flowLayout, LiveScore(), Choices(), FieldProps, FieldVariant (+30 more)

### Community 38 - "offline/views.py"
Cohesion: 0.08
Nodes (24): build_matches_dataset(), LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer, PackageFileUrlSerializer, PackageManifestSerializer, PackageUrlsRequestSerializer (+16 more)

### Community 39 - "common.tsx"
Cohesion: 0.16
Nodes (25): bandFor(), Chip(), Collapse(), Extra, Extras(), fmt(), LEVEL_TONES, plain() (+17 more)

### Community 40 - "calculatorModel.ts"
Cohesion: 0.14
Nodes (24): CalculatorResultDef, StagingResult(), ComputedResult, allWholeNumbers(), cache, classify(), classifyCalculator(), isNumeric() (+16 more)

### Community 41 - "Ingredient"
Cohesion: 0.06
Nodes (22): Command, AtcCategory, Meta, Ingredient, Meta, fold(), l2_slug_index(), _l2_slug_index() (+14 more)

### Community 42 - "QuizApiTests"
Cohesion: 0.10
Nodes (3): QuizAccessTests, QuizApiTests, QuizLockedTests

### Community 43 - "sources.ts"
Cohesion: 0.09
Nodes (29): lexicompApi, uptodateApi, LexicompDrug, LexicompInteraction, UptodateArticle, UptodateImage, UptodateSearchResult, UptodateTopic (+21 more)

### Community 44 - "billing/tests.py"
Cohesion: 0.09
Nodes (13): _div(), format_date(), _jal_cal(), _mod(), month_start(), to_gregorian(), to_jalali(), DiscountTests (+5 more)

### Community 45 - "guest.py"
Cohesion: 0.09
Nodes (12): AuthTokenResponseSerializer, OnboardingSerializer, UserSerializer, Meta, OnboardingView, create_guest(), GuestSessionView, GuestStatusView (+4 more)

### Community 47 - "pack.py"
Cohesion: 0.05
Nodes (24): writing(), _make_snapshot(), build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections() (+16 more)

### Community 48 - "drugs/serializers.py"
Cohesion: 0.06
Nodes (18): Command, AtcCode, Meta, AtcCodeSerializer, Meta, IngredientDetailSerializer, Meta, IngredientListSerializer (+10 more)

### Community 49 - "FlashcardApiTests"
Cohesion: 0.12
Nodes (6): seed_deck(), FlashcardApiTests, FlashcardLockedTests, _refresh_facts(), _rich_ingredient(), TopicDeckTests

### Community 50 - "LessonTaxonomyTests"
Cohesion: 0.06
Nodes (8): ChapterProgress, Meta, ReadDrug, Meta, DrugSearchTests, _ingredient(), LessonTaxonomyFallbackTests, LessonTaxonomyTests

### Community 51 - "expo"
Cohesion: 0.06
Nodes (31): backgroundColor, foregroundImage, adaptiveIcon, package, versionCode, projectId, typedRoutes, expo (+23 more)

### Community 52 - "planning.py"
Cohesion: 0.06
Nodes (25): due_card_count(), _seed_candidates(), _with_enough_content(), mark_drug_read(), ensure_today_items(), _flashcard_recall_for_slugs(), _flatten(), _goal_items() (+17 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.16
Nodes (7): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label()

### Community 54 - "ResultCard"
Cohesion: 0.34
Nodes (21): Explain(), Hero(), Interpretation(), ResultCard(), showTierBar(), toneOf(), useShown(), useTier() (+13 more)

### Community 55 - "data_quality_center/tests.py"
Cohesion: 0.24
Nodes (6): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), word_diff(), CheckTests

### Community 56 - "فاز ۳ — اپ‌های بک‌اند (زیرفازی)"
Cohesion: 0.25
Nodes (6): Migration, seed(), فاز ۳ — اپ‌های بک‌اند (زیرفازی), ۳a — جدول مرجع ATC + `apps.lessons` ✅, ۳c — `apps.flashcards` + `apps.quiz` (ساخته‌شده، پشت فلگ خاموش) ✅, ۳d — بازنویسی `data_quality_center` ✅

### Community 57 - "Article"
Cohesion: 0.07
Nodes (17): ReferenceImportCommand, open_for_import(), Command, Command, Article, Meta, ArticleImage, ArticleDetailSerializer (+9 more)

### Community 58 - "test_phone_auth.py"
Cohesion: 0.08
Nodes (14): EmailOrUsernameBackend, LearnerProfile, InvalidPhone, looks_like_phone(), normalize_phone(), PhoneField, NormalizePhoneTests, ProfileTests (+6 more)

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.12
Nodes (16): HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت, دادهٔ مرجع (UpToDate و Lexicomp), دیتابیس، کش و آمادگی, سایت (+8 more)

### Community 61 - "6. Lesson study topics (52)"
Cohesion: 0.06
Nodes (34): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 6. Lesson study topics (52), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups (+26 more)

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "billing/models.py"
Cohesion: 0.12
Nodes (12): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, DiscountCode, Meta (+4 more)

### Community 66 - "logging"
Cohesion: 0.06
Nodes (11): password_reset_url_for_user(), send_password_reset_email(), send_password_reset_emails_for_email(), send_password_reset_email_task(), PlatformTask, retry_delay_seconds(), get_request_id(), JsonFormatter (+3 more)

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (25): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+17 more)

### Community 68 - "uptodate/services.py"
Cohesion: 0.09
Nodes (19): Command, article_from_row(), _dir(), get_image(), get_topic(), is_available(), mysql_config(), _mysql_conn() (+11 more)

### Community 69 - "dependencies"
Cohesion: 0.08
Nodes (26): dependencies, axios, expo, expo-crypto, expo-file-system, expo-font, @expo-google-fonts/vazirmatn, expo-linear-gradient (+18 more)

### Community 70 - "medscape/tests.py"
Cohesion: 0.12
Nodes (6): _disease_record(), _guideline_record(), ImportMedscapeArticlesTests, MedscapeApiTests, _write_diseases_tree(), _write_guidelines()

### Community 71 - "crypto.web.ts"
Cohesion: 0.23
Nodes (9): اجرای کامل با Docker, db(), idb(), keyring, openRecord(), openRecordBase64(), PackageKey, rsaPair() (+1 more)

### Community 72 - "panel.js"
Cohesion: 0.16
Nodes (14): buildEditor(), align(), block(), exec(), sync(), toggleSource(), wrapBlock(), filterNav() (+6 more)

### Community 73 - "DownloadAndMachineTests"
Cohesion: 0.11
Nodes (4): CommentTests, DownloadAndMachineTests, make_post(), PostVisibilityTests

### Community 74 - "اپ‌ها (`backend/apps/`)"
Cohesion: 0.06
Nodes (22): BillingConfig, clear_cache(), current(), gateway_spec(), _gateways(), GatewaySpec, _load(), row() (+14 more)

### Community 75 - "django_core_management"
Cohesion: 0.14
Nodes (3): HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests

### Community 76 - "SectionEdit"
Cohesion: 0.15
Nodes (7): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin, SectionEdit, Meta, مرکز کیفیت داده (`/ops/data-quality/`)

### Community 77 - "sms.py"
Cohesion: 0.21
Nodes (6): _error_message(), send_code(), _send_smsir(), SentCode, SmsSendError, SmsIrBackendTests

### Community 81 - "LessonDetailScreen.tsx"
Cohesion: 0.07
Nodes (53): lessonsApi, LessonSection, TopInset, useBleedTop(), countWords(), numberByDepth(), Numbered, readingMinutes() (+45 more)

### Community 82 - "drugs/admin.py"
Cohesion: 0.27
Nodes (5): AtcCategoryAdmin, AtcCodeAdmin, IngredientAdmin, IngredientProfileSectionAdmin, IngredientProfileSectionInline

### Community 84 - "ResultProps"
Cohesion: 0.36
Nodes (8): CalculatorDetail, CalculatorQuestion, ResultProps, LIST_FROM, FlowProps, CalculatorAnswers, ResultRange, ModelInfo

### Community 85 - "website_extras.py"
Cohesion: 0.15
Nodes (8): atc_groups(), feature_icon(), nav_on(), oneline(), person(), split_highlight(), split_lines(), آنچه کد انجام می‌دهد

### Community 86 - "clean_profile_boilerplate.py"
Cohesion: 0.12
Nodes (11): clean_text(), Command, cleaned(), is_hypersensitivity_boilerplate(), is_hypersensitivity_boilerplate_en(), is_negative_indication_en(), is_negative_indication_fa(), is_null_placeholder() (+3 more)

### Community 87 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.07
Nodes (17): build.sh script, validate_production_broker(), validate_production_cache(), validate_production_secret_key(), CorsPreflightTests, ProductionSecretKeyTests, DJANGO_SETTINGS_MODULE, release.sh script (+9 more)

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

### Community 92 - "DrugPageTests"
Cohesion: 0.12
Nodes (3): DrugPageTests, SiteIdentityTests, structured()

### Community 94 - "offline/reader.ts"
Cohesion: 0.13
Nodes (16): Coding Style & Naming Conventions, پایهٔ Django, OfflineDataset, OfflineLicense, OfflineManifest, keyring, openRecord(), openRecordBase64() (+8 more)

### Community 97 - "files.ts"
Cohesion: 0.24
Nodes (14): buildDir(), closeHandles(), ensureBuildDir(), handles, partFile(), partPath(), partSize(), readRange() (+6 more)

### Community 98 - "django_core_management_base"
Cohesion: 0.11
Nodes (5): Command, ensure_title_search_index(), _has_title_search_index(), MysqlTitleIndexTests, MysqlTitleSearchTests

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

### Community 100 - "BuildTests"
Cohesion: 0.18
Nodes (3): BuildTests, DownloadHostTests, PackFormatTests

### Community 101 - "۴. اپ (Expo — اندروید، iOS و وب)"
Cohesion: 0.29
Nodes (8): ارتباط با API و کش, افزودن صفحهٔ تازه, دانلود آفلاین (`src/offline/`), ناوبری, وب‌اپ و PWA, پیکربندی اپ بومی, ۴. اپ (Expo — اندروید، iOS و وب), ScreenKey

### Community 102 - "downloader.web.ts"
Cohesion: 0.20
Nodes (9): downloader, DownloadEvents, newWorker(), PartJob, PartRef, Run, runFor(), runs (+1 more)

### Community 103 - "dqc_extras.py"
Cohesion: 0.12
Nodes (17): ago(), fa(), get_item(), guest_access_on(), initial(), jdate(), num(), toman() (+9 more)

### Community 105 - "calculators/tests.py"
Cohesion: 0.09
Nodes (7): _build_sqlite(), CalculatorApiTests, ChoiceErrataTests, FaUnitsTests, ImportCalculatorsTests, _one_calculator(), QuestionUnitTests

### Community 106 - "DateResult.tsx"
Cohesion: 0.43
Nodes (7): hasPersian(), Ltr(), Rows(), DateResult(), useDateFormat(), parseAge(), parseDateText()

### Community 107 - "Repository Guidelines"
Cohesion: 0.29
Nodes (6): Build, Test, and Development Commands, Commit & Pull Request Guidelines, Project Structure & Module Organization, Repository Guidelines, Security & Configuration Tips, Testing Guidelines

### Community 109 - "Media"
Cohesion: 0.04
Nodes (34): make_slug(), Media, Meta, unique_slug(), AnnouncementForm, Meta, CategoryForm, Meta (+26 more)

### Community 110 - "۲. راه‌اندازی محیط توسعه"
Cohesion: 0.17
Nodes (12): اندروید و iOS, اپ (Expo), بک‌اند, تست بستهٔ آفلاین بدون باکت, تست و بررسی, روال کار با مخزن, ساخت دیتابیس و اجرای سرور, نسخهٔ وب (+4 more)

### Community 111 - "bidi.ts"
Cohesion: 0.25
Nodes (7): isolated(), ENGLISH_RUN, hasPersianLetters(), isolateEnglish(), LRI, PDI, RLM

### Community 112 - "accounts/services.py"
Cohesion: 0.06
Nodes (25): SessionTokenAuthentication, SessionTokenAuthenticationScheme, Role, Meta, RoleAssignment, Meta, SessionRefreshToken, Meta (+17 more)

### Community 113 - "۵. قرارداد API (نسخهٔ ۱)"
Cohesion: 0.12
Nodes (17): Lexicomp — `/lexicomp/` (ویژگی `lexicomp`), Medscape — `/medscape/` (ویژگی `medscape`), UpToDate — `/uptodate/` (ویژگی `uptodate`), آزمون — `/quiz/` (ویژگی `quiz`؛ پرچم `QUIZ_API_ENABLED`), تغییر دادن API, داروها — `/drugs/` و `/atc/`, دانلود آفلاین — `/offline/`, درس‌نامه — `/lessons/` (ویژگی `lessons`) (+9 more)

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

### Community 122 - "scripts"
Cohesion: 0.18
Nodes (10): devDependencies, @types/react, typescript, scripts, android, build:web, ios, start (+2 more)

### Community 123 - "Command"
Cohesion: 0.12
Nodes (5): Command, _int(), _json_list(), _name_fa(), Migration

### Community 126 - "views_account.py"
Cohesion: 0.08
Nodes (33): OneTimeCode, Meta, SecurityAuditEvent, Meta, account_for_signup(), _hash(), _new_code(), OtpError (+25 more)

### Community 134 - "OfflinePackageCard.tsx"
Cohesion: 0.12
Nodes (38): DateInput(), DaysInput(), Field(), QuestionTitle(), OfflineDownloadButton(), OfflineSheet(), ERROR_TEXT, LOGO (+30 more)

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
Cohesion: 0.25
Nodes (8): ادمین Django (`/admin/`), درگاه پرداخت و کلیدهای فروش, دسترسی مهمان, ویژگی‌ها, پلن‌ها و محصول‌ها, کاربران, کنسول فروش (`/ops/`), ۱۱. کنسول‌های مدیریت

### Community 226 - "مستندات فارمنتا"
Cohesion: 0.50
Nodes (4): سندهای دیگر مخزن, فهرست, قرارداد نگهداری این مستندات, مستندات فارمنتا

### Community 230 - "فارمنتا (Pharmenta)"
Cohesion: 0.67
Nodes (3): شروع سریع, فارمنتا (Pharmenta), مستندات

## Knowledge Gaps
- **8 isolated node(s):** `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-splash-screen`, `react-dom`, `react-native-web` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1531 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **83 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `useLang` to `accounts/services.py`, `package.json`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.146) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `AppText()` (e.g. with `زبان، جهت و تم` and `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅`) actually correct?**
  _`AppText()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-splash-screen` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.03576437587657784 - nodes in this community are weakly interconnected._
- **Why does `UserSession` connect `accounts/services.py` to `billing/models.py`, `WebsiteAuthTests`, `console/views.py`, `useLang`, `اپ‌ها (`backend/apps/`)`, `guest.py`, `accounts/views.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`, `test_phone_auth.py`, `views_account.py`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `PlatformAPIError` (e.g. with `LoginView` and `OtpVerifyView`) actually correct?**
  _`PlatformAPIError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.02353998203054807 - nodes in this community are weakly interconnected._