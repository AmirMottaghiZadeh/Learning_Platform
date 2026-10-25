# Graph Report - Learning Platform  (2026-10-25)

## Corpus Check
- 514 files · ~411,473 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 32 file(s) not represented in the graph (top: (none) 11, .ttf 7, .woff2 4)

## Summary
- 4949 nodes · 14000 edges · 208 communities (120 shown, 88 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1249 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7d404ce2`
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
- UserSerializer
- PlatformAPIError
- useTheme
- GatewayError
- ImportOpenfdaTests
- billing/services.py
- Page
- 0003_about_contact_text.py
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
- CalculatorDetailScreen.tsx
- offline/views.py
- api.py
- ResultCard
- DrugPageTests
- QuizApiTests
- Article
- progress/views.py
- release.mjs
- config.py
- json
- drugs/views.py
- FlashcardApiTests
- LessonTaxonomyTests
- expo
- planning.py
- import_medscape_articles.py
- common.tsx
- data_quality_center/tests.py
- django_utils
- Article
- test_phone_auth.py
- ۶. پیکربندی و متغیرهای محیطی
- billing/tests.py
- files.web.ts
- data_quality_center/forms.py
- throttling.py
- Post
- WebsiteAuthTests
- celery_tasks.py
- ۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین
- uptodate/services.py
- dependencies
- medscape/tests.py
- crypto.web.ts
- panel.js
- website/models.py
- اپ‌ها (`backend/apps/`)
- calculatorModel.ts
- SectionEdit
- views_account.py
- maintenance_urls.py
- ConsoleTestCase
- StudyTopicsCoverageTests
- LessonDetailScreen.tsx
- PaymentGateway
- UptodateTests
- MedscapeApiTests
- dqc_extras.py
- clean_profile_boilerplate.py
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- porter.ts
- gateways.py
- offline/reader.ts
- offline/services.py
- lessons/selectors.py
- Pharmexa — custom icon prompts
- offline/reader.ts
- docs/README.md
- 6. Lesson study topics (52)
- downloader.ts
- FlashcardFact
- site.js
- VisitorDay
- Command
- downloader.web.ts
- ۲. راه‌اندازی محیط توسعه
- drugs/admin.py
- ImportCalculatorsTests
- ReferenceDbTests
- Repository Guidelines
- Section
- Media
- AtcSupplementTests
- bidi.ts
- accounts/services.py
- ۵. قرارداد API (نسخهٔ ۱)
- bootstrap_superuser.py
- ۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی
- tsconfig.json
- ResultProps
- django_apps
- UpdatePrompt.tsx
- sw.js
- Command
- AtcCode
- DrugSearchTests
- pagination.py
- IngredientDetailSerializer
- otp.py
- jalali.ts
- IngredientProfileSection
- docker-start.sh
- billing/apps.py
- apply_atc_supplement.py
- .claude/CLAUDE.md
- OfflinePackageCard.tsx
- app.config.js
- .mcp.json
- drugs/serializers.py
- ۱۲. سایت `pharmenta.ir` و پنل محتوا
- HostRoutingTests
- brand_file
- DateResult.tsx
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
- session.ts
- LessonTaxonomyFallbackTests
- ArticleTreeView
- ۸. دیپلوی
- ۱. معرفی و معماری
- ۱۰. مرجع سریع دستورها
- کنسول فروش (`/ops/`)
- مستندات فارمنتا
- فارمنتا (Pharmenta)

## God Nodes (most connected - your core abstractions)
1. `useTheme()` - 181 edges
2. `AppText()` - 178 edges
3. `useLang()` - 166 edges
4. `react` - 83 edges
5. `PlatformAPIError` - 79 edges
6. `Ingredient` - 72 edges
7. `react-native` - 72 edges
8. `useNav` - 63 edges
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

## Communities (208 total, 88 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.04
Nodes (80): حساب و احراز هویت — `/auth/`, flashcardsApi, guestApi, quizApi, releaseApi, AppReleaseInfo, AtcCode, AtcGroup (+72 more)

### Community 1 - "django_db"
Cohesion: 0.02
Nodes (52): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+44 more)

### Community 2 - "test_panel.py"
Cohesion: 0.06
Nodes (10): Media, Meta, AdminTests, AuthorTests, AuthTests, make_user(), MediaTests, PermissionTests (+2 more)

### Community 3 - "console/views.py"
Cohesion: 0.06
Nodes (64): DiscountForm, FeatureEditForm, Meta, FeatureForm, Meta, latin_digits(), parse_amount(), parse_jalali() (+56 more)

### Community 4 - "react"
Cohesion: 0.08
Nodes (61): calculatorsApi, lessonsApi, meApi, medscapeApi, MedscapeKind, ALPHABET, AlphabeticalArticleList(), buildOffsets() (+53 more)

### Community 5 - "Post"
Cohesion: 0.07
Nodes (55): Post, Meta, orders(), plans(), subscriptions(), comment_action(), comments(), contact() (+47 more)

### Community 6 - "useTheme"
Cohesion: 0.10
Nodes (76): قابلیت‌ها, آنبوردینگ و برنامهٔ مطالعه, افزودن صفحهٔ تازه, قواعد کدنویسی اپ, ناوبری, SectionTone, useNavClearance(), Card() (+68 more)

### Community 7 - "views_public.py"
Cohesion: 0.04
Nodes (65): fa(), site(), DailyStat, Meta, SiteSettings, Meta, article(), breadcrumbs() (+57 more)

### Community 8 - ".reverse"
Cohesion: 0.05
Nodes (12): AuthenticationSecurityTests, OnboardingTests, enabled_gateways(), AccessTests, FeatureTests, GatewayPageTests, PlanBuilderTests, UsersPageTests (+4 more)

### Community 9 - "package.json"
Cohesion: 0.04
Nodes (58): زبان، جهت و تم, App(), ThemedStatusBar(), main, name, private, version, API_BASE_URL (+50 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.05
Nodes (40): require_topic_content(), Ingredient, Meta, all_decks(), _carded_slugs(), deck_slugs(), next_topic(), progress_map() (+32 more)

### Community 11 - "UserSerializer"
Cohesion: 0.09
Nodes (11): LearnerProfileSerializer, Meta, OnboardingSerializer, UserSerializer, Meta, active_role_keys(), MeView, OnboardingView (+3 more)

### Community 12 - "PlatformAPIError"
Cohesion: 0.06
Nodes (35): is_guest(), CatalogSerializer, CheckoutSerializer, OrderSerializer, Meta, PurchaseRequestSerializer, QuoteSerializer, _billing_error() (+27 more)

### Community 13 - "useTheme"
Cohesion: 0.12
Nodes (34): ارتباط با API و کش, دانلود آفلاین (`src/offline/`), ساختار `frontend/src/`, شروع اپ, نمایش بزرگ عکس و جدول, وب‌اپ و PWA, پیکربندی اپ بومی, ۴. اپ (Expo — اندروید، iOS و وب) (+26 more)

### Community 14 - "GatewayError"
Cohesion: 0.06
Nodes (11): GatewayError, _post_json(), SepGateway, Verification, ZarinpalGateway, ZibalGateway, _fake_urlopen(), GatewayChoiceTests (+3 more)

### Community 16 - "billing/services.py"
Cohesion: 0.04
Nodes (35): Order, Meta, UsageRecord, Meta, MyAccessSerializer, Access, active_entitlements(), BillingError (+27 more)

### Community 17 - "Page"
Cohesion: 0.08
Nodes (6): clean_html(), _Cleaner, plain_text(), safe_url(), _Text, SanitizeTests

### Community 19 - "useLang"
Cohesion: 0.09
Nodes (48): LessonGroup, StudyPlanItem, CategoryPicker(), Chip(), ChipRow(), DateField(), ExamDatePicker(), latin() (+40 more)

### Community 20 - "accounts/views.py"
Cohesion: 0.05
Nodes (62): Role, Meta, RoleAssignment, Meta, SecurityAuditEvent, Meta, CanManagePlatformRoles, CanViewSecurityAudit (+54 more)

### Community 21 - "fix_results"
Cohesion: 0.07
Nodes (15): fix_questions(), fix_results(), fix_strings_fa(), renumber_from_one(), _with_choices(), apply_fixes(), Migration, apply_fixes() (+7 more)

### Community 22 - "data_quality_center/views.py"
Cohesion: 0.12
Nodes (25): warning_count(), section_state(), _diffs(), discard(), history(), _login_key(), login_view(), logout_view() (+17 more)

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.08
Nodes (56): CalculatorErrorCheck, LiveScore(), useLiveScore(), buildHeuristicSeeds(), cartesian(), classifyResultTone(), computeCalculator(), ComputeOptions (+48 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.05
Nodes (43): record_quiz_answers(), BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, ingredient_ids_for_selection(), preview_selection(), sample_bank_questions(), _sample_rows() (+35 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.05
Nodes (79): MedscapeBlock, MedscapeSection, useBleedTop(), countMatches(), FindState, highlight(), ListMarker(), LTR (+71 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.09
Nodes (18): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, _categories_for_generics(), check_interactions(), close_all(), _conn(), _dir() (+10 more)

### Community 28 - ".request_code"
Cohesion: 0.08
Nodes (21): CodeRuleTests, PhoneAuthTestCase, ResetTests, SignUpTests, برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی, روش تبدیل پیشنهادها به کلمات کلیدی معتبر, ساخت Analytics از ابتدا (+13 more)

### Community 29 - "progress/tests.py"
Cohesion: 0.05
Nodes (28): Migration, seed(), DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin, DailyStudy, Meta (+20 more)

### Community 30 - "core/views.py"
Cohesion: 0.14
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 31 - "lessons/views.py"
Cohesion: 0.09
Nodes (23): _applies(), require_atc_content(), _require_content(), require_feature(), get_chapter(), get_lesson_drug(), topics_for_chapter(), AtcGroupSerializer (+15 more)

### Community 33 - "store.ts"
Cohesion: 0.11
Nodes (45): offlineApi, buildDir(), closeHandles(), ensureBuildDir(), handles, partFile(), partPath(), partSize() (+37 more)

### Community 34 - "Calculator"
Cohesion: 0.05
Nodes (30): standardize_fa_units(), Command, _error_checks_for(), _formula_strings_fa(), _import_categories(), _import_tags(), _questions_for(), _references_for() (+22 more)

### Community 35 - "SectionEditRequest"
Cohesion: 0.10
Nodes (21): ReviewEvent, Meta, SectionEditRequest, Meta, approve(), _clean(), _client_ip(), _close() (+13 more)

### Community 36 - "re"
Cohesion: 0.08
Nodes (15): _fa_keys_standardized(), _stage_names_without_prefix(), _title_formula_as_result(), _with_unit(), StandardizeUnitsTests, _adjective(), _chain(), _key() (+7 more)

### Community 37 - "CalculatorDetailScreen.tsx"
Cohesion: 0.12
Nodes (39): describeInputs(), DateInput(), DaysInput(), Field(), QuestionTitle(), CardsFlow(), ChecklistFlow(), flowLayout (+31 more)

### Community 38 - "offline/views.py"
Cohesion: 0.06
Nodes (32): Command, cors_rule(), _request(), build_matches_dataset(), LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer (+24 more)

### Community 39 - "api.py"
Cohesion: 0.08
Nodes (13): note_lines(), ReleaseCheckView, ReleaseQuerySerializer, AppRelease, Meta, version_code(), ReleaseForm, Meta (+5 more)

### Community 40 - "ResultCard"
Cohesion: 0.34
Nodes (21): Explain(), Hero(), Interpretation(), Ltr(), ResultCard(), showTierBar(), TierBar(), tierText() (+13 more)

### Community 41 - "DrugPageTests"
Cohesion: 0.09
Nodes (5): DrugPageTests, make_drug(), SiteIdentityTests, structured(), summary_html()

### Community 42 - "QuizApiTests"
Cohesion: 0.09
Nodes (3): QuizAccessTests, QuizApiTests, QuizLockedTests

### Community 43 - "Article"
Cohesion: 0.10
Nodes (14): Command, Command, Article, Meta, ArticleImage, ArticleDetailSerializer, Meta, ArticleImageSerializer (+6 more)

### Community 44 - "progress/views.py"
Cohesion: 0.07
Nodes (35): Mistake, Meta, dashboard(), _display_name(), _leitner_focus_row(), _mastery_pct(), _next_chapter(), statistics() (+27 more)

### Community 45 - "release.mjs"
Cohesion: 0.09
Nodes (15): appJson, at, dryRun, file(), frontend, [kind, ...flags], lock, [major, minor, patch] (+7 more)

### Community 46 - "config.py"
Cohesion: 0.05
Nodes (18): BillingConfig, clear_cache(), current(), gateway_spec(), _gateways(), GatewaySpec, _load(), row() (+10 more)

### Community 47 - "json"
Cohesion: 0.06
Nodes (25): build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections(), _varints(), Command (+17 more)

### Community 48 - "drugs/views.py"
Cohesion: 0.17
Nodes (7): AtcCodeSerializer, Meta, IngredientListSerializer, Meta, AtcCodeListView, IngredientDetailView, IngredientListView

### Community 49 - "FlashcardApiTests"
Cohesion: 0.11
Nodes (5): FlashcardApiTests, FlashcardLockedTests, _refresh_facts(), _rich_ingredient(), TopicDeckTests

### Community 51 - "expo"
Cohesion: 0.06
Nodes (32): backgroundColor, foregroundImage, adaptiveIcon, allowBackup, blockedPermissions, package, projectId, typedRoutes (+24 more)

### Community 52 - "planning.py"
Cohesion: 0.06
Nodes (32): mark_drug_read(), StudyPlanItem, Meta, _chapter(), complete_item(), ensure_today_items(), _flashcard_recall_for_slugs(), _flatten() (+24 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.16
Nodes (7): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label()

### Community 54 - "common.tsx"
Cohesion: 0.16
Nodes (26): bandFor(), Chip(), Collapse(), Extra, Extras(), fmt(), LEVEL_TONES, plain() (+18 more)

### Community 55 - "data_quality_center/tests.py"
Cohesion: 0.24
Nodes (6): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), word_diff(), CheckTests

### Community 56 - "django_utils"
Cohesion: 0.09
Nodes (6): writing(), HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests, _make_snapshot(), _make_snapshot()

### Community 57 - "Article"
Cohesion: 0.03
Nodes (30): Command, export(), load(), Command, _DryRun, ReferenceImportCommand, dumps(), expected_count() (+22 more)

### Community 58 - "test_phone_auth.py"
Cohesion: 0.08
Nodes (16): EmailOrUsernameBackend, LearnerProfile, UserSession, Meta, InvalidPhone, looks_like_phone(), normalize_phone(), PhoneField (+8 more)

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.12
Nodes (16): HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت, دادهٔ مرجع (UpToDate و Lexicomp), دیتابیس، کش و آمادگی, سایت (+8 more)

### Community 60 - "billing/tests.py"
Cohesion: 0.20
Nodes (10): _div(), format_date(), _jal_cal(), _mod(), month_start(), to_gregorian(), to_jalali(), DiscountTests (+2 more)

### Community 61 - "files.web.ts"
Cohesion: 0.19
Nodes (9): file(), forget(), partSize(), readRange(), removeBuild(), removeOtherBuilds(), removePart(), snapshots (+1 more)

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "Post"
Cohesion: 0.11
Nodes (4): CommentTests, DownloadAndMachineTests, make_post(), PostVisibilityTests

### Community 66 - "celery_tasks.py"
Cohesion: 0.12
Nodes (3): PlatformTask, retry_delay_seconds(), configure_runtime()

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (26): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+18 more)

### Community 68 - "uptodate/services.py"
Cohesion: 0.06
Nodes (23): Command, Command, ensure_title_search_index(), _has_title_search_index(), article_from_row(), _dir(), get_image(), get_topic() (+15 more)

### Community 69 - "dependencies"
Cohesion: 0.05
Nodes (39): dependencies, axios, expo, expo-build-properties, expo-constants, expo-crypto, expo-file-system, expo-font (+31 more)

### Community 70 - "medscape/tests.py"
Cohesion: 0.27
Nodes (5): _disease_record(), _guideline_record(), ImportMedscapeArticlesTests, _write_diseases_tree(), _write_guidelines()

### Community 71 - "crypto.web.ts"
Cohesion: 0.23
Nodes (9): اجرای کامل با Docker, db(), idb(), keyring, openRecord(), openRecordBase64(), PackageKey, rsaPair() (+1 more)

### Community 72 - "panel.js"
Cohesion: 0.16
Nodes (14): buildEditor(), align(), block(), exec(), sync(), toggleSource(), wrapBlock(), filterNav() (+6 more)

### Community 73 - "website/models.py"
Cohesion: 0.06
Nodes (33): Command, Command, ActivityLog, Meta, Announcement, Meta, Category, Meta (+25 more)

### Community 74 - "اپ‌ها (`backend/apps/`)"
Cohesion: 0.06
Nodes (29): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, AdminAction, Meta (+21 more)

### Community 75 - "calculatorModel.ts"
Cohesion: 0.15
Nodes (23): CalculatorResultDef, StagingResult(), allWholeNumbers(), cache, classify(), classifyCalculator(), isNumeric(), LadderRung (+15 more)

### Community 76 - "SectionEdit"
Cohesion: 0.16
Nodes (6): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin, SectionEdit, Meta

### Community 77 - "views_account.py"
Cohesion: 0.11
Nodes (18): OneTimeCode, Meta, AccountForm, CodeForm, LoginForm, PasswordForm, PhoneForm, account() (+10 more)

### Community 79 - "ConsoleTestCase"
Cohesion: 0.16
Nodes (3): ConsoleTestCase, DraftAndSubmitTests, ReviewTests

### Community 81 - "LessonDetailScreen.tsx"
Cohesion: 0.30
Nodes (11): Badge(), joinOpenParens(), LessonBlock, LessonBody(), LessonLine, parenDepth(), parseLessonText(), sectionText() (+3 more)

### Community 82 - "PaymentGateway"
Cohesion: 0.17
Nodes (11): gateway(), gateway_edit(), _gateway_facts(), _gateway_state(), gateway_test(), _masked(), _site_callback(), _site_url() (+3 more)

### Community 85 - "dqc_extras.py"
Cohesion: 0.13
Nodes (16): ago(), get_item(), guest_access_on(), initial(), jdate(), num(), toman(), action_label() (+8 more)

### Community 86 - "clean_profile_boilerplate.py"
Cohesion: 0.09
Nodes (15): clean_text(), Command, cleaned(), is_hypersensitivity_boilerplate(), is_hypersensitivity_boilerplate_en(), is_negative_indication_en(), is_negative_indication_fa(), is_null_placeholder() (+7 more)

### Community 87 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.05
Nodes (18): build.sh script, validate_production_broker(), validate_production_cache(), validate_production_secret_key(), CorsPreflightTests, ProductionSecretKeyTests, DJANGO_SETTINGS_MODULE, release.sh script (+10 more)

### Community 88 - "porter.ts"
Cohesion: 0.23
Nodes (8): firstRule(), isVowelLetter(), porterStem(), Rule, STEP2, STEP3, STEP4, Word

### Community 89 - "gateways.py"
Cohesion: 0.20
Nodes (3): FakeGateway, get_gateway(), start_payment()

### Community 90 - "offline/reader.ts"
Cohesion: 0.24
Nodes (9): OfflineDataset, OfflineLicense, OfflineManifest, keyring, openRecord(), openRecordBase64(), PackageKey, sealed() (+1 more)

### Community 91 - "offline/services.py"
Cohesion: 0.24
Nodes (7): has_paid_plan_with(), is_entitled(), is_guest(), issue_license(), license_days(), LicenseError, _wrap_for()

### Community 92 - "lessons/selectors.py"
Cohesion: 0.07
Nodes (19): AtcCategory, Meta, ChapterProgress, Meta, ReadDrug, Meta, fold(), l2_slug_index() (+11 more)

### Community 93 - "Pharmexa — custom icon prompts"
Cohesion: 0.15
Nodes (12): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups, 9. App identity (optional) (+4 more)

### Community 94 - "offline/reader.ts"
Cohesion: 0.08
Nodes (34): Coding Style & Naming Conventions, پایهٔ Django, lexicompApi, uptodateApi, LexicompDrug, LexicompInteraction, UptodateImage, cache (+26 more)

### Community 96 - "6. Lesson study topics (52)"
Cohesion: 0.15
Nodes (13): 6. Lesson study topics (52), Cardiovascular & blood, Dermatology, Endocrine & metabolism, Gastrointestinal, Infectious disease, Miscellaneous, Musculoskeletal (+5 more)

### Community 97 - "downloader.ts"
Cohesion: 0.20
Nodes (6): downloader, DownloadEvents, PartJob, PartRef, tasks, @kesha-antonov/react-native-background-downloader

### Community 98 - "FlashcardFact"
Cohesion: 0.20
Nodes (5): FlashcardFactAdmin, LeitnerCardAdmin, FlashcardFact, Meta, Command

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

### Community 100 - "VisitorDay"
Cohesion: 0.24
Nodes (4): VisitorDay, Meta, UniqueVisitorTests, visit()

### Community 101 - "Command"
Cohesion: 0.14
Nodes (5): Command, _int(), _json_list(), _name_fa(), Migration

### Community 102 - "downloader.web.ts"
Cohesion: 0.20
Nodes (9): downloader, DownloadEvents, newWorker(), PartJob, PartRef, Run, runFor(), runs (+1 more)

### Community 103 - "۲. راه‌اندازی محیط توسعه"
Cohesion: 0.17
Nodes (12): اندروید و iOS, اپ (Expo), بک‌اند, تست بستهٔ آفلاین بدون باکت, تست و بررسی, روال کار با مخزن, ساخت دیتابیس و اجرای سرور, نسخهٔ وب (+4 more)

### Community 104 - "drugs/admin.py"
Cohesion: 0.27
Nodes (5): AtcCategoryAdmin, AtcCodeAdmin, IngredientAdmin, IngredientProfileSectionAdmin, IngredientProfileSectionInline

### Community 105 - "ImportCalculatorsTests"
Cohesion: 0.32
Nodes (3): _build_sqlite(), ImportCalculatorsTests, _one_calculator()

### Community 107 - "Repository Guidelines"
Cohesion: 0.29
Nodes (6): Build, Test, and Development Commands, Commit & Pull Request Guidelines, Project Structure & Module Organization, Repository Guidelines, Security & Configuration Tips, Testing Guidelines

### Community 109 - "Media"
Cohesion: 0.04
Nodes (39): SiteMaintenanceMiddleware, ContentBlock, Meta, DownloadLink, Meta, Redirect, Meta, Tag (+31 more)

### Community 110 - "AtcSupplementTests"
Cohesion: 0.07
Nodes (7): AtcSupplementTests, CleanBoilerplateInPipelineTests, DrugApiTests, LoadAtcReferenceTests, _make_source_db(), ModelTests, StandardizePipelineUnitsTests

### Community 111 - "bidi.ts"
Cohesion: 0.25
Nodes (7): isolated(), ENGLISH_RUN, hasPersianLetters(), isolateEnglish(), LRI, PDI, RLM

### Community 112 - "accounts/services.py"
Cohesion: 0.05
Nodes (20): SessionTokenAuthentication, SessionTokenAuthenticationScheme, SessionRefreshToken, Meta, hash_session_token(), issue_user_session(), IssuedSession, _new_token() (+12 more)

### Community 113 - "۵. قرارداد API (نسخهٔ ۱)"
Cohesion: 0.11
Nodes (19): Lexicomp — `/lexicomp/` (ویژگی `lexicomp`), Medscape — `/medscape/` (ویژگی `medscape`), UpToDate — `/uptodate/` (ویژگی `uptodate`), آزمون — `/quiz/` (ویژگی `quiz`؛ پرچم `QUIZ_API_ENABLED`), برنامهٔ ساخته‌شده از آنبوردینگ, تغییر دادن API, داروها — `/drugs/` و `/atc/`, دانلود آفلاین — `/offline/` (+11 more)

### Community 115 - "۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی"
Cohesion: 0.12
Nodes (17): اطلاعات غیرمحرمانه‌ای که باید جایی ثبت باشد, بازیابی, بکاپ و بازیابی, حساب‌های سرویس, رازها و چیزهایی که باید امن نگه داشته شوند, رازهای فنی, شاخص‌هایی که مرتب دیده شوند, عیب‌یابی (+9 more)

### Community 116 - "tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, paths, strict, extends, include, expo/tsconfig.base

### Community 117 - "ResultProps"
Cohesion: 0.27
Nodes (10): CalculatorDetail, CalculatorQuestion, ResultProps, LIST_FROM, FieldProps, FlowProps, CalculatorAnswers, ComputedResult (+2 more)

### Community 119 - "UpdatePrompt.tsx"
Cohesion: 0.14
Nodes (21): HelpSheet(), dismissedRecently(), Notes(), Offer, openRelease(), OptionalUpdate(), RequiredUpdate(), UpdatePrompt() (+13 more)

### Community 120 - "sw.js"
Cohesion: 0.38
Nodes (4): inScope(), referencedFiles(), SCOPE, storeShell()

### Community 122 - "AtcCode"
Cohesion: 0.22
Nodes (3): Command, AtcCode, Meta

### Community 125 - "IngredientDetailSerializer"
Cohesion: 0.36
Nodes (3): IngredientDetailSerializer, Meta, LessonDrugSerializer

### Community 126 - "otp.py"
Cohesion: 0.09
Nodes (19): account_for_signup(), _hash(), _minutes(), _new_code(), OtpError, request_code(), user_for_phone(), verify_code() (+11 more)

### Community 127 - "jalali.ts"
Cohesion: 0.19
Nodes (19): OfflinePackageInfo, InstalledPackage, licenseExpiresAt(), OfflineErrorCode, PendingPackage, PackagePhase, PackageView, BREAKS (+11 more)

### Community 134 - "OfflinePackageCard.tsx"
Cohesion: 0.20
Nodes (15): OfflineDownloadButton(), OfflineSheet(), ERROR_TEXT, LOGO, NAME, OfflinePackageCard(), PHASE_TEXT, SUPPORTS_BACKGROUND (+7 more)

### Community 152 - "drugs/serializers.py"
Cohesion: 0.25
Nodes (5): LessonDrugSectionSerializer, Meta, LessonSectionSerializer, ProfileSectionSerializer, Meta

### Community 182 - "۱۲. سایت `pharmenta.ir` و پنل محتوا"
Cohesion: 0.05
Nodes (35): RequestIdMiddleware, SiteHostMiddleware, atc_groups(), feature_icon(), nav_on(), oneline(), person(), split_highlight() (+27 more)

### Community 185 - "DateResult.tsx"
Cohesion: 0.48
Nodes (6): hasPersian(), Rows(), DateResult(), useDateFormat(), parseAge(), parseDateText()

### Community 196 - "session.ts"
Cohesion: 0.29
Nodes (5): get(), KEYS, sessionStore, StoredSession, expo-secure-store

### Community 204 - "۸. دیپلوی"
Cohesion: 0.12
Nodes (16): CI, امنیت و هشدار نصب, اپ اندروید و iOS, برگرداندن یک دیپلوی خراب, بک‌اند, جریان دیپلوی, حجم APK, راه‌اندازی از صفر (یک بار) (+8 more)

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
- **9 isolated node(s):** `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-build-properties`, `expo-splash-screen`, `react-dom` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1613 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **88 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `useTheme` to `CalculatorDetailScreen.tsx`, `useTheme`, `package.json`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`, `test_phone_auth.py`?**
  _High betweenness centrality (0.164) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `AppText()` (e.g. with `زبان، جهت و تم` and `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅`) actually correct?**
  _`AppText()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-build-properties` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.03614457831325301 - nodes in this community are weakly interconnected._
- **Why does `UserSession` connect `test_phone_auth.py` to `WebsiteAuthTests`, `console/views.py`, `اپ‌ها (`backend/apps/`)`, `PlatformAPIError`, `useTheme`, `config.py`, `accounts/services.py`, `accounts/views.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`, `otp.py`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.022123893805309734 - nodes in this community are weakly interconnected._
- **Why does `اپ‌ها (`backend/apps/`)` connect `اپ‌ها (`backend/apps/`)` to `IngredientProfileSection`, `test_panel.py`, `console/views.py`, `Post`, `views_public.py`, `flashcards/views.py`, `billing/services.py`, `accounts/views.py`, `quiz/views.py`, `progress/tests.py`, `Calculator`, `SectionEditRequest`, `Article`, `config.py`, `planning.py`, `۱۲. سایت `pharmenta.ir` و پنل محتوا`, `test_phone_auth.py`, `website/models.py`, `SectionEdit`, `views_account.py`, `PaymentGateway`, `lessons/selectors.py`, `FlashcardFact`, `accounts/services.py`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._