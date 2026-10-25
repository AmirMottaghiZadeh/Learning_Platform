# Graph Report - Learning Platform  (2026-10-25)

## Corpus Check
- 509 files · ~404,914 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 32 file(s) not represented in the graph (top: (none) 11, .ttf 7, .woff2 4)

## Summary
- 4868 nodes · 13647 edges · 208 communities (116 shown, 92 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1222 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a2afdc61`
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
- auth.ts
- flashcards/views.py
- UserSerializer
- billing/views.py
- App.tsx
- GatewayError
- ImportOpenfdaTests
- billing/services.py
- Page
- 0003_about_contact_text.py
- config.py
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
- BuildTests
- store.ts
- Calculator
- SectionEditRequest
- re
- CalculatorDetailScreen.tsx
- offline/views.py
- api.py
- package.json
- import_calculators.py
- QuizApiTests
- medscape/views.py
- progress/views.py
- release.mjs
- config.py
- json
- drugs/serializers.py
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
- django_conf
- throttling.py
- Post
- WebsiteAuthTests
- logging
- ۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین
- uptodate/services.py
- dependencies
- medscape/tests.py
- crypto.web.ts
- panel.js
- website/models.py
- اپ‌ها (`backend/apps/`)
- django_core_management
- SectionEdit
- views_account.py
- maintenance_urls.py
- ConsoleTestCase
- StudyTopicsCoverageTests
- LessonDetailScreen.tsx
- StandardizeUnitsTests
- UptodateTests
- MedscapeApiTests
- dqc_extras.py
- clean_profile_boilerplate.py
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- porter.ts
- storage.py
- ReviewTests
- guest.py
- lessons/selectors.py
- Pharmexa — custom icon prompts
- offline/reader.ts
- docs/README.md
- 6. Lesson study topics (52)
- files.ts
- django_core_management_base
- site.js
- drugs/reference_db.py
- Command
- downloader.web.ts
- ۲. راه‌اندازی محیط توسعه
- drugs/admin.py
- ImportCalculatorsTests
- ReferenceDbTests
- Repository Guidelines
- Section
- Media
- TestCase
- bidi.ts
- accounts/services.py
- ۵. قرارداد API (نسخهٔ ۱)
- bootstrap_superuser.py
- ۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی
- tsconfig.json
- AtcSupplementTests
- django_apps
- back.ts
- sw.js
- Command
- Media
- ModelTests
- pagination.py
- settings/base.py
- otp.py
- jalali.ts
- IngredientProfileSection
- docker-start.sh
- billing/apps.py
- DrugApiTests
- .claude/CLAUDE.md
- OfflinePackageCard.tsx
- app.config.js
- .mcp.json
- 0005_atccode_name_fa.py
- ۱۲. سایت `pharmenta.ir` و پنل محتوا
- LoadAtcReferenceTests
- brand_file
- 0004_clear_rule_based_facts.py
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
- 0007_clear_rule_based_bank.py
- writing
- ۸. دیپلوی
- ۱. معرفی و معماری
- ۱۰. مرجع سریع دستورها
- کنسول فروش (`/ops/`)
- مستندات فارمنتا
- فارمنتا (Pharmenta)

## God Nodes (most connected - your core abstractions)
1. `useTheme()` - 171 edges
2. `AppText()` - 166 edges
3. `useLang()` - 152 edges
4. `react` - 81 edges
5. `PlatformAPIError` - 79 edges
6. `Ingredient` - 72 edges
7. `react-native` - 70 edges
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

## Communities (208 total, 92 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.04
Nodes (74): flashcardsApi, quizApi, releaseApi, AppReleaseInfo, AtcCode, AtcGroup, BoxSummary, CalculatorCategoryRef (+66 more)

### Community 1 - "django_db"
Cohesion: 0.03
Nodes (43): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+35 more)

### Community 2 - "test_panel.py"
Cohesion: 0.06
Nodes (10): AdminTests, AuthorTests, AuthTests, InboxTests, make_user(), MediaTests, PermissionTests, PostTests (+2 more)

### Community 3 - "console/views.py"
Cohesion: 0.05
Nodes (71): DiscountForm, FeatureEditForm, Meta, FeatureForm, Meta, latin_digits(), parse_amount(), parse_jalali() (+63 more)

### Community 4 - "react"
Cohesion: 0.06
Nodes (82): calculatorsApi, lessonsApi, meApi, medscapeApi, LessonGroup, MedscapeKind, ALPHABET, AlphabeticalArticleList() (+74 more)

### Community 5 - "Post"
Cohesion: 0.06
Nodes (61): ActivityLog, Meta, Comment, Meta, ContactMessage, Meta, StaffRole, Meta (+53 more)

### Community 6 - "useTheme"
Cohesion: 0.14
Nodes (73): قابلیت‌ها, افزودن صفحهٔ تازه, قواعد کدنویسی اپ, ناوبری, HelpSheet(), LoadFailed(), AppText(), Card() (+65 more)

### Community 7 - "views_public.py"
Cohesion: 0.04
Nodes (63): site(), SiteMaintenanceMiddleware, SiteSettings, Meta, article(), breadcrumbs(), editorial_team(), home_graph() (+55 more)

### Community 8 - ".reverse"
Cohesion: 0.04
Nodes (16): AuthenticationSecurityTests, OnboardingTests, enabled_gateways(), wrapper(), AccessTests, ConsoleTestCase, DeleteUserTests, DiscountAndReportTests (+8 more)

### Community 9 - "auth.ts"
Cohesion: 0.06
Nodes (33): حساب و احراز هویت — `/auth/`, API_BASE_URL, apiClient, ApiErrorBody, AuthController, configureAuth(), RetryableConfig, unwrapList() (+25 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.05
Nodes (38): all_decks(), _carded_slugs(), deck_slugs(), next_topic(), progress_map(), topic_meta(), LeitnerCard, Meta (+30 more)

### Community 11 - "UserSerializer"
Cohesion: 0.18
Nodes (7): LearnerProfileSerializer, Meta, OnboardingSerializer, UserSerializer, Meta, MeView, OnboardingView

### Community 12 - "billing/views.py"
Cohesion: 0.05
Nodes (46): start_payment(), is_guest(), Order, Meta, CatalogSerializer, CheckoutSerializer, MyAccessSerializer, MyEntitlementSerializer (+38 more)

### Community 13 - "App.tsx"
Cohesion: 0.06
Nodes (57): ارتباط با API و کش, دانلود آفلاین (`src/offline/`), زبان، جهت و تم, ساختار `frontend/src/`, شروع اپ, نمایش بزرگ عکس و جدول, وب‌اپ و PWA, پیکربندی اپ بومی (+49 more)

### Community 14 - "GatewayError"
Cohesion: 0.06
Nodes (13): FakeGateway, GatewayError, get_gateway(), _post_json(), SepGateway, Verification, ZarinpalGateway, ZibalGateway (+5 more)

### Community 16 - "billing/services.py"
Cohesion: 0.06
Nodes (16): Access, active_entitlements(), check_feature(), content_lock(), effective_features(), take(), free_plan(), grant() (+8 more)

### Community 17 - "Page"
Cohesion: 0.10
Nodes (5): clean_html(), _Cleaner, safe_url(), _Text, SanitizeTests

### Community 19 - "config.py"
Cohesion: 0.11
Nodes (14): BillingConfig, current(), gateway_spec(), _gateways(), GatewaySpec, _load(), row(), _settings_changed() (+6 more)

### Community 20 - "accounts/views.py"
Cohesion: 0.07
Nodes (46): CanManagePlatformRoles, AuthTokenResponseSerializer, LoginSerializer, OtpRequestResponseSerializer, OtpRequestSerializer, OtpVerifySerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer (+38 more)

### Community 21 - "fix_results"
Cohesion: 0.12
Nodes (8): fix_results(), fix_strings_fa(), renumber_from_one(), apply_fixes(), Migration, apply_fixes(), Migration, FormulaErrataTests

### Community 22 - "data_quality_center/views.py"
Cohesion: 0.12
Nodes (25): warning_count(), section_state(), _diffs(), discard(), history(), _login_key(), login_view(), logout_view() (+17 more)

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.07
Nodes (57): CalculatorErrorCheck, CalculatorResultDef, Tier, useLiveScore(), buildHeuristicSeeds(), cartesian(), classifyResultTone(), computeCalculator() (+49 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.06
Nodes (43): slugs_for_topic(), record_quiz_answers(), BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, ingredient_ids_for_selection(), preview_selection(), sample_bank_questions() (+35 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.05
Nodes (81): MedscapeBlock, MedscapeSection, useBleedTop(), countMatches(), FindState, highlight(), ListMarker(), LTR (+73 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.09
Nodes (18): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, _categories_for_generics(), check_interactions(), close_all(), _conn(), _dir() (+10 more)

### Community 28 - ".request_code"
Cohesion: 0.09
Nodes (21): CodeRuleTests, PhoneAuthTestCase, ResetTests, SignUpTests, برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی, روش تبدیل پیشنهادها به کلمات کلیدی معتبر, ساخت Analytics از ابتدا (+13 more)

### Community 29 - "progress/tests.py"
Cohesion: 0.06
Nodes (21): seed(), DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin, DailyStudy, Meta, LearnerProgress (+13 more)

### Community 30 - "core/views.py"
Cohesion: 0.14
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 31 - "lessons/views.py"
Cohesion: 0.08
Nodes (25): _applies(), require_atc_content(), _require_content(), require_topic_content(), LessonDrugSerializer, get_chapter(), get_lesson_drug(), _topic_lookup() (+17 more)

### Community 32 - "BuildTests"
Cohesion: 0.09
Nodes (5): clear_cache(), ApiTests, BucketManifestTests, BuildTests, DownloadHostTests

### Community 33 - "store.ts"
Cohesion: 0.11
Nodes (42): offlineApi, OfflinePackageInfo, useOfflineBoot(), requestPersistence(), closeReaders(), bootOffline(), cancel(), currentUserId() (+34 more)

### Community 34 - "Calculator"
Cohesion: 0.08
Nodes (18): Calculator, Meta, CalculatorCategory, Meta, CalculatorTag, Meta, CalculatorCategorySerializer, Meta (+10 more)

### Community 35 - "SectionEditRequest"
Cohesion: 0.10
Nodes (21): ReviewEvent, Meta, SectionEditRequest, Meta, approve(), _clean(), _client_ip(), _close() (+13 more)

### Community 36 - "re"
Cohesion: 0.09
Nodes (19): _fa_keys_standardized(), fix_questions(), _stage_names_without_prefix(), _title_formula_as_result(), _with_choices(), _with_unit(), apply_fixes(), Migration (+11 more)

### Community 37 - "CalculatorDetailScreen.tsx"
Cohesion: 0.12
Nodes (34): CalculatorQuestion, describeInputs(), DaysInput(), Field(), QuestionTitle(), CardsFlow(), ChecklistFlow(), flowLayout (+26 more)

### Community 38 - "offline/views.py"
Cohesion: 0.08
Nodes (24): build_matches_dataset(), LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer, PackageFileUrlSerializer, PackageManifestSerializer, PackageUrlsRequestSerializer (+16 more)

### Community 39 - "api.py"
Cohesion: 0.07
Nodes (16): LatestReleaseSerializer, note_lines(), ReleaseCheckSerializer, ReleaseCheckView, ReleaseQuerySerializer, AppRelease, Meta, version_code() (+8 more)

### Community 40 - "package.json"
Cohesion: 0.07
Nodes (27): devDependencies, @types/react, typescript, main, name, private, scripts, android (+19 more)

### Community 41 - "import_calculators.py"
Cohesion: 0.14
Nodes (12): standardize_fa_units(), Command, _error_checks_for(), _formula_strings_fa(), _import_categories(), _import_tags(), _questions_for(), _references_for() (+4 more)

### Community 42 - "QuizApiTests"
Cohesion: 0.09
Nodes (4): QuizAccessTests, QuizApiTests, QuizLockedTests, _seed_atc_world()

### Community 43 - "medscape/views.py"
Cohesion: 0.13
Nodes (10): ArticleDetailSerializer, Meta, ArticleImageSerializer, Meta, ArticleListSerializer, Meta, ArticleDetailView, ArticleImageDetailView (+2 more)

### Community 44 - "progress/views.py"
Cohesion: 0.09
Nodes (27): require_feature(), Mistake, Meta, DashboardSerializer, FocusRowSerializer, FocusSessionSerializer, MistakeSerializer, Meta (+19 more)

### Community 45 - "release.mjs"
Cohesion: 0.09
Nodes (15): appJson, at, dryRun, file(), frontend, [kind, ...flags], lock, [major, minor, patch] (+7 more)

### Community 46 - "config.py"
Cohesion: 0.08
Nodes (4): clear_cache(), GuestAccessTests, GuestConsoleTests, PurchaseFlowTests

### Community 47 - "json"
Cohesion: 0.07
Nodes (23): build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections(), _varints(), Command (+15 more)

### Community 48 - "drugs/serializers.py"
Cohesion: 0.06
Nodes (20): Command, AtcCode, Meta, Ingredient, Meta, AtcCodeSerializer, Meta, IngredientDetailSerializer (+12 more)

### Community 49 - "FlashcardApiTests"
Cohesion: 0.07
Nodes (10): FlashcardFactAdmin, LeitnerCardAdmin, FlashcardFact, Meta, FlashcardApiTests, FlashcardLockedTests, _refresh_facts(), _rich_ingredient() (+2 more)

### Community 50 - "LessonTaxonomyTests"
Cohesion: 0.08
Nodes (4): DrugSearchTests, _ingredient(), LessonTaxonomyFallbackTests, LessonTaxonomyTests

### Community 51 - "expo"
Cohesion: 0.06
Nodes (32): backgroundColor, foregroundImage, adaptiveIcon, allowBackup, blockedPermissions, package, projectId, typedRoutes (+24 more)

### Community 52 - "planning.py"
Cohesion: 0.07
Nodes (28): mark_drug_read(), topic_chapters(), topic_progress(), StudyPlanItem, Meta, complete_item(), ensure_today_items(), _flashcard_recall_for_slugs() (+20 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.16
Nodes (7): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label()

### Community 54 - "common.tsx"
Cohesion: 0.09
Nodes (82): CalculatorDetail, bandFor(), Chip(), Collapse(), Explain(), Extra, Extras(), fmt() (+74 more)

### Community 55 - "data_quality_center/tests.py"
Cohesion: 0.24
Nodes (6): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), word_diff(), CheckTests

### Community 56 - "django_utils"
Cohesion: 0.09
Nodes (4): Command, rewrite_summaries(), _make_snapshot(), _make_snapshot()

### Community 57 - "Article"
Cohesion: 0.05
Nodes (24): Command, export(), load(), Command, _DryRun, ReferenceImportCommand, dumps(), expected_count() (+16 more)

### Community 58 - "test_phone_auth.py"
Cohesion: 0.11
Nodes (9): EmailOrUsernameBackend, LearnerProfile, InvalidPhone, looks_like_phone(), normalize_phone(), PhoneField, NormalizePhoneTests, ProfileTests (+1 more)

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.12
Nodes (16): HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت, دادهٔ مرجع (UpToDate و Lexicomp), دیتابیس، کش و آمادگی, سایت (+8 more)

### Community 60 - "billing/tests.py"
Cohesion: 0.13
Nodes (18): _div(), fa_digits(), format_date(), _jal_cal(), _mod(), month_start(), to_gregorian(), to_jalali() (+10 more)

### Community 61 - "files.web.ts"
Cohesion: 0.19
Nodes (9): file(), forget(), partSize(), readRange(), removeBuild(), removeOtherBuilds(), removePart(), snapshots (+1 more)

### Community 62 - "django_conf"
Cohesion: 0.11
Nodes (8): Migration, Migration, enqueue(), ReviewForm, SectionEditForm, Migration, Migration, Migration

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "Post"
Cohesion: 0.07
Nodes (7): Post, Meta, plain_text(), CommentTests, DownloadAndMachineTests, make_post(), PostVisibilityTests

### Community 66 - "logging"
Cohesion: 0.07
Nodes (10): password_reset_url_for_user(), send_password_reset_email(), send_password_reset_emails_for_email(), send_password_reset_email_task(), PlatformTask, retry_delay_seconds(), get_request_id(), JsonFormatter (+2 more)

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (26): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+18 more)

### Community 68 - "uptodate/services.py"
Cohesion: 0.11
Nodes (18): Command, article_from_row(), _dir(), get_image(), get_topic(), is_available(), mysql_config(), _mysql_conn() (+10 more)

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
Cohesion: 0.04
Nodes (23): DailyStat, Meta, Page, Meta, PostRevision, Meta, Subscriber, Meta (+15 more)

### Community 74 - "اپ‌ها (`backend/apps/`)"
Cohesion: 0.08
Nodes (22): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, AdminAction, Meta (+14 more)

### Community 75 - "django_core_management"
Cohesion: 0.15
Nodes (3): HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests

### Community 76 - "SectionEdit"
Cohesion: 0.15
Nodes (7): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin, SectionEdit, Meta, مرکز کیفیت داده (`/ops/data-quality/`)

### Community 77 - "views_account.py"
Cohesion: 0.11
Nodes (15): AccountForm, CodeForm, LoginForm, PasswordForm, PhoneForm, account(), login_phone(), _login_url() (+7 more)

### Community 81 - "LessonDetailScreen.tsx"
Cohesion: 0.24
Nodes (12): SectionTone, joinOpenParens(), LessonBlock, LessonLine, parenDepth(), parseLessonText(), sectionText(), splitIssues() (+4 more)

### Community 85 - "dqc_extras.py"
Cohesion: 0.22
Nodes (9): action_label(), action_tone(), ago(), dict_get(), fa_digits(), percent(), status_label(), status_tone() (+1 more)

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
Cohesion: 0.12
Nodes (13): Command, cors_rule(), _request(), file_urls(), is_configured(), latest_manifest(), local_dir(), local_file_for_token() (+5 more)

### Community 91 - "guest.py"
Cohesion: 0.10
Nodes (15): create_guest(), GuestSessionView, GuestStatusView, _first_message(), _message_from_data(), _normalize_code(), platform_exception_handler(), UptodateArticleSerializer (+7 more)

### Community 92 - "lessons/selectors.py"
Cohesion: 0.07
Nodes (23): Command, AtcCategory, Meta, due_card_count(), ChapterProgress, Meta, ReadDrug, Meta (+15 more)

### Community 93 - "Pharmexa — custom icon prompts"
Cohesion: 0.15
Nodes (12): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups, 9. App identity (optional) (+4 more)

### Community 94 - "offline/reader.ts"
Cohesion: 0.07
Nodes (41): Coding Style & Naming Conventions, پایهٔ Django, lexicompApi, uptodateApi, LexicompDrug, LexicompInteraction, OfflineDataset, OfflineManifest (+33 more)

### Community 96 - "6. Lesson study topics (52)"
Cohesion: 0.15
Nodes (13): 6. Lesson study topics (52), Cardiovascular & blood, Dermatology, Endocrine & metabolism, Gastrointestinal, Infectious disease, Miscellaneous, Musculoskeletal (+5 more)

### Community 97 - "files.ts"
Cohesion: 0.13
Nodes (18): downloader, DownloadEvents, PartJob, PartRef, tasks, buildDir(), closeHandles(), ensureBuildDir() (+10 more)

### Community 98 - "django_core_management_base"
Cohesion: 0.11
Nodes (5): Command, ensure_title_search_index(), _has_title_search_index(), MysqlTitleIndexTests, MysqlTitleSearchTests

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

### Community 100 - "drugs/reference_db.py"
Cohesion: 0.07
Nodes (11): Command, Command, _DryRun, _checked(), _digest(), export(), load(), open_parts() (+3 more)

### Community 101 - "Command"
Cohesion: 0.21
Nodes (4): Command, _int(), _json_list(), _name_fa()

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
Cohesion: 0.18
Nodes (5): _build_sqlite(), FaUnitsTests, ImportCalculatorsTests, _one_calculator(), QuestionUnitTests

### Community 107 - "Repository Guidelines"
Cohesion: 0.29
Nodes (6): Build, Test, and Development Commands, Commit & Pull Request Guidelines, Project Structure & Module Organization, Repository Guidelines, Security & Configuration Tips, Testing Guidelines

### Community 109 - "Media"
Cohesion: 0.03
Nodes (48): Command, Command, Announcement, Meta, Category, Meta, ContentBlock, Meta (+40 more)

### Community 110 - "TestCase"
Cohesion: 0.28
Nodes (3): CleanBoilerplateInPipelineTests, _make_source_db(), StandardizePipelineUnitsTests

### Community 111 - "bidi.ts"
Cohesion: 0.25
Nodes (7): isolated(), ENGLISH_RUN, hasPersianLetters(), isolateEnglish(), LRI, PDI, RLM

### Community 112 - "accounts/services.py"
Cohesion: 0.07
Nodes (33): Role, Meta, RoleAssignment, Meta, SecurityAuditEvent, Meta, SessionRefreshToken, Meta (+25 more)

### Community 113 - "۵. قرارداد API (نسخهٔ ۱)"
Cohesion: 0.11
Nodes (18): Lexicomp — `/lexicomp/` (ویژگی `lexicomp`), Medscape — `/medscape/` (ویژگی `medscape`), UpToDate — `/uptodate/` (ویژگی `uptodate`), آزمون — `/quiz/` (ویژگی `quiz`؛ پرچم `QUIZ_API_ENABLED`), تغییر دادن API, داروها — `/drugs/` و `/atc/`, دانلود آفلاین — `/offline/`, درس‌نامه — `/lessons/` (ویژگی `lessons`) (+10 more)

### Community 115 - "۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی"
Cohesion: 0.12
Nodes (17): اطلاعات غیرمحرمانه‌ای که باید جایی ثبت باشد, بازیابی, بکاپ و بازیابی, حساب‌های سرویس, رازها و چیزهایی که باید امن نگه داشته شوند, رازهای فنی, شاخص‌هایی که مرتب دیده شوند, عیب‌یابی (+9 more)

### Community 116 - "tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, paths, strict, extends, include, expo/tsconfig.base

### Community 119 - "back.ts"
Cohesion: 0.28
Nodes (8): canGoBack(), installWebBackGuard(), Interceptor, interceptors, listeners, notify(), subscribeBackState(), WebBackGuard()

### Community 120 - "sw.js"
Cohesion: 0.38
Nodes (4): inScope(), referencedFiles(), SCOPE, storeShell()

### Community 125 - "settings/base.py"
Cohesion: 0.11
Nodes (3): build.sh script, DJANGO_SETTINGS_MODULE, release.sh script

### Community 126 - "otp.py"
Cohesion: 0.08
Nodes (20): OneTimeCode, Meta, account_for_signup(), _hash(), _minutes(), _new_code(), OtpError, request_code() (+12 more)

### Community 127 - "jalali.ts"
Cohesion: 0.33
Nodes (15): DateInput(), BREAKS, d2g(), d2j(), dateToMs(), div(), g2d(), isValidGregorian() (+7 more)

### Community 134 - "OfflinePackageCard.tsx"
Cohesion: 0.17
Nodes (21): OfflineDownloadButton(), OfflineSheet(), ERROR_TEXT, LOGO, NAME, OfflinePackageCard(), PHASE_TEXT, SUPPORTS_BACKGROUND (+13 more)

### Community 182 - "۱۲. سایت `pharmenta.ir` و پنل محتوا"
Cohesion: 0.05
Nodes (35): RequestIdMiddleware, SiteHostMiddleware, atc_groups(), feature_icon(), nav_on(), oneline(), person(), split_highlight() (+27 more)

### Community 196 - "authentication.py"
Cohesion: 0.12
Nodes (7): SessionTokenAuthentication, SessionTokenAuthenticationScheme, احراز هویت و حساب, ثبت‌نام و ورود, رمز عبور, نشست و توکن, نقش‌ها و رویدادهای امنیتی

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
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1594 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **92 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `App.tsx` to `accounts/services.py`, `useTheme`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.146) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `AppText()` (e.g. with `زبان، جهت و تم` and `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅`) actually correct?**
  _`AppText()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-build-properties` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.0393028024606972 - nodes in this community are weakly interconnected._
- **Why does `UserSession` connect `accounts/services.py` to `WebsiteAuthTests`, `console/views.py`, `authentication.py`, `اپ‌ها (`backend/apps/`)`, `App.tsx`, `config.py`, `config.py`, `accounts/views.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`, `test_phone_auth.py`, `guest.py`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.02562342713337909 - nodes in this community are weakly interconnected._
- **Why does `اپ‌ها (`backend/apps/`)` connect `اپ‌ها (`backend/apps/`)` to `IngredientProfileSection`, `console/views.py`, `Post`, `views_public.py`, `flashcards/views.py`, `billing/views.py`, `quiz/views.py`, `progress/tests.py`, `Calculator`, `SectionEditRequest`, `drugs/serializers.py`, `FlashcardApiTests`, `۱۲. سایت `pharmenta.ir` و پنل محتوا`, `Article`, `Post`, `website/models.py`, `SectionEdit`, `lessons/selectors.py`, `accounts/services.py`, `Media`, `otp.py`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._