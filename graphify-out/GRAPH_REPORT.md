# Graph Report - Learning Platform  (2026-10-26)

## Corpus Check
- 531 files · ~427,912 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 35 file(s) not represented in the graph (top: (none) 11, .ttf 7, .css 5)

## Summary
- 5250 nodes · 15048 edges · 229 communities (138 shown, 91 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1352 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3313355e`
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
- useTheme
- PlatformAPIError
- LeitnerCard
- SepGateway
- tests_console.py
- data_quality_center/views.py
- Page
- 0003_about_contact_text.py
- useLang
- accounts/views.py
- TourContext.tsx
- time
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
- billing/services.py
- progress/views.py
- release.mjs
- PurchaseFlowTests
- offline/tests.py
- drugs/serializers.py
- FlashcardApiTests
- LessonTaxonomyTests
- expo
- planning.py
- import_medscape_articles.py
- ResultCard
- AppRelease
- manage/views.py
- 0005_atccode_name_fa.py
- bootstrap_superuser.py
- ۶. پیکربندی و متغیرهای محیطی
- offline/views.py
- files.web.ts
- billing/tests.py
- throttling.py
- calculators/reference_db.py
- WebsiteAuthTests
- PurchaseApiTests
- ۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین
- accounts/serializers.py
- dependencies
- medscape/tests.py
- crypto.web.ts
- panel.js
- views_drugs.py
- HealthCheckTests
- logging
- SectionEdit
- views_account.py
- decks.py
- ReviewTests
- common.tsx
- calculatorModel.ts
- Article
- UptodateTests
- ZarinpalGateway
- dqc_extras.py
- clean_profile_boilerplate.py
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- re
- django_conf
- Calculator
- make
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
- nav.py
- settings/base.py
- Repository Guidelines
- authentication.py
- CalculatorDetail
- website_extras.py
- StandardizeUnitsTests
- issue_user_session
- ۵. قرارداد API (نسخهٔ ۱)
- import_calculators.py
- ۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی
- tsconfig.json
- Command
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
- PaymentGateway
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
- ZibalGateway
- AuthenticationSecurityTests
- OfflinePackageCard.tsx
- data_quality_center/apps.py
- drugs/apps.py
- flashcards/apps.py
- lessons/apps.py
- lexicomp/apps.py
- offline/apps.py
- _Cleaner
- quiz/apps.py
- uptodate/apps.py
- website/apps.py
- drugs/views.py
- GatewayPageTests
- accounts/views.py
- LessonDetailScreen.tsx
- downloader.ts
- ۸. دیپلوی
- OnboardingTests
- Section
- ReleaseCheckTests
- PlanSerializer
- _Parts
- website/models.py
- ۱. معرفی و معماری
- ۱۰. مرجع سریع دستورها
- ۱۱. مدیریت
- logging.py
- exceptions.py
- NavigationTests
- website/services.py
- DateResult.tsx
- SearchTests
- 0004_clear_rule_based_facts.py
- MyEntitlementSerializer
- AccessTests
- writing
- manage/apps.py
- medscape/apps.py
- مستندات فارمنتا
- devDependencies
- فارمنتا (Pharmenta)

## God Nodes (most connected - your core abstractions)
1. `useTheme()` - 204 edges
2. `AppText()` - 192 edges
3. `useLang()` - 181 edges
4. `react` - 88 edges
5. `PlatformAPIError` - 83 edges
6. `Ingredient` - 81 edges
7. `react-native` - 77 edges
8. `useNav` - 65 edges
9. `Post` - 58 edges
10. `Plan` - 53 edges

## Surprising Connections (you probably didn't know these)
- `فاز ۰.۵ — حذف زیرساخت رهاشده ✅` --references--> `UserSession`  [INFERRED]
  PHASES.md → backend/apps/accounts/models.py
- `ورود و دسترسی` --references--> `SecurityAuditEvent`  [INFERRED]
  docs/11-admin-consoles.md → backend/apps/accounts/models.py
- `۳d — بازنویسی `data_quality_center` ✅` --references--> `SectionEdit`  [INFERRED]
  PHASES.md → backend/apps/data_quality_center/models.py
- `دستورهای خودکار هنگام شروع` --references--> `AtcCategory`  [INFERRED]
  docs/07-data.md → backend/apps/drugs/models.py
- `۳a — جدول مرجع ATC + `apps.lessons` ✅` --references--> `AtcCategory`  [INFERRED]
  PHASES.md → backend/apps/drugs/models.py

## Import Cycles
- None detected.

## Communities (229 total, 91 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.03
Nodes (84): حساب و احراز هویت — `/auth/`, lexicompApi, offlineApi, quizApi, releaseApi, uptodateApi, AppReleaseInfo, AtcCode (+76 more)

### Community 1 - "django_db"
Cohesion: 0.02
Nodes (53): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+45 more)

### Community 2 - "test_panel.py"
Cohesion: 0.06
Nodes (11): AdminTests, AuthorTests, AuthTests, make_user(), MediaTests, PanelCase, PermissionTests, PostTests (+3 more)

### Community 3 - "console/views.py"
Cohesion: 0.06
Nodes (62): DiscountForm, FeatureEditForm, Meta, FeatureForm, Meta, latin_digits(), parse_amount(), parse_jalali() (+54 more)

### Community 4 - "react"
Cohesion: 0.06
Nodes (64): lessonsApi, medscapeApi, PlanMode, ALPHABET, AlphabeticalArticleList(), buildOffsets(), groupAlphabetically(), Section (+56 more)

### Community 5 - "Post"
Cohesion: 0.06
Nodes (56): ActivityLog, Meta, Media, Meta, Post, Meta, orders(), plans() (+48 more)

### Community 6 - "useTheme"
Cohesion: 0.12
Nodes (74): قابلیت‌ها, افزودن صفحهٔ تازه, قواعد کدنویسی اپ, ناوبری, calculatorsApi, meApi, BottomNav(), Drawers() (+66 more)

### Community 7 - "views_public.py"
Cohesion: 0.05
Nodes (51): site(), SiteMaintenanceMiddleware, DailyStat, Meta, SiteSettings, Meta, article(), breadcrumbs() (+43 more)

### Community 8 - ".reverse"
Cohesion: 0.08
Nodes (6): PlanBuilderTests, UsersPageTests, AccessTests, render_links(), link(), search()

### Community 9 - "package.json"
Cohesion: 0.03
Nodes (87): آنبوردینگ و برنامهٔ مطالعه, ارتباط با API و کش, دانلود آفلاین (`src/offline/`), زبان، جهت و تم, ساختار `frontend/src/`, شروع اپ, فلش‌کارت و جعبهٔ لایتنر, نمایش بزرگ عکس و جدول (+79 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.05
Nodes (48): _applies(), _require_content(), require_feature(), require_topic_content(), FlashcardFactAdmin, LeitnerCardAdmin, progress_map(), topic_meta() (+40 more)

### Community 11 - "useTheme"
Cohesion: 0.08
Nodes (57): flashcardsApi, BoxRating, LeitnerOverview, PlanDay, PlanToday, RatingOutcome, SectionTone, StudyPlanItem (+49 more)

### Community 12 - "PlatformAPIError"
Cohesion: 0.26
Nodes (9): PlatformAPIError, UptodateArticleSerializer, UptodateImageSerializer, UptodateSearchResultSerializer, UptodateTopicSerializer, ImageDetailView, _require_available(), TopicDetailView (+1 more)

### Community 13 - "LeitnerCard"
Cohesion: 0.07
Nodes (18): add_miss(), add_quiz_miss(), daily_minutes(), drawer_cards(), _exam_cap_days(), outcome(), overview(), previews() (+10 more)

### Community 14 - "SepGateway"
Cohesion: 0.12
Nodes (4): SepGateway, _fake_urlopen(), GatewayChoiceTests, SepTests

### Community 15 - "tests_console.py"
Cohesion: 0.07
Nodes (30): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, AdminAction, Meta (+22 more)

### Community 16 - "data_quality_center/views.py"
Cohesion: 0.12
Nodes (25): wrapper(), warning_count(), section_state(), _diffs(), discard(), history(), logout_view(), my_requests() (+17 more)

### Community 17 - "Page"
Cohesion: 0.13
Nodes (4): clean_html(), plain_text(), safe_url(), SanitizeTests

### Community 19 - "useLang"
Cohesion: 0.10
Nodes (49): DateInput(), DaysInput(), Field(), QuestionTitle(), CategoryPicker(), Chip(), ChipRow(), DateField() (+41 more)

### Community 20 - "accounts/views.py"
Cohesion: 0.08
Nodes (25): RoleAssignment, Meta, OtpRequestSerializer, PasswordResetRequestSerializer, RoleAssignmentCreateSerializer, RoleAssignmentRevokeSerializer, RoleAssignmentSerializer, Meta (+17 more)

### Community 21 - "TourContext.tsx"
Cohesion: 0.11
Nodes (21): canGoBack(), installWebBackGuard(), Interceptor, interceptors, listeners, notify(), subscribeBackState(), WebBackGuard() (+13 more)

### Community 22 - "time"
Cohesion: 0.14
Nodes (3): Command, Command, _DryRun

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.08
Nodes (56): CalculatorErrorCheck, LiveScore(), useLiveScore(), buildHeuristicSeeds(), cartesian(), classifyResultTone(), computeCalculator(), ComputeOptions (+48 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.05
Nodes (43): slugs_for_topic(), record_quiz_answers(), BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, ingredient_ids_for_selection(), preview_selection(), sample_bank_questions() (+35 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.05
Nodes (89): تور راهنما (`src/tour/`), MedscapeBlock, MedscapeSection, useBleedTop(), countMatches(), FindState, highlight(), ListMarker() (+81 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.08
Nodes (19): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, _categories_for_generics(), check_interactions(), close_all(), _conn(), _dir() (+11 more)

### Community 28 - ".request_code"
Cohesion: 0.06
Nodes (27): _error_message(), send_code(), _send_smsir(), SentCode, SmsSendError, CodeRuleTests, PhoneAuthTestCase, ResetTests (+19 more)

### Community 29 - "progress/tests.py"
Cohesion: 0.05
Nodes (28): seed(), lesson_groups(), topic_chapters(), DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin, DailyStudy (+20 more)

### Community 30 - "core/views.py"
Cohesion: 0.15
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 31 - "lessons/views.py"
Cohesion: 0.06
Nodes (29): require_atc_content(), ChapterProgress, Meta, ReadDrug, Meta, fold(), get_chapter(), get_lesson_drug() (+21 more)

### Community 33 - "store.ts"
Cohesion: 0.14
Nodes (35): removeBuild(), removeOtherBuilds(), closeReaders(), bootOffline(), cancel(), currentUserId(), DatasetState, download() (+27 more)

### Community 34 - "fix_results"
Cohesion: 0.08
Nodes (13): fix_questions(), fix_results(), fix_strings_fa(), renumber_from_one(), _with_choices(), apply_fixes(), Migration, apply_fixes() (+5 more)

### Community 35 - "SectionEditRequest"
Cohesion: 0.10
Nodes (22): ReviewEvent, Meta, SectionEditRequest, Meta, approve(), _clean(), _client_ip(), _close() (+14 more)

### Community 36 - "panel/forms.py"
Cohesion: 0.05
Nodes (30): make_slug(), unique_slug(), AnnouncementForm, Meta, CategoryForm, Meta, ContentBlockForm, Meta (+22 more)

### Community 37 - "CalculatorDetailScreen.tsx"
Cohesion: 0.18
Nodes (22): describeInputs(), Choices(), FieldVariant, isBinaryQuestion(), label(), Numeric(), QuestionField(), Weight() (+14 more)

### Community 38 - "offline/views.py"
Cohesion: 0.14
Nodes (13): Command, cors_rule(), _request(), file_urls(), is_configured(), latest_manifest(), local_dir(), local_file_for_token() (+5 more)

### Community 39 - "test_public.py"
Cohesion: 0.15
Nodes (3): DownloadAndMachineTests, make_post(), PostVisibilityTests

### Community 40 - "search_topics"
Cohesion: 0.10
Nodes (26): article_from_row(), build_title_index(), _dir(), get_image(), get_topic(), is_available(), _is_word(), _letters() (+18 more)

### Community 41 - "DrugPageTests"
Cohesion: 0.12
Nodes (3): DrugPageTests, SiteIdentityTests, structured()

### Community 42 - "QuizApiTests"
Cohesion: 0.09
Nodes (3): QuizAccessTests, QuizApiTests, QuizLockedTests

### Community 43 - "billing/services.py"
Cohesion: 0.08
Nodes (26): Access, active_entitlements(), BillingError, check_feature(), content_lock(), create_order(), effective_features(), take() (+18 more)

### Community 44 - "progress/views.py"
Cohesion: 0.08
Nodes (27): Mistake, Meta, DashboardSerializer, FocusRowSerializer, FocusSessionSerializer, MistakeSerializer, Meta, NextChapterSerializer (+19 more)

### Community 45 - "release.mjs"
Cohesion: 0.09
Nodes (15): appJson, at, dryRun, file(), frontend, [kind, ...flags], lock, [major, minor, patch] (+7 more)

### Community 46 - "PurchaseFlowTests"
Cohesion: 0.07
Nodes (5): clear_cache(), _settings_changed(), GuestAccessTests, GuestConsoleTests, PurchaseFlowTests

### Community 47 - "offline/tests.py"
Cohesion: 0.06
Nodes (23): build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections(), _varints(), Command (+15 more)

### Community 48 - "drugs/serializers.py"
Cohesion: 0.13
Nodes (12): AtcCodeSerializer, Meta, IngredientDetailSerializer, Meta, IngredientListSerializer, Meta, LessonDrugSectionSerializer, Meta (+4 more)

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
Cohesion: 0.05
Nodes (40): due_card_count(), mark_drug_read(), topic_progress(), StudyPlanItem, Meta, _chapter(), complete_item(), ensure_today_items() (+32 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.16
Nodes (7): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label()

### Community 54 - "ResultCard"
Cohesion: 0.34
Nodes (21): Explain(), Hero(), Interpretation(), Ltr(), ResultCard(), showTierBar(), TierBar(), tierText() (+13 more)

### Community 55 - "AppRelease"
Cohesion: 0.09
Nodes (12): LatestReleaseSerializer, note_lines(), ReleaseCheckSerializer, ReleaseCheckView, ReleaseQuerySerializer, AppRelease, Meta, version_code() (+4 more)

### Community 56 - "manage/views.py"
Cohesion: 0.09
Nodes (31): anyone(), can_enter(), has_site_role(), is_operator(), is_super(), site(), site_admin(), activity() (+23 more)

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.10
Nodes (20): local(), open(), paint(), HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت (+12 more)

### Community 60 - "offline/views.py"
Cohesion: 0.08
Nodes (24): build_matches_dataset(), LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer, PackageFileUrlSerializer, PackageManifestSerializer, PackageUrlsRequestSerializer (+16 more)

### Community 61 - "files.web.ts"
Cohesion: 0.19
Nodes (9): file(), forget(), partSize(), readRange(), removeBuild(), removeOtherBuilds(), removePart(), snapshots (+1 more)

### Community 62 - "billing/tests.py"
Cohesion: 0.16
Nodes (17): _div(), fa_digits(), format_date(), _jal_cal(), _mod(), month_start(), to_gregorian(), to_jalali() (+9 more)

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "calculators/reference_db.py"
Cohesion: 0.07
Nodes (17): export(), load(), Command, dumps(), expected_count(), loads(), record_counts(), rows() (+9 more)

### Community 66 - "PurchaseApiTests"
Cohesion: 0.11
Nodes (4): EnforcementTests, narrow_free_plan(), PurchaseApiTests, SeedTests

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (26): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+18 more)

### Community 68 - "accounts/serializers.py"
Cohesion: 0.11
Nodes (17): Role, Meta, AuthTokenResponseSerializer, LoginSerializer, OtpRequestResponseSerializer, PasswordResetResponseSerializer, RefreshSessionSerializer, RegisterSerializer (+9 more)

### Community 69 - "dependencies"
Cohesion: 0.05
Nodes (36): dependencies, axios, expo, expo-build-properties, expo-constants, expo-crypto, expo-file-system, expo-font (+28 more)

### Community 70 - "medscape/tests.py"
Cohesion: 0.11
Nodes (6): _disease_record(), _guideline_record(), ImportMedscapeArticlesTests, MedscapeApiTests, _write_diseases_tree(), _write_guidelines()

### Community 71 - "crypto.web.ts"
Cohesion: 0.23
Nodes (9): اجرای کامل با Docker, db(), idb(), keyring, openRecord(), openRecordBase64(), PackageKey, rsaPair() (+1 more)

### Community 72 - "panel.js"
Cohesion: 0.19
Nodes (11): buildEditor(), align(), block(), exec(), sync(), toggleSource(), wrapBlock(), loadPicker() (+3 more)

### Community 73 - "views_drugs.py"
Cohesion: 0.08
Nodes (14): Command, _build_catalog(), catalog(), _drop_title(), drug_detail(), english_name(), fa_key(), _group_code() (+6 more)

### Community 74 - "HealthCheckTests"
Cohesion: 0.15
Nodes (3): HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests

### Community 75 - "logging"
Cohesion: 0.07
Nodes (8): password_reset_url_for_user(), send_password_reset_email(), send_password_reset_emails_for_email(), send_password_reset_email_task(), PlatformTask, retry_delay_seconds(), enqueue(), configure_runtime()

### Community 76 - "SectionEdit"
Cohesion: 0.16
Nodes (6): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin, SectionEdit, Meta

### Community 77 - "views_account.py"
Cohesion: 0.06
Nodes (17): EmailOrUsernameBackend, LearnerProfile, InvalidPhone, looks_like_phone(), normalize_phone(), PhoneField, NormalizePhoneTests, ProfileTests (+9 more)

### Community 78 - "decks.py"
Cohesion: 0.13
Nodes (11): all_decks(), _carded_slugs(), _cards(), deck_cards(), deck_slugs(), next_topic(), _sections_by_slug(), card_sections() (+3 more)

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
Cohesion: 0.05
Nodes (20): Command, _DryRun, ReferenceImportCommand, open_for_import(), Command, Command, Article, Meta (+12 more)

### Community 84 - "ZarinpalGateway"
Cohesion: 0.14
Nodes (4): FakeGateway, Verification, ZarinpalGateway, ZarinpalTests

### Community 85 - "dqc_extras.py"
Cohesion: 0.22
Nodes (9): action_label(), action_tone(), ago(), dict_get(), fa_digits(), percent(), status_label(), status_tone() (+1 more)

### Community 86 - "clean_profile_boilerplate.py"
Cohesion: 0.10
Nodes (15): clean_text(), Command, cleaned(), is_hypersensitivity_boilerplate(), is_hypersensitivity_boilerplate_en(), is_negative_indication_en(), is_negative_indication_fa(), is_null_placeholder() (+7 more)

### Community 87 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.10
Nodes (15): validate_production_broker(), validate_production_cache(), validate_production_secret_key(), CorsPreflightTests, ProductionSecretKeyTests, PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa, 🎉 بازنویسی کامل شد, فاز ۰ — تثبیت بک‌اند ✅ (+7 more)

### Community 88 - "re"
Cohesion: 0.13
Nodes (14): _fa_keys_standardized(), _stage_names_without_prefix(), _title_formula_as_result(), _with_unit(), _adjective(), _chain(), _key(), _latin_quantity() (+6 more)

### Community 89 - "django_conf"
Cohesion: 0.04
Nodes (42): BillingConfig, current(), enabled_gateways(), gateway_spec(), _gateways(), GatewaySpec, _load(), row() (+34 more)

### Community 90 - "Calculator"
Cohesion: 0.09
Nodes (19): Calculator, Meta, CalculatorCategory, Meta, CalculatorTag, Meta, CalculatorCategorySerializer, Meta (+11 more)

### Community 91 - "make"
Cohesion: 0.15
Nodes (3): ActivityTests, make(), SignInTests

### Community 92 - "Ingredient"
Cohesion: 0.03
Nodes (34): AtcCategoryAdmin, AtcCodeAdmin, IngredientAdmin, IngredientProfileSectionAdmin, IngredientProfileSectionInline, Command, Command, AtcCategory (+26 more)

### Community 93 - "Pharmexa — custom icon prompts"
Cohesion: 0.15
Nodes (12): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups, 9. App identity (optional) (+4 more)

### Community 94 - "sources.ts"
Cohesion: 0.15
Nodes (16): LexicompDrug, LexicompInteraction, UptodateImage, cache, checkInteractions(), LexIndex, searchDrugs(), SEVERITY_RANK (+8 more)

### Community 96 - "6. Lesson study topics (52)"
Cohesion: 0.15
Nodes (13): 6. Lesson study topics (52), Cardiovascular & blood, Dermatology, Endocrine & metabolism, Gastrointestinal, Infectious disease, Miscellaneous, Musculoskeletal (+5 more)

### Community 97 - "files.ts"
Cohesion: 0.29
Nodes (11): buildDir(), closeHandles(), ensureBuildDir(), handles, partFile(), partPath(), partSize(), readRange() (+3 more)

### Community 98 - "previews.tsx"
Cohesion: 0.37
Nodes (21): Bands(), Check(), CheckDot(), Choice(), Drawers(), Flip(), Interaction(), kf() (+13 more)

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

### Community 101 - "uptodateLocal.ts"
Cohesion: 0.14
Nodes (23): bitCount(), buildTitleIndex(), cache, compareKeys(), getImage(), getTopic(), IMAGE_TYPES, isWord() (+15 more)

### Community 102 - "downloader.web.ts"
Cohesion: 0.20
Nodes (9): downloader, DownloadEvents, newWorker(), PartJob, PartRef, Run, runFor(), runs (+1 more)

### Community 103 - "۲. راه‌اندازی محیط توسعه"
Cohesion: 0.17
Nodes (12): اندروید و iOS, اپ (Expo), بک‌اند, تست بستهٔ آفلاین بدون باکت, تست و بررسی, روال کار با مخزن, ساخت دیتابیس و اجرای سرور, نسخهٔ وب (+4 more)

### Community 104 - "offline/reader.ts"
Cohesion: 0.15
Nodes (12): Coding Style & Naming Conventions, OfflineDataset, OfflineLicense, OfflineManifest, keyring, openRecord(), openRecordBase64(), PackageKey (+4 more)

### Community 105 - "nav.py"
Cohesion: 0.12
Nodes (11): shell(), build(), _matches(), Module, _my_changes(), _new_messages(), Page, _pending_comments() (+3 more)

### Community 106 - "settings/base.py"
Cohesion: 0.11
Nodes (3): build.sh script, DJANGO_SETTINGS_MODULE, release.sh script

### Community 107 - "Repository Guidelines"
Cohesion: 0.29
Nodes (6): Build, Test, and Development Commands, Commit & Pull Request Guidelines, Project Structure & Module Organization, Repository Guidelines, Security & Configuration Tips, Testing Guidelines

### Community 108 - "authentication.py"
Cohesion: 0.12
Nodes (7): SessionTokenAuthentication, SessionTokenAuthenticationScheme, احراز هویت و حساب, ثبت‌نام و ورود, رمز عبور, نشست و توکن, نقش‌ها و رویدادهای امنیتی

### Community 109 - "CalculatorDetail"
Cohesion: 0.27
Nodes (10): CalculatorDetail, CalculatorQuestion, ResultProps, LIST_FROM, FieldProps, FlowProps, CalculatorAnswers, ComputedResult (+2 more)

### Community 110 - "website_extras.py"
Cohesion: 0.13
Nodes (10): atc_groups(), feature_icon(), nav_on(), on_site(), oneline(), person(), post_link(), split_highlight() (+2 more)

### Community 112 - "issue_user_session"
Cohesion: 0.16
Nodes (6): SessionRefreshToken, Meta, hash_session_token(), issue_user_session(), PhaseTwoAuthorizationTests, PhaseTwoSessionSecurityTests

### Community 113 - "۵. قرارداد API (نسخهٔ ۱)"
Cohesion: 0.10
Nodes (21): Lexicomp — `/lexicomp/` (ویژگی `lexicomp`), Medscape — `/medscape/` (ویژگی `medscape`), UpToDate — `/uptodate/` (ویژگی `uptodate`), آزمون — `/quiz/` (ویژگی `quiz`؛ پرچم `QUIZ_API_ENABLED`), تغییر دادن API, جعبهٔ قدیمی, جعبهٔ لایتنر, داروها — `/drugs/` و `/atc/` (+13 more)

### Community 114 - "import_calculators.py"
Cohesion: 0.14
Nodes (12): standardize_fa_units(), Command, _error_checks_for(), _formula_strings_fa(), _import_categories(), _import_tags(), _questions_for(), _references_for() (+4 more)

### Community 115 - "۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی"
Cohesion: 0.12
Nodes (17): اطلاعات غیرمحرمانه‌ای که باید جایی ثبت باشد, بازیابی, بکاپ و بازیابی, حساب‌های سرویس, رازها و چیزهایی که باید امن نگه داشته شوند, رازهای فنی, شاخص‌هایی که مرتب دیده شوند, عیب‌یابی (+9 more)

### Community 116 - "tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, paths, strict, extends, include, expo/tsconfig.base

### Community 117 - "Command"
Cohesion: 0.09
Nodes (7): Command, Command, ensure_title_search_index(), _has_title_search_index(), mysql_config(), MysqlTitleIndexTests, MysqlTitleSearchTests

### Community 119 - "UserSerializer"
Cohesion: 0.10
Nodes (10): LearnerProfileSerializer, Meta, OnboardingSerializer, UserSerializer, Meta, active_role_keys(), MeView, OnboardingView (+2 more)

### Community 120 - "sw.js"
Cohesion: 0.38
Nodes (4): inScope(), referencedFiles(), SCOPE, storeShell()

### Community 122 - "TitleSearchTests"
Cohesion: 0.13
Nodes (5): snippet_source(), _typo_distance(), HeaderTextTests, TitleSearchTests, TypoDistanceTests

### Community 123 - "۱۲. سایت `pharmenta.ir` و پنل محتوا"
Cohesion: 0.14
Nodes (14): not_found(), آمار بازدید, حساب و خرید روی سایت, دارونامهٔ عمومی (`/drugs/`), رسانه, سئو, ساختار کد, صفحه‌های عمومی (+6 more)

### Community 125 - "_SectionCard"
Cohesion: 0.19
Nodes (3): _card_back_fields(), DeckCardSerializer, _SectionCard

### Community 126 - "otp.py"
Cohesion: 0.10
Nodes (22): OneTimeCode, Meta, account_for_signup(), _hash(), _minutes(), _new_code(), OtpError, request_code() (+14 more)

### Community 127 - "latest_manifest"
Cohesion: 0.16
Nodes (4): clear_cache(), BucketManifestTests, BuildTests, DownloadHostTests

### Community 128 - "PaymentGateway"
Cohesion: 0.17
Nodes (10): gateway(), gateway_edit(), _gateway_facts(), _gateway_state(), _masked(), _site_callback(), _site_url(), _tristate() (+2 more)

### Community 132 - "CalculatorApiTests"
Cohesion: 0.11
Nodes (6): _build_sqlite(), CalculatorApiTests, FaUnitsTests, ImportCalculatorsTests, _one_calculator(), QuestionUnitTests

### Community 152 - "Command"
Cohesion: 0.21
Nodes (4): Command, _int(), _json_list(), _name_fa()

### Community 156 - "data_quality_center/tests.py"
Cohesion: 0.24
Nodes (6): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), word_diff(), CheckTests

### Community 182 - "۳. بک‌اند (Django)"
Cohesion: 0.12
Nodes (12): RequestIdMiddleware, SiteHostMiddleware, UpToDate و Lexicomp, افزودن یک قابلیت فروشی تازه, زنجیرهٔ middleware, صورتحساب و دسترسی (`apps.billing`), قواعد مشترک API, قواعد کدنویسی بک‌اند (+4 more)

### Community 185 - "OfflinePackageCard.tsx"
Cohesion: 0.15
Nodes (22): OfflinePackageInfo, OfflineDownloadButton(), OfflineSheet(), ERROR_TEXT, LOGO, NAME, OfflinePackageCard(), PHASE_TEXT (+14 more)

### Community 196 - "drugs/views.py"
Cohesion: 0.23
Nodes (3): AtcCodeListView, IngredientDetailView, IngredientListView

### Community 198 - "accounts/views.py"
Cohesion: 0.12
Nodes (26): SecurityAuditEvent, Meta, UserSession, Meta, CanManagePlatformRoles, CanViewSecurityAudit, HasPlatformPermission, HasRecentStepUp (+18 more)

### Community 202 - "LessonDetailScreen.tsx"
Cohesion: 0.27
Nodes (13): LessonSection, Badge(), joinOpenParens(), LessonBlock, LessonBody(), LessonDetailScreen(), LessonLine, parenDepth() (+5 more)

### Community 203 - "downloader.ts"
Cohesion: 0.20
Nodes (6): downloader, DownloadEvents, PartJob, PartRef, tasks, @kesha-antonov/react-native-background-downloader

### Community 204 - "۸. دیپلوی"
Cohesion: 0.12
Nodes (16): CI, امنیت و هشدار نصب, اپ اندروید و iOS, برگرداندن یک دیپلوی خراب, بک‌اند, جریان دیپلوی, حجم APK, راه‌اندازی از صفر (یک بار) (+8 more)

### Community 208 - "PlanSerializer"
Cohesion: 0.29
Nodes (5): PlanFeatureItemSerializer, PlanPriceSerializer, Meta, PlanSerializer, Meta

### Community 210 - "website/models.py"
Cohesion: 0.05
Nodes (32): HomeTests, MediaOnTheAdminHostTests, OldAddressTests, ShellTests, Command, Announcement, Meta, Category (+24 more)

### Community 211 - "۱. معرفی و معماری"
Cohesion: 0.25
Nodes (8): دامنه‌ها و سرویس‌ها, ذخیره‌گاه‌های داده, ساختار مخزن, سرویس‌های بیرونی, فناوری‌ها, محصول, معماری, ۱. معرفی و معماری

### Community 212 - "۱۰. مرجع سریع دستورها"
Cohesion: 0.25
Nodes (8): اپ موبایل (EAS), تست و بررسی, توسعهٔ محلی, دستورهای مدیریتی Django (همه), دیپلوی و گیت, عیب‌یابی, پایپلاین study_content (بیرون از مخزن), ۱۰. مرجع سریع دستورها

### Community 213 - "۱۱. مدیریت"
Cohesion: 0.14
Nodes (14): ادمین Django (`/admin/`), خانه (`/manage/`), درگاه پرداخت و کلیدهای فروش, دسترسی مهمان, فروش و کاربران (`/manage/sales/`), مرکز کیفیت داده (`/manage/data/`), نشانی‌های قدیمی, ورود و دسترسی (+6 more)

### Community 214 - "logging.py"
Cohesion: 0.33
Nodes (3): get_request_id(), JsonFormatter, RequestContextFilter

### Community 215 - "exceptions.py"
Cohesion: 0.53
Nodes (4): _first_message(), _message_from_data(), _normalize_code(), platform_exception_handler()

### Community 217 - "website/services.py"
Cohesion: 0.05
Nodes (20): ContentBlock, Meta, Redirect, Meta, Tag, Meta, VisitorDay, Meta (+12 more)

### Community 218 - "DateResult.tsx"
Cohesion: 0.48
Nodes (6): hasPersian(), Rows(), DateResult(), useDateFormat(), parseAge(), parseDateText()

### Community 226 - "مستندات فارمنتا"
Cohesion: 0.50
Nodes (4): سندهای دیگر مخزن, فهرست, قرارداد نگهداری این مستندات, مستندات فارمنتا

### Community 227 - "devDependencies"
Cohesion: 0.67
Nodes (3): devDependencies, @types/react, typescript

### Community 230 - "فارمنتا (Pharmenta)"
Cohesion: 0.67
Nodes (3): شروع سریع, فارمنتا (Pharmenta), مستندات

## Knowledge Gaps
- **9 isolated node(s):** `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-build-properties`, `expo-splash-screen`, `react-dom` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1692 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **91 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `useTheme` to `react`, `accounts/views.py`, `package.json`, `useTheme`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `AppText()` (e.g. with `زبان، جهت و تم` and `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅`) actually correct?**
  _`AppText()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-build-properties` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.03472931562819203 - nodes in this community are weakly interconnected._
- **Why does `UserSession` connect `accounts/views.py` to `WebsiteAuthTests`, `console/views.py`, `accounts/serializers.py`, `useTheme`, `authentication.py`, `views_account.py`, `PurchaseFlowTests`, `tests_console.py`, `issue_user_session`, `accounts/views.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`, `manage/views.py`, `django_conf`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.02143928035982009 - nodes in this community are weakly interconnected._
- **Why does `اپ‌ها (`backend/apps/`)` connect `tests_console.py` to `PaymentGateway`, `console/views.py`, `Post`, `views_public.py`, `flashcards/views.py`, `accounts/views.py`, `quiz/views.py`, `progress/tests.py`, `lessons/views.py`, `SectionEditRequest`, `planning.py`, `۳. بک‌اند (Django)`, `accounts/serializers.py`, `accounts/views.py`, `SectionEdit`, `Article`, `website/models.py`, `Calculator`, `Ingredient`, `issue_user_session`, `otp.py`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._