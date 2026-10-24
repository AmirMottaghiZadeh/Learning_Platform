# Graph Report - Learning Platform  (2026-10-24)

## Corpus Check
- 488 files · ~390,658 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 32 file(s) not represented in the graph (top: (none) 11, .ttf 7, .woff2 4)

## Summary
- 4639 nodes · 13095 edges · 207 communities (120 shown, 87 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1201 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cdaa8189`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- api/types.ts
- django_db
- test_panel.py
- console/views.py
- react
- Post
- AppText
- views_public.py
- .reverse
- package.json
- flashcards/views.py
- calculators/reference_db.py
- billing/views.py
- website/models.py
- GatewayError
- ImportOpenfdaTests
- billing/tests.py
- Navigator.tsx
- decks.py
- data_quality_center/forms.py
- accounts/views.py
- calculators/tests.py
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
- Command
- store.ts
- Calculator
- SectionEditRequest
- clear_cache
- CalculatorDetailScreen.tsx
- offline/views.py
- common.tsx
- calculatorModel.ts
- Ingredient
- QuizApiTests
- sources.ts
- billing/tests.py
- VisitorDay
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
- progress/models.py
- Article
- test_phone_auth.py
- ۶. پیکربندی و متغیرهای محیطی
- drugs/admin.py
- 6. Lesson study topics (52)
- LiveScore.tsx
- throttling.py
- django_utils
- import_calculators.py
- logging
- ۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین
- uptodate/services.py
- dependencies
- medscape/tests.py
- ۲. راه‌اندازی محیط توسعه
- panel.js
- DownloadAndMachineTests
- guest.py
- HealthCheckTests
- SectionEdit
- lexicomp/views.py
- maintenance_urls.py
- ConsoleTestCase
- StudyTopicsCoverageTests
- LessonDetailScreen.tsx
- settings/base.py
- UptodateTests
- ReferenceDbTests
- website_extras.py
- clean_profile_boilerplate.py
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- porter.ts
- storage.py
- ReferenceImportCommand
- uptodate/views.py
- DrugPageTests
- offline/services.py
- offline/reader.ts
- docs/README.md
- views_drugs.py
- files.ts
- django_core_management_base
- site.js
- ApiTests
- WebsiteAuthTests
- downloader.web.ts
- dqc_extras.py
- Section
- ImportCalculatorsTests
- MedscapeApiTests
- Repository Guidelines
- QuizAccessTests
- Media
- GatewayPageTests
- CalculatorApiTests
- tasks.py
- ۵. قرارداد API (نسخهٔ ۱)
- lessons/serializers.py
- ۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی
- tsconfig.json
- ۱۲. سایت `pharmenta.ir` و پنل محتوا
- django_apps
- exceptions.py
- sw.js
- Command
- _card_back_fields
- Command
- pagination.py
- OfflinePackageCard.tsx
- django_conf
- Subscriber
- HostRoutingTests
- docker-start.sh
- billing/apps.py
- DateResult.tsx
- .claude/CLAUDE.md
- view.ts
- app.config.js
- .mcp.json
- ۳. بک‌اند (Django)
- PlanSerializer
- downloader.ts
- enqueue
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
- authentication.py
- ۸. دیپلوی
- ۱. معرفی و معماری
- ۱۰. مرجع سریع دستورها
- کنسول فروش (`/ops/`)
- FlashcardFact
- مستندات فارمنتا
- فارمنتا (Pharmenta)

## God Nodes (most connected - your core abstractions)
1. `useTheme()` - 163 edges
2. `AppText()` - 153 edges
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
- `فلش‌کارت — `/flashcards/` (ویژگی `flashcards`؛ پرچم `FLASHCARDS_API_ENABLED`)` --references--> `next_topic()`  [INFERRED]
  docs/05-api.md → backend/apps/flashcards/decks.py

## Import Cycles
- None detected.

## Communities (207 total, 87 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.03
Nodes (90): حساب و احراز هویت — `/auth/`, flashcardsApi, lessonsApi, offlineApi, quizApi, AtcCode, AtcGroup, AuthTokenResponse (+82 more)

### Community 1 - "django_db"
Cohesion: 0.02
Nodes (51): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+43 more)

### Community 2 - "test_panel.py"
Cohesion: 0.06
Nodes (18): PostRevision, Meta, StaffRole, Meta, SiteTestCase, AdminTests, AuthorTests, AuthTests (+10 more)

### Community 3 - "console/views.py"
Cohesion: 0.05
Nodes (69): DiscountForm, FeatureEditForm, Meta, FeatureForm, Meta, latin_digits(), parse_amount(), parse_jalali() (+61 more)

### Community 4 - "react"
Cohesion: 0.08
Nodes (63): calculatorsApi, meApi, MedscapeKind, ALPHABET, AlphabeticalArticleList(), buildOffsets(), groupAlphabetically(), Section (+55 more)

### Community 5 - "Post"
Cohesion: 0.06
Nodes (59): ActivityLog, Meta, Comment, Meta, ContactMessage, Meta, orders(), plans() (+51 more)

### Community 6 - "AppText"
Cohesion: 0.15
Nodes (74): قابلیت‌ها, قواعد کدنویسی اپ, ChecklistFlow(), HelpSheet(), LoadFailed(), AppText(), Button(), Card() (+66 more)

### Community 7 - "views_public.py"
Cohesion: 0.05
Nodes (57): site(), SiteMaintenanceMiddleware, DailyStat, Meta, SiteSettings, Meta, article(), breadcrumbs() (+49 more)

### Community 8 - ".reverse"
Cohesion: 0.04
Nodes (13): PhaseTwoAuthorizationTests, PhaseTwoSessionSecurityTests, AuthenticationSecurityTests, OnboardingTests, wrapper(), AccessTests, FeatureTests, PlanBuilderTests (+5 more)

### Community 9 - "package.json"
Cohesion: 0.04
Nodes (66): زبان، جهت و تم, App(), ThemedStatusBar(), devDependencies, @types/react, typescript, main, name (+58 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.11
Nodes (23): deck_slugs(), topic_meta(), BoxSummarySerializer, CategoryDecksSerializer, DeckAnswerSerializer, DeckOverviewSerializer, DeckProgressSerializer, LeitnerCardSerializer (+15 more)

### Community 11 - "calculators/reference_db.py"
Cohesion: 0.08
Nodes (15): export(), load(), Command, dumps(), expected_count(), loads(), record_counts(), rows() (+7 more)

### Community 12 - "billing/views.py"
Cohesion: 0.08
Nodes (29): is_guest(), CatalogSerializer, CheckoutSerializer, MyAccessSerializer, OrderSerializer, Meta, PurchaseRequestSerializer, QuoteSerializer (+21 more)

### Community 13 - "website/models.py"
Cohesion: 0.04
Nodes (35): Command, Command, Announcement, Meta, AppRelease, Meta, Category, Meta (+27 more)

### Community 14 - "GatewayError"
Cohesion: 0.06
Nodes (10): _post_json(), SepGateway, Verification, ZarinpalGateway, ZibalGateway, _fake_urlopen(), GatewayChoiceTests, SepTests (+2 more)

### Community 15 - "ImportOpenfdaTests"
Cohesion: 0.07
Nodes (6): AtcSupplementTests, DrugApiTests, ImportOpenfdaTests, LoadAtcReferenceTests, _make_source_db(), ModelTests

### Community 16 - "billing/tests.py"
Cohesion: 0.05
Nodes (18): Access, check_feature(), content_lock(), effective_features(), take(), free_plan(), grant(), _monthly() (+10 more)

### Community 17 - "Navigator.tsx"
Cohesion: 0.09
Nodes (43): ارتباط با API و کش, افزودن صفحهٔ تازه, دانلود آفلاین (`src/offline/`), ساختار `frontend/src/`, شروع اپ, ناوبری, وب‌اپ و PWA, پیکربندی اپ بومی (+35 more)

### Community 18 - "decks.py"
Cohesion: 0.14
Nodes (8): all_decks(), _carded_slugs(), next_topic(), progress_map(), TopicProgress, Meta, l2_slug_index(), ordered_topic_slugs()

### Community 20 - "accounts/views.py"
Cohesion: 0.04
Nodes (82): Role, Meta, RoleAssignment, Meta, SecurityAuditEvent, Meta, SessionRefreshToken, Meta (+74 more)

### Community 21 - "calculators/tests.py"
Cohesion: 0.07
Nodes (17): fix_questions(), fix_results(), fix_strings_fa(), renumber_from_one(), _stage_names_without_prefix(), _title_formula_as_result(), _with_choices(), _with_unit() (+9 more)

### Community 22 - "data_quality_center/views.py"
Cohesion: 0.11
Nodes (26): warning_count(), word_diff(), section_state(), _diffs(), discard(), history(), _login_key(), login_view() (+18 more)

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.09
Nodes (47): CalculatorErrorCheck, buildHeuristicSeeds(), cartesian(), classifyResultTone(), computeCalculator(), ComputeOptions, computeResultRanges(), computeTierBands() (+39 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.06
Nodes (41): record_quiz_answers(), BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, preview_selection(), sample_bank_questions(), _sample_rows(), best_score_pct_for_topic() (+33 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.06
Nodes (68): medscapeApi, MedscapeBlock, MedscapeSection, useBleedTop(), countMatches(), FindState, highlight(), ListMarker() (+60 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.10
Nodes (13): _categories_for_generics(), check_interactions(), close_all(), _conn(), _dir(), _exceptions_for_monographs(), is_available(), _names_for_generics() (+5 more)

### Community 28 - ".request_code"
Cohesion: 0.08
Nodes (22): CodeRuleTests, PhoneAuthTestCase, ResetTests, SignUpTests, SmsIrBackendTests, برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی, روش تبدیل پیشنهادها به کلمات کلیدی معتبر (+14 more)

### Community 29 - "progress/views.py"
Cohesion: 0.08
Nodes (30): Mistake, Meta, StudyPlanItem, Meta, complete_item(), skip_item(), DashboardSerializer, FocusRowSerializer (+22 more)

### Community 30 - "core/views.py"
Cohesion: 0.14
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 31 - "lessons/views.py"
Cohesion: 0.11
Nodes (18): _applies(), require_atc_content(), _require_content(), require_feature(), require_topic_content(), LessonDrugSerializer, _topic_lookup(), topics_for_chapter() (+10 more)

### Community 33 - "store.ts"
Cohesion: 0.13
Nodes (38): useOfflineBoot(), requestPersistence(), closeReaders(), bootOffline(), cancel(), currentUserId(), DATASETS, DatasetState (+30 more)

### Community 34 - "Calculator"
Cohesion: 0.11
Nodes (17): Calculator, Meta, CalculatorCategory, Meta, CalculatorTag, Meta, CalculatorCategorySerializer, Meta (+9 more)

### Community 35 - "SectionEditRequest"
Cohesion: 0.10
Nodes (21): ReviewEvent, Meta, SectionEditRequest, Meta, approve(), _clean(), _client_ip(), _close() (+13 more)

### Community 37 - "CalculatorDetailScreen.tsx"
Cohesion: 0.12
Nodes (34): describeInputs(), DateInput(), DaysInput(), Field(), QuestionTitle(), CardsFlow(), flowLayout, Choices() (+26 more)

### Community 38 - "offline/views.py"
Cohesion: 0.11
Nodes (17): build_matches_dataset(), LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer, PackageFileUrlSerializer, PackageManifestSerializer, PackageUrlsRequestSerializer (+9 more)

### Community 39 - "common.tsx"
Cohesion: 0.16
Nodes (25): bandFor(), Chip(), Collapse(), Extra, Extras(), fmt(), LEVEL_TONES, plain() (+17 more)

### Community 40 - "calculatorModel.ts"
Cohesion: 0.15
Nodes (23): CalculatorResultDef, StagingResult(), allWholeNumbers(), cache, classify(), classifyCalculator(), isNumeric(), LadderRung (+15 more)

### Community 41 - "Ingredient"
Cohesion: 0.04
Nodes (34): Command, Command, AtcCategory, Meta, AtcCode, Meta, Ingredient, Meta (+26 more)

### Community 43 - "sources.ts"
Cohesion: 0.08
Nodes (29): Coding Style & Naming Conventions, پایهٔ Django, lexicompApi, uptodateApi, LexicompDrug, LexicompInteraction, UptodateImage, cache (+21 more)

### Community 44 - "billing/tests.py"
Cohesion: 0.31
Nodes (8): _div(), fa_digits(), format_date(), _jal_cal(), _mod(), month_start(), to_gregorian(), to_jalali()

### Community 45 - "VisitorDay"
Cohesion: 0.24
Nodes (4): VisitorDay, Meta, UniqueVisitorTests, visit()

### Community 47 - "pack.py"
Cohesion: 0.07
Nodes (20): build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections(), _varints(), Command (+12 more)

### Community 48 - "drugs/serializers.py"
Cohesion: 0.10
Nodes (14): AtcCodeSerializer, Meta, IngredientDetailSerializer, Meta, IngredientListSerializer, Meta, LessonDrugSectionSerializer, Meta (+6 more)

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
Cohesion: 0.07
Nodes (26): due_card_count(), mark_drug_read(), topic_chapters(), topic_progress(), StudyPlan, ensure_today_items(), _flashcard_recall_for_slugs(), _flatten() (+18 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.16
Nodes (7): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label()

### Community 54 - "ResultCard"
Cohesion: 0.31
Nodes (23): Explain(), Hero(), Interpretation(), Ltr(), ResultCard(), showTierBar(), toneOf(), useShown() (+15 more)

### Community 55 - "data_quality_center/tests.py"
Cohesion: 0.26
Nodes (5): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), CheckTests

### Community 56 - "progress/models.py"
Cohesion: 0.05
Nodes (28): Migration, seed(), DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin, DailyStudy, Meta (+20 more)

### Community 57 - "Article"
Cohesion: 0.09
Nodes (15): Command, Command, Article, Meta, ArticleImage, ArticleDetailSerializer, Meta, ArticleImageSerializer (+7 more)

### Community 58 - "test_phone_auth.py"
Cohesion: 0.14
Nodes (6): EmailOrUsernameBackend, looks_like_phone(), normalize_phone(), PhoneField, NormalizePhoneTests, _find_user()

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.12
Nodes (16): HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت, دادهٔ مرجع (UpToDate و Lexicomp), دیتابیس، کش و آمادگی, سایت (+8 more)

### Community 60 - "drugs/admin.py"
Cohesion: 0.27
Nodes (5): AtcCategoryAdmin, AtcCodeAdmin, IngredientAdmin, IngredientProfileSectionAdmin, IngredientProfileSectionInline

### Community 61 - "6. Lesson study topics (52)"
Cohesion: 0.06
Nodes (34): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 6. Lesson study topics (52), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups (+26 more)

### Community 62 - "LiveScore.tsx"
Cohesion: 0.19
Nodes (19): CalculatorDetail, CalculatorQuestion, ResultProps, LIST_FROM, LiveScore(), useLiveScore(), FieldProps, FlowProps (+11 more)

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "django_utils"
Cohesion: 0.04
Nodes (52): SessionTokenAuthenticationScheme, LearnerProfile, UserSession, Meta, ProfileTests, EntitlementAdmin, FeatureAdmin, OrderAdmin (+44 more)

### Community 65 - "import_calculators.py"
Cohesion: 0.20
Nodes (9): Command, _error_checks_for(), _formula_strings_fa(), _import_categories(), _import_tags(), _questions_for(), _references_for(), _results_for() (+1 more)

### Community 66 - "logging"
Cohesion: 0.12
Nodes (3): PlatformTask, retry_delay_seconds(), configure_runtime()

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (24): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+16 more)

### Community 68 - "uptodate/services.py"
Cohesion: 0.10
Nodes (19): Command, article_from_row(), _dir(), get_image(), get_topic(), is_available(), mysql_config(), _mysql_conn() (+11 more)

### Community 69 - "dependencies"
Cohesion: 0.06
Nodes (33): dependencies, axios, expo, expo-crypto, expo-file-system, expo-font, @expo-google-fonts/vazirmatn, expo-linear-gradient (+25 more)

### Community 70 - "medscape/tests.py"
Cohesion: 0.27
Nodes (5): _disease_record(), _guideline_record(), ImportMedscapeArticlesTests, _write_diseases_tree(), _write_guidelines()

### Community 71 - "۲. راه‌اندازی محیط توسعه"
Cohesion: 0.09
Nodes (22): اجرای کامل با Docker, اندروید و iOS, اپ (Expo), بک‌اند, تست بستهٔ آفلاین بدون باکت, تست و بررسی, روال کار با مخزن, ساخت دیتابیس و اجرای سرور (+14 more)

### Community 72 - "panel.js"
Cohesion: 0.16
Nodes (14): buildEditor(), align(), block(), exec(), sync(), toggleSource(), wrapBlock(), filterNav() (+6 more)

### Community 73 - "DownloadAndMachineTests"
Cohesion: 0.11
Nodes (4): CommentTests, DownloadAndMachineTests, make_post(), PostVisibilityTests

### Community 74 - "guest.py"
Cohesion: 0.08
Nodes (14): BillingConfig, current(), gateway_spec(), access(), create_guest(), delete_guests(), end_guest_sessions(), guests() (+6 more)

### Community 75 - "HealthCheckTests"
Cohesion: 0.15
Nodes (3): HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests

### Community 76 - "SectionEdit"
Cohesion: 0.15
Nodes (7): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin, SectionEdit, Meta, مرکز کیفیت داده (`/ops/data-quality/`)

### Community 77 - "lexicomp/views.py"
Cohesion: 0.35
Nodes (6): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, DrugSearchView, InteractionCheckView, _require_available()

### Community 79 - "ConsoleTestCase"
Cohesion: 0.15
Nodes (3): ConsoleTestCase, DraftAndSubmitTests, ReviewTests

### Community 81 - "LessonDetailScreen.tsx"
Cohesion: 0.33
Nodes (10): LessonSection, joinOpenParens(), LessonBlock, LessonLine, parenDepth(), parseLessonText(), sectionText(), splitIssues() (+2 more)

### Community 82 - "settings/base.py"
Cohesion: 0.11
Nodes (3): build.sh script, DJANGO_SETTINGS_MODULE, release.sh script

### Community 85 - "website_extras.py"
Cohesion: 0.15
Nodes (8): atc_groups(), feature_icon(), nav_on(), oneline(), person(), split_highlight(), split_lines(), آنچه کد انجام می‌دهد

### Community 86 - "clean_profile_boilerplate.py"
Cohesion: 0.23
Nodes (8): clean_text(), Command, is_hypersensitivity_boilerplate(), is_hypersensitivity_boilerplate_en(), is_negative_indication_en(), is_negative_indication_fa(), is_null_placeholder(), _normalize()

### Community 87 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.10
Nodes (14): validate_production_broker(), validate_production_cache(), validate_production_secret_key(), CorsPreflightTests, ProductionSecretKeyTests, PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa, 🎉 بازنویسی کامل شد, فاز ۰.۵ — حذف زیرساخت رهاشده ✅ (+6 more)

### Community 88 - "porter.ts"
Cohesion: 0.23
Nodes (8): firstRule(), isVowelLetter(), porterStem(), Rule, STEP2, STEP3, STEP4, Word

### Community 89 - "storage.py"
Cohesion: 0.10
Nodes (15): Command, cors_rule(), _request(), clear_cache(), file_urls(), is_configured(), latest_manifest(), local_dir() (+7 more)

### Community 90 - "ReferenceImportCommand"
Cohesion: 0.14
Nodes (4): Command, ReferenceImportCommand, open_for_import(), Command

### Community 91 - "uptodate/views.py"
Cohesion: 0.30
Nodes (8): UptodateArticleSerializer, UptodateImageSerializer, UptodateSearchResultSerializer, UptodateTopicSerializer, ImageDetailView, _require_available(), TopicDetailView, TopicSearchView

### Community 92 - "DrugPageTests"
Cohesion: 0.12
Nodes (3): DrugPageTests, SiteIdentityTests, structured()

### Community 93 - "offline/services.py"
Cohesion: 0.24
Nodes (7): has_paid_plan_with(), is_entitled(), is_guest(), issue_license(), license_days(), LicenseError, _wrap_for()

### Community 94 - "offline/reader.ts"
Cohesion: 0.22
Nodes (10): OfflineDataset, OfflineManifest, keyring, openRecord(), openRecordBase64(), PackageKey, sealed(), open (+2 more)

### Community 96 - "views_drugs.py"
Cohesion: 0.07
Nodes (14): fa(), Migration, Migration, _build_catalog(), _drop_title(), english_name(), fa_key(), _group_code() (+6 more)

### Community 97 - "files.ts"
Cohesion: 0.29
Nodes (12): buildDir(), closeHandles(), ensureBuildDir(), handles, partFile(), partPath(), partSize(), readRange() (+4 more)

### Community 98 - "django_core_management_base"
Cohesion: 0.11
Nodes (5): Command, ensure_title_search_index(), _has_title_search_index(), MysqlTitleIndexTests, MysqlTitleSearchTests

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

### Community 100 - "ApiTests"
Cohesion: 0.09
Nodes (6): derive_key(), new_build_id(), ApiTests, BuildTests, DownloadHostTests, PackFormatTests

### Community 102 - "downloader.web.ts"
Cohesion: 0.20
Nodes (9): downloader, DownloadEvents, newWorker(), PartJob, PartRef, Run, runFor(), runs (+1 more)

### Community 103 - "dqc_extras.py"
Cohesion: 0.13
Nodes (16): ago(), get_item(), guest_access_on(), initial(), jdate(), num(), toman(), action_label() (+8 more)

### Community 105 - "ImportCalculatorsTests"
Cohesion: 0.32
Nodes (3): _build_sqlite(), ImportCalculatorsTests, _one_calculator()

### Community 107 - "Repository Guidelines"
Cohesion: 0.29
Nodes (6): Build, Test, and Development Commands, Commit & Pull Request Guidelines, Project Structure & Module Organization, Repository Guidelines, Security & Configuration Tips, Testing Guidelines

### Community 109 - "Media"
Cohesion: 0.03
Nodes (31): Media, Meta, AnnouncementForm, Meta, CategoryForm, Meta, MediaMetaForm, Meta (+23 more)

### Community 112 - "tasks.py"
Cohesion: 0.25
Nodes (3): password_reset_url_for_user(), send_password_reset_email(), send_password_reset_email_task()

### Community 113 - "۵. قرارداد API (نسخهٔ ۱)"
Cohesion: 0.11
Nodes (18): Lexicomp — `/lexicomp/` (ویژگی `lexicomp`), Medscape — `/medscape/` (ویژگی `medscape`), UpToDate — `/uptodate/` (ویژگی `uptodate`), آزمون — `/quiz/` (ویژگی `quiz`؛ پرچم `QUIZ_API_ENABLED`), تغییر دادن API, داروها — `/drugs/` و `/atc/`, دانلود آفلاین — `/offline/`, درس‌نامه — `/lessons/` (ویژگی `lessons`) (+10 more)

### Community 114 - "lessons/serializers.py"
Cohesion: 0.22
Nodes (6): AtcGroupSerializer, ChapterDrugSerializer, ChapterProgressSerializer, DrugSearchChapterSerializer, SubgroupSerializer, TopicSerializer

### Community 115 - "۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی"
Cohesion: 0.12
Nodes (17): اطلاعات غیرمحرمانه‌ای که باید جایی ثبت باشد, بازیابی, بکاپ و بازیابی, حساب‌های سرویس, رازها و چیزهایی که باید امن نگه داشته شوند, رازهای فنی, شاخص‌هایی که مرتب دیده شوند, عیب‌یابی (+9 more)

### Community 116 - "tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, paths, strict, extends, include, expo/tsconfig.base

### Community 117 - "۱۲. سایت `pharmenta.ir` و پنل محتوا"
Cohesion: 0.14
Nodes (14): not_found(), آمار بازدید, حساب و خرید روی سایت, دارونامهٔ عمومی (`/drugs/`), رسانه, سئو, ساختار کد, صفحه‌های عمومی (+6 more)

### Community 119 - "exceptions.py"
Cohesion: 0.36
Nodes (4): _first_message(), _message_from_data(), _normalize_code(), platform_exception_handler()

### Community 120 - "sw.js"
Cohesion: 0.38
Nodes (4): inScope(), referencedFiles(), SCOPE, storeShell()

### Community 123 - "Command"
Cohesion: 0.12
Nodes (5): Command, _int(), _json_list(), _name_fa(), Migration

### Community 125 - "OfflinePackageCard.tsx"
Cohesion: 0.24
Nodes (13): OfflineDownloadButton(), OfflineSheet(), ERROR_TEXT, LOGO, NAME, OfflinePackageCard(), PHASE_TEXT, SUPPORTS_BACKGROUND (+5 more)

### Community 126 - "django_conf"
Cohesion: 0.05
Nodes (40): OneTimeCode, Meta, account_for_signup(), _hash(), _new_code(), OtpError, request_code(), user_for_phone() (+32 more)

### Community 127 - "Subscriber"
Cohesion: 0.25
Nodes (3): Subscriber, Meta, FormsTests

### Community 132 - "DateResult.tsx"
Cohesion: 0.48
Nodes (6): hasPersian(), Rows(), DateResult(), useDateFormat(), parseAge(), parseDateText()

### Community 134 - "view.ts"
Cohesion: 0.17
Nodes (22): OfflinePackageInfo, InstalledPackage, licenseExpiresAt(), OfflineErrorCode, PendingPackage, formatDay(), PackagePhase, PackageView (+14 more)

### Community 182 - "۳. بک‌اند (Django)"
Cohesion: 0.12
Nodes (13): RequestIdMiddleware, SiteHostMiddleware, UpToDate و Lexicomp, افزودن یک قابلیت فروشی تازه, بستهٔ آفلاین (`apps.offline`), زنجیرهٔ middleware, صورتحساب و دسترسی (`apps.billing`), قواعد مشترک API (+5 more)

### Community 183 - "PlanSerializer"
Cohesion: 0.40
Nodes (3): PlanFeatureItemSerializer, PlanSerializer, Meta

### Community 184 - "downloader.ts"
Cohesion: 0.20
Nodes (6): downloader, DownloadEvents, PartJob, PartRef, tasks, @kesha-antonov/react-native-background-downloader

### Community 196 - "authentication.py"
Cohesion: 0.22
Nodes (6): SessionTokenAuthentication, احراز هویت و حساب, ثبت‌نام و ورود, رمز عبور, نشست و توکن, نقش‌ها و رویدادهای امنیتی

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

### Community 217 - "FlashcardFact"
Cohesion: 0.20
Nodes (5): FlashcardFactAdmin, LeitnerCardAdmin, FlashcardFact, Meta, Command

### Community 226 - "مستندات فارمنتا"
Cohesion: 0.50
Nodes (4): سندهای دیگر مخزن, فهرست, قرارداد نگهداری این مستندات, مستندات فارمنتا

### Community 230 - "فارمنتا (Pharmenta)"
Cohesion: 0.67
Nodes (3): شروع سریع, فارمنتا (Pharmenta), مستندات

## Knowledge Gaps
- **8 isolated node(s):** `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-splash-screen`, `react-dom`, `react-native-web` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1512 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **87 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `AppText` to `django_utils`, `Navigator.tsx`, `package.json`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.151) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `PlatformAPIError` (e.g. with `LoginView` and `OtpVerifyView`) actually correct?**
  _`PlatformAPIError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-splash-screen` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.03393939393939394 - nodes in this community are weakly interconnected._
- **Why does `UserSession` connect `django_utils` to `console/views.py`, `authentication.py`, `WebsiteAuthTests`, `AppText`, `.reverse`, `guest.py`, `accounts/views.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.149) - this node is a cross-community bridge._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.022123893805309734 - nodes in this community are weakly interconnected._
- **Why does `اپ‌ها (`backend/apps/`)` connect `django_utils` to `Calculator`, `SectionEditRequest`, `console/views.py`, `test_panel.py`, `views_public.py`, `Ingredient`, `SectionEdit`, `Media`, `website/models.py`, `decks.py`, `accounts/views.py`, `۳. بک‌اند (Django)`, `quiz/views.py`, `progress/models.py`, `FlashcardFact`, `django_conf`, `Article`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._