# Graph Report - Learning Platform  (2026-10-25)

## Corpus Check
- 522 files · ~426,138 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 32 file(s) not represented in the graph (top: (none) 11, .ttf 7, .woff2 4)

## Summary
- 5130 nodes · 14660 edges · 224 communities (137 shown, 87 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1285 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d74397f3`
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
- test_onboarding_plan.py
- guest.py
- LeitnerCard
- SepGateway
- tests_console.py
- data_quality_center/views.py
- Page
- 0003_about_contact_text.py
- useLang
- accounts/views.py
- TourContext.tsx
- drugs/reference_db.py
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
- fix_results
- SectionEditRequest
- panel/forms.py
- CalculatorDetailScreen.tsx
- offline/views.py
- test_public.py
- search_topics
- DrugPageTests
- QuizApiTests
- derive_key
- progress/views.py
- release.mjs
- PurchaseFlowTests
- json
- drugs/serializers.py
- FlashcardApiTests
- LessonTaxonomyTests
- expo
- planning.py
- import_medscape_articles.py
- ResultCard
- AppRelease
- TestCase
- 0005_atccode_name_fa.py
- offline/tests.py
- ۶. پیکربندی و متغیرهای محیطی
- offline/views.py
- files.web.ts
- ReferenceImportCommand
- throttling.py
- calculators/reference_db.py
- WebsiteAuthTests
- billing/tests.py
- ۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین
- Command
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
- Article
- UptodateTests
- OfflinePackageCard.tsx
- dqc_extras.py
- clean_profile_boilerplate.py
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- re
- billing/views.py
- Calculator
- offline/services.py
- Ingredient
- Pharmexa — custom icon prompts
- sources.ts
- docs/README.md
- 6. Lesson study topics (52)
- files.ts
- previews.tsx
- site.js
- VisitorDay
- uptodateLocal.ts
- downloader.web.ts
- ۲. راه‌اندازی محیط توسعه
- offline/reader.ts
- ImportCalculatorsTests
- ReferenceDbTests
- Repository Guidelines
- django_conf
- CalculatorDetail
- website_extras.py
- StandardizeUnitsTests
- accounts/services.py
- ۵. قرارداد API (نسخهٔ ۱)
- import_calculators.py
- ۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی
- tsconfig.json
- ensure_title_search_index
- django_apps
- UserSerializer
- sw.js
- Command
- TitleSearchTests
- ۱۲. سایت `pharmenta.ir` و پنل محتوا
- pagination.py
- _SectionCard
- otp.py
- latest_manifest
- ۴. اپ (Expo — اندروید، iOS و وب)
- docker-start.sh
- billing/apps.py
- CalculatorApiTests
- .claude/CLAUDE.md
- StudyTopicsCoverageTests
- app.config.js
- .mcp.json
- Command
- data_quality_center/tests.py
- ۳. بک‌اند (Django)
- snippet_source
- MedscapeApiTests
- view.ts
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
- IngredientProfileSection
- AtcSupplementTests
- rest_framework_permissions
- LessonDetailScreen.tsx
- ImportOpenfdaTests
- ۸. دیپلوی
- _nearest
- Section
- jalali.ts
- drugs/admin.py
- 0006_leitner_by_section.py
- Subscriber
- ۱. معرفی و معماری
- ۱۰. مرجع سریع دستورها
- کنسول فروش (`/ops/`)
- bidi.ts
- PackageFileView
- MysqlTitleSearchTests
- HostRoutingTests
- DateResult.tsx
- DrugApiTests
- 0004_clear_rule_based_facts.py
- Command
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

## Communities (224 total, 87 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.03
Nodes (96): حساب و احراز هویت — `/auth/`, flashcardsApi, guestApi, lessonsApi, offlineApi, quizApi, AtcCode, AtcGroup (+88 more)

### Community 1 - "django_db"
Cohesion: 0.02
Nodes (48): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+40 more)

### Community 2 - "test_panel.py"
Cohesion: 0.06
Nodes (16): StaffRole, Meta, SiteTestCase, AdminTests, AuthorTests, AuthTests, CommercePagesTests, InboxTests (+8 more)

### Community 3 - "console/views.py"
Cohesion: 0.05
Nodes (70): DiscountForm, FeatureEditForm, Meta, FeatureForm, Meta, latin_digits(), parse_amount(), parse_jalali() (+62 more)

### Community 4 - "react"
Cohesion: 0.07
Nodes (70): calculatorsApi, meApi, medscapeApi, CalculatorCategoryRef, CalculatorListItem, MedscapeKind, StudyPlanItem, TopInset (+62 more)

### Community 5 - "Post"
Cohesion: 0.06
Nodes (61): ActivityLog, Meta, Comment, Meta, ContactMessage, Meta, PostRevision, Meta (+53 more)

### Community 6 - "useTheme"
Cohesion: 0.11
Nodes (95): قابلیت‌ها, تور راهنما (`src/tour/`), ساختار `frontend/src/`, قواعد کدنویسی اپ, MediaViewer(), BottomNav(), Drawers(), LeitnerBox() (+87 more)

### Community 7 - "views_public.py"
Cohesion: 0.05
Nodes (57): fa(), site(), SiteMaintenanceMiddleware, DailyStat, Meta, SiteSettings, Meta, article() (+49 more)

### Community 8 - ".reverse"
Cohesion: 0.04
Nodes (12): AuthenticationSecurityTests, OnboardingTests, enabled_gateways(), wrapper(), AccessTests, GatewayPageTests, PlanBuilderTests, UsersPageTests (+4 more)

### Community 9 - "package.json"
Cohesion: 0.04
Nodes (81): زبان، جهت و تم, شروع اپ, App(), Gate(), ThemedStatusBar(), main, name, private (+73 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.05
Nodes (48): require_feature(), all_decks(), _carded_slugs(), _cards(), deck_cards(), deck_slugs(), next_topic(), progress_map() (+40 more)

### Community 11 - "test_onboarding_plan.py"
Cohesion: 0.13
Nodes (6): get_plan(), _onboarding(), OnboardingPlanTests, PlanTodayApiTests, MaintenancePlanAndApiTests, _two_chapter_topic()

### Community 12 - "guest.py"
Cohesion: 0.09
Nodes (17): create_guest(), GuestSessionView, GuestStatusView, _first_message(), _message_from_data(), _normalize_code(), platform_exception_handler(), UptodateArticleSerializer (+9 more)

### Community 13 - "LeitnerCard"
Cohesion: 0.07
Nodes (19): add_miss(), add_quiz_miss(), daily_minutes(), drawer_cards(), _exam_cap_days(), outcome(), overview(), previews() (+11 more)

### Community 14 - "SepGateway"
Cohesion: 0.06
Nodes (14): FakeGateway, GatewayError, get_gateway(), _post_json(), SepGateway, start_payment(), Verification, ZarinpalGateway (+6 more)

### Community 15 - "tests_console.py"
Cohesion: 0.05
Nodes (41): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, AdminAction, Meta (+33 more)

### Community 16 - "data_quality_center/views.py"
Cohesion: 0.12
Nodes (25): warning_count(), section_state(), _diffs(), discard(), history(), _login_key(), login_view(), logout_view() (+17 more)

### Community 17 - "Page"
Cohesion: 0.08
Nodes (6): clean_html(), _Cleaner, plain_text(), safe_url(), _Text, SanitizeTests

### Community 19 - "useLang"
Cohesion: 0.13
Nodes (31): CategoryPicker(), Chip(), ChipRow(), DateField(), ExamDatePicker(), latin(), MinutesPicker(), PRESET_MONTHS (+23 more)

### Community 20 - "accounts/views.py"
Cohesion: 0.07
Nodes (46): AuthTokenResponseSerializer, LoginSerializer, OtpRequestResponseSerializer, OtpRequestSerializer, OtpVerifySerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, PasswordResetResponseSerializer (+38 more)

### Community 21 - "TourContext.tsx"
Cohesion: 0.06
Nodes (47): releaseApi, AppReleaseInfo, escape(), MediaContent, mediaPage(), MediaPageColors, page(), Button() (+39 more)

### Community 22 - "drugs/reference_db.py"
Cohesion: 0.08
Nodes (9): Command, Command, _checked(), _digest(), export(), load(), open_parts(), part_name() (+1 more)

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.08
Nodes (56): CalculatorErrorCheck, LiveScore(), useLiveScore(), buildHeuristicSeeds(), cartesian(), classifyResultTone(), computeCalculator(), ComputeOptions (+48 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.07
Nodes (37): record_quiz_answers(), BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, preview_selection(), best_score_pct_for_topic(), _finished_sessions(), _finished_topic_sessions() (+29 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.05
Nodes (70): MedscapeBlock, MedscapeSection, ALPHABET, AlphabeticalArticleList(), buildOffsets(), groupAlphabetically(), Section, useBleedTop() (+62 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.09
Nodes (18): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, _categories_for_generics(), check_interactions(), close_all(), _conn(), _dir() (+10 more)

### Community 28 - ".request_code"
Cohesion: 0.09
Nodes (21): CodeRuleTests, PhoneAuthTestCase, ResetTests, SignUpTests, برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی, روش تبدیل پیشنهادها به کلمات کلیدی معتبر, ساخت Analytics از ابتدا (+13 more)

### Community 29 - "progress/tests.py"
Cohesion: 0.06
Nodes (27): Migration, seed(), DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin, DailyStudy, Meta (+19 more)

### Community 30 - "core/views.py"
Cohesion: 0.14
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 31 - "lessons/views.py"
Cohesion: 0.07
Nodes (27): _applies(), require_atc_content(), _require_content(), require_topic_content(), LessonDrugSerializer, fold(), get_lesson_drug(), _rank() (+19 more)

### Community 33 - "store.ts"
Cohesion: 0.17
Nodes (31): closeReaders(), bootOffline(), cancel(), currentUserId(), DatasetState, download(), events, finish() (+23 more)

### Community 34 - "fix_results"
Cohesion: 0.08
Nodes (13): fix_questions(), fix_results(), fix_strings_fa(), renumber_from_one(), _with_choices(), apply_fixes(), Migration, apply_fixes() (+5 more)

### Community 35 - "SectionEditRequest"
Cohesion: 0.10
Nodes (22): ReviewEvent, Meta, SectionEditRequest, Meta, approve(), _clean(), _client_ip(), _close() (+14 more)

### Community 36 - "panel/forms.py"
Cohesion: 0.05
Nodes (30): Media, Meta, AnnouncementForm, Meta, CategoryForm, Meta, ContentBlockForm, Meta (+22 more)

### Community 37 - "CalculatorDetailScreen.tsx"
Cohesion: 0.12
Nodes (34): describeInputs(), DateInput(), DaysInput(), Field(), QuestionTitle(), CardsFlow(), ChecklistFlow(), flowLayout (+26 more)

### Community 38 - "offline/views.py"
Cohesion: 0.13
Nodes (12): Command, cors_rule(), _request(), file_urls(), is_configured(), local_dir(), local_file_for_token(), _on_download_host() (+4 more)

### Community 39 - "test_public.py"
Cohesion: 0.09
Nodes (6): Post, Meta, CommentTests, DownloadAndMachineTests, make_post(), PostVisibilityTests

### Community 40 - "search_topics"
Cohesion: 0.14
Nodes (19): article_from_row(), _dir(), get_image(), get_topic(), is_available(), _is_word(), _mysql_conn(), _prefixed() (+11 more)

### Community 41 - "DrugPageTests"
Cohesion: 0.10
Nodes (4): DrugPageTests, make_drug(), SiteIdentityTests, structured()

### Community 42 - "QuizApiTests"
Cohesion: 0.09
Nodes (3): QuizAccessTests, QuizApiTests, QuizLockedTests

### Community 43 - "derive_key"
Cohesion: 0.17
Nodes (6): Command, derive_key(), open_sealed(), read_record(), secret(), PackFormatTests

### Community 44 - "progress/views.py"
Cohesion: 0.08
Nodes (27): Mistake, Meta, DashboardSerializer, FocusRowSerializer, FocusSessionSerializer, MistakeSerializer, Meta, NextChapterSerializer (+19 more)

### Community 45 - "release.mjs"
Cohesion: 0.09
Nodes (15): appJson, at, dryRun, file(), frontend, [kind, ...flags], lock, [major, minor, patch] (+7 more)

### Community 46 - "PurchaseFlowTests"
Cohesion: 0.05
Nodes (19): BillingConfig, clear_cache(), current(), gateway_spec(), _gateways(), GatewaySpec, _load(), row() (+11 more)

### Community 47 - "json"
Cohesion: 0.10
Nodes (12): build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections(), _varints(), new_build_id() (+4 more)

### Community 48 - "drugs/serializers.py"
Cohesion: 0.12
Nodes (10): AtcCodeSerializer, Meta, IngredientDetailSerializer, Meta, IngredientListSerializer, Meta, LessonSectionSerializer, AtcCodeListView (+2 more)

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
Cohesion: 0.06
Nodes (33): due_card_count(), mark_drug_read(), StudyPlanItem, Meta, _chapter(), complete_item(), ensure_today_items(), _flashcard_recall_for_slugs() (+25 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.16
Nodes (7): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label()

### Community 54 - "ResultCard"
Cohesion: 0.34
Nodes (21): Explain(), Hero(), Interpretation(), Ltr(), ResultCard(), showTierBar(), TierBar(), tierText() (+13 more)

### Community 55 - "AppRelease"
Cohesion: 0.08
Nodes (13): note_lines(), ReleaseCheckView, ReleaseQuerySerializer, AppRelease, Meta, version_code(), ReleaseForm, Meta (+5 more)

### Community 56 - "TestCase"
Cohesion: 0.16
Nodes (4): CleanBoilerplateInPipelineTests, LoadAtcReferenceTests, _make_source_db(), StandardizePipelineUnitsTests

### Community 58 - "offline/tests.py"
Cohesion: 0.06
Nodes (9): Command, CalculatorTag, Meta, _DryRun, Command, rewrite_summaries(), _make_snapshot(), _index() (+1 more)

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.12
Nodes (16): HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت, دادهٔ مرجع (UpToDate و Lexicomp), دیتابیس، کش و آمادگی, سایت (+8 more)

### Community 60 - "offline/views.py"
Cohesion: 0.14
Nodes (17): build_matches_dataset(), PackError, LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer, PackageFileUrlSerializer, PackageManifestSerializer (+9 more)

### Community 61 - "files.web.ts"
Cohesion: 0.19
Nodes (9): file(), forget(), partSize(), readRange(), removeBuild(), removeOtherBuilds(), removePart(), snapshots (+1 more)

### Community 62 - "ReferenceImportCommand"
Cohesion: 0.09
Nodes (6): Command, _DryRun, ReferenceImportCommand, Command, Command, Command

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "calculators/reference_db.py"
Cohesion: 0.09
Nodes (15): export(), load(), dumps(), expected_count(), loads(), open_for_import(), record_counts(), rows() (+7 more)

### Community 66 - "billing/tests.py"
Cohesion: 0.06
Nodes (22): _div(), format_date(), _jal_cal(), _mod(), month_start(), to_gregorian(), to_jalali(), content_lock() (+14 more)

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (26): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+18 more)

### Community 69 - "dependencies"
Cohesion: 0.05
Nodes (39): dependencies, axios, expo, expo-build-properties, expo-constants, expo-crypto, expo-file-system, expo-font (+31 more)

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
Nodes (36): Command, Command, Announcement, Meta, Category, Meta, ContentBlock, Meta (+28 more)

### Community 74 - "HealthCheckTests"
Cohesion: 0.15
Nodes (3): HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests

### Community 75 - "logging"
Cohesion: 0.07
Nodes (10): password_reset_url_for_user(), send_password_reset_email(), send_password_reset_emails_for_email(), send_password_reset_email_task(), PlatformTask, retry_delay_seconds(), get_request_id(), JsonFormatter (+2 more)

### Community 76 - "SectionEdit"
Cohesion: 0.16
Nodes (6): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin, SectionEdit, Meta

### Community 77 - "views_account.py"
Cohesion: 0.08
Nodes (14): EmailOrUsernameBackend, LearnerProfile, InvalidPhone, looks_like_phone(), normalize_phone(), PhoneField, NormalizePhoneTests, ProfileTests (+6 more)

### Community 79 - "ReviewTests"
Cohesion: 0.16
Nodes (3): ConsoleTestCase, DraftAndSubmitTests, ReviewTests

### Community 80 - "common.tsx"
Cohesion: 0.16
Nodes (26): bandFor(), Chip(), Collapse(), Extra, Extras(), fmt(), LEVEL_TONES, plain() (+18 more)

### Community 81 - "calculatorModel.ts"
Cohesion: 0.15
Nodes (23): CalculatorResultDef, StagingResult(), allWholeNumbers(), cache, classify(), classifyCalculator(), isNumeric(), LadderRung (+15 more)

### Community 82 - "Article"
Cohesion: 0.11
Nodes (13): Article, Meta, ArticleImage, ArticleDetailSerializer, Meta, ArticleImageSerializer, Meta, ArticleListSerializer (+5 more)

### Community 84 - "OfflinePackageCard.tsx"
Cohesion: 0.31
Nodes (8): ERROR_TEXT, LOGO, NAME, OfflinePackageCard(), PHASE_TEXT, formatBytes(), formatDay(), sourceVersion()

### Community 85 - "dqc_extras.py"
Cohesion: 0.13
Nodes (16): ago(), get_item(), guest_access_on(), initial(), jdate(), num(), toman(), action_label() (+8 more)

### Community 86 - "clean_profile_boilerplate.py"
Cohesion: 0.14
Nodes (13): clean_text(), Command, cleaned(), is_hypersensitivity_boilerplate(), is_hypersensitivity_boilerplate_en(), is_negative_indication_en(), is_negative_indication_fa(), is_null_placeholder() (+5 more)

### Community 87 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.06
Nodes (18): build.sh script, validate_production_broker(), validate_production_cache(), validate_production_secret_key(), CorsPreflightTests, ProductionSecretKeyTests, DJANGO_SETTINGS_MODULE, release.sh script (+10 more)

### Community 88 - "re"
Cohesion: 0.13
Nodes (14): _fa_keys_standardized(), _stage_names_without_prefix(), _title_formula_as_result(), _with_unit(), _adjective(), _chain(), _key(), _latin_quantity() (+6 more)

### Community 89 - "billing/views.py"
Cohesion: 0.07
Nodes (36): is_guest(), Order, Meta, Plan, Meta, CatalogSerializer, CheckoutSerializer, MyAccessSerializer (+28 more)

### Community 90 - "Calculator"
Cohesion: 0.13
Nodes (15): Calculator, Meta, CalculatorCategory, Meta, CalculatorCategorySerializer, Meta, CalculatorDetailSerializer, Meta (+7 more)

### Community 91 - "offline/services.py"
Cohesion: 0.24
Nodes (7): has_paid_plan_with(), is_entitled(), is_guest(), issue_license(), license_days(), LicenseError, _wrap_for()

### Community 92 - "Ingredient"
Cohesion: 0.04
Nodes (37): Command, Command, AtcCategory, Meta, AtcCode, Meta, Ingredient, Meta (+29 more)

### Community 93 - "Pharmexa — custom icon prompts"
Cohesion: 0.15
Nodes (12): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups, 9. App identity (optional) (+4 more)

### Community 94 - "sources.ts"
Cohesion: 0.15
Nodes (16): lexicompApi, uptodateApi, LexicompDrug, LexicompInteraction, cache, checkInteractions(), LexIndex, searchDrugs() (+8 more)

### Community 96 - "6. Lesson study topics (52)"
Cohesion: 0.15
Nodes (13): 6. Lesson study topics (52), Cardiovascular & blood, Dermatology, Endocrine & metabolism, Gastrointestinal, Infectious disease, Miscellaneous, Musculoskeletal (+5 more)

### Community 97 - "files.ts"
Cohesion: 0.13
Nodes (19): downloader, DownloadEvents, PartJob, PartRef, tasks, buildDir(), closeHandles(), ensureBuildDir() (+11 more)

### Community 98 - "previews.tsx"
Cohesion: 0.37
Nodes (21): Bands(), Check(), CheckDot(), Choice(), Drawers(), Flip(), Interaction(), kf() (+13 more)

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

### Community 100 - "VisitorDay"
Cohesion: 0.24
Nodes (4): VisitorDay, Meta, UniqueVisitorTests, visit()

### Community 101 - "uptodateLocal.ts"
Cohesion: 0.13
Nodes (24): UptodateImage, Prepared, bitCount(), buildTitleIndex(), cache, compareKeys(), getTopic(), IMAGE_TYPES (+16 more)

### Community 102 - "downloader.web.ts"
Cohesion: 0.20
Nodes (9): downloader, DownloadEvents, newWorker(), PartJob, PartRef, Run, runFor(), runs (+1 more)

### Community 103 - "۲. راه‌اندازی محیط توسعه"
Cohesion: 0.17
Nodes (12): اندروید و iOS, اپ (Expo), بک‌اند, تست بستهٔ آفلاین بدون باکت, تست و بررسی, روال کار با مخزن, ساخت دیتابیس و اجرای سرور, نسخهٔ وب (+4 more)

### Community 104 - "offline/reader.ts"
Cohesion: 0.17
Nodes (12): پایهٔ Django, OfflineDataset, OfflineManifest, keyring, openRecord(), openRecordBase64(), PackageKey, sealed() (+4 more)

### Community 105 - "ImportCalculatorsTests"
Cohesion: 0.32
Nodes (3): _build_sqlite(), ImportCalculatorsTests, _one_calculator()

### Community 107 - "Repository Guidelines"
Cohesion: 0.25
Nodes (7): Build, Test, and Development Commands, Coding Style & Naming Conventions, Commit & Pull Request Guidelines, Project Structure & Module Organization, Repository Guidelines, Security & Configuration Tips, Testing Guidelines

### Community 108 - "django_conf"
Cohesion: 0.10
Nodes (9): _error_message(), send_code(), _send_smsir(), SentCode, SmsSendError, SmsIrBackendTests, enqueue(), ReviewForm (+1 more)

### Community 109 - "CalculatorDetail"
Cohesion: 0.27
Nodes (10): CalculatorDetail, CalculatorQuestion, ResultProps, LIST_FROM, FieldProps, FlowProps, CalculatorAnswers, ComputedResult (+2 more)

### Community 110 - "website_extras.py"
Cohesion: 0.15
Nodes (8): atc_groups(), feature_icon(), nav_on(), oneline(), person(), split_highlight(), split_lines(), آنچه کد انجام می‌دهد

### Community 112 - "accounts/services.py"
Cohesion: 0.05
Nodes (25): SessionTokenAuthentication, SessionTokenAuthenticationScheme, Role, Meta, RoleAssignment, Meta, SessionRefreshToken, Meta (+17 more)

### Community 113 - "۵. قرارداد API (نسخهٔ ۱)"
Cohesion: 0.10
Nodes (20): Lexicomp — `/lexicomp/` (ویژگی `lexicomp`), Medscape — `/medscape/` (ویژگی `medscape`), UpToDate — `/uptodate/` (ویژگی `uptodate`), آزمون — `/quiz/` (ویژگی `quiz`؛ پرچم `QUIZ_API_ENABLED`), تغییر دادن API, جعبهٔ قدیمی, جعبهٔ لایتنر, داروها — `/drugs/` و `/atc/` (+12 more)

### Community 114 - "import_calculators.py"
Cohesion: 0.14
Nodes (12): standardize_fa_units(), Command, _error_checks_for(), _formula_strings_fa(), _import_categories(), _import_tags(), _questions_for(), _references_for() (+4 more)

### Community 115 - "۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی"
Cohesion: 0.12
Nodes (17): اطلاعات غیرمحرمانه‌ای که باید جایی ثبت باشد, بازیابی, بکاپ و بازیابی, حساب‌های سرویس, رازها و چیزهایی که باید امن نگه داشته شوند, رازهای فنی, شاخص‌هایی که مرتب دیده شوند, عیب‌یابی (+9 more)

### Community 116 - "tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, paths, strict, extends, include, expo/tsconfig.base

### Community 117 - "ensure_title_search_index"
Cohesion: 0.16
Nodes (5): Command, ensure_title_search_index(), _has_title_search_index(), mysql_config(), MysqlTitleIndexTests

### Community 119 - "UserSerializer"
Cohesion: 0.16
Nodes (7): LearnerProfileSerializer, Meta, OnboardingSerializer, UserSerializer, Meta, MeView, OnboardingView

### Community 120 - "sw.js"
Cohesion: 0.38
Nodes (4): inScope(), referencedFiles(), SCOPE, storeShell()

### Community 122 - "TitleSearchTests"
Cohesion: 0.21
Nodes (3): build_title_index(), _title_words(), TitleSearchTests

### Community 123 - "۱۲. سایت `pharmenta.ir` و پنل محتوا"
Cohesion: 0.14
Nodes (14): not_found(), آمار بازدید, حساب و خرید روی سایت, دارونامهٔ عمومی (`/drugs/`), رسانه, سئو, ساختار کد, صفحه‌های عمومی (+6 more)

### Community 125 - "_SectionCard"
Cohesion: 0.19
Nodes (3): _card_back_fields(), DeckCardSerializer, _SectionCard

### Community 126 - "otp.py"
Cohesion: 0.08
Nodes (31): OneTimeCode, Meta, SecurityAuditEvent, Meta, account_for_signup(), _hash(), _minutes(), _new_code() (+23 more)

### Community 127 - "latest_manifest"
Cohesion: 0.11
Nodes (7): clear_cache(), latest_manifest(), BucketManifestTests, BuildTests, DownloadHostTests, _quiet(), _record()

### Community 128 - "۴. اپ (Expo — اندروید، iOS و وب)"
Cohesion: 0.20
Nodes (11): آنبوردینگ و برنامهٔ مطالعه, ارتباط با API و کش, افزودن صفحهٔ تازه, دانلود آفلاین (`src/offline/`), فلش‌کارت و جعبهٔ لایتنر, ناوبری, نمایش بزرگ عکس و جدول, وب‌اپ و PWA (+3 more)

### Community 132 - "CalculatorApiTests"
Cohesion: 0.12
Nodes (3): CalculatorApiTests, FaUnitsTests, QuestionUnitTests

### Community 152 - "Command"
Cohesion: 0.21
Nodes (4): Command, _int(), _json_list(), _name_fa()

### Community 156 - "data_quality_center/tests.py"
Cohesion: 0.24
Nodes (6): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), word_diff(), CheckTests

### Community 182 - "۳. بک‌اند (Django)"
Cohesion: 0.12
Nodes (13): RequestIdMiddleware, SiteHostMiddleware, UpToDate و Lexicomp, افزودن یک قابلیت فروشی تازه, بستهٔ آفلاین (`apps.offline`), زنجیرهٔ middleware, صورتحساب و دسترسی (`apps.billing`), قواعد مشترک API (+5 more)

### Community 183 - "snippet_source"
Cohesion: 0.29
Nodes (4): snippet_source(), _updated_from_html(), _updated_from_text(), HeaderTextTests

### Community 185 - "view.ts"
Cohesion: 0.18
Nodes (13): OfflinePackageInfo, empty(), InstalledPackage, licenseExpiresAt(), OfflineErrorCode, pendingBytes(), PendingPackage, useOffline (+5 more)

### Community 196 - "IngredientProfileSection"
Cohesion: 0.15
Nodes (7): IngredientProfileSectionInline, IngredientProfileSection, Meta, LessonDrugSectionSerializer, Meta, ProfileSectionSerializer, Meta

### Community 198 - "rest_framework_permissions"
Cohesion: 0.27
Nodes (6): CanManagePlatformRoles, CanViewSecurityAudit, HasPlatformPermission, HasRecentStepUp, session_has_recent_step_up(), user_has_platform_permission()

### Community 202 - "LessonDetailScreen.tsx"
Cohesion: 0.33
Nodes (10): LessonSection, joinOpenParens(), LessonBlock, LessonLine, parenDepth(), parseLessonText(), sectionText(), splitIssues() (+2 more)

### Community 204 - "۸. دیپلوی"
Cohesion: 0.12
Nodes (16): CI, امنیت و هشدار نصب, اپ اندروید و iOS, برگرداندن یک دیپلوی خراب, بک‌اند, جریان دیپلوی, حجم APK, راه‌اندازی از صفر (یک بار) (+8 more)

### Community 205 - "_nearest"
Cohesion: 0.22
Nodes (5): _letters(), _max_typos(), _nearest(), _typo_distance(), TypoDistanceTests

### Community 207 - "jalali.ts"
Cohesion: 0.56
Nodes (9): BREAKS, d2g(), d2j(), div(), g2d(), j2d(), jalCal(), mod() (+1 more)

### Community 208 - "drugs/admin.py"
Cohesion: 0.36
Nodes (4): AtcCategoryAdmin, AtcCodeAdmin, IngredientAdmin, IngredientProfileSectionAdmin

### Community 209 - "0006_leitner_by_section.py"
Cohesion: 0.21
Nodes (4): Migration, restart_decks(), clear_bank(), Migration

### Community 210 - "Subscriber"
Cohesion: 0.25
Nodes (3): Subscriber, Meta, FormsTests

### Community 211 - "۱. معرفی و معماری"
Cohesion: 0.25
Nodes (8): دامنه‌ها و سرویس‌ها, ذخیره‌گاه‌های داده, ساختار مخزن, سرویس‌های بیرونی, فناوری‌ها, محصول, معماری, ۱. معرفی و معماری

### Community 212 - "۱۰. مرجع سریع دستورها"
Cohesion: 0.25
Nodes (8): اپ موبایل (EAS), تست و بررسی, توسعهٔ محلی, دستورهای مدیریتی Django (همه), دیپلوی و گیت, عیب‌یابی, پایپلاین study_content (بیرون از مخزن), ۱۰. مرجع سریع دستورها

### Community 213 - "کنسول فروش (`/ops/`)"
Cohesion: 0.25
Nodes (8): ادمین Django (`/admin/`), درگاه پرداخت و کلیدهای فروش, دسترسی مهمان, ویژگی‌ها, پلن‌ها و محصول‌ها, کاربران, کنسول فروش (`/ops/`), ۱۱. کنسول‌های مدیریت

### Community 214 - "bidi.ts"
Cohesion: 0.25
Nodes (7): isolated(), ENGLISH_RUN, hasPersianLetters(), isolateEnglish(), LRI, PDI, RLM

### Community 218 - "DateResult.tsx"
Cohesion: 0.48
Nodes (6): hasPersian(), Rows(), DateResult(), useDateFormat(), parseAge(), parseDateText()

### Community 226 - "مستندات فارمنتا"
Cohesion: 0.50
Nodes (4): سندهای دیگر مخزن, فهرست, قرارداد نگهداری این مستندات, مستندات فارمنتا

### Community 230 - "فارمنتا (Pharmenta)"
Cohesion: 0.67
Nodes (3): شروع سریع, فارمنتا (Pharmenta), مستندات

## Knowledge Gaps
- **9 isolated node(s):** `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-build-properties`, `expo-splash-screen`, `react-dom` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1661 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **87 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `useTheme` to `accounts/services.py`, `package.json`, `TourContext.tsx`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.163) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `AppText()` (e.g. with `زبان، جهت و تم` and `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅`) actually correct?**
  _`AppText()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-build-properties` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.0336996336996337 - nodes in this community are weakly interconnected._
- **Why does `UserSession` connect `accounts/services.py` to `WebsiteAuthTests`, `console/views.py`, `useTheme`, `guest.py`, `views_account.py`, `PurchaseFlowTests`, `tests_console.py`, `accounts/views.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`, `offline/tests.py`, `otp.py`?**
  _High betweenness centrality (0.161) - this node is a cross-community bridge._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.024175824175824177 - nodes in this community are weakly interconnected._
- **Why does `اپ‌ها (`backend/apps/`)` connect `tests_console.py` to `test_panel.py`, `console/views.py`, `views_public.py`, `flashcards/views.py`, `LeitnerCard`, `quiz/views.py`, `progress/tests.py`, `SectionEditRequest`, `panel/forms.py`, `test_public.py`, `PurchaseFlowTests`, `planning.py`, `۳. بک‌اند (Django)`, `offline/tests.py`, `IngredientProfileSection`, `website/models.py`, `SectionEdit`, `Article`, `billing/views.py`, `Calculator`, `Ingredient`, `accounts/services.py`, `otp.py`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._