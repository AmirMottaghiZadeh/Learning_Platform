# Graph Report - Learning Platform  (2026-10-26)

## Corpus Check
- 532 files · ~429,746 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 35 file(s) not represented in the graph (top: (none) 11, .ttf 7, .css 5)

## Summary
- 5269 nodes · 15089 edges · 217 communities (129 shown, 88 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1360 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `64407d0e`
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
- App.tsx
- flashcards/views.py
- useTheme
- guest.py
- LeitnerCard
- SepGateway
- tests_console.py
- data_quality_center/views.py
- Page
- ImportOpenfdaTests
- useLang
- PlatformAPIError
- views_account.py
- drugs/reference_db.py
- calculatorEngine.ts
- accounts/checks.py
- quiz/views.py
- MedscapeArticleScreen.tsx
- lexicomp/services.py
- .request_code
- MaintenancePlanAndApiTests
- core/views.py
- lessons/views.py
- ApiTests
- store.ts
- fix_results
- SectionEditRequest
- panel/forms.py
- html.ts
- progress/selectors.py
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
- TopicDeckTests
- LessonTaxonomyTests
- expo
- planning.py
- import_medscape_articles.py
- ResultCard
- AppRelease
- manage/views.py
- برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای
- offline/tests.py
- ۶. پیکربندی و متغیرهای محیطی
- offline/views.py
- files.web.ts
- billing_extras.py
- throttling.py
- package.json
- WebsiteAuthTests
- PurchaseApiTests
- ۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین
- ReferenceDbTests
- dependencies
- medscape/tests.py
- crypto.web.ts
- panel.js
- views_drugs.py
- HealthCheckTests
- logging
- SectionEdit
- views_account.py
- queryClient.ts
- ReviewTests
- common.tsx
- calculatorModel.ts
- Article
- UptodateTests
- drugs/admin.py
- dqc_extras.py
- clean_profile_boilerplate.py
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- re
- billing/views.py
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
- rest_framework_permissions
- uptodateLocal.ts
- downloader.web.ts
- ۲. راه‌اندازی محیط توسعه
- offline/reader.ts
- nav.py
- settings/base.py
- Repository Guidelines
- SessionTokenAuthenticationScheme
- CalculatorDetail
- website_extras.py
- StandardizeUnitsTests
- DiscountForm
- ۵. قرارداد API (نسخهٔ ۱)
- scripts
- ۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی
- tsconfig.json
- Command
- django_apps
- UserSerializer
- sw.js
- Command
- maintenance_urls.py
- revert
- pagination.py
- _SectionCard
- otp.py
- django
- config.py
- docker-start.sh
- billing/apps.py
- ImportCalculatorsTests
- .claude/CLAUDE.md
- StudyTopicsCoverageTests
- app.config.js
- .mcp.json
- enqueue
- data_quality_center/tests.py
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
- GatewayPageTests
- accounts/services.py
- LessonDetailScreen.tsx
- ۸. دیپلوی
- OnboardingTests
- Section
- PlanBuilderTests
- website/models.py
- ۱. معرفی و معماری
- ۱۰. مرجع سریع دستورها
- ۱۱. مدیریت
- NavigationTests
- DateResult.tsx
- AccessTests
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
10. `Plan` - 56 edges

## Surprising Connections (you probably didn't know these)
- `فاز ۰.۵ — حذف زیرساخت رهاشده ✅` --references--> `UserSession`  [INFERRED]
  PHASES.md → backend/apps/accounts/models.py
- `ورود و دسترسی` --references--> `SecurityAuditEvent`  [INFERRED]
  docs/11-admin-consoles.md → backend/apps/accounts/models.py
- `۳c — `apps.flashcards` + `apps.quiz` (ساخته‌شده، پشت فلگ خاموش) ✅` --references--> `seed()`  [INFERRED]
  PHASES.md → backend/apps/billing/migrations/0002_seed_features_and_free_plan.py
- `۳d — بازنویسی `data_quality_center` ✅` --references--> `SectionEdit`  [INFERRED]
  PHASES.md → backend/apps/data_quality_center/models.py
- `دستورهای خودکار هنگام شروع` --references--> `AtcCategory`  [INFERRED]
  docs/07-data.md → backend/apps/drugs/models.py

## Import Cycles
- None detected.

## Communities (217 total, 88 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.03
Nodes (108): حساب و احراز هویت — `/auth/`, API_BASE_URL, apiClient, ApiErrorBody, AuthController, configureAuth(), RetryableConfig, unwrapList() (+100 more)

### Community 1 - "django_db"
Cohesion: 0.02
Nodes (57): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+49 more)

