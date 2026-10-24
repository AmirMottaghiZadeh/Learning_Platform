# Graph Report - Learning Platform  (2026-10-24)

## Corpus Check
- 489 files · ~823,468 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 32 file(s) not represented in the graph (top: (none) 11, .ttf 7, .woff2 4)

## Summary
- 4621 nodes · 13033 edges · 207 communities (118 shown, 89 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1200 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `43c1061a`
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
- App.tsx
- flashcards/views.py
- calculators/reference_db.py
- billing/views.py
- website/models.py
- GatewayError
- ImportOpenfdaTests
- billing/tests.py
- accounts/permissions.py
- lessons/selectors.py
- django_conf
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
- config.py
- CalculatorDetailScreen.tsx
- offline/views.py
- MaintenancePlanAndApiTests
- package.json
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
- common.tsx
- data_quality_center/tests.py
- progress/models.py
- Article
- test_phone_auth.py
- ۶. پیکربندی و متغیرهای محیطی
- IngredientProfileSection
- 6. Lesson study topics (52)
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- throttling.py
- اپ‌ها (`backend/apps/`)
- crypto.web.ts
- logging
- ۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین
- uptodate/services.py
- dependencies
- medscape/tests.py
- ۲. راه‌اندازی محیط توسعه
- panel.js
- test_public.py
- UserSerializer
- offline/tests.py
- SectionEdit
- ImportOpenfdaTests
- maintenance_urls.py
- ConsoleTestCase
- StudyTopicsCoverageTests
- useLang
- manage.py
- UptodateTests
- ReferenceDbTests
- website_extras.py
- clean_profile_boilerplate.py
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- porter.ts
- storage.py
- django_core_management_base
- uptodate/views.py
- DrugPageTests
- scripts
- offline/reader.ts
- docs/README.md
- views_drugs.py
- session.ts
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
- view.ts
- clean_html
- 0004_remove_misfit_atc_codes.py
- 0003_about_contact_text.py
- 0004_clear_rule_based_facts.py
- ۵. قرارداد API (نسخهٔ ۱)
- 0007_clear_rule_based_bank.py
- ۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی
- tsconfig.json
- ۱۲. سایت `pharmenta.ir` و پنل محتوا
- django_apps
- accounts/services.py
- sw.js
- Command
- devDependencies
- Command
- pagination.py
- OfflinePackageCard.tsx
- views_account.py
- ReviewTests
- docker-start.sh
- billing/apps.py
- .claude/CLAUDE.md
- jalali.ts
- app.config.js
- .mcp.json
- ۳. بک‌اند (Django)
- downloader.ts
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
- Media
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
- `ایمپورت از منبع خام (روی لپ‌تاپ)` --references--> `ArticleImage`  [INFERRED]
  docs/07-data.md → backend/apps/medscape/models.py

## Import Cycles
- None detected.

## Communities (207 total, 89 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.04
Nodes (75): حساب و احراز هویت — `/auth/`, flashcardsApi, guestApi, quizApi, AtcCode, AtcGroup, AuthTokenResponse, BoxSummary (+67 more)

### Community 1 - "django_db"
Cohesion: 0.03
Nodes (44): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+36 more)

### Community 2 - "test_panel.py"
Cohesion: 0.06
Nodes (14): StaffRole, Meta, AdminTests, AuthorTests, AuthTests, InboxTests, make_user(), MediaTests (+6 more)

### Community 3 - "console/views.py"
Cohesion: 0.05
Nodes (73): DiscountForm, FeatureEditForm, Meta, FeatureForm, Meta, latin_digits(), parse_amount(), parse_jalali() (+65 more)

### Community 4 - "react"
Cohesion: 0.07
Nodes (67): زبان، جهت و تم, meApi, medscapeApi, MedscapeKind, ALPHABET, AlphabeticalArticleList(), buildOffsets(), groupAlphabetically() (+59 more)

### Community 5 - "Post"
Cohesion: 0.06
Nodes (65): ActivityLog, Meta, Comment, Meta, ContactMessage, Meta, Post, Meta (+57 more)

### Community 6 - "AppText"
Cohesion: 0.11
Nodes (81): قابلیت‌ها, افزودن صفحهٔ تازه, قواعد کدنویسی اپ, ناوبری, LessonGroup, SectionTone, BottomNav(), HelpSheet() (+73 more)

### Community 7 - "views_public.py"
Cohesion: 0.05
Nodes (56): site(), DailyStat, Meta, PostQuerySet, SiteSettings, Meta, article(), breadcrumbs() (+48 more)

