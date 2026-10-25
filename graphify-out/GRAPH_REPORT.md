# Graph Report - Learning Platform  (2026-10-25)

## Corpus Check
- 523 files · ~424,176 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 32 file(s) not represented in the graph (top: (none) 11, .ttf 7, .woff2 4)

## Summary
- 5097 nodes · 14593 edges · 205 communities (123 shown, 82 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1286 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `602dc2bc`
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
- get_plan
- guest.py
- LeitnerCard
- SepGateway
- tests_console.py
- billing/services.py
- Page
- IngredientProfileSection
- useLang
- accounts/views.py
- ScreenChrome.tsx
- IngredientProfileSection
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
- calculators/tests.py
- data_quality_center/views.py
- panel/forms.py
- QuestionField.tsx
- offline/views.py
- test_public.py
- search_topics
- DrugPageTests
- QuizApiTests
- offline/tests.py
- progress/views.py
- release.mjs
- PurchaseFlowTests
- json
- IngredientDetailSerializer
- FlashcardApiTests
- LessonTaxonomyTests
- expo
- planning.py
- import_medscape_articles.py
- ResultCard
- AppRelease
- ImportOpenfdaTests
- django_db
- bootstrap_superuser.py
- ۶. پیکربندی و متغیرهای محیطی
- offline/views.py
- files.web.ts
- regenerate_items
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
- HealthCheckTests
- logging
- SectionEdit
- views_account.py
- maintenance_urls.py
- ReviewTests
- common.tsx
- calculatorModel.ts
- views_account.py
- UptodateTests
- OfflinePackageCard.tsx
- dqc_extras.py
- re
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- porter.ts
- billing/views.py
- decks.py
- offline/services.py
- Ingredient
- Pharmexa — custom icon prompts
- uptodateLocal.ts
- docs/README.md
- 6. Lesson study topics (52)
- files.ts
- previews.tsx
- site.js
- VisitorDay
- CalculatorDetailScreen.tsx
- downloader.web.ts
- ۲. راه‌اندازی محیط توسعه
- offline/reader.ts
- ImportCalculatorsTests
- ReferenceDbTests
- Repository Guidelines
- progress/selectors.py
- CalculatorDetail
- website_extras.py
- StandardizeUnitsTests
- accounts/services.py
- ۵. قرارداد API (نسخهٔ ۱)
- ZibalGateway
- ۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی
- tsconfig.json
- uptodate/views.py
- django_apps
- App.tsx
- sw.js
- Command
- require_feature
- ۱۲. سایت `pharmenta.ir` و پنل محتوا
- pagination.py
- _SectionCard
- otp.py
- BuildTests
- LexicompScreen.tsx
- docker-start.sh
- billing/apps.py
- GatewayPageTests
- .claude/CLAUDE.md
- StudyTopicsCoverageTests
- app.config.js
- .mcp.json
- record_study
- downloader.ts
- ۳. بک‌اند (Django)
- _snippet
- flashcards/admin.py
- QuizQuestionSerializer
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
1. `useTheme()` - 204 edges
2. `AppText()` - 192 edges
3. `useLang()` - 181 edges
4. `react` - 88 edges
5. `PlatformAPIError` - 83 edges
6. `Ingredient` - 77 edges
7. `react-native` - 77 edges
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

## Communities (205 total, 82 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.04
Nodes (89): حساب و احراز هویت — `/auth/`, flashcardsApi, offlineApi, quizApi, AtcCode, AuthTokenResponse, BoxCard, BoxRating (+81 more)

### Community 1 - "django_db"
Cohesion: 0.04
Nodes (31): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+23 more)

### Community 2 - "test_panel.py"
Cohesion: 0.06
Nodes (18): PostRevision, Meta, StaffRole, Meta, SiteTestCase, AdminTests, AuthorTests, AuthTests (+10 more)

### Community 3 - "console/views.py"
Cohesion: 0.05
Nodes (72): DiscountForm, FeatureEditForm, Meta, FeatureForm, Meta, latin_digits(), parse_amount(), parse_jalali() (+64 more)

### Community 4 - "react"
Cohesion: 0.08
Nodes (49): authApi, ALPHABET, AlphabeticalArticleList(), buildOffsets(), groupAlphabetically(), Section, AppShell(), TopInset (+41 more)