### Community 2 - "test_panel.py"
Cohesion: 0.05
Nodes (16): post_link(), preview_token(), AdminTests, AuthorTests, AuthTests, CommercePagesTests, InboxTests, make_user() (+8 more)

### Community 3 - "console/views.py"
Cohesion: 0.05
Nodes (72): FeatureEditForm, Meta, FeatureForm, Meta, latin_digits(), parse_amount(), PlanBasicsForm, Meta (+64 more)

### Community 4 - "react"
Cohesion: 0.08
Nodes (67): calculatorsApi, meApi, medscapeApi, MedscapeKind, ALPHABET, AlphabeticalArticleList(), buildOffsets(), groupAlphabetically() (+59 more)

### Community 5 - "Post"
Cohesion: 0.07
Nodes (51): ActivityLog, Meta, Post, Meta, PostRevision, Meta, orders(), plans() (+43 more)

### Community 6 - "useTheme"
Cohesion: 0.10
Nodes (79): قابلیت‌ها, آنبوردینگ و برنامهٔ مطالعه, ارتباط با API و کش, افزودن صفحهٔ تازه, تور راهنما (`src/tour/`), دانلود آفلاین (`src/offline/`), ساختار `frontend/src/`, فلش‌کارت و جعبهٔ لایتنر (+71 more)

### Community 7 - "views_public.py"
Cohesion: 0.06
Nodes (45): site(), Announcement, Meta, DailyStat, Meta, SiteSettings, Meta, add_toc() (+37 more)

### Community 8 - ".reverse"
Cohesion: 0.09
Nodes (5): UsersPageTests, AccessTests, render_links(), link(), search()

