# Graph Report - Learning Platform  (2026-10-25)

## Corpus Check
- 519 files · ~416,775 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 32 file(s) not represented in the graph (top: (none) 11, .ttf 7, .woff2 4)

## Summary
- 5053 nodes · 14328 edges · 215 communities (128 shown, 87 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1278 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8e2a024d`
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
- accounts/serializers.py
- PlatformAPIError
- LeitnerCard
- SepGateway
- tests_console.py
- billing/services.py
- Page
- IngredientProfileSection
- useLang
- accounts/views.py
- fix_results
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
- ApiTests
- store.ts
- Calculator
- SectionEditRequest
- re
- QuestionField.tsx
- offline/views.py
- SiteTestCase
- search_topics
- DrugPageTests
- QuizApiTests
- errata.py
- progress/views.py
- release.mjs
- PurchaseFlowTests
- json
- drugs/serializers.py
- TopicDeckTests
- LessonTaxonomyTests
- expo
- planning.py
- import_medscape_articles.py
- ResultCard
- data_quality_center/tests.py
- ImportOpenfdaTests
- django_db
- bootstrap_superuser.py
- ۶. پیکربندی و متغیرهای محیطی
- offline/views.py
- files.web.ts
- import_calculators.py
- throttling.py
- Article
- WebsiteAuthTests
- billing/tests.py
- ۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین
- migrate_uptodate_to_mysql.py
- dependencies
- medscape/tests.py
- crypto.web.ts
- panel.js
- website/models.py
- اپ‌ها (`backend/apps/`)
- logging
- SectionEdit
- views_account.py
- maintenance_urls.py
- ConsoleTestCase
- common.tsx
- calculatorModel.ts
- config.py
- UptodateTests
- OfflinePackageCard.tsx
- dqc_extras.py
- clean_profile_boilerplate.py
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- porter.ts
- billing/views.py
- medscape/views.py
- offline/services.py
- Ingredient
- Pharmexa — custom icon prompts
- uptodateLocal.ts
- docs/README.md
- 6. Lesson study topics (52)
- files.ts
- ReferenceImportCommand
- site.js
- VisitorDay
- Command
- downloader.web.ts
- ۲. راه‌اندازی محیط توسعه
- offline/reader.ts
- ImportCalculatorsTests
- ReferenceDbTests
- Repository Guidelines
- sources.ts
- calculatorLive.ts
- QuizSession
- StandardizeUnitsTests
- accounts/services.py
- ۵. قرارداد API (نسخهٔ ۱)
- ZibalGateway
- ۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی
- tsconfig.json
- MedscapeApiTests
- django_apps
- App.tsx
- sw.js
- Command
- require_feature
- ReviewTests
- pagination.py
- _SectionCard
- sms.py
- BuildTests
- ۴. اپ (Expo — اندروید، iOS و وب)
- docker-start.sh
- billing/apps.py
- CalculatorApiTests
- .claude/CLAUDE.md
- StudyTopicsCoverageTests
- app.config.js
- .mcp.json
- scripts
- downloader.ts
- ۱۲. سایت `pharmenta.ir` و پنل محتوا
- RegisterSerializer
- lessons/serializers.py
- QuizQuestion
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
- .post
- PlanSerializer
- 0004_clear_rule_based_facts.py
- authentication.py
- DateResult.tsx
- ۸. دیپلوی
- bidi.ts
- Command
- 0004_remove_misfit_atc_codes.py
- 0007_clear_rule_based_bank.py
- devDependencies
- ۱. معرفی و معماری
- ۱۰. مرجع سریع دستورها
- کنسول فروش (`/ops/`)
- مستندات فارمنتا
- فارمنتا (Pharmenta)

## God Nodes (most connected - your core abstractions)
1. `useTheme()` - 187 edges
2. `AppText()` - 183 edges
3. `useLang()` - 169 edges
4. `react` - 85 edges
5. `PlatformAPIError` - 83 edges
6. `Ingredient` - 77 edges
7. `react-native` - 74 edges
8. `useNav` - 65 edges
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
- `دسته‌ها` --references--> `next_topic()`  [INFERRED]
  docs/05-api.md → backend/apps/flashcards/decks.py

## Import Cycles
- None detected.

## Communities (215 total, 87 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.03
Nodes (101): حساب و احراز هویت — `/auth/`, lessonsApi, offlineApi, quizApi, AtcCode, AtcGroup, AuthTokenResponse, BoxCard (+93 more)

### Community 1 - "django_db"
Cohesion: 0.04
Nodes (30): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+22 more)

### Community 2 - "test_panel.py"
Cohesion: 0.06
Nodes (17): PostRevision, Meta, StaffRole, Meta, AdminTests, AuthorTests, AuthTests, CommercePagesTests (+9 more)

### Community 3 - "console/views.py"
Cohesion: 0.05
Nodes (74): DiscountForm, FeatureEditForm, Meta, FeatureForm, Meta, latin_digits(), parse_amount(), parse_jalali() (+66 more)

### Community 4 - "react"
Cohesion: 0.08
Nodes (68): calculatorsApi, meApi, medscapeApi, MedscapeKind, StudyPlanItem, ALPHABET, AlphabeticalArticleList(), buildOffsets() (+60 more)

### Community 5 - "Post"
Cohesion: 0.06
Nodes (61): ActivityLog, Meta, Comment, Meta, ContactMessage, Meta, Media, Meta (+53 more)

### Community 6 - "useTheme"
Cohesion: 0.11
Nodes (98): قابلیت‌ها, ساختار `frontend/src/`, قواعد کدنویسی اپ, flashcardsApi, AppShell(), AuthLayout(), BottomNav(), ChecklistFlow() (+90 more)

### Community 7 - "views_public.py"
Cohesion: 0.05
Nodes (56): site(), SiteMaintenanceMiddleware, DailyStat, Meta, SiteSettings, Meta, article(), breadcrumbs() (+48 more)

### Community 8 - ".reverse"
Cohesion: 0.05
Nodes (12): AuthenticationSecurityTests, OnboardingTests, wrapper(), GatewayPageTests, PlanBuilderTests, UsersPageTests, AccessTests, render_links() (+4 more)

### Community 9 - "package.json"
Cohesion: 0.04
Nodes (70): زبان، جهت و تم, شروع اپ, App(), Gate(), ThemedStatusBar(), main, name, private (+62 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.06
Nodes (39): deck_cards(), next_topic(), progress_map(), topic_meta(), TopicProgress, Meta, BoxCardSerializer, BoxReviewSerializer (+31 more)

### Community 11 - "accounts/serializers.py"
Cohesion: 0.09
Nodes (13): OneTimeCode, Meta, AuthTokenResponseSerializer, OnboardingSerializer, OtpRequestResponseSerializer, OtpVerifySerializer, PasswordResetResponseSerializer, active_role_keys() (+5 more)

### Community 12 - "PlatformAPIError"
Cohesion: 0.09
Nodes (18): _first_message(), _message_from_data(), _normalize_code(), platform_exception_handler(), PlatformAPIError, UptodateArticleSerializer, UptodateImageSerializer, UptodateSearchResultSerializer (+10 more)

### Community 13 - "LeitnerCard"
Cohesion: 0.08
Nodes (17): add_miss(), add_quiz_miss(), daily_minutes(), drawer_cards(), _exam_cap_days(), outcome(), overview(), previews() (+9 more)

### Community 14 - "SepGateway"
Cohesion: 0.08
Nodes (7): FakeGateway, SepGateway, Verification, ZarinpalGateway, _fake_urlopen(), SepTests, ZarinpalTests

### Community 15 - "tests_console.py"
Cohesion: 0.08
Nodes (17): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, DiscountCode, Meta (+9 more)

### Community 16 - "billing/services.py"
Cohesion: 0.06
Nodes (20): UsageRecord, Meta, Access, check_feature(), content_lock(), effective_features(), take(), free_plan() (+12 more)

### Community 17 - "Page"
Cohesion: 0.06
Nodes (8): Post, Meta, clean_html(), _Cleaner, plain_text(), safe_url(), _Text, SanitizeTests

### Community 18 - "IngredientProfileSection"
Cohesion: 0.07
Nodes (21): AtcCategoryAdmin, AtcCodeAdmin, IngredientAdmin, IngredientProfileSectionAdmin, IngredientProfileSectionInline, IngredientProfileSection, Meta, make_drug() (+13 more)

### Community 19 - "useLang"
Cohesion: 0.09
Nodes (53): DateInput(), DaysInput(), Field(), QuestionTitle(), CategoryPicker(), Chip(), ChipRow(), DateField() (+45 more)

### Community 20 - "accounts/views.py"
Cohesion: 0.05
Nodes (48): CanManagePlatformRoles, CanViewSecurityAudit, HasPlatformPermission, HasRecentStepUp, LearnerProfileSerializer, Meta, LoginSerializer, OtpRequestSerializer (+40 more)

### Community 21 - "fix_results"
Cohesion: 0.12
Nodes (8): fix_results(), fix_strings_fa(), renumber_from_one(), apply_fixes(), Migration, apply_fixes(), Migration, FormulaErrataTests

### Community 22 - "data_quality_center/views.py"
Cohesion: 0.12
Nodes (25): warning_count(), section_state(), _diffs(), discard(), history(), _login_key(), login_view(), logout_view() (+17 more)

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.08
Nodes (51): LiveScore(), useLiveScore(), buildHeuristicSeeds(), cartesian(), checkErrors(), classifyResultTone(), computeCalculator(), ComputeOptions (+43 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.18
Nodes (17): FieldBreakdownSerializer, FieldPreviewSerializer, MissedQuestionSerializer, QuizAnswerInSerializer, QuizAnswerOutSerializer, QuizOverviewSerializer, QuizPreviewSerializer, QuizResultSerializer (+9 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.05
Nodes (89): MedscapeBlock, MedscapeSection, TopInset, useBleedTop(), countMatches(), FindState, highlight(), ListMarker() (+81 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.08
Nodes (19): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, _categories_for_generics(), check_interactions(), close_all(), _conn(), _dir() (+11 more)

### Community 28 - ".request_code"
Cohesion: 0.08
Nodes (21): CodeRuleTests, PhoneAuthTestCase, ResetTests, SignUpTests, برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی, روش تبدیل پیشنهادها به کلمات کلیدی معتبر, ساخت Analytics از ابتدا (+13 more)

### Community 29 - "progress/tests.py"
Cohesion: 0.06
Nodes (16): Migration, seed(), DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin, LearnerProgress, bump_mistake() (+8 more)

### Community 30 - "core/views.py"
Cohesion: 0.14
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 31 - "lessons/views.py"
Cohesion: 0.15
Nodes (13): LessonDrugSerializer, _topic_lookup(), topics_for_chapter(), ChapterProgressUpdateSerializer, ChapterSerializer, DrugSearchResultSerializer, LessonGroupSerializer, _chapter_not_found() (+5 more)

### Community 33 - "store.ts"
Cohesion: 0.14
Nodes (35): requestPersistence(), closeReaders(), bootOffline(), cancel(), currentUserId(), DatasetState, download(), empty() (+27 more)

### Community 34 - "Calculator"
Cohesion: 0.14
Nodes (15): Calculator, Meta, CalculatorCategory, Meta, CalculatorCategorySerializer, Meta, CalculatorDetailSerializer, Meta (+7 more)

### Community 35 - "SectionEditRequest"
Cohesion: 0.10
Nodes (21): ReviewEvent, Meta, SectionEditRequest, Meta, approve(), _clean(), _client_ip(), _close() (+13 more)

### Community 36 - "re"
Cohesion: 0.14
Nodes (13): _fa_keys_standardized(), _stage_names_without_prefix(), _title_formula_as_result(), _adjective(), _chain(), _key(), _latin_quantity(), _spelling() (+5 more)

### Community 37 - "QuestionField.tsx"
Cohesion: 0.19
Nodes (18): CardsFlow(), flowLayout, Choices(), FieldVariant, isBinaryQuestion(), label(), Numeric(), QuestionField() (+10 more)

### Community 38 - "offline/views.py"
Cohesion: 0.09
Nodes (15): Command, cors_rule(), _request(), clear_cache(), file_urls(), is_configured(), latest_manifest(), local_dir() (+7 more)

### Community 39 - "SiteTestCase"
Cohesion: 0.04
Nodes (18): Subscriber, Meta, version_code(), ReleaseForm, Meta, JalaliDateTimeField, SiteTestCase, CommentTests (+10 more)

### Community 40 - "search_topics"
Cohesion: 0.12
Nodes (18): article_from_row(), _dir(), get_image(), get_topic(), is_available(), _mysql_conn(), search_topics(), _search_words() (+10 more)

### Community 41 - "DrugPageTests"
Cohesion: 0.10
Nodes (4): DrugPageTests, SeedSeoContentTests, SiteIdentityTests, structured()

### Community 42 - "QuizApiTests"
Cohesion: 0.10
Nodes (3): QuizAccessTests, QuizApiTests, QuizLockedTests

### Community 43 - "errata.py"
Cohesion: 0.13
Nodes (8): fix_questions(), _with_choices(), _with_unit(), apply_fixes(), Migration, ChoiceErrataTests, FaUnitsTests, QuestionUnitTests

### Community 44 - "progress/views.py"
Cohesion: 0.07
Nodes (36): topic_progress(), Mistake, Meta, dashboard(), _display_name(), _leitner_focus_row(), _mastery_pct(), _next_chapter() (+28 more)

### Community 45 - "release.mjs"
Cohesion: 0.09
Nodes (15): appJson, at, dryRun, file(), frontend, [kind, ...flags], lock, [major, minor, patch] (+7 more)

### Community 46 - "PurchaseFlowTests"
Cohesion: 0.09
Nodes (3): clear_cache(), GatewayChoiceTests, PurchaseFlowTests

### Community 47 - "json"
Cohesion: 0.06
Nodes (23): build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections(), _varints(), Command (+15 more)

### Community 48 - "drugs/serializers.py"
Cohesion: 0.10
Nodes (14): AtcCodeSerializer, Meta, IngredientDetailSerializer, Meta, IngredientListSerializer, Meta, LessonDrugSectionSerializer, Meta (+6 more)

### Community 50 - "LessonTaxonomyTests"
Cohesion: 0.07
Nodes (8): ChapterProgress, Meta, ReadDrug, Meta, DrugSearchTests, _ingredient(), LessonTaxonomyFallbackTests, LessonTaxonomyTests

### Community 51 - "expo"
Cohesion: 0.06
Nodes (32): backgroundColor, foregroundImage, adaptiveIcon, allowBackup, blockedPermissions, package, projectId, typedRoutes (+24 more)

### Community 52 - "planning.py"
Cohesion: 0.04
Nodes (43): LeitnerCardQuerySet, due_card_count(), mark_drug_read(), DailyStudy, Meta, StudyPlan, StudyPlanItem, Meta (+35 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.16
Nodes (7): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label()

### Community 54 - "ResultCard"
Cohesion: 0.34
Nodes (22): Explain(), Hero(), Interpretation(), ResultCard(), ResultProps, showTierBar(), toneOf(), useShown() (+14 more)

### Community 55 - "data_quality_center/tests.py"
Cohesion: 0.24
Nodes (6): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), word_diff(), CheckTests

### Community 56 - "ImportOpenfdaTests"
Cohesion: 0.06
Nodes (8): AtcSupplementTests, CleanBoilerplateInPipelineTests, DrugApiTests, ImportOpenfdaTests, LoadAtcReferenceTests, _make_source_db(), ModelTests, StandardizePipelineUnitsTests

### Community 57 - "django_db"
Cohesion: 0.02
Nodes (50): Migration, Migration, Migration, Migration, Migration, Migration, export(), load() (+42 more)

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.12
Nodes (16): HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت, دادهٔ مرجع (UpToDate و Lexicomp), دیتابیس، کش و آمادگی, سایت (+8 more)

### Community 60 - "offline/views.py"
Cohesion: 0.11
Nodes (17): build_matches_dataset(), LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer, PackageFileUrlSerializer, PackageManifestSerializer, PackageUrlsRequestSerializer (+9 more)

### Community 61 - "files.web.ts"
Cohesion: 0.19
Nodes (9): file(), forget(), partSize(), readRange(), removeBuild(), removeOtherBuilds(), removePart(), snapshots (+1 more)

### Community 62 - "import_calculators.py"
Cohesion: 0.14
Nodes (12): standardize_fa_units(), Command, _error_checks_for(), _formula_strings_fa(), _import_categories(), _import_tags(), _questions_for(), _references_for() (+4 more)

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "Article"
Cohesion: 0.11
Nodes (8): Command, Command, Command, Article, Meta, export(), load(), _map_images()

### Community 66 - "billing/tests.py"
Cohesion: 0.13
Nodes (12): _div(), format_date(), _jal_cal(), _mod(), month_start(), to_gregorian(), to_jalali(), PaymentGateway (+4 more)

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (26): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+18 more)

### Community 68 - "migrate_uptodate_to_mysql.py"
Cohesion: 0.09
Nodes (6): Command, Command, ensure_title_search_index(), _has_title_search_index(), mysql_config(), MysqlTitleIndexTests

### Community 69 - "dependencies"
Cohesion: 0.07
Nodes (28): dependencies, axios, expo, expo-build-properties, expo-constants, expo-crypto, expo-file-system, expo-font (+20 more)

### Community 70 - "medscape/tests.py"
Cohesion: 0.27
Nodes (5): _disease_record(), _guideline_record(), ImportMedscapeArticlesTests, _write_diseases_tree(), _write_guidelines()

### Community 71 - "crypto.web.ts"
Cohesion: 0.21
Nodes (10): اجرای کامل با Docker, OfflineLicense, db(), idb(), keyring, openRecord(), openRecordBase64(), PackageKey (+2 more)

### Community 72 - "panel.js"
Cohesion: 0.16
Nodes (14): buildEditor(), align(), block(), exec(), sync(), toggleSource(), wrapBlock(), filterNav() (+6 more)

### Community 73 - "website/models.py"
Cohesion: 0.03
Nodes (54): Command, Command, Migration, Migration, Announcement, Meta, AppRelease, Meta (+46 more)

### Community 74 - "اپ‌ها (`backend/apps/`)"
Cohesion: 0.06
Nodes (13): AdminAction, Meta, BillingSettings, Meta, GuestAccount, GuestAccessTests, GuestConsoleTests, CalculatorTag (+5 more)

### Community 75 - "logging"
Cohesion: 0.06
Nodes (11): password_reset_url_for_user(), send_password_reset_email(), send_password_reset_emails_for_email(), send_password_reset_email_task(), PlatformTask, retry_delay_seconds(), get_request_id(), JsonFormatter (+3 more)

### Community 76 - "SectionEdit"
Cohesion: 0.15
Nodes (7): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin, SectionEdit, Meta, مرکز کیفیت داده (`/ops/data-quality/`)

### Community 77 - "views_account.py"
Cohesion: 0.06
Nodes (26): EmailOrUsernameBackend, LearnerProfile, account_for_signup(), InvalidPhone, looks_like_phone(), normalize_phone(), PhoneField, NormalizePhoneTests (+18 more)

### Community 80 - "common.tsx"
Cohesion: 0.16
Nodes (25): bandFor(), Chip(), Collapse(), Extra, Extras(), fmt(), LEVEL_TONES, plain() (+17 more)

### Community 81 - "calculatorModel.ts"
Cohesion: 0.14
Nodes (24): CalculatorResultDef, StagingResult(), ComputedResult, allWholeNumbers(), cache, classify(), classifyCalculator(), isNumeric() (+16 more)

### Community 82 - "config.py"
Cohesion: 0.11
Nodes (12): BillingConfig, gateway_spec(), _gateways(), GatewaySpec, _load(), row(), _settings_changed(), access() (+4 more)

### Community 84 - "OfflinePackageCard.tsx"
Cohesion: 0.18
Nodes (21): OfflineDownloadButton(), OfflineSheet(), ERROR_TEXT, LOGO, NAME, OfflinePackageCard(), PHASE_TEXT, SUPPORTS_BACKGROUND (+13 more)

### Community 85 - "dqc_extras.py"
Cohesion: 0.12
Nodes (17): ago(), fa(), get_item(), guest_access_on(), initial(), jdate(), num(), toman() (+9 more)

### Community 86 - "clean_profile_boilerplate.py"
Cohesion: 0.14
Nodes (13): clean_text(), Command, cleaned(), is_hypersensitivity_boilerplate(), is_hypersensitivity_boilerplate_en(), is_negative_indication_en(), is_negative_indication_fa(), is_null_placeholder() (+5 more)

### Community 87 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.07
Nodes (17): build.sh script, validate_production_broker(), validate_production_cache(), validate_production_secret_key(), CorsPreflightTests, ProductionSecretKeyTests, DJANGO_SETTINGS_MODULE, release.sh script (+9 more)

### Community 88 - "porter.ts"
Cohesion: 0.23
Nodes (8): firstRule(), isVowelLetter(), porterStem(), Rule, STEP2, STEP3, STEP4, Word

### Community 89 - "billing/views.py"
Cohesion: 0.06
Nodes (43): current(), enabled_gateways(), GatewayError, get_gateway(), _post_json(), start_payment(), is_guest(), Order (+35 more)

### Community 90 - "medscape/views.py"
Cohesion: 0.14
Nodes (11): ArticleImage, ArticleDetailSerializer, Meta, ArticleImageSerializer, Meta, ArticleListSerializer, Meta, ArticleDetailView (+3 more)

### Community 91 - "offline/services.py"
Cohesion: 0.22
Nodes (8): active_entitlements(), has_paid_plan_with(), is_entitled(), is_guest(), issue_license(), license_days(), LicenseError, _wrap_for()

### Community 92 - "Ingredient"
Cohesion: 0.03
Nodes (42): AtcCategory, Meta, Ingredient, Meta, FlashcardFactAdmin, LeitnerCardAdmin, all_decks(), _carded_slugs() (+34 more)

### Community 93 - "Pharmexa — custom icon prompts"
Cohesion: 0.15
Nodes (12): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups, 9. App identity (optional) (+4 more)

### Community 94 - "uptodateLocal.ts"
Cohesion: 0.13
Nodes (16): Coding Style & Naming Conventions, پایهٔ Django, UptodateImage, Prepared, queryTerm(), Locator, cache, cutSnippet() (+8 more)

### Community 96 - "6. Lesson study topics (52)"
Cohesion: 0.15
Nodes (13): 6. Lesson study topics (52), Cardiovascular & blood, Dermatology, Endocrine & metabolism, Gastrointestinal, Infectious disease, Miscellaneous, Musculoskeletal (+5 more)

### Community 97 - "files.ts"
Cohesion: 0.29
Nodes (12): buildDir(), closeHandles(), ensureBuildDir(), handles, partFile(), partPath(), partSize(), readRange() (+4 more)

### Community 98 - "ReferenceImportCommand"
Cohesion: 0.12
Nodes (4): Command, _DryRun, ReferenceImportCommand, Command

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

### Community 100 - "VisitorDay"
Cohesion: 0.24
Nodes (4): VisitorDay, Meta, UniqueVisitorTests, visit()

### Community 101 - "Command"
Cohesion: 0.21
Nodes (4): Command, _int(), _json_list(), _name_fa()

### Community 102 - "downloader.web.ts"
Cohesion: 0.20
Nodes (9): downloader, DownloadEvents, newWorker(), PartJob, PartRef, Run, runFor(), runs (+1 more)

### Community 103 - "۲. راه‌اندازی محیط توسعه"
Cohesion: 0.17
Nodes (12): اندروید و iOS, اپ (Expo), بک‌اند, تست بستهٔ آفلاین بدون باکت, تست و بررسی, روال کار با مخزن, ساخت دیتابیس و اجرای سرور, نسخهٔ وب (+4 more)

### Community 104 - "offline/reader.ts"
Cohesion: 0.19
Nodes (12): OfflineDataset, OfflineManifest, keyring, openRecord(), openRecordBase64(), PackageKey, sealed(), open (+4 more)

### Community 105 - "ImportCalculatorsTests"
Cohesion: 0.32
Nodes (3): _build_sqlite(), ImportCalculatorsTests, _one_calculator()

### Community 107 - "Repository Guidelines"
Cohesion: 0.29
Nodes (6): Build, Test, and Development Commands, Commit & Pull Request Guidelines, Project Structure & Module Organization, Repository Guidelines, Security & Configuration Tips, Testing Guidelines

### Community 108 - "sources.ts"
Cohesion: 0.16
Nodes (14): lexicompApi, uptodateApi, LexicompDrug, LexicompInteraction, cache, checkInteractions(), LexIndex, searchDrugs() (+6 more)

### Community 109 - "calculatorLive.ts"
Cohesion: 0.23
Nodes (14): CalculatorDetail, CalculatorQuestion, LIST_FROM, FieldProps, FlowProps, CalculatorAnswers, choiceWeights(), extremes() (+6 more)

### Community 110 - "QuizSession"
Cohesion: 0.17
Nodes (7): best_score_pct_for_topic(), _finished_sessions(), _finished_topic_sessions(), topic_mastery_map(), weak_topics_count(), QuizSession, Meta

### Community 112 - "accounts/services.py"
Cohesion: 0.06
Nodes (35): Role, Meta, RoleAssignment, Meta, SecurityAuditEvent, Meta, SessionRefreshToken, Meta (+27 more)

### Community 113 - "۵. قرارداد API (نسخهٔ ۱)"
Cohesion: 0.09
Nodes (22): Lexicomp — `/lexicomp/` (ویژگی `lexicomp`), Medscape — `/medscape/` (ویژگی `medscape`), UpToDate — `/uptodate/` (ویژگی `uptodate`), آزمون — `/quiz/` (ویژگی `quiz`؛ پرچم `QUIZ_API_ENABLED`), برنامهٔ ساخته‌شده از آنبوردینگ, تغییر دادن API, جعبهٔ قدیمی, جعبهٔ لایتنر (+14 more)

### Community 115 - "۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی"
Cohesion: 0.12
Nodes (17): اطلاعات غیرمحرمانه‌ای که باید جایی ثبت باشد, بازیابی, بکاپ و بازیابی, حساب‌های سرویس, رازها و چیزهایی که باید امن نگه داشته شوند, رازهای فنی, شاخص‌هایی که مرتب دیده شوند, عیب‌یابی (+9 more)

### Community 116 - "tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, paths, strict, extends, include, expo/tsconfig.base

### Community 119 - "App.tsx"
Cohesion: 0.11
Nodes (24): releaseApi, AppReleaseInfo, dismissedRecently(), Notes(), Offer, openRelease(), OptionalUpdate(), RequiredUpdate() (+16 more)

### Community 120 - "sw.js"
Cohesion: 0.38
Nodes (4): inScope(), referencedFiles(), SCOPE, storeShell()

### Community 122 - "require_feature"
Cohesion: 0.23
Nodes (5): _applies(), require_atc_content(), _require_content(), require_feature(), require_topic_content()

### Community 125 - "_SectionCard"
Cohesion: 0.19
Nodes (3): _card_back_fields(), DeckCardSerializer, _SectionCard

### Community 126 - "sms.py"
Cohesion: 0.20
Nodes (7): _error_message(), mask(), send_code(), _send_smsir(), SentCode, SmsSendError, SmsIrBackendTests

### Community 128 - "۴. اپ (Expo — اندروید، iOS و وب)"
Cohesion: 0.20
Nodes (11): آنبوردینگ و برنامهٔ مطالعه, ارتباط با API و کش, افزودن صفحهٔ تازه, دانلود آفلاین (`src/offline/`), فلش‌کارت و جعبهٔ لایتنر, ناوبری, نمایش بزرگ عکس و جدول, وب‌اپ و PWA (+3 more)

### Community 152 - "scripts"
Cohesion: 0.25
Nodes (8): scripts, android, build:web, ios, release, start, typecheck, web

### Community 156 - "downloader.ts"
Cohesion: 0.20
Nodes (6): downloader, DownloadEvents, PartJob, PartRef, tasks, @kesha-antonov/react-native-background-downloader

### Community 182 - "۱۲. سایت `pharmenta.ir` و پنل محتوا"
Cohesion: 0.05
Nodes (35): RequestIdMiddleware, SiteHostMiddleware, atc_groups(), feature_icon(), nav_on(), oneline(), person(), split_highlight() (+27 more)

### Community 184 - "lessons/serializers.py"
Cohesion: 0.22
Nodes (6): AtcGroupSerializer, ChapterDrugSerializer, ChapterProgressSerializer, DrugSearchChapterSerializer, SubgroupSerializer, TopicSerializer

### Community 185 - "QuizQuestion"
Cohesion: 0.18
Nodes (8): BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, QuizQuestion, Meta, QuizQuestionSerializer, Meta, _questions_from_bank()

### Community 196 - ".post"
Cohesion: 0.28
Nodes (3): record_quiz_answers(), _extra_context(), _owned_session()

### Community 197 - "PlanSerializer"
Cohesion: 0.29
Nodes (5): PlanFeatureItemSerializer, PlanPriceSerializer, Meta, PlanSerializer, Meta

### Community 202 - "authentication.py"
Cohesion: 0.12
Nodes (7): SessionTokenAuthentication, SessionTokenAuthenticationScheme, احراز هویت و حساب, ثبت‌نام و ورود, رمز عبور, نشست و توکن, نقش‌ها و رویدادهای امنیتی

### Community 203 - "DateResult.tsx"
Cohesion: 0.43
Nodes (7): hasPersian(), Ltr(), Rows(), DateResult(), useDateFormat(), parseAge(), parseDateText()

### Community 204 - "۸. دیپلوی"
Cohesion: 0.12
Nodes (16): CI, امنیت و هشدار نصب, اپ اندروید و iOS, برگرداندن یک دیپلوی خراب, بک‌اند, جریان دیپلوی, حجم APK, راه‌اندازی از صفر (یک بار) (+8 more)

### Community 205 - "bidi.ts"
Cohesion: 0.25
Nodes (7): isolated(), ENGLISH_RUN, hasPersianLetters(), isolateEnglish(), LRI, PDI, RLM

### Community 209 - "devDependencies"
Cohesion: 0.67
Nodes (3): devDependencies, @types/react, typescript

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
- **9 isolated node(s):** `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-build-properties`, `expo-splash-screen`, `react-dom` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1649 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **87 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `useTheme` to `accounts/services.py`, `package.json`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `AppText()` (e.g. with `زبان، جهت و تم` and `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅`) actually correct?**
  _`AppText()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-build-properties` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.03143051308188923 - nodes in this community are weakly interconnected._
- **Why does `UserSession` connect `accounts/services.py` to `WebsiteAuthTests`, `console/views.py`, `useTheme`, `authentication.py`, `accounts/serializers.py`, `اپ‌ها (`backend/apps/`)`, `views_account.py`, `tests_console.py`, `config.py`, `accounts/views.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.03844414292175486 - nodes in this community are weakly interconnected._
- **Why does `اپ‌ها (`backend/apps/`)` connect `اپ‌ها (`backend/apps/`)` to `test_panel.py`, `console/views.py`, `Post`, `views_public.py`, `flashcards/views.py`, `accounts/serializers.py`, `LeitnerCard`, `tests_console.py`, `billing/services.py`, `Page`, `IngredientProfileSection`, `progress/tests.py`, `Calculator`, `SectionEditRequest`, `LessonTaxonomyTests`, `planning.py`, `۱۲. سایت `pharmenta.ir` و پنل محتوا`, `Article`, `billing/tests.py`, `website/models.py`, `SectionEdit`, `billing/views.py`, `medscape/views.py`, `Ingredient`, `accounts/services.py`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._