### Community 5 - "Post"
Cohesion: 0.06
Nodes (61): ActivityLog, Meta, Comment, Meta, ContactMessage, Meta, Subscriber, Meta (+53 more)

### Community 6 - "useTheme"
Cohesion: 0.11
Nodes (91): قابلیت‌ها, قواعد کدنویسی اپ, calculatorsApi, meApi, medscapeApi, BottomNav(), ChecklistFlow(), CardBackField() (+83 more)

### Community 7 - "views_public.py"
Cohesion: 0.04
Nodes (58): site(), SiteMaintenanceMiddleware, DailyStat, Meta, Post, Meta, SiteSettings, Meta (+50 more)

### Community 8 - ".reverse"
Cohesion: 0.05
Nodes (9): AuthenticationSecurityTests, OnboardingTests, wrapper(), PlanBuilderTests, UsersPageTests, AccessTests, Section, search() (+1 more)

### Community 9 - "package.json"
Cohesion: 0.04
Nodes (64): شروع اپ, App(), Gate(), ThemedStatusBar(), main, name, private, version (+56 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.14
Nodes (19): TopicProgress, Meta, BoxSummarySerializer, DeckAnswerSerializer, DeckOverviewSerializer, DeckProgressSerializer, ReviewSerializer, TopicDeckSerializer (+11 more)

### Community 11 - "get_plan"
Cohesion: 0.29
Nodes (5): plan_from_onboarding(), get_plan(), _onboarding(), OnboardingPlanTests, PlanTodayApiTests

### Community 12 - "guest.py"
Cohesion: 0.10
Nodes (10): create_guest(), GuestSessionView, GuestStatusView, _first_message(), _message_from_data(), _normalize_code(), platform_exception_handler(), LatestReleaseSerializer (+2 more)

### Community 13 - "LeitnerCard"
Cohesion: 0.07
Nodes (16): add_miss(), add_quiz_miss(), daily_minutes(), drawer_cards(), _exam_cap_days(), outcome(), overview(), previews() (+8 more)

### Community 14 - "SepGateway"
Cohesion: 0.07
Nodes (8): GatewayError, _post_json(), SepGateway, ZarinpalGateway, _fake_urlopen(), PurchaseApiTests, SepTests, ZarinpalTests

### Community 15 - "tests_console.py"
Cohesion: 0.06
Nodes (26): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, AdminAction, Meta (+18 more)

### Community 16 - "billing/services.py"
Cohesion: 0.07
Nodes (24): Access, active_entitlements(), BillingError, check_feature(), content_lock(), create_order(), effective_features(), take() (+16 more)

### Community 17 - "Page"
Cohesion: 0.07
Nodes (6): clean_html(), _Cleaner, plain_text(), safe_url(), _Text, SanitizeTests

### Community 18 - "IngredientProfileSection"
Cohesion: 0.08
Nodes (15): fa(), Migration, Migration, _build_catalog(), _drop_title(), drug_detail(), english_name(), fa_key() (+7 more)

### Community 19 - "useLang"
Cohesion: 0.08
Nodes (53): زبان، جهت و تم, LessonGroup, PlanDay, PlanMode, CategoryPicker(), Chip(), ChipRow(), DateField() (+45 more)

### Community 20 - "accounts/views.py"
Cohesion: 0.05
Nodes (52): CanManagePlatformRoles, AuthTokenResponseSerializer, LearnerProfileSerializer, Meta, LoginSerializer, OnboardingSerializer, OtpRequestResponseSerializer, OtpRequestSerializer (+44 more)

### Community 21 - "ScreenChrome.tsx"
Cohesion: 0.05
Nodes (60): تور راهنما (`src/tour/`), lessonsApi, AtcGroup, ChapterDrug, LessonSection, escape(), MediaContent, mediaPage() (+52 more)

### Community 22 - "IngredientProfileSection"
Cohesion: 0.04
Nodes (23): AtcCategoryAdmin, AtcCodeAdmin, IngredientAdmin, IngredientProfileSectionAdmin, IngredientProfileSectionInline, Command, Command, _DryRun (+15 more)

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.08
Nodes (54): CalculatorErrorCheck, LiveScore(), useLiveScore(), buildHeuristicSeeds(), cartesian(), classifyResultTone(), computeCalculator(), ComputeOptions (+46 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.07
Nodes (35): record_quiz_answers(), BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, preview_selection(), best_score_pct_for_topic(), _finished_sessions(), _finished_topic_sessions() (+27 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.06
Nodes (70): MedscapeBlock, MedscapeSection, useBleedTop(), countMatches(), FindState, highlight(), ListMarker(), LTR (+62 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.08
Nodes (19): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, _categories_for_generics(), check_interactions(), close_all(), _conn(), _dir() (+11 more)

### Community 28 - ".request_code"
Cohesion: 0.09
Nodes (21): CodeRuleTests, PhoneAuthTestCase, ResetTests, SignUpTests, برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی, روش تبدیل پیشنهادها به کلمات کلیدی معتبر, ساخت Analytics از ابتدا (+13 more)

### Community 29 - "progress/tests.py"
Cohesion: 0.06
Nodes (18): DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin, DailyStudy, Meta, LearnerProgress, Mistake (+10 more)

### Community 30 - "core/views.py"
Cohesion: 0.14
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 31 - "lessons/views.py"
Cohesion: 0.09
Nodes (21): require_atc_content(), LessonDrugSerializer, get_chapter(), _topic_lookup(), topics_for_chapter(), AtcGroupSerializer, ChapterDrugSerializer, ChapterProgressSerializer (+13 more)

### Community 33 - "store.ts"
Cohesion: 0.13
Nodes (39): closeReaders(), localFirst(), localReader(), bootOffline(), cancel(), currentUserId(), DatasetState, download() (+31 more)

### Community 34 - "calculators/tests.py"
Cohesion: 0.03
Nodes (50): _fa_keys_standardized(), fix_questions(), fix_results(), fix_strings_fa(), renumber_from_one(), standardize_fa_units(), _title_formula_as_result(), _with_choices() (+42 more)

### Community 35 - "data_quality_center/views.py"
Cohesion: 0.05
Nodes (56): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), warning_count(), word_diff(), section_state(), ReviewEvent (+48 more)

### Community 36 - "panel/forms.py"
Cohesion: 0.05
Nodes (32): Media, Meta, AnnouncementForm, Meta, CategoryForm, Meta, ContentBlockForm, Meta (+24 more)

### Community 37 - "QuestionField.tsx"
Cohesion: 0.17
Nodes (28): DateInput(), DaysInput(), Field(), QuestionTitle(), Choices(), FieldProps, FieldVariant, isBinaryQuestion() (+20 more)

### Community 38 - "offline/views.py"
Cohesion: 0.09
Nodes (15): Command, cors_rule(), _request(), clear_cache(), file_urls(), is_configured(), latest_manifest(), local_dir() (+7 more)

### Community 39 - "test_public.py"
Cohesion: 0.06
Nodes (8): Redirect, Meta, CommentTests, DownloadAndMachineTests, FormsTests, HostRoutingTests, make_post(), PostVisibilityTests

### Community 40 - "search_topics"
Cohesion: 0.12
Nodes (16): Command, article_from_row(), _dir(), get_image(), get_topic(), is_available(), mysql_config(), _mysql_conn() (+8 more)

### Community 41 - "DrugPageTests"
Cohesion: 0.10
Nodes (4): DrugPageTests, SeedSeoContentTests, SiteIdentityTests, structured()

### Community 42 - "QuizApiTests"
Cohesion: 0.09
Nodes (3): QuizAccessTests, QuizApiTests, QuizLockedTests

### Community 43 - "offline/tests.py"
Cohesion: 0.10
Nodes (12): Command, derive_key(), open_sealed(), PackError, read_record(), secret(), BuildTests, _index() (+4 more)

### Community 44 - "progress/views.py"
Cohesion: 0.09
Nodes (26): topic_progress(), DashboardSerializer, FocusRowSerializer, FocusSessionSerializer, MistakeSerializer, Meta, NextChapterSerializer, PlanDaySerializer (+18 more)

### Community 45 - "release.mjs"
Cohesion: 0.09
Nodes (15): appJson, at, dryRun, file(), frontend, [kind, ...flags], lock, [major, minor, patch] (+7 more)

### Community 46 - "PurchaseFlowTests"
Cohesion: 0.06
Nodes (9): clear_cache(), _settings_changed(), BillingSettings, Meta, GuestAccount, GatewayChoiceTests, GuestAccessTests, GuestConsoleTests (+1 more)

### Community 47 - "json"
Cohesion: 0.10
Nodes (12): build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections(), _varints(), new_build_id() (+4 more)

### Community 49 - "FlashcardApiTests"
Cohesion: 0.10
Nodes (5): FlashcardApiTests, FlashcardLockedTests, _refresh_facts(), _rich_ingredient(), TopicDeckTests

### Community 50 - "LessonTaxonomyTests"
Cohesion: 0.08
Nodes (4): DrugSearchTests, _ingredient(), LessonTaxonomyFallbackTests, LessonTaxonomyTests

### Community 51 - "expo"
Cohesion: 0.06
Nodes (32): backgroundColor, foregroundImage, adaptiveIcon, allowBackup, blockedPermissions, package, projectId, typedRoutes (+24 more)

### Community 52 - "planning.py"
Cohesion: 0.08
Nodes (25): StudyPlanItem, Meta, _chapter(), complete_item(), ensure_today_items(), _flatten(), _goal_items(), _groups_by_topic() (+17 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.16
Nodes (7): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label()

### Community 54 - "ResultCard"
Cohesion: 0.34
Nodes (22): Explain(), Hero(), Interpretation(), ResultCard(), ResultProps, showTierBar(), toneOf(), useShown() (+14 more)

### Community 55 - "AppRelease"
Cohesion: 0.10
Nodes (10): note_lines(), ReleaseQuerySerializer, AppRelease, Meta, version_code(), release(), ReleaseCheckTests, ReleaseFormTests (+2 more)

### Community 56 - "ImportOpenfdaTests"
Cohesion: 0.06
Nodes (8): AtcSupplementTests, CleanBoilerplateInPipelineTests, DrugApiTests, ImportOpenfdaTests, LoadAtcReferenceTests, _make_source_db(), ModelTests, StandardizePipelineUnitsTests

### Community 57 - "django_db"
Cohesion: 0.03
Nodes (26): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+18 more)

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.12
Nodes (16): HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت, دادهٔ مرجع (UpToDate و Lexicomp), دیتابیس، کش و آمادگی, سایت (+8 more)

### Community 60 - "offline/views.py"
Cohesion: 0.11
Nodes (17): build_matches_dataset(), LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer, PackageFileUrlSerializer, PackageManifestSerializer, PackageUrlsRequestSerializer (+9 more)

### Community 61 - "files.web.ts"
Cohesion: 0.19
Nodes (9): file(), forget(), partSize(), readRange(), removeBuild(), removeOtherBuilds(), removePart(), snapshots (+1 more)

### Community 62 - "regenerate_items"
Cohesion: 0.13
Nodes (8): mark_drug_read(), _flashcard_recall_for_slugs(), _quiz_accuracy_for_slugs(), regenerate_items(), topic_mastery(), GoalPlanGenerationTests, TopicMasteryTests, _two_chapter_topic()

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "Article"
Cohesion: 0.04
Nodes (32): Command, Command, _DryRun, ReferenceImportCommand, dumps(), expected_count(), loads(), open_for_import() (+24 more)

### Community 66 - "billing/tests.py"
Cohesion: 0.14
Nodes (11): _div(), format_date(), _jal_cal(), _mod(), month_start(), to_gregorian(), to_jalali(), EnforcementTests (+3 more)

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (26): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+18 more)

### Community 68 - "migrate_uptodate_to_mysql.py"
Cohesion: 0.11
Nodes (5): Command, ensure_title_search_index(), _has_title_search_index(), MysqlTitleIndexTests, MysqlTitleSearchTests

### Community 69 - "dependencies"
Cohesion: 0.05
Nodes (39): dependencies, axios, expo, expo-build-properties, expo-constants, expo-crypto, expo-file-system, expo-font (+31 more)

### Community 70 - "medscape/tests.py"
Cohesion: 0.12
Nodes (6): _disease_record(), _guideline_record(), ImportMedscapeArticlesTests, MedscapeApiTests, _write_diseases_tree(), _write_guidelines()

### Community 71 - "crypto.web.ts"
Cohesion: 0.21
Nodes (10): اجرای کامل با Docker, OfflineLicense, db(), idb(), keyring, openRecord(), openRecordBase64(), PackageKey (+2 more)

### Community 72 - "panel.js"
Cohesion: 0.16
Nodes (14): buildEditor(), align(), block(), exec(), sync(), toggleSource(), wrapBlock(), filterNav() (+6 more)

### Community 73 - "website/models.py"
Cohesion: 0.05
Nodes (24): Command, render_links(), link(), Command, Announcement, Meta, Category, Meta (+16 more)

### Community 74 - "HealthCheckTests"
Cohesion: 0.15
Nodes (3): HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests

### Community 75 - "logging"
Cohesion: 0.07
Nodes (8): password_reset_url_for_user(), send_password_reset_email(), send_password_reset_emails_for_email(), send_password_reset_email_task(), PlatformTask, retry_delay_seconds(), enqueue(), configure_runtime()

### Community 76 - "SectionEdit"
Cohesion: 0.27
Nodes (4): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin

### Community 77 - "views_account.py"
Cohesion: 0.05
Nodes (23): SessionTokenAuthentication, SessionTokenAuthenticationScheme, EmailOrUsernameBackend, LearnerProfile, UserSession, Meta, InvalidPhone, looks_like_phone() (+15 more)

### Community 80 - "common.tsx"
Cohesion: 0.14
Nodes (31): bandFor(), Chip(), Collapse(), Extra, Extras(), fmt(), hasPersian(), LEVEL_TONES (+23 more)

### Community 81 - "calculatorModel.ts"
Cohesion: 0.15
Nodes (23): CalculatorResultDef, StagingResult(), ComputedResult, allWholeNumbers(), cache, classify(), isNumeric(), LadderRung (+15 more)

### Community 82 - "views_account.py"
Cohesion: 0.06
Nodes (22): BillingConfig, current(), enabled_gateways(), gateway_spec(), _gateways(), GatewaySpec, _load(), row() (+14 more)

### Community 84 - "OfflinePackageCard.tsx"
Cohesion: 0.22
Nodes (18): OfflineSheet(), ERROR_TEXT, LOGO, NAME, OfflinePackageCard(), PHASE_TEXT, SUPPORTS_BACKGROUND, freeBytes() (+10 more)

### Community 85 - "dqc_extras.py"
Cohesion: 0.13
Nodes (16): ago(), get_item(), guest_access_on(), initial(), jdate(), num(), toman(), action_label() (+8 more)

### Community 86 - "re"
Cohesion: 0.05
Nodes (31): _stage_names_without_prefix(), writing(), _adjective(), _chain(), _key(), _latin_quantity(), _spelling(), standardize_in() (+23 more)

### Community 87 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.07
Nodes (17): build.sh script, validate_production_broker(), validate_production_cache(), validate_production_secret_key(), CorsPreflightTests, ProductionSecretKeyTests, DJANGO_SETTINGS_MODULE, release.sh script (+9 more)

### Community 88 - "porter.ts"
Cohesion: 0.22
Nodes (9): firstRule(), isVowelLetter(), porterStem(), queryTerm(), Rule, STEP2, STEP3, STEP4 (+1 more)

### Community 89 - "billing/views.py"
Cohesion: 0.07
Nodes (33): is_guest(), Order, Meta, CatalogSerializer, CheckoutSerializer, MyAccessSerializer, MyEntitlementSerializer, Meta (+25 more)

### Community 90 - "decks.py"
Cohesion: 0.13
Nodes (11): all_decks(), _carded_slugs(), _cards(), deck_cards(), deck_slugs(), next_topic(), progress_map(), _sections_by_slug() (+3 more)

### Community 91 - "offline/services.py"
Cohesion: 0.24
Nodes (7): has_paid_plan_with(), is_entitled(), is_guest(), issue_license(), license_days(), LicenseError, _wrap_for()

### Community 92 - "Ingredient"
Cohesion: 0.03
Nodes (43): Command, Command, AtcCategory, Meta, AtcCode, Meta, Ingredient, Meta (+35 more)

### Community 93 - "Pharmexa — custom icon prompts"
Cohesion: 0.15
Nodes (12): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups, 9. App identity (optional) (+4 more)

### Community 94 - "uptodateLocal.ts"
Cohesion: 0.09
Nodes (26): Coding Style & Naming Conventions, پایهٔ Django, lexicompApi, uptodateApi, LexicompDrug, LexicompInteraction, UptodateImage, cache (+18 more)

### Community 96 - "6. Lesson study topics (52)"
Cohesion: 0.15
Nodes (13): 6. Lesson study topics (52), Cardiovascular & blood, Dermatology, Endocrine & metabolism, Gastrointestinal, Infectious disease, Miscellaneous, Musculoskeletal (+5 more)

### Community 97 - "files.ts"
Cohesion: 0.26
Nodes (13): buildDir(), closeHandles(), ensureBuildDir(), handles, partFile(), partPath(), partSize(), readRange() (+5 more)

### Community 98 - "previews.tsx"
Cohesion: 0.37
Nodes (21): Bands(), Check(), CheckDot(), Choice(), Drawers(), Flip(), Interaction(), kf() (+13 more)

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

### Community 100 - "VisitorDay"
Cohesion: 0.24
Nodes (4): VisitorDay, Meta, UniqueVisitorTests, visit()

### Community 101 - "CalculatorDetailScreen.tsx"
Cohesion: 0.16
Nodes (19): describeInputs(), AboutBody(), CalculatorDetailScreen(), dirStyle(), checkErrors(), hasUnsupportedQuestions(), questionDomain(), ResultRange (+11 more)

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

### Community 108 - "progress/selectors.py"
Cohesion: 0.19
Nodes (12): due_card_count(), lesson_groups(), _subgroup(), topic_chapters(), dashboard(), _display_name(), _leitner_focus_row(), _mastery_pct() (+4 more)

### Community 109 - "CalculatorDetail"
Cohesion: 0.32
Nodes (9): CalculatorDetail, CalculatorQuestion, CardsFlow(), flowLayout, LIST_FROM, QuestionFlow(), FlowProps, CalculatorAnswers (+1 more)

### Community 110 - "website_extras.py"
Cohesion: 0.15
Nodes (8): atc_groups(), feature_icon(), nav_on(), oneline(), person(), split_highlight(), split_lines(), آنچه کد انجام می‌دهد

### Community 112 - "accounts/services.py"
Cohesion: 0.07
Nodes (29): Role, Meta, RoleAssignment, Meta, SecurityAuditEvent, Meta, SessionRefreshToken, Meta (+21 more)

### Community 113 - "۵. قرارداد API (نسخهٔ ۱)"
Cohesion: 0.09
Nodes (22): Lexicomp — `/lexicomp/` (ویژگی `lexicomp`), Medscape — `/medscape/` (ویژگی `medscape`), UpToDate — `/uptodate/` (ویژگی `uptodate`), آزمون — `/quiz/` (ویژگی `quiz`؛ پرچم `QUIZ_API_ENABLED`), برنامهٔ ساخته‌شده از آنبوردینگ, تغییر دادن API, جعبهٔ قدیمی, جعبهٔ لایتنر (+14 more)

### Community 115 - "۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی"
Cohesion: 0.12
Nodes (17): اطلاعات غیرمحرمانه‌ای که باید جایی ثبت باشد, بازیابی, بکاپ و بازیابی, حساب‌های سرویس, رازها و چیزهایی که باید امن نگه داشته شوند, رازهای فنی, شاخص‌هایی که مرتب دیده شوند, عیب‌یابی (+9 more)

### Community 116 - "tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, paths, strict, extends, include, expo/tsconfig.base

### Community 117 - "uptodate/views.py"
Cohesion: 0.30
Nodes (8): UptodateArticleSerializer, UptodateImageSerializer, UptodateSearchResultSerializer, UptodateTopicSerializer, ImageDetailView, _require_available(), TopicDetailView, TopicSearchView

### Community 119 - "App.tsx"
Cohesion: 0.18
Nodes (16): releaseApi, AppReleaseInfo, dismissedRecently(), Notes(), Offer, openRelease(), OptionalUpdate(), RequiredUpdate() (+8 more)

### Community 120 - "sw.js"
Cohesion: 0.38
Nodes (4): inScope(), referencedFiles(), SCOPE, storeShell()

### Community 122 - "require_feature"
Cohesion: 0.11
Nodes (12): _applies(), _require_content(), require_feature(), require_topic_content(), topic_meta(), BoxCardSerializer, BoxReviewSerializer, LeitnerOverviewSerializer (+4 more)

### Community 123 - "۱۲. سایت `pharmenta.ir` و پنل محتوا"
Cohesion: 0.14
Nodes (14): not_found(), آمار بازدید, حساب و خرید روی سایت, دارونامهٔ عمومی (`/drugs/`), رسانه, سئو, ساختار کد, صفحه‌های عمومی (+6 more)

### Community 125 - "_SectionCard"
Cohesion: 0.11
Nodes (10): _card_back_fields(), CategoryDecksSerializer, DeckCardSerializer, DrawerSerializer, LeitnerCardSerializer, Meta, NextTopicSerializer, RatingOutcomeSerializer (+2 more)

### Community 126 - "otp.py"
Cohesion: 0.06
Nodes (30): OneTimeCode, Meta, account_for_signup(), _hash(), _minutes(), _new_code(), OtpError, request_code() (+22 more)

### Community 128 - "LexicompScreen.tsx"
Cohesion: 0.10
Nodes (23): آنبوردینگ و برنامهٔ مطالعه, ارتباط با API و کش, افزودن صفحهٔ تازه, دانلود آفلاین (`src/offline/`), ساختار `frontend/src/`, فلش‌کارت و جعبهٔ لایتنر, ناوبری, نمایش بزرگ عکس و جدول (+15 more)

### Community 152 - "record_study"
Cohesion: 0.22
Nodes (5): Migration, seed(), record_study(), _touch_streak(), ۳c — `apps.flashcards` + `apps.quiz` (ساخته‌شده، پشت فلگ خاموش) ✅

### Community 156 - "downloader.ts"
Cohesion: 0.20
Nodes (6): downloader, DownloadEvents, PartJob, PartRef, tasks, @kesha-antonov/react-native-background-downloader

### Community 182 - "۳. بک‌اند (Django)"
Cohesion: 0.12
Nodes (13): RequestIdMiddleware, SiteHostMiddleware, UpToDate و Lexicomp, افزودن یک قابلیت فروشی تازه, بستهٔ آفلاین (`apps.offline`), زنجیرهٔ middleware, صورتحساب و دسترسی (`apps.billing`), قواعد مشترک API (+5 more)

### Community 183 - "_snippet"
Cohesion: 0.29
Nodes (3): _snippet(), snippet_source(), SnippetTests

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
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1655 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **82 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `react` to `useLang`, `views_account.py`, `useTheme`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.173) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `AppText()` (e.g. with `زبان، جهت و تم` and `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅`) actually correct?**
  _`AppText()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-build-properties` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.03574561403508772 - nodes in this community are weakly interconnected._
- **Why does `UserSession` connect `views_account.py` to `WebsiteAuthTests`, `console/views.py`, `react`, `guest.py`, `PurchaseFlowTests`, `tests_console.py`, `accounts/services.py`, `views_account.py`, `accounts/views.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.171) - this node is a cross-community bridge._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.03793691389599318 - nodes in this community are weakly interconnected._
- **Why does `اپ‌ها (`backend/apps/`)` connect `tests_console.py` to `test_panel.py`, `console/views.py`, `views_public.py`, `flashcards/views.py`, `get_plan`, `LeitnerCard`, `IngredientProfileSection`, `quiz/views.py`, `progress/tests.py`, `calculators/tests.py`, `data_quality_center/views.py`, `panel/forms.py`, `PurchaseFlowTests`, `planning.py`, `۳. بک‌اند (Django)`, `Article`, `website/models.py`, `views_account.py`, `billing/views.py`, `Ingredient`, `accounts/services.py`, `otp.py`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._