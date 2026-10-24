# Graph Report - Learning Platform  (2026-10-25)

## Corpus Check
- 501 files · ~400,023 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 32 file(s) not represented in the graph (top: (none) 11, .ttf 7, .woff2 4)

## Summary
- 4775 nodes · 13435 edges · 206 communities (122 shown, 84 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1215 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `455be433`
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
- billing/views.py
- ۴. اپ (Expo — اندروید، iOS و وب)
- GatewayError
- ImportOpenfdaTests
- billing/services.py
- Page
- views_drugs.py
- config.py
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
- BuildTests
- store.ts
- Calculator
- SectionEditRequest
- re
- CalculatorDetailScreen.tsx
- offline/views.py
- VerdictResult.tsx
- calculatorModel.ts
- Ingredient
- QuizApiTests
- sources.ts
- progress/views.py
- accounts/permissions.py
- config.py
- builders.py
- drugs/serializers.py
- FlashcardApiTests
- AtcCode
- expo
- planning.py
- import_medscape_articles.py
- ResultCard
- data_quality_center/tests.py
- django_utils
- Article
- test_phone_auth.py
- ۶. پیکربندی و متغیرهای محیطی
- billing/tests.py
- 6. Lesson study topics (52)
- ApiTests
- throttling.py
- Post
- WebsiteAuthTests
- tasks.py
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
- common.tsx
- UptodateTests
- pack.py
- dqc_extras.py
- clean_profile_boilerplate.py
- production.py
- porter.ts
- storage.py
- downloader.ts
- uptodate/views.py
- progress/selectors.py
- DrugPageTests
- offline/reader.ts
- docs/README.md
- exceptions.py
- files.ts
- django_core_management_base
- site.js
- drugs/reference_db.py
- Command
- downloader.web.ts
- billing_extras.py
- offline/services.py
- ImportCalculatorsTests
- ReferenceDbTests
- Repository Guidelines
- celery_tasks.py
- Media
- Command
- bidi.ts
- accounts/services.py
- ۵. قرارداد API (نسخهٔ ۱)
- bootstrap_superuser.py
- ۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی
- tsconfig.json
- ۱۲. سایت `pharmenta.ir` و پنل محتوا
- django_apps
- back.ts
- sw.js
- Command
- PackageFileView
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- pagination.py
- manage.py
- otp.py
- jalali.ts
- logging.py
- docker-start.sh
- billing/apps.py
- .claude/CLAUDE.md
- OfflinePackageCard.tsx
- app.config.js
- .mcp.json
- CorsPreflightTests
- ۳. بک‌اند (Django)
- _snippet
- celery.py
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
- SessionTokenAuthenticationScheme
- ۸. دیپلوی
- ۱. معرفی و معماری
- ۱۰. مرجع سریع دستورها
- کنسول فروش (`/ops/`)
- مستندات فارمنتا
- فارمنتا (Pharmenta)

## God Nodes (most connected - your core abstractions)
1. `useTheme()` - 165 edges
2. `AppText()` - 160 edges
3. `useLang()` - 146 edges
4. `PlatformAPIError` - 79 edges
5. `react` - 79 edges
6. `Ingredient` - 72 edges
7. `react-native` - 68 edges
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

## Communities (206 total, 84 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.04
Nodes (89): حساب و احراز هویت — `/auth/`, flashcardsApi, lessonsApi, quizApi, AtcCode, AtcGroup, AuthTokenResponse, BoxSummary (+81 more)

### Community 1 - "django_db"
Cohesion: 0.02
Nodes (51): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+43 more)

### Community 2 - "test_panel.py"
Cohesion: 0.06
Nodes (8): AdminTests, AuthorTests, AuthTests, make_user(), MediaTests, PermissionTests, PostTests, url()

### Community 3 - "console/views.py"
Cohesion: 0.05
Nodes (70): DiscountForm, FeatureEditForm, Meta, FeatureForm, Meta, latin_digits(), parse_amount(), parse_jalali() (+62 more)