### Community 9 - "App.tsx"
Cohesion: 0.11
Nodes (25): زبان، جهت و تم, شروع اپ, App(), Gate(), ThemedStatusBar(), guestApi, queryClient, queryPersister (+17 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.04
Nodes (51): _applies(), _require_content(), require_feature(), require_topic_content(), all_decks(), _carded_slugs(), _cards(), deck_cards() (+43 more)

### Community 11 - "useTheme"
Cohesion: 0.08
Nodes (74): ApiError, authApi, AuthLayout(), CardsFlow(), ChecklistFlow(), flowLayout, Choices(), FieldVariant (+66 more)

### Community 12 - "guest.py"
Cohesion: 0.11
Nodes (16): create_guest(), end_guest_sessions(), guests(), GuestSessionView, GuestStatusView, _first_message(), _message_from_data(), _normalize_code() (+8 more)

### Community 13 - "LeitnerCard"
Cohesion: 0.10
Nodes (10): add_miss(), add_quiz_miss(), card_sections(), _exam_cap_days(), outcome(), review(), _start_of_tomorrow(), _drug() (+2 more)

### Community 14 - "SepGateway"
Cohesion: 0.07
Nodes (9): FakeGateway, _post_json(), SepGateway, Verification, ZarinpalGateway, _fake_urlopen(), GatewayChoiceTests, SepTests (+1 more)

### Community 15 - "tests_console.py"
Cohesion: 0.06
Nodes (25): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, AdminAction, Meta (+17 more)

### Community 16 - "data_quality_center/views.py"
Cohesion: 0.14
Nodes (19): warning_count(), section_state(), _diffs(), discard(), history(), logout_view(), my_requests(), _neighbours() (+11 more)

### Community 17 - "Page"
Cohesion: 0.13
Nodes (4): clean_html(), plain_text(), safe_url(), SanitizeTests

### Community 18 - "ImportOpenfdaTests"
Cohesion: 0.08
Nodes (7): AtcSupplementTests, CleanBoilerplateInPipelineTests, DrugApiTests, ImportOpenfdaTests, LoadAtcReferenceTests, _make_source_db(), StandardizePipelineUnitsTests

### Community 19 - "useLang"
Cohesion: 0.10
Nodes (50): DateInput(), DaysInput(), Field(), QuestionTitle(), CategoryPicker(), Chip(), ChipRow(), DateField() (+42 more)

### Community 20 - "PlatformAPIError"
Cohesion: 0.06
Nodes (47): AuthTokenResponseSerializer, LoginSerializer, OtpRequestResponseSerializer, OtpRequestSerializer, OtpVerifySerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, PasswordResetResponseSerializer (+39 more)

### Community 21 - "views_account.py"
Cohesion: 0.11
Nodes (18): OneTimeCode, Meta, AccountForm, CodeForm, LoginForm, PasswordForm, PhoneForm, account() (+10 more)

### Community 22 - "drugs/reference_db.py"
Cohesion: 0.07
Nodes (9): Command, Command, _DryRun, _checked(), _digest(), load(), open_parts(), part_name() (+1 more)

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.08
Nodes (51): LiveScore(), useLiveScore(), buildHeuristicSeeds(), cartesian(), checkErrors(), classifyResultTone(), computeCalculator(), ComputeOptions (+43 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.05
Nodes (46): slugs_for_topic(), record_quiz_answers(), record_study(), _touch_streak(), BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, ingredient_ids_for_selection() (+38 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.04
Nodes (96): MedscapeBlock, MedscapeSection, TopInset, useBleedTop(), countMatches(), FindState, highlight(), ListMarker() (+88 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.09
Nodes (18): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, _categories_for_generics(), check_interactions(), close_all(), _conn(), _dir() (+10 more)

### Community 28 - ".request_code"
Cohesion: 0.17
Nodes (4): CodeRuleTests, PhoneAuthTestCase, ResetTests, SignUpTests

### Community 29 - "MaintenancePlanAndApiTests"
Cohesion: 0.09
Nodes (9): bump_mistake(), MaintenancePlanAndApiTests, MeApiTests, ProgressServiceTests, فاز ۳ — اپ‌های بک‌اند (زیرفازی), ۳a — جدول مرجع ATC + `apps.lessons` ✅, ۳b — `apps.progress` → `/me/*` ✅, ۳c — `apps.flashcards` + `apps.quiz` (ساخته‌شده، پشت فلگ خاموش) ✅ (+1 more)

### Community 30 - "core/views.py"
Cohesion: 0.14
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 31 - "lessons/views.py"
Cohesion: 0.07
Nodes (26): require_atc_content(), LessonDrugSerializer, fold(), get_chapter(), get_lesson_drug(), _rank(), search_drugs(), _subgroup() (+18 more)

### Community 33 - "store.ts"
Cohesion: 0.14
Nodes (34): offlineApi, removeOtherBuilds(), requestPersistence(), closeReaders(), bootOffline(), cancel(), currentUserId(), DatasetState (+26 more)

### Community 34 - "fix_results"
Cohesion: 0.07
Nodes (16): fix_questions(), fix_results(), fix_strings_fa(), renumber_from_one(), _with_choices(), _with_unit(), apply_fixes(), Migration (+8 more)

### Community 35 - "SectionEditRequest"
Cohesion: 0.12
Nodes (20): SectionEditRequest, Meta, approve(), _clean(), _client_ip(), _close(), discard(), editable_request() (+12 more)

### Community 36 - "panel/forms.py"
Cohesion: 0.03
Nodes (50): Command, Command, Category, Meta, ContentBlock, Meta, DownloadLink, Meta (+42 more)

### Community 37 - "html.ts"
Cohesion: 0.24
Nodes (9): AboutBody(), dirStyle(), AboutBlock, COMPARED_NUMBER, decodeEntities(), htmlToParagraphs(), NAMED_ENTITIES, parseAboutHtml() (+1 more)

### Community 38 - "progress/selectors.py"
Cohesion: 0.13
Nodes (16): lesson_groups(), topic_chapters(), DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin, DailyStudy, Meta (+8 more)

### Community 39 - "test_public.py"
Cohesion: 0.15
Nodes (3): DownloadAndMachineTests, make_post(), PostVisibilityTests

### Community 40 - "search_topics"
Cohesion: 0.07
Nodes (31): article_from_row(), build_title_index(), _dir(), get_image(), get_topic(), is_available(), _is_word(), _letters() (+23 more)

### Community 41 - "DrugPageTests"
Cohesion: 0.12
Nodes (3): DrugPageTests, SiteIdentityTests, structured()

### Community 42 - "QuizApiTests"
Cohesion: 0.09
Nodes (3): QuizAccessTests, QuizApiTests, QuizLockedTests

### Community 43 - "billing/services.py"
Cohesion: 0.07
Nodes (22): MyAccessSerializer, Access, active_entitlements(), BillingError, check_feature(), content_lock(), effective_features(), take() (+14 more)

### Community 44 - "progress/views.py"
Cohesion: 0.08
Nodes (27): Mistake, Meta, DashboardSerializer, FocusRowSerializer, FocusSessionSerializer, MistakeSerializer, Meta, NextChapterSerializer (+19 more)

### Community 45 - "release.mjs"
Cohesion: 0.09
Nodes (15): appJson, at, dryRun, file(), frontend, [kind, ...flags], lock, [major, minor, patch] (+7 more)

### Community 46 - "PurchaseFlowTests"
Cohesion: 0.07
Nodes (6): clear_cache(), BillingSettings, Meta, GuestAccessTests, GuestConsoleTests, PurchaseFlowTests

### Community 47 - "offline/tests.py"
Cohesion: 0.05
Nodes (25): build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections(), _varints(), Command (+17 more)

### Community 48 - "drugs/serializers.py"
Cohesion: 0.10
Nodes (14): AtcCodeSerializer, Meta, IngredientDetailSerializer, Meta, IngredientListSerializer, Meta, LessonDrugSectionSerializer, Meta (+6 more)

### Community 50 - "LessonTaxonomyTests"
Cohesion: 0.05
Nodes (11): Command, AtcCategory, Meta, ChapterProgress, Meta, ReadDrug, Meta, DrugSearchTests (+3 more)

### Community 51 - "expo"
Cohesion: 0.06
Nodes (32): backgroundColor, foregroundImage, adaptiveIcon, allowBackup, blockedPermissions, package, projectId, typedRoutes (+24 more)

### Community 52 - "planning.py"
Cohesion: 0.05
Nodes (42): due_card_count(), mark_drug_read(), topic_progress(), StudyPlanItem, Meta, _chapter(), complete_item(), ensure_today_items() (+34 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.16
Nodes (7): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label()

### Community 54 - "ResultCard"
Cohesion: 0.34
Nodes (22): Explain(), Hero(), Interpretation(), ResultCard(), ResultProps, showTierBar(), toneOf(), useShown() (+14 more)

### Community 55 - "AppRelease"
Cohesion: 0.09
Nodes (11): LatestReleaseSerializer, note_lines(), ReleaseCheckSerializer, ReleaseCheckView, ReleaseQuerySerializer, AppRelease, Meta, version_code() (+3 more)

### Community 56 - "manage/views.py"
Cohesion: 0.07
Nodes (37): anyone(), can_enter(), has_site_role(), is_operator(), is_super(), site(), site_admin(), activity() (+29 more)

### Community 57 - "برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای"
Cohesion: 0.12
Nodes (17): برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی, روش تبدیل پیشنهادها به کلمات کلیدی معتبر, ساخت Analytics از ابتدا, ساخت Search Console از ابتدا, منابع رسمی بررسی‌شده, چک‌لیست انتشار هر صفحه, ۱. نتیجهٔ بررسی واقعی سایت (+9 more)

### Community 58 - "offline/tests.py"
Cohesion: 0.07
Nodes (11): Command, writing(), _make_snapshot(), has_paid_plan_with(), is_entitled(), is_guest(), issue_license(), license_days() (+3 more)

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.10
Nodes (20): local(), open(), paint(), HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت (+12 more)

### Community 60 - "offline/views.py"
Cohesion: 0.06
Nodes (32): Command, cors_rule(), _request(), build_matches_dataset(), LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer (+24 more)

### Community 61 - "files.web.ts"
Cohesion: 0.19
Nodes (9): file(), forget(), partSize(), readRange(), removeBuild(), removeOtherBuilds(), removePart(), snapshots (+1 more)

### Community 62 - "billing_extras.py"
Cohesion: 0.29
Nodes (8): ago(), fa(), get_item(), guest_access_on(), initial(), jdate(), num(), toman()

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "package.json"
Cohesion: 0.12
Nodes (16): main, name, private, version, expo, expo-build-properties, expo-file-system, expo-font (+8 more)

### Community 66 - "PurchaseApiTests"
Cohesion: 0.10
Nodes (12): _div(), format_date(), _jal_cal(), _mod(), month_start(), to_gregorian(), to_jalali(), EnforcementTests (+4 more)

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (26): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+18 more)

### Community 69 - "dependencies"
Cohesion: 0.07
Nodes (28): dependencies, axios, expo, expo-build-properties, expo-constants, expo-crypto, expo-file-system, expo-font (+20 more)

### Community 70 - "medscape/tests.py"
Cohesion: 0.12
Nodes (6): _disease_record(), _guideline_record(), ImportMedscapeArticlesTests, MedscapeApiTests, _write_diseases_tree(), _write_guidelines()

### Community 71 - "crypto.web.ts"
Cohesion: 0.23
Nodes (9): اجرای کامل با Docker, db(), idb(), keyring, openRecord(), openRecordBase64(), PackageKey, rsaPair() (+1 more)

### Community 72 - "panel.js"
Cohesion: 0.19
Nodes (11): buildEditor(), align(), block(), exec(), sync(), toggleSource(), wrapBlock(), loadPicker() (+3 more)

### Community 73 - "views_drugs.py"
Cohesion: 0.06
Nodes (26): Migration, Migration, article(), breadcrumbs(), editorial_team(), home_graph(), _id(), organization() (+18 more)

### Community 74 - "HealthCheckTests"
Cohesion: 0.15
Nodes (3): HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests

### Community 75 - "logging"
Cohesion: 0.06
Nodes (10): password_reset_url_for_user(), send_password_reset_email(), send_password_reset_email_task(), PlatformTask, retry_delay_seconds(), get_request_id(), JsonFormatter, RequestContextFilter (+2 more)

### Community 76 - "SectionEdit"
Cohesion: 0.12
Nodes (9): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin, ReviewEvent, Meta, SectionEdit, Meta (+1 more)

### Community 77 - "views_account.py"
Cohesion: 0.10
Nodes (9): EmailOrUsernameBackend, LearnerProfile, InvalidPhone, looks_like_phone(), normalize_phone(), PhoneField, NormalizePhoneTests, ProfileTests (+1 more)

### Community 78 - "queryClient.ts"
Cohesion: 0.18
Nodes (11): CACHE_BUSTER, CACHE_MAX_AGE, DehydratedQuery, isEmptyList(), MOST_RECENT, PERSISTED_KEYS, REFERENCE_KEYS, storagePersister (+3 more)

### Community 79 - "ReviewTests"
Cohesion: 0.16
Nodes (3): ConsoleTestCase, DraftAndSubmitTests, ReviewTests

### Community 80 - "common.tsx"
Cohesion: 0.16
Nodes (25): bandFor(), Chip(), Collapse(), Extra, Extras(), fmt(), LEVEL_TONES, plain() (+17 more)

### Community 81 - "calculatorModel.ts"
Cohesion: 0.14
Nodes (24): CalculatorResultDef, StagingResult(), ComputedResult, allWholeNumbers(), cache, classify(), classifyCalculator(), isNumeric() (+16 more)

### Community 82 - "Article"
Cohesion: 0.04
Nodes (34): Command, export(), load(), Command, _DryRun, ReferenceImportCommand, dumps(), expected_count() (+26 more)

### Community 84 - "drugs/admin.py"
Cohesion: 0.27
Nodes (5): AtcCategoryAdmin, AtcCodeAdmin, IngredientAdmin, IngredientProfileSectionAdmin, IngredientProfileSectionInline

### Community 85 - "dqc_extras.py"
Cohesion: 0.22
Nodes (9): action_label(), action_tone(), ago(), dict_get(), fa_digits(), percent(), status_label(), status_tone() (+1 more)

### Community 86 - "clean_profile_boilerplate.py"
Cohesion: 0.11
Nodes (14): clean_text(), Command, cleaned(), is_hypersensitivity_boilerplate(), is_hypersensitivity_boilerplate_en(), is_negative_indication_en(), is_negative_indication_fa(), is_null_placeholder() (+6 more)

### Community 87 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.10
Nodes (14): validate_production_broker(), validate_production_cache(), validate_production_secret_key(), CorsPreflightTests, ProductionSecretKeyTests, PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa, 🎉 بازنویسی کامل شد, فاز ۰.۵ — حذف زیرساخت رهاشده ✅ (+6 more)

### Community 88 - "re"
Cohesion: 0.05
Nodes (22): _fa_keys_standardized(), _stage_names_without_prefix(), standardize_fa_units(), _title_formula_as_result(), apply(), Migration, _adjective(), _chain() (+14 more)

### Community 89 - "billing/views.py"
Cohesion: 0.07
Nodes (39): current(), enabled_gateways(), GatewayError, get_gateway(), start_payment(), is_guest(), Order, Meta (+31 more)

### Community 90 - "Calculator"
Cohesion: 0.06
Nodes (27): Command, _error_checks_for(), _formula_strings_fa(), _import_categories(), _import_tags(), _questions_for(), _references_for(), _results_for() (+19 more)

### Community 91 - "make"
Cohesion: 0.13
Nodes (5): ActivityTests, make(), SearchTests, ShellTests, SignInTests

### Community 92 - "Ingredient"
Cohesion: 0.03
Nodes (35): Command, AtcCode, Meta, Ingredient, Meta, IngredientProfileSection, Meta, export() (+27 more)

### Community 93 - "Pharmexa — custom icon prompts"
Cohesion: 0.15
Nodes (12): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups, 9. App identity (optional) (+4 more)

### Community 94 - "sources.ts"
Cohesion: 0.15
Nodes (17): lexicompApi, uptodateApi, LexicompDrug, LexicompInteraction, cache, checkInteractions(), LexIndex, searchDrugs() (+9 more)

### Community 96 - "6. Lesson study topics (52)"
Cohesion: 0.15
Nodes (13): 6. Lesson study topics (52), Cardiovascular & blood, Dermatology, Endocrine & metabolism, Gastrointestinal, Infectious disease, Miscellaneous, Musculoskeletal (+5 more)

### Community 97 - "files.ts"
Cohesion: 0.14
Nodes (17): downloader, DownloadEvents, PartJob, PartRef, tasks, buildDir(), closeHandles(), ensureBuildDir() (+9 more)

### Community 98 - "previews.tsx"
Cohesion: 0.16
Nodes (34): Bands(), Check(), CheckDot(), Choice(), Drawers(), Flip(), Interaction(), kf() (+26 more)

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

### Community 100 - "rest_framework_permissions"
Cohesion: 0.33
Nodes (5): CanManagePlatformRoles, CanViewSecurityAudit, HasPlatformPermission, HasRecentStepUp, session_has_recent_step_up()

### Community 101 - "uptodateLocal.ts"
Cohesion: 0.12
Nodes (25): UptodateImage, Prepared, bitCount(), buildTitleIndex(), cache, compareKeys(), getImage(), getTopic() (+17 more)

### Community 102 - "downloader.web.ts"
Cohesion: 0.20
Nodes (9): downloader, DownloadEvents, newWorker(), PartJob, PartRef, Run, runFor(), runs (+1 more)

### Community 103 - "۲. راه‌اندازی محیط توسعه"
Cohesion: 0.17
Nodes (12): اندروید و iOS, اپ (Expo), بک‌اند, تست بستهٔ آفلاین بدون باکت, تست و بررسی, روال کار با مخزن, ساخت دیتابیس و اجرای سرور, نسخهٔ وب (+4 more)

### Community 104 - "offline/reader.ts"
Cohesion: 0.14
Nodes (14): Coding Style & Naming Conventions, OfflineDataset, OfflineLicense, OfflineManifest, keyring, openRecord(), openRecordBase64(), PackageKey (+6 more)

### Community 105 - "nav.py"
Cohesion: 0.07
Nodes (21): shell(), build(), _matches(), Module, _my_changes(), _new_messages(), Page, _pending_comments() (+13 more)

### Community 106 - "settings/base.py"
Cohesion: 0.17
Nodes (3): build.sh script, DJANGO_SETTINGS_MODULE, release.sh script

### Community 107 - "Repository Guidelines"
Cohesion: 0.29
Nodes (6): Build, Test, and Development Commands, Commit & Pull Request Guidelines, Project Structure & Module Organization, Repository Guidelines, Security & Configuration Tips, Testing Guidelines

### Community 109 - "CalculatorDetail"
Cohesion: 0.23
Nodes (14): CalculatorDetail, CalculatorQuestion, LIST_FROM, FieldProps, FlowProps, CalculatorAnswers, choiceWeights(), extremes() (+6 more)

### Community 110 - "website_extras.py"
Cohesion: 0.06
Nodes (26): SiteHostMiddleware, atc_groups(), feature_icon(), nav_on(), on_site(), oneline(), person(), post_link() (+18 more)

### Community 113 - "۵. قرارداد API (نسخهٔ ۱)"
Cohesion: 0.10
Nodes (21): Lexicomp — `/lexicomp/` (ویژگی `lexicomp`), Medscape — `/medscape/` (ویژگی `medscape`), UpToDate — `/uptodate/` (ویژگی `uptodate`), آزمون — `/quiz/` (ویژگی `quiz`؛ پرچم `QUIZ_API_ENABLED`), تغییر دادن API, جعبهٔ قدیمی, جعبهٔ لایتنر, داروها — `/drugs/` و `/atc/` (+13 more)

### Community 114 - "scripts"
Cohesion: 0.25
Nodes (8): scripts, android, build:web, ios, release, start, typecheck, web

### Community 115 - "۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی"
Cohesion: 0.12
Nodes (17): اطلاعات غیرمحرمانه‌ای که باید جایی ثبت باشد, بازیابی, بکاپ و بازیابی, حساب‌های سرویس, رازها و چیزهایی که باید امن نگه داشته شوند, رازهای فنی, شاخص‌هایی که مرتب دیده شوند, عیب‌یابی (+9 more)

### Community 116 - "tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, paths, strict, extends, include, expo/tsconfig.base

### Community 117 - "Command"
Cohesion: 0.10
Nodes (6): Command, Command, ensure_title_search_index(), _has_title_search_index(), MysqlTitleIndexTests, MysqlTitleSearchTests

### Community 119 - "UserSerializer"
Cohesion: 0.14
Nodes (6): LearnerProfileSerializer, Meta, OnboardingSerializer, UserSerializer, Meta, MeView

### Community 120 - "sw.js"
Cohesion: 0.38
Nodes (4): inScope(), referencedFiles(), SCOPE, storeShell()

### Community 123 - "revert"
Cohesion: 0.40
Nodes (6): wrapper(), wrapper(), revert(), superuser_required(), wrapper(), view()

### Community 125 - "_SectionCard"
Cohesion: 0.19
Nodes (3): _card_back_fields(), DeckCardSerializer, _SectionCard

### Community 126 - "otp.py"
Cohesion: 0.08
Nodes (18): account_for_signup(), _hash(), _minutes(), _new_code(), OtpError, request_code(), user_for_phone(), verify_code() (+10 more)

### Community 128 - "config.py"
Cohesion: 0.11
Nodes (11): BillingConfig, gateway_spec(), _gateways(), GatewaySpec, _load(), row(), _settings_changed(), delete_guests() (+3 more)

### Community 132 - "ImportCalculatorsTests"
Cohesion: 0.32
Nodes (3): _build_sqlite(), ImportCalculatorsTests, _one_calculator()

### Community 156 - "data_quality_center/tests.py"
Cohesion: 0.22
Nodes (6): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), word_diff(), CheckTests

### Community 185 - "OfflinePackageCard.tsx"
Cohesion: 0.18
Nodes (17): OfflinePackageInfo, ERROR_TEXT, LOGO, NAME, OfflinePackageCard(), PHASE_TEXT, InstalledPackage, licenseExpiresAt() (+9 more)

### Community 198 - "accounts/services.py"
Cohesion: 0.06
Nodes (34): SessionTokenAuthentication, Role, Meta, RoleAssignment, Meta, SecurityAuditEvent, Meta, SessionRefreshToken (+26 more)

### Community 202 - "LessonDetailScreen.tsx"
Cohesion: 0.26
Nodes (12): lessonsApi, LessonSection, Badge(), joinOpenParens(), LessonBlock, LessonLine, parenDepth(), parseLessonText() (+4 more)

### Community 204 - "۸. دیپلوی"
Cohesion: 0.12
Nodes (16): CI, امنیت و هشدار نصب, اپ اندروید و iOS, برگرداندن یک دیپلوی خراب, بک‌اند, جریان دیپلوی, حجم APK, راه‌اندازی از صفر (یک بار) (+8 more)

### Community 208 - "PlanBuilderTests"
Cohesion: 0.16
Nodes (4): PlanFeatureItemSerializer, PlanSerializer, Meta, PlanBuilderTests

### Community 210 - "website/models.py"
Cohesion: 0.04
Nodes (22): HomeTests, MediaOnTheAdminHostTests, OldAddressTests, Comment, Meta, Media, Meta, PostQuerySet (+14 more)

### Community 211 - "۱. معرفی و معماری"
Cohesion: 0.25
Nodes (8): دامنه‌ها و سرویس‌ها, ذخیره‌گاه‌های داده, ساختار مخزن, سرویس‌های بیرونی, فناوری‌ها, محصول, معماری, ۱. معرفی و معماری

### Community 212 - "۱۰. مرجع سریع دستورها"
Cohesion: 0.25
Nodes (8): اپ موبایل (EAS), تست و بررسی, توسعهٔ محلی, دستورهای مدیریتی Django (همه), دیپلوی و گیت, عیب‌یابی, پایپلاین study_content (بیرون از مخزن), ۱۰. مرجع سریع دستورها

### Community 213 - "۱۱. مدیریت"
Cohesion: 0.14
Nodes (14): ادمین Django (`/admin/`), خانه (`/manage/`), درگاه پرداخت و کلیدهای فروش, دسترسی مهمان, فروش و کاربران (`/manage/sales/`), نشانی‌های قدیمی, ورود و دسترسی, ویژگی‌ها (+6 more)

### Community 218 - "DateResult.tsx"
Cohesion: 0.43
Nodes (7): hasPersian(), Ltr(), Rows(), DateResult(), useDateFormat(), parseAge(), parseDateText()

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
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1699 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **88 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UserSession` connect `accounts/services.py` to `WebsiteAuthTests`, `console/views.py`, `useTheme`, `guest.py`, `views_account.py`, `PurchaseFlowTests`, `tests_console.py`, `PlatformAPIError`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`, `manage/views.py`?**
  _High betweenness centrality (0.170) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `AppText()` (e.g. with `زبان، جهت و تم` and `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅`) actually correct?**
  _`AppText()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-build-properties` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.029030356616563512 - nodes in this community are weakly interconnected._
- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `useTheme` to `App.tsx`, `useTheme`, `accounts/services.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.168) - this node is a cross-community bridge._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.019992003198720514 - nodes in this community are weakly interconnected._
- **Why does `اپ‌ها (`backend/apps/`)` connect `tests_console.py` to `config.py`, `console/views.py`, `Post`, `views_public.py`, `flashcards/views.py`, `views_account.py`, `quiz/views.py`, `SectionEditRequest`, `progress/selectors.py`, `PurchaseFlowTests`, `LessonTaxonomyTests`, `planning.py`, `accounts/services.py`, `views_drugs.py`, `SectionEdit`, `Article`, `website/models.py`, `billing/views.py`, `Calculator`, `Ingredient`, `nav.py`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._