### Community 8 - ".reverse"
Cohesion: 0.04
Nodes (16): AuthenticationSecurityTests, OnboardingTests, enabled_gateways(), wrapper(), AccessTests, ConsoleTestCase, DeleteUserTests, DiscountAndReportTests (+8 more)

### Community 9 - "App.tsx"
Cohesion: 0.06
Nodes (63): شروع اپ, App(), Gate(), ThemedStatusBar(), API_BASE_URL, apiClient, ApiError, ApiErrorBody (+55 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.07
Nodes (31): require_feature(), deck_slugs(), progress_map(), topic_meta(), LeitnerCard, Meta, TopicProgress, Meta (+23 more)

### Community 11 - "calculators/reference_db.py"
Cohesion: 0.11
Nodes (13): export(), load(), dumps(), expected_count(), loads(), record_counts(), rows(), writing() (+5 more)

### Community 12 - "billing/views.py"
Cohesion: 0.06
Nodes (35): FakeGateway, get_gateway(), start_payment(), Verification, is_guest(), Order, Meta, CatalogSerializer (+27 more)

### Community 13 - "website/models.py"
Cohesion: 0.03
Nodes (53): Command, Command, Announcement, Meta, AppRelease, Meta, Category, Meta (+45 more)

### Community 14 - "GatewayError"
Cohesion: 0.05
Nodes (12): GatewayError, _post_json(), SepGateway, ZarinpalGateway, ZibalGateway, _fake_urlopen(), GatewayChoiceTests, PurchaseApiTests (+4 more)

### Community 15 - "ImportOpenfdaTests"
Cohesion: 0.09
Nodes (4): AtcSupplementTests, DrugApiTests, LoadAtcReferenceTests, ModelTests

### Community 16 - "billing/tests.py"
Cohesion: 0.05
Nodes (33): DiscountCode, Meta, Feature, Meta, Access, BillingError, check_feature(), content_lock() (+25 more)

### Community 17 - "accounts/permissions.py"
Cohesion: 0.16
Nodes (11): CanManagePlatformRoles, CanViewSecurityAudit, HasPlatformPermission, HasRecentStepUp, RoleAssignmentCreateSerializer, RoleAssignmentRevokeSerializer, RoleAssignmentSerializer, Meta (+3 more)

### Community 18 - "lessons/selectors.py"
Cohesion: 0.07
Nodes (22): all_decks(), _carded_slugs(), next_topic(), ChapterProgress, Meta, ReadDrug, Meta, fold() (+14 more)

### Community 19 - "django_conf"
Cohesion: 0.08
Nodes (17): account_for_signup(), _hash(), _new_code(), OtpError, request_code(), user_for_phone(), verify_code(), ensure_default_learner_role() (+9 more)

### Community 20 - "accounts/views.py"
Cohesion: 0.06
Nodes (46): AuthTokenResponseSerializer, LearnerProfileSerializer, Meta, LoginSerializer, OtpRequestResponseSerializer, OtpRequestSerializer, OtpVerifySerializer, PasswordResetConfirmSerializer (+38 more)

### Community 21 - "calculators/tests.py"
Cohesion: 0.07
Nodes (20): fix_questions(), fix_results(), renumber_from_one(), _stage_names_without_prefix(), _with_unit(), Command, _error_checks_for(), _formula_strings_fa() (+12 more)

### Community 22 - "data_quality_center/views.py"
Cohesion: 0.12
Nodes (25): warning_count(), section_state(), _diffs(), discard(), history(), _login_key(), login_view(), logout_view() (+17 more)

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.08
Nodes (49): CalculatorErrorCheck, CalculatorResultDef, Tier, buildHeuristicSeeds(), cartesian(), classifyResultTone(), computeCalculator(), ComputeOptions (+41 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.06
Nodes (41): BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, ingredient_ids_for_selection(), preview_selection(), sample_bank_questions(), _sample_rows(), best_score_pct_for_topic() (+33 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.08
Nodes (50): MedscapeBlock, MedscapeSection, countMatches(), FindState, highlight(), ListMarker(), LTR, NumberedHeading() (+42 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.09
Nodes (18): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, _categories_for_generics(), check_interactions(), close_all(), _conn(), _dir() (+10 more)

### Community 28 - ".request_code"
Cohesion: 0.08
Nodes (22): CodeRuleTests, PhoneAuthTestCase, ResetTests, SignUpTests, SmsIrBackendTests, برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی, روش تبدیل پیشنهادها به کلمات کلیدی معتبر (+14 more)

### Community 29 - "progress/views.py"
Cohesion: 0.09
Nodes (26): Mistake, Meta, DashboardSerializer, FocusRowSerializer, FocusSessionSerializer, MistakeSerializer, Meta, NextChapterSerializer (+18 more)

### Community 30 - "core/views.py"
Cohesion: 0.14
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 31 - "lessons/views.py"
Cohesion: 0.09
Nodes (22): _applies(), require_atc_content(), _require_content(), require_topic_content(), get_chapter(), get_lesson_drug(), AtcGroupSerializer, ChapterDrugSerializer (+14 more)

### Community 33 - "store.ts"
Cohesion: 0.11
Nodes (44): offlineApi, buildDir(), closeHandles(), ensureBuildDir(), handles, partFile(), partPath(), partSize() (+36 more)

### Community 34 - "Calculator"
Cohesion: 0.08
Nodes (18): Calculator, Meta, CalculatorCategory, Meta, CalculatorTag, Meta, CalculatorCategorySerializer, Meta (+10 more)

### Community 35 - "SectionEditRequest"
Cohesion: 0.10
Nodes (21): ReviewEvent, Meta, SectionEditRequest, Meta, approve(), _clean(), _client_ip(), _close() (+13 more)

### Community 36 - "config.py"
Cohesion: 0.11
Nodes (14): BillingConfig, current(), gateway_spec(), _gateways(), GatewaySpec, _load(), row(), _settings_changed() (+6 more)

### Community 37 - "CalculatorDetailScreen.tsx"
Cohesion: 0.09
Nodes (43): calculatorsApi, CalculatorDetail, CalculatorQuestion, describeInputs(), DateInput(), DaysInput(), Field(), QuestionTitle() (+35 more)

### Community 38 - "offline/views.py"
Cohesion: 0.08
Nodes (24): build_matches_dataset(), LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer, PackageFileUrlSerializer, PackageManifestSerializer, PackageUrlsRequestSerializer (+16 more)

### Community 39 - "MaintenancePlanAndApiTests"
Cohesion: 0.13
Nodes (3): bump_mistake(), MaintenancePlanAndApiTests, MeApiTests

### Community 40 - "package.json"
Cohesion: 0.11
Nodes (17): main, name, private, version, expo, expo-file-system, expo-font, @expo-google-fonts/vazirmatn (+9 more)

### Community 41 - "Ingredient"
Cohesion: 0.09
Nodes (10): Command, Command, AtcCategory, Meta, AtcCode, Meta, Ingredient, Meta (+2 more)

### Community 42 - "QuizApiTests"
Cohesion: 0.09
Nodes (4): QuizAccessTests, QuizApiTests, QuizLockedTests, _seed_atc_world()

### Community 43 - "sources.ts"
Cohesion: 0.08
Nodes (33): Coding Style & Naming Conventions, پایهٔ Django, lexicompApi, uptodateApi, LexicompDrug, LexicompInteraction, UptodateImage, cache (+25 more)

### Community 44 - "billing/tests.py"
Cohesion: 0.18
Nodes (16): _div(), fa_digits(), format_date(), _jal_cal(), _mod(), month_start(), to_gregorian(), to_jalali() (+8 more)

### Community 45 - "VisitorDay"
Cohesion: 0.24
Nodes (4): VisitorDay, Meta, UniqueVisitorTests, visit()

### Community 47 - "pack.py"
Cohesion: 0.06
Nodes (23): build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections(), _varints(), Command (+15 more)

### Community 48 - "drugs/serializers.py"
Cohesion: 0.12
Nodes (11): AtcCodeSerializer, Meta, IngredientDetailSerializer, Meta, IngredientListSerializer, Meta, LessonDrugSerializer, LessonSectionSerializer (+3 more)

### Community 49 - "FlashcardApiTests"
Cohesion: 0.13
Nodes (6): seed_deck(), FlashcardApiTests, FlashcardLockedTests, _refresh_facts(), _rich_ingredient(), TopicDeckTests

### Community 50 - "LessonTaxonomyTests"
Cohesion: 0.08
Nodes (4): DrugSearchTests, _ingredient(), LessonTaxonomyFallbackTests, LessonTaxonomyTests

### Community 51 - "expo"
Cohesion: 0.06
Nodes (31): backgroundColor, foregroundImage, adaptiveIcon, package, versionCode, projectId, typedRoutes, expo (+23 more)

### Community 52 - "planning.py"
Cohesion: 0.05
Nodes (29): due_card_count(), _seed_candidates(), _with_enough_content(), mark_drug_read(), StudyPlanItem, Meta, complete_item(), ensure_today_items() (+21 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.15
Nodes (7): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label()

### Community 54 - "common.tsx"
Cohesion: 0.09
Nodes (82): bandFor(), Chip(), Collapse(), Explain(), Extra, Extras(), fmt(), hasPersian() (+74 more)

### Community 55 - "data_quality_center/tests.py"
Cohesion: 0.24
Nodes (6): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), word_diff(), CheckTests

### Community 56 - "progress/models.py"
Cohesion: 0.07
Nodes (27): Migration, seed(), DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin, DailyStudy, Meta (+19 more)

### Community 57 - "Article"
Cohesion: 0.09
Nodes (15): Command, Command, Article, Meta, ArticleImage, ArticleDetailSerializer, Meta, ArticleImageSerializer (+7 more)

### Community 58 - "test_phone_auth.py"
Cohesion: 0.11
Nodes (9): EmailOrUsernameBackend, LearnerProfile, InvalidPhone, looks_like_phone(), normalize_phone(), PhoneField, NormalizePhoneTests, ProfileTests (+1 more)

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.12
Nodes (16): HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت, دادهٔ مرجع (UpToDate و Lexicomp), دیتابیس، کش و آمادگی, سایت (+8 more)

### Community 60 - "IngredientProfileSection"
Cohesion: 0.11
Nodes (11): AtcCategoryAdmin, AtcCodeAdmin, IngredientAdmin, IngredientProfileSectionAdmin, IngredientProfileSectionInline, IngredientProfileSection, Meta, LessonDrugSectionSerializer (+3 more)

### Community 61 - "6. Lesson study topics (52)"
Cohesion: 0.06
Nodes (34): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 6. Lesson study topics (52), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups (+26 more)

### Community 62 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.17
Nodes (10): PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa, 🎉 بازنویسی کامل شد, فاز ۰.۵ — حذف زیرساخت رهاشده ✅, فاز ۱ — دیتابیس دارویی ✅, فاز ۲ — قرارداد API + API دانش دارویی + onboarding ✅, فاز ۶ — uptodate + جمع‌بندی + انتشار (زیرفازی), پس از انتشار — حذف کدهای ATC نامرتبط با اندیکاسیون ✅ (برنچ `fix-chapter-indication-fit`), پس از انتشار — سایت و بلاگ `pharmenta.ir` + پنل مدیریت ✅ (+2 more)

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "اپ‌ها (`backend/apps/`)"
Cohesion: 0.06
Nodes (21): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, BillingSettings, Meta (+13 more)

### Community 65 - "crypto.web.ts"
Cohesion: 0.23
Nodes (9): OfflineLicense, db(), idb(), keyring, openRecord(), openRecordBase64(), PackageKey, rsaPair() (+1 more)

### Community 66 - "logging"
Cohesion: 0.07
Nodes (8): password_reset_url_for_user(), send_password_reset_email(), send_password_reset_emails_for_email(), send_password_reset_email_task(), PlatformTask, retry_delay_seconds(), enqueue(), configure_runtime()

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (24): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+16 more)

### Community 68 - "uptodate/services.py"
Cohesion: 0.10
Nodes (18): Command, article_from_row(), _dir(), get_image(), get_topic(), is_available(), mysql_config(), _mysql_conn() (+10 more)

### Community 69 - "dependencies"
Cohesion: 0.08
Nodes (26): dependencies, axios, expo, expo-crypto, expo-file-system, expo-font, @expo-google-fonts/vazirmatn, expo-linear-gradient (+18 more)

### Community 70 - "medscape/tests.py"
Cohesion: 0.27
Nodes (5): _disease_record(), _guideline_record(), ImportMedscapeArticlesTests, _write_diseases_tree(), _write_guidelines()

### Community 71 - "۲. راه‌اندازی محیط توسعه"
Cohesion: 0.15
Nodes (13): اجرای کامل با Docker, اندروید و iOS, اپ (Expo), بک‌اند, تست بستهٔ آفلاین بدون باکت, تست و بررسی, روال کار با مخزن, ساخت دیتابیس و اجرای سرور (+5 more)

### Community 72 - "panel.js"
Cohesion: 0.16
Nodes (14): buildEditor(), align(), block(), exec(), sync(), toggleSource(), wrapBlock(), filterNav() (+6 more)

### Community 73 - "test_public.py"
Cohesion: 0.05
Nodes (10): SiteMaintenanceMiddleware, Redirect, Meta, SiteTestCase, CommentTests, DownloadAndMachineTests, FormsTests, HostRoutingTests (+2 more)

### Community 74 - "UserSerializer"
Cohesion: 0.07
Nodes (11): Migration, OnboardingSerializer, UserSerializer, Meta, active_role_keys(), OnboardingView, create_guest(), GuestStatusView (+3 more)

### Community 75 - "offline/tests.py"
Cohesion: 0.09
Nodes (6): HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests, _make_source_db(), _make_snapshot(), _make_snapshot()

### Community 76 - "SectionEdit"
Cohesion: 0.15
Nodes (7): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin, SectionEdit, Meta, مرکز کیفیت داده (`/ops/data-quality/`)

### Community 81 - "useLang"
Cohesion: 0.08
Nodes (47): ارتباط با API و کش, دانلود آفلاین (`src/offline/`), ساختار `frontend/src/`, وب‌اپ و PWA, پیکربندی اپ بومی, ۴. اپ (Expo — اندروید، iOS و وب), lessonsApi, useBleedTop() (+39 more)

### Community 82 - "manage.py"
Cohesion: 0.29
Nodes (3): build.sh script, DJANGO_SETTINGS_MODULE, release.sh script

### Community 85 - "website_extras.py"
Cohesion: 0.15
Nodes (8): atc_groups(), feature_icon(), nav_on(), oneline(), person(), split_highlight(), split_lines(), آنچه کد انجام می‌دهد

### Community 86 - "clean_profile_boilerplate.py"
Cohesion: 0.23
Nodes (8): clean_text(), Command, is_hypersensitivity_boilerplate(), is_hypersensitivity_boilerplate_en(), is_negative_indication_en(), is_negative_indication_fa(), is_null_placeholder(), _normalize()

### Community 87 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.15
Nodes (5): validate_production_broker(), validate_production_cache(), validate_production_secret_key(), CorsPreflightTests, ProductionSecretKeyTests

### Community 88 - "porter.ts"
Cohesion: 0.23
Nodes (8): firstRule(), isVowelLetter(), porterStem(), Rule, STEP2, STEP3, STEP4, Word

### Community 89 - "storage.py"
Cohesion: 0.09
Nodes (15): Command, cors_rule(), _request(), clear_cache(), file_urls(), is_configured(), latest_manifest(), local_dir() (+7 more)

### Community 90 - "django_core_management_base"
Cohesion: 0.07
Nodes (7): Command, Command, _DryRun, ReferenceImportCommand, open_for_import(), Command, Command

### Community 91 - "uptodate/views.py"
Cohesion: 0.30
Nodes (8): UptodateArticleSerializer, UptodateImageSerializer, UptodateSearchResultSerializer, UptodateTopicSerializer, ImageDetailView, _require_available(), TopicDetailView, TopicSearchView

### Community 92 - "DrugPageTests"
Cohesion: 0.12
Nodes (3): DrugPageTests, SiteIdentityTests, structured()

### Community 93 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, android, build:web, ios, start, typecheck, web

### Community 94 - "offline/reader.ts"
Cohesion: 0.20
Nodes (11): OfflineDataset, OfflineManifest, keyring, openRecord(), openRecordBase64(), PackageKey, sealed(), Locator (+3 more)

### Community 96 - "views_drugs.py"
Cohesion: 0.13
Nodes (12): _build_catalog(), _drop_title(), drug_detail(), english_name(), fa_key(), _group_code(), _group_titles(), grouped() (+4 more)

### Community 97 - "session.ts"
Cohesion: 0.29
Nodes (5): get(), KEYS, sessionStore, StoredSession, expo-secure-store

### Community 98 - "django_core_management_base"
Cohesion: 0.11
Nodes (5): Command, ensure_title_search_index(), _has_title_search_index(), MysqlTitleIndexTests, MysqlTitleSearchTests

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

### Community 100 - "ApiTests"
Cohesion: 0.13
Nodes (3): ApiTests, BuildTests, DownloadHostTests

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

### Community 108 - "view.ts"
Cohesion: 0.21
Nodes (11): OfflinePackageInfo, empty(), InstalledPackage, licenseExpiresAt(), OfflineErrorCode, pendingBytes(), PendingPackage, useOffline (+3 more)

### Community 109 - "clean_html"
Cohesion: 0.08
Nodes (6): clean_html(), _Cleaner, plain_text(), safe_url(), _Text, SanitizeTests

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

### Community 119 - "accounts/services.py"
Cohesion: 0.08
Nodes (27): Role, Meta, RoleAssignment, Meta, SecurityAuditEvent, Meta, SessionRefreshToken, Meta (+19 more)

### Community 120 - "sw.js"
Cohesion: 0.38
Nodes (4): inScope(), referencedFiles(), SCOPE, storeShell()

### Community 122 - "devDependencies"
Cohesion: 0.67
Nodes (3): devDependencies, @types/react, typescript

### Community 123 - "Command"
Cohesion: 0.12
Nodes (5): Command, _int(), _json_list(), _name_fa(), Migration

### Community 125 - "OfflinePackageCard.tsx"
Cohesion: 0.14
Nodes (19): OfflineDownloadButton(), OfflineSheet(), ERROR_TEXT, LOGO, NAME, OfflinePackageCard(), PHASE_TEXT, canGoBack() (+11 more)

### Community 126 - "views_account.py"
Cohesion: 0.10
Nodes (19): OneTimeCode, Meta, callback_url(), AccountForm, CodeForm, LoginForm, PasswordForm, PhoneForm (+11 more)

### Community 134 - "jalali.ts"
Cohesion: 0.47
Nodes (11): BREAKS, d2g(), d2j(), div(), g2d(), isValidJalali(), j2d(), jalCal() (+3 more)

### Community 182 - "۳. بک‌اند (Django)"
Cohesion: 0.12
Nodes (13): RequestIdMiddleware, SiteHostMiddleware, UpToDate و Lexicomp, افزودن یک قابلیت فروشی تازه, بستهٔ آفلاین (`apps.offline`), زنجیرهٔ middleware, صورتحساب و دسترسی (`apps.billing`), قواعد مشترک API (+5 more)

### Community 184 - "downloader.ts"
Cohesion: 0.20
Nodes (6): downloader, DownloadEvents, PartJob, PartRef, SUPPORTS_BACKGROUND, tasks

### Community 196 - "authentication.py"
Cohesion: 0.12
Nodes (7): SessionTokenAuthentication, SessionTokenAuthenticationScheme, احراز هویت و حساب, ثبت‌نام و ورود, رمز عبور, نشست و توکن, نقش‌ها و رویدادهای امنیتی

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
Cohesion: 0.18
Nodes (5): FlashcardFactAdmin, LeitnerCardAdmin, FlashcardFact, Meta, Command

### Community 226 - "مستندات فارمنتا"
Cohesion: 0.50
Nodes (4): سندهای دیگر مخزن, فهرست, قرارداد نگهداری این مستندات, مستندات فارمنتا

### Community 230 - "فارمنتا (Pharmenta)"
Cohesion: 0.67
Nodes (3): شروع سریع, فارمنتا (Pharmenta), مستندات

## Knowledge Gaps
- **8 isolated node(s):** `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-splash-screen`, `react-dom`, `react-native-web` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1509 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **89 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UserSession` connect `accounts/services.py` to `اپ‌ها (`backend/apps/`)`, `console/views.py`, `authentication.py`, `config.py`, `WebsiteAuthTests`, `AppText`, `accounts/views.py`, `test_phone_auth.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `PlatformAPIError` (e.g. with `LoginView` and `OtpVerifyView`) actually correct?**
  _`PlatformAPIError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-splash-screen` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.039294039294039296 - nodes in this community are weakly interconnected._
- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `AppText` to `App.tsx`, `react`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`, `accounts/services.py`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.02722489132921528 - nodes in this community are weakly interconnected._
- **Why does `اپ‌ها (`backend/apps/`)` connect `اپ‌ها (`backend/apps/`)` to `test_panel.py`, `console/views.py`, `Post`, `views_public.py`, `flashcards/views.py`, `billing/views.py`, `website/models.py`, `billing/tests.py`, `lessons/selectors.py`, `quiz/views.py`, `Calculator`, `SectionEditRequest`, `Ingredient`, `۳. بک‌اند (Django)`, `progress/models.py`, `Article`, `IngredientProfileSection`, `SectionEdit`, `Media`, `FlashcardFact`, `accounts/services.py`, `views_account.py`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._