### Community 4 - "react"
Cohesion: 0.07
Nodes (68): calculatorsApi, meApi, medscapeApi, MedscapeKind, ALPHABET, AlphabeticalArticleList(), buildOffsets(), groupAlphabetically() (+60 more)

### Community 5 - "Post"
Cohesion: 0.07
Nodes (55): DailyStat, Meta, Subscriber, Meta, orders(), plans(), subscriptions(), comment_action() (+47 more)

### Community 6 - "useTheme"
Cohesion: 0.14
Nodes (78): قابلیت‌ها, افزودن صفحهٔ تازه, قواعد کدنویسی اپ, AppShell(), AuthLayout(), BottomNav(), ChecklistFlow(), LiveScore() (+70 more)

### Community 7 - "views_public.py"
Cohesion: 0.05
Nodes (44): site(), SiteMaintenanceMiddleware, Announcement, Meta, SiteSettings, Meta, add_toc(), blocks() (+36 more)

### Community 8 - ".reverse"
Cohesion: 0.05
Nodes (11): AuthenticationSecurityTests, OnboardingTests, wrapper(), PlanBuilderTests, UsersPageTests, AccessTests, Section, _safe_next() (+3 more)

### Community 9 - "package.json"
Cohesion: 0.04
Nodes (76): شروع اپ, App(), Gate(), ThemedStatusBar(), main, name, private, version (+68 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.07
Nodes (30): deck_slugs(), next_topic(), progress_map(), topic_meta(), TopicProgress, Meta, BoxSummarySerializer, _card_back_fields() (+22 more)

### Community 11 - "accounts/serializers.py"
Cohesion: 0.08
Nodes (15): LearnerProfile, AuthTokenResponseSerializer, LearnerProfileSerializer, Meta, OnboardingSerializer, OtpRequestResponseSerializer, PasswordSetSerializer, UserSerializer (+7 more)

### Community 12 - "billing/views.py"
Cohesion: 0.07
Nodes (32): is_guest(), Order, Meta, CatalogSerializer, CheckoutSerializer, MyAccessSerializer, MyEntitlementSerializer, Meta (+24 more)

### Community 13 - "۴. اپ (Expo — اندروید، iOS و وب)"
Cohesion: 0.22
Nodes (9): ارتباط با API و کش, دانلود آفلاین (`src/offline/`), زبان، جهت و تم, ساختار `frontend/src/`, ناوبری, نمایش بزرگ عکس و جدول, وب‌اپ و PWA, پیکربندی اپ بومی (+1 more)

### Community 14 - "GatewayError"
Cohesion: 0.06
Nodes (13): FakeGateway, GatewayError, get_gateway(), _post_json(), SepGateway, Verification, ZarinpalGateway, ZibalGateway (+5 more)

### Community 15 - "ImportOpenfdaTests"
Cohesion: 0.06
Nodes (8): AtcSupplementTests, CleanBoilerplateInPipelineTests, DrugApiTests, ImportOpenfdaTests, LoadAtcReferenceTests, _make_source_db(), ModelTests, StandardizePipelineUnitsTests

### Community 16 - "billing/services.py"
Cohesion: 0.05
Nodes (31): start_payment(), DiscountCode, Meta, Access, active_entitlements(), BillingError, check_feature(), content_lock() (+23 more)

### Community 17 - "Page"
Cohesion: 0.08
Nodes (6): clean_html(), _Cleaner, plain_text(), safe_url(), _Text, SanitizeTests

### Community 18 - "views_drugs.py"
Cohesion: 0.05
Nodes (29): fa(), Command, render_links(), link(), Migration, Migration, article(), breadcrumbs() (+21 more)

### Community 19 - "config.py"
Cohesion: 0.08
Nodes (16): BillingConfig, current(), enabled_gateways(), gateway_spec(), _gateways(), GatewaySpec, _load(), row() (+8 more)

### Community 20 - "accounts/views.py"
Cohesion: 0.07
Nodes (41): LoginSerializer, OtpRequestSerializer, OtpVerifySerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, PasswordResetResponseSerializer, RefreshSessionSerializer, RegisterSerializer (+33 more)

### Community 21 - "import_calculators.py"
Cohesion: 0.05
Nodes (16): fix_questions(), fix_results(), fix_strings_fa(), renumber_from_one(), _with_choices(), apply_fixes(), Migration, apply_fixes() (+8 more)

### Community 22 - "data_quality_center/views.py"
Cohesion: 0.12
Nodes (25): warning_count(), section_state(), _diffs(), discard(), history(), _login_key(), login_view(), logout_view() (+17 more)

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.08
Nodes (57): CalculatorErrorCheck, CalculatorResultDef, useLiveScore(), buildHeuristicSeeds(), cartesian(), checkErrors(), classifyResultTone(), computeCalculator() (+49 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.07
Nodes (37): record_quiz_answers(), BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, preview_selection(), best_score_pct_for_topic(), _finished_sessions(), _finished_topic_sessions() (+29 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.05
Nodes (83): MedscapeBlock, MedscapeSection, useBleedTop(), countMatches(), FindState, highlight(), ListMarker(), LTR (+75 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.11
Nodes (12): _categories_for_generics(), check_interactions(), close_all(), _conn(), _dir(), _exceptions_for_monographs(), is_available(), _names_for_generics() (+4 more)

### Community 28 - ".request_code"
Cohesion: 0.09
Nodes (21): CodeRuleTests, PhoneAuthTestCase, ResetTests, SignUpTests, برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی, روش تبدیل پیشنهادها به کلمات کلیدی معتبر, ساخت Analytics از ابتدا (+13 more)

### Community 29 - "progress/tests.py"
Cohesion: 0.07
Nodes (13): Migration, seed(), bump_mistake(), record_study(), _touch_streak(), MaintenancePlanAndApiTests, MeApiTests, ProgressServiceTests (+5 more)

### Community 30 - "core/views.py"
Cohesion: 0.14
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 31 - "lessons/views.py"
Cohesion: 0.09
Nodes (23): _applies(), require_atc_content(), _require_content(), require_feature(), require_topic_content(), _topic_lookup(), topics_for_chapter(), AtcGroupSerializer (+15 more)

### Community 32 - "BuildTests"
Cohesion: 0.09
Nodes (8): clear_cache(), BucketManifestTests, BuildTests, DownloadHostTests, PackFormatTests, _quiet(), _record(), snippet_source()

### Community 33 - "store.ts"
Cohesion: 0.13
Nodes (38): offlineApi, removeBuild(), removeOtherBuilds(), closeReaders(), bootOffline(), cancel(), currentUserId(), DatasetState (+30 more)

### Community 34 - "Calculator"
Cohesion: 0.07
Nodes (29): standardize_fa_units(), Command, _error_checks_for(), _formula_strings_fa(), _import_categories(), _import_tags(), _questions_for(), _references_for() (+21 more)

### Community 35 - "SectionEditRequest"
Cohesion: 0.10
Nodes (21): ReviewEvent, Meta, SectionEditRequest, Meta, approve(), _clean(), _client_ip(), _close() (+13 more)

### Community 36 - "re"
Cohesion: 0.07
Nodes (16): _fa_keys_standardized(), _stage_names_without_prefix(), _title_formula_as_result(), _with_unit(), StandardizeUnitsTests, _adjective(), _chain(), _key() (+8 more)

### Community 37 - "CalculatorDetailScreen.tsx"
Cohesion: 0.17
Nodes (24): describeInputs(), CardsFlow(), flowLayout, Choices(), FieldVariant, isBinaryQuestion(), label(), Numeric() (+16 more)

### Community 38 - "offline/views.py"
Cohesion: 0.16
Nodes (14): build_matches_dataset(), LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer, PackageFileUrlSerializer, PackageManifestSerializer, PackageUrlsRequestSerializer (+6 more)

### Community 39 - "VerdictResult.tsx"
Cohesion: 0.24
Nodes (15): Chip(), Collapse(), Extras(), hasPersian(), RichLines(), Rows(), Tone, useDisplayText() (+7 more)

### Community 40 - "calculatorModel.ts"
Cohesion: 0.15
Nodes (23): tierText(), StagingResult(), allWholeNumbers(), cache, classify(), classifyCalculator(), isNumeric(), LadderRung (+15 more)

### Community 41 - "Ingredient"
Cohesion: 0.06
Nodes (23): Ingredient, Meta, all_decks(), _carded_slugs(), _seed_candidates(), _with_enough_content(), fold(), get_chapter() (+15 more)

### Community 42 - "QuizApiTests"
Cohesion: 0.09
Nodes (3): QuizAccessTests, QuizApiTests, QuizLockedTests

### Community 43 - "sources.ts"
Cohesion: 0.14
Nodes (22): lexicompApi, uptodateApi, UptodateArticle, UptodateImage, UptodateSearchResult, UptodateTopic, queryTerm(), openReader() (+14 more)

### Community 44 - "progress/views.py"
Cohesion: 0.09
Nodes (26): Mistake, Meta, DashboardSerializer, FocusRowSerializer, FocusSessionSerializer, MistakeSerializer, Meta, NextChapterSerializer (+18 more)

### Community 45 - "accounts/permissions.py"
Cohesion: 0.33
Nodes (5): CanManagePlatformRoles, CanViewSecurityAudit, HasPlatformPermission, HasRecentStepUp, session_has_recent_step_up()

### Community 46 - "config.py"
Cohesion: 0.12
Nodes (3): clear_cache(), _settings_changed(), PurchaseFlowTests

### Community 47 - "builders.py"
Cohesion: 0.16
Nodes (10): build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections(), _varints(), pack_json() (+2 more)

### Community 48 - "drugs/serializers.py"
Cohesion: 0.09
Nodes (15): AtcCodeSerializer, Meta, IngredientDetailSerializer, Meta, IngredientListSerializer, Meta, LessonDrugSectionSerializer, Meta (+7 more)

### Community 49 - "FlashcardApiTests"
Cohesion: 0.07
Nodes (14): AtcCategoryAdmin, AtcCodeAdmin, IngredientAdmin, IngredientProfileSectionAdmin, IngredientProfileSectionInline, IngredientProfileSection, Meta, seed_deck() (+6 more)

### Community 50 - "AtcCode"
Cohesion: 0.04
Nodes (16): Command, Command, AtcCategory, Meta, AtcCode, Meta, ChapterProgress, Meta (+8 more)

### Community 51 - "expo"
Cohesion: 0.06
Nodes (31): backgroundColor, foregroundImage, adaptiveIcon, package, versionCode, projectId, typedRoutes, expo (+23 more)

### Community 52 - "planning.py"
Cohesion: 0.07
Nodes (28): mark_drug_read(), topic_chapters(), topic_progress(), StudyPlanItem, Meta, complete_item(), ensure_today_items(), _flashcard_recall_for_slugs() (+20 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.18
Nodes (7): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label()

### Community 54 - "ResultCard"
Cohesion: 0.32
Nodes (24): Explain(), Hero(), Interpretation(), Ltr(), ResultCard(), showTierBar(), TierBar(), toneOf() (+16 more)

### Community 55 - "data_quality_center/tests.py"
Cohesion: 0.24
Nodes (6): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), word_diff(), CheckTests

### Community 56 - "django_utils"
Cohesion: 0.06
Nodes (10): rewrite_summaries(), FlashcardFactAdmin, LeitnerCardAdmin, LeitnerCard, Meta, due_card_count(), _make_snapshot(), LearnerProgress (+2 more)

### Community 57 - "Article"
Cohesion: 0.05
Nodes (22): Command, Command, _DryRun, ReferenceImportCommand, Command, Command, Article, Meta (+14 more)

### Community 58 - "test_phone_auth.py"
Cohesion: 0.11
Nodes (8): EmailOrUsernameBackend, InvalidPhone, looks_like_phone(), normalize_phone(), PhoneField, NormalizePhoneTests, ProfileTests, _find_user()

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.12
Nodes (16): HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت, دادهٔ مرجع (UpToDate و Lexicomp), دیتابیس، کش و آمادگی, سایت (+8 more)

### Community 60 - "billing/tests.py"
Cohesion: 0.14
Nodes (11): _div(), format_date(), _jal_cal(), _mod(), month_start(), to_gregorian(), to_jalali(), EnforcementTests (+3 more)

### Community 61 - "6. Lesson study topics (52)"
Cohesion: 0.06
Nodes (34): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 6. Lesson study topics (52), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups (+26 more)

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "Post"
Cohesion: 0.10
Nodes (5): Post, Meta, DownloadAndMachineTests, make_post(), PostVisibilityTests

### Community 66 - "tasks.py"
Cohesion: 0.15
Nodes (5): password_reset_url_for_user(), send_password_reset_email(), send_password_reset_emails_for_email(), send_password_reset_email_task(), enqueue()

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (26): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+18 more)

### Community 68 - "uptodate/services.py"
Cohesion: 0.19
Nodes (14): article_from_row(), _dir(), get_image(), get_topic(), is_available(), _mysql_conn(), search_topics(), _search_words() (+6 more)

### Community 69 - "dependencies"
Cohesion: 0.05
Nodes (36): dependencies, axios, expo, expo-crypto, expo-file-system, expo-font, @expo-google-fonts/vazirmatn, expo-linear-gradient (+28 more)

### Community 70 - "medscape/tests.py"
Cohesion: 0.12
Nodes (6): _disease_record(), _guideline_record(), ImportMedscapeArticlesTests, MedscapeApiTests, _write_diseases_tree(), _write_guidelines()

### Community 71 - "crypto.web.ts"
Cohesion: 0.10
Nodes (21): اجرای کامل با Docker, اندروید و iOS, اپ (Expo), بک‌اند, تست بستهٔ آفلاین بدون باکت, تست و بررسی, روال کار با مخزن, ساخت دیتابیس و اجرای سرور (+13 more)

### Community 72 - "panel.js"
Cohesion: 0.16
Nodes (14): buildEditor(), align(), block(), exec(), sync(), toggleSource(), wrapBlock(), filterNav() (+6 more)

### Community 73 - "website/models.py"
Cohesion: 0.04
Nodes (30): ActivityLog, Meta, Comment, Meta, ContactMessage, Meta, Media, Meta (+22 more)

### Community 74 - "اپ‌ها (`backend/apps/`)"
Cohesion: 0.05
Nodes (28): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, AdminAction, Meta (+20 more)

### Community 75 - "django_core_management"
Cohesion: 0.15
Nodes (3): HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests

### Community 76 - "SectionEdit"
Cohesion: 0.15
Nodes (7): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin, SectionEdit, Meta, مرکز کیفیت داده (`/ops/data-quality/`)

### Community 77 - "views_account.py"
Cohesion: 0.11
Nodes (18): OneTimeCode, Meta, AccountForm, CodeForm, LoginForm, PasswordForm, PhoneForm, account() (+10 more)

### Community 79 - "ConsoleTestCase"
Cohesion: 0.15
Nodes (3): ConsoleTestCase, DraftAndSubmitTests, ReviewTests

### Community 81 - "LessonDetailScreen.tsx"
Cohesion: 0.33
Nodes (10): LessonSection, joinOpenParens(), LessonBlock, LessonLine, parenDepth(), parseLessonText(), sectionText(), splitIssues() (+2 more)

### Community 82 - "common.tsx"
Cohesion: 0.13
Nodes (23): CalculatorDetail, CalculatorQuestion, bandFor(), Extra, fmt(), LEVEL_TONES, plain(), ResultProps (+15 more)

### Community 84 - "pack.py"
Cohesion: 0.15
Nodes (9): Command, derive_key(), new_build_id(), open_sealed(), pack_text(), PackError, read_record(), secret() (+1 more)

### Community 85 - "dqc_extras.py"
Cohesion: 0.08
Nodes (19): ReviewForm, SectionEditForm, action_label(), action_tone(), ago(), dict_get(), fa_digits(), percent() (+11 more)

### Community 86 - "clean_profile_boilerplate.py"
Cohesion: 0.14
Nodes (13): clean_text(), Command, cleaned(), is_hypersensitivity_boilerplate(), is_hypersensitivity_boilerplate_en(), is_negative_indication_en(), is_negative_indication_fa(), is_null_placeholder() (+5 more)

### Community 87 - "production.py"
Cohesion: 0.29
Nodes (4): validate_production_broker(), validate_production_cache(), validate_production_secret_key(), ProductionSecretKeyTests

### Community 88 - "porter.ts"
Cohesion: 0.23
Nodes (8): firstRule(), isVowelLetter(), porterStem(), Rule, STEP2, STEP3, STEP4, Word

### Community 89 - "storage.py"
Cohesion: 0.12
Nodes (14): Command, cors_rule(), _request(), file_urls(), is_configured(), latest_manifest(), local_dir(), local_file_for_token() (+6 more)

### Community 90 - "downloader.ts"
Cohesion: 0.20
Nodes (6): downloader, DownloadEvents, PartJob, PartRef, tasks, @kesha-antonov/react-native-background-downloader

### Community 91 - "uptodate/views.py"
Cohesion: 0.30
Nodes (8): UptodateArticleSerializer, UptodateImageSerializer, UptodateSearchResultSerializer, UptodateTopicSerializer, ImageDetailView, _require_available(), TopicDetailView, TopicSearchView

### Community 92 - "progress/selectors.py"
Cohesion: 0.14
Nodes (16): lesson_groups(), _subgroup(), DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin, DailyStudy, Meta (+8 more)

### Community 93 - "DrugPageTests"
Cohesion: 0.09
Nodes (4): DrugPageTests, SiteIdentityTests, structured(), summary_html()

### Community 94 - "offline/reader.ts"
Cohesion: 0.09
Nodes (21): Coding Style & Naming Conventions, پایهٔ Django, OfflineManifest, keyring, openRecord(), openRecordBase64(), PackageKey, sealed() (+13 more)

### Community 96 - "exceptions.py"
Cohesion: 0.19
Nodes (10): _first_message(), _message_from_data(), _normalize_code(), platform_exception_handler(), InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, DrugSearchView (+2 more)

### Community 97 - "files.ts"
Cohesion: 0.26
Nodes (12): buildDir(), closeHandles(), ensureBuildDir(), handles, partFile(), partPath(), partSize(), readRange() (+4 more)

### Community 98 - "django_core_management_base"
Cohesion: 0.12
Nodes (6): Command, ensure_title_search_index(), _has_title_search_index(), mysql_config(), MysqlTitleIndexTests, MysqlTitleSearchTests

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

### Community 100 - "drugs/reference_db.py"
Cohesion: 0.04
Nodes (26): export(), load(), dumps(), expected_count(), loads(), open_for_import(), record_counts(), rows() (+18 more)

### Community 101 - "Command"
Cohesion: 0.21
Nodes (4): Command, _int(), _json_list(), _name_fa()

### Community 102 - "downloader.web.ts"
Cohesion: 0.20
Nodes (9): downloader, DownloadEvents, newWorker(), PartJob, PartRef, Run, runFor(), runs (+1 more)

### Community 103 - "billing_extras.py"
Cohesion: 0.27
Nodes (7): ago(), get_item(), guest_access_on(), initial(), jdate(), num(), toman()

### Community 104 - "offline/services.py"
Cohesion: 0.24
Nodes (7): has_paid_plan_with(), is_entitled(), is_guest(), issue_license(), license_days(), LicenseError, _wrap_for()

### Community 105 - "ImportCalculatorsTests"
Cohesion: 0.32
Nodes (3): _build_sqlite(), ImportCalculatorsTests, _one_calculator()

### Community 107 - "Repository Guidelines"
Cohesion: 0.29
Nodes (6): Build, Test, and Development Commands, Commit & Pull Request Guidelines, Project Structure & Module Organization, Repository Guidelines, Security & Configuration Tips, Testing Guidelines

### Community 109 - "Media"
Cohesion: 0.03
Nodes (47): Command, AppRelease, Meta, Category, Meta, ContentBlock, Meta, DownloadLink (+39 more)

### Community 111 - "bidi.ts"
Cohesion: 0.25
Nodes (7): isolated(), ENGLISH_RUN, hasPersianLetters(), isolateEnglish(), LRI, PDI, RLM

### Community 112 - "accounts/services.py"
Cohesion: 0.06
Nodes (36): SessionTokenAuthentication, Role, Meta, RoleAssignment, Meta, SecurityAuditEvent, Meta, SessionRefreshToken (+28 more)

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

### Community 119 - "back.ts"
Cohesion: 0.24
Nodes (10): canGoBack(), goBackInApp(), installWebBackGuard(), Interceptor, interceptors, listeners, notify(), subscribeBackState() (+2 more)

### Community 120 - "sw.js"
Cohesion: 0.38
Nodes (4): inScope(), referencedFiles(), SCOPE, storeShell()

### Community 123 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.25
Nodes (8): PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa, 🎉 بازنویسی کامل شد, فاز ۰.۵ — حذف زیرساخت رهاشده ✅, فاز ۶ — uptodate + جمع‌بندی + انتشار (زیرفازی), پس از انتشار — حذف کدهای ATC نامرتبط با اندیکاسیون ✅ (برنچ `fix-chapter-indication-fit`), پس از انتشار — سایت و بلاگ `pharmenta.ir` + پنل مدیریت ✅, پس از انتشار — گروه ATC چهارحرفی در فهرست داروها ✅, ۶b — جمع‌بندی و انتشار ✅

### Community 125 - "manage.py"
Cohesion: 0.29
Nodes (3): build.sh script, DJANGO_SETTINGS_MODULE, release.sh script

### Community 126 - "otp.py"
Cohesion: 0.09
Nodes (16): account_for_signup(), _hash(), _minutes(), _new_code(), OtpError, request_code(), user_for_phone(), verify_code() (+8 more)

### Community 127 - "jalali.ts"
Cohesion: 0.26
Nodes (20): DateInput(), DaysInput(), Field(), QuestionTitle(), BREAKS, d2g(), d2j(), dateToMs() (+12 more)

### Community 128 - "logging.py"
Cohesion: 0.33
Nodes (3): get_request_id(), JsonFormatter, RequestContextFilter

### Community 134 - "OfflinePackageCard.tsx"
Cohesion: 0.19
Nodes (21): OfflineDataset, OfflinePackageInfo, OfflineDownloadButton(), OfflineSheet(), ERROR_TEXT, LOGO, NAME, OfflinePackageCard() (+13 more)

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
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1553 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **84 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UserSession` connect `accounts/services.py` to `WebsiteAuthTests`, `console/views.py`, `useTheme`, `اپ‌ها (`backend/apps/`)`, `accounts/serializers.py`, `config.py`, `accounts/views.py`, `test_phone_auth.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `AppText()` (e.g. with `زبان، جهت و تم` and `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅`) actually correct?**
  _`AppText()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-splash-screen` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.035346097201767304 - nodes in this community are weakly interconnected._
- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `useTheme` to `accounts/services.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`, `react`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `PlatformAPIError` (e.g. with `LoginView` and `OtpVerifyView`) actually correct?**
  _`PlatformAPIError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.021891010712622262 - nodes in this community are weakly interconnected._