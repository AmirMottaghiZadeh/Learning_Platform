# Graph Report - Learning Platform  (2026-10-25)

## Corpus Check
- 514 files · ~411,558 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 32 file(s) not represented in the graph (top: (none) 11, .ttf 7, .woff2 4)

## Summary
- 4950 nodes · 14004 edges · 209 communities (121 shown, 88 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1249 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e947a30c`
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
- progress/services.py
- GatewayError
- ImportOpenfdaTests
- billing/services.py
- Page
- views_drugs.py
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
- search_topics
- DrugPageTests
- QuizApiTests
- errata.py
- progress/views.py
- release.mjs
- PurchaseFlowTests
- json
- Ingredient
- FlashcardApiTests
- LessonTaxonomyTests
- expo
- planning.py
- Article
- common.tsx
- data_quality_center/tests.py
- offline/tests.py
- Article
- test_phone_auth.py
- ۶. پیکربندی و متغیرهای محیطی
- export
- files.web.ts
- import_calculators.py
- throttling.py
- Post
- WebsiteAuthTests
- celery_tasks.py
- ۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین
- migrate_uptodate_to_mysql.py
- dependencies
- medscape/tests.py
- crypto.web.ts
- panel.js
- panel/views.py
- اپ‌ها (`backend/apps/`)
- logging
- SectionEdit
- views_account.py
- django_urls
- ConsoleTestCase
- test_onboarding_plan.py
- LessonDetailScreen.tsx
- config.py
- UptodateTests
- website_extras.py
- dqc_extras.py
- clean_profile_boilerplate.py
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- porter.ts
- billing/views.py
- medscapeArticle.ts
- offline/services.py
- lessons/selectors.py
- Pharmexa — custom icon prompts
- offline/reader.ts
- docs/README.md
- 6. Lesson study topics (52)
- files.ts
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
- DrugApiTests
- StandardizeUnitsTests
- accounts/services.py
- ۵. قرارداد API (نسخهٔ ۱)
- topic_mastery
- ۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی
- tsconfig.json
- ۱۲. سایت `pharmenta.ir` و پنل محتوا
- django_apps
- App.tsx
- sw.js
- Command
- HealthCheckTests
- ReviewTests
- pagination.py
- LeitnerCardSerializer
- otp.py
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- accounts/permissions.py
- docker-start.sh
- billing/apps.py
- CalculatorApiTests
- .claude/CLAUDE.md
- Subscriber
- app.config.js
- .mcp.json
- scripts
- ۳. بک‌اند (Django)
- RegisterSerializer
- 0005_atccode_name_fa.py
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
- ۷. کارهای فنی با معیار پذیرش
- flashcards/admin.py
- 0004_clear_rule_based_facts.py
- SessionTokenAuthenticationScheme
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

## Communities (209 total, 88 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.04
Nodes (77): flashcardsApi, offlineApi, quizApi, releaseApi, AppReleaseInfo, AtcCode, AtcGroup, BoxSummary (+69 more)

### Community 1 - "django_db"
Cohesion: 0.02
Nodes (52): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+44 more)

### Community 2 - "test_panel.py"
Cohesion: 0.06
Nodes (16): StaffRole, Meta, SiteTestCase, AdminTests, AuthorTests, AuthTests, CommercePagesTests, InboxTests (+8 more)

### Community 3 - "console/views.py"
Cohesion: 0.05
Nodes (73): DiscountForm, FeatureEditForm, Meta, FeatureForm, Meta, latin_digits(), parse_amount(), parse_jalali() (+65 more)

### Community 4 - "react"
Cohesion: 0.07
Nodes (72): ApiError, authApi, calculatorsApi, lessonsApi, meApi, medscapeApi, MedscapeKind, ALPHABET (+64 more)

### Community 5 - "Post"
Cohesion: 0.07
Nodes (50): Comment, Meta, ContactMessage, Meta, Post, Meta, PostRevision, Meta (+42 more)

### Community 6 - "useTheme"
Cohesion: 0.09
Nodes (100): قابلیت‌ها, آنبوردینگ و برنامهٔ مطالعه, ارتباط با API و کش, افزودن صفحهٔ تازه, دانلود آفلاین (`src/offline/`), ساختار `frontend/src/`, شروع اپ, قواعد کدنویسی اپ (+92 more)

### Community 7 - "views_public.py"
Cohesion: 0.05
Nodes (41): site(), SiteMaintenanceMiddleware, DailyStat, Meta, SiteSettings, Meta, login_view(), _safe_next() (+33 more)

### Community 8 - ".reverse"
Cohesion: 0.04
Nodes (15): AuthenticationSecurityTests, OnboardingTests, enabled_gateways(), AccessTests, ConsoleTestCase, DeleteUserTests, DiscountAndReportTests, FeatureTests (+7 more)

### Community 9 - "package.json"
Cohesion: 0.04
Nodes (54): حساب و احراز هویت — `/auth/`, devDependencies, @types/react, typescript, main, name, private, version (+46 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.06
Nodes (36): all_decks(), _carded_slugs(), deck_slugs(), next_topic(), progress_map(), topic_meta(), LeitnerCard, Meta (+28 more)

### Community 11 - "UserSerializer"
Cohesion: 0.12
Nodes (7): OnboardingSerializer, PasswordSetSerializer, UserSerializer, Meta, OnboardingView, PasswordSetView, plan_from_onboarding()

### Community 12 - "PlatformAPIError"
Cohesion: 0.09
Nodes (19): AuthTokenResponseSerializer, create_guest(), GuestSessionView, GuestStatusView, _first_message(), _message_from_data(), _normalize_code(), platform_exception_handler() (+11 more)

### Community 13 - "progress/services.py"
Cohesion: 0.09
Nodes (20): DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin, DailyStudy, Meta, LearnerProgress, dashboard() (+12 more)

### Community 14 - "GatewayError"
Cohesion: 0.06
Nodes (19): GatewayError, _post_json(), SepGateway, ZarinpalGateway, ZibalGateway, _div(), format_date(), _jal_cal() (+11 more)

### Community 16 - "billing/services.py"
Cohesion: 0.04
Nodes (33): DiscountCode, Meta, Order, Meta, Access, active_entitlements(), BillingError, check_feature() (+25 more)

### Community 17 - "Page"
Cohesion: 0.08
Nodes (6): clean_html(), _Cleaner, plain_text(), safe_url(), _Text, SanitizeTests

### Community 18 - "views_drugs.py"
Cohesion: 0.06
Nodes (30): fa(), Migration, Migration, article(), breadcrumbs(), editorial_team(), home_graph(), _id() (+22 more)

### Community 19 - "useLang"
Cohesion: 0.09
Nodes (53): LessonGroup, DateInput(), DaysInput(), Field(), QuestionTitle(), CategoryPicker(), Chip(), ChipRow() (+45 more)

### Community 20 - "accounts/views.py"
Cohesion: 0.06
Nodes (42): LearnerProfileSerializer, Meta, LoginSerializer, OtpRequestResponseSerializer, OtpRequestSerializer, OtpVerifySerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer (+34 more)

### Community 21 - "fix_results"
Cohesion: 0.14
Nodes (7): fix_results(), fix_strings_fa(), apply_fixes(), Migration, apply_fixes(), Migration, FormulaErrataTests

### Community 22 - "data_quality_center/views.py"
Cohesion: 0.11
Nodes (25): warning_count(), section_state(), _diffs(), discard(), history(), _login_key(), login_view(), logout_view() (+17 more)

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.07
Nodes (57): CalculatorErrorCheck, CalculatorResultDef, Tier, useLiveScore(), buildHeuristicSeeds(), cartesian(), classifyResultTone(), computeCalculator() (+49 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.06
Nodes (40): record_quiz_answers(), BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, ingredient_ids_for_selection(), preview_selection(), sample_bank_questions(), _sample_rows() (+32 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.06
Nodes (74): TopInset, useBleedTop(), countMatches(), FindState, highlight(), ListMarker(), LTR, NumberedHeading() (+66 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.09
Nodes (18): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, _categories_for_generics(), check_interactions(), close_all(), _conn(), _dir() (+10 more)

### Community 28 - ".request_code"
Cohesion: 0.08
Nodes (21): CodeRuleTests, PhoneAuthTestCase, ResetTests, SignUpTests, برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی, روش تبدیل پیشنهادها به کلمات کلیدی معتبر, ساخت Analytics از ابتدا (+13 more)

### Community 29 - "progress/tests.py"
Cohesion: 0.08
Nodes (8): Migration, seed(), bump_mistake(), _chapter_with_drug(), MaintenancePlanAndApiTests, MeApiTests, ProgressServiceTests, ۳c — `apps.flashcards` + `apps.quiz` (ساخته‌شده، پشت فلگ خاموش) ✅

### Community 30 - "core/views.py"
Cohesion: 0.14
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 31 - "lessons/views.py"
Cohesion: 0.09
Nodes (24): _applies(), require_atc_content(), _require_content(), require_feature(), require_topic_content(), LessonDrugSerializer, get_lesson_drug(), topics_for_chapter() (+16 more)

### Community 33 - "store.ts"
Cohesion: 0.09
Nodes (55): OfflinePackageInfo, ERROR_TEXT, LOGO, NAME, OfflinePackageCard(), PHASE_TEXT, useOfflineBoot(), partSize() (+47 more)

### Community 34 - "Calculator"
Cohesion: 0.13
Nodes (15): Calculator, Meta, CalculatorCategory, Meta, CalculatorCategorySerializer, Meta, CalculatorDetailSerializer, Meta (+7 more)

### Community 35 - "SectionEditRequest"
Cohesion: 0.10
Nodes (21): ReviewEvent, Meta, SectionEditRequest, Meta, approve(), _clean(), _client_ip(), _close() (+13 more)

### Community 36 - "re"
Cohesion: 0.21
Nodes (10): _adjective(), _chain(), _key(), _latin_quantity(), _spelling(), standardize_in(), standardize_units(), _symbol_of() (+2 more)

### Community 37 - "CalculatorDetailScreen.tsx"
Cohesion: 0.09
Nodes (48): StudyPlanItem, describeInputs(), CardsFlow(), ChecklistFlow(), flowLayout, LiveScore(), Choices(), FieldProps (+40 more)

### Community 38 - "offline/views.py"
Cohesion: 0.05
Nodes (32): Command, cors_rule(), _request(), build_matches_dataset(), LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer (+24 more)

### Community 39 - "api.py"
Cohesion: 0.08
Nodes (13): note_lines(), ReleaseCheckView, ReleaseQuerySerializer, AppRelease, Meta, version_code(), ReleaseForm, Meta (+5 more)

### Community 40 - "search_topics"
Cohesion: 0.10
Nodes (17): article_from_row(), _dir(), get_image(), get_topic(), is_available(), _mysql_conn(), search_topics(), _search_words() (+9 more)

### Community 41 - "DrugPageTests"
Cohesion: 0.12
Nodes (3): DrugPageTests, SiteIdentityTests, structured()

### Community 42 - "QuizApiTests"
Cohesion: 0.09
Nodes (4): QuizAccessTests, QuizApiTests, QuizLockedTests, _seed_atc_world()

### Community 43 - "errata.py"
Cohesion: 0.09
Nodes (12): _fa_keys_standardized(), fix_questions(), renumber_from_one(), _stage_names_without_prefix(), _title_formula_as_result(), _with_choices(), _with_unit(), apply_fixes() (+4 more)

### Community 44 - "progress/views.py"
Cohesion: 0.08
Nodes (28): Mistake, Meta, skip_item(), DashboardSerializer, FocusRowSerializer, FocusSessionSerializer, MistakeSerializer, Meta (+20 more)

### Community 45 - "release.mjs"
Cohesion: 0.09
Nodes (15): appJson, at, dryRun, file(), frontend, [kind, ...flags], lock, [major, minor, patch] (+7 more)

### Community 46 - "PurchaseFlowTests"
Cohesion: 0.11
Nodes (3): clear_cache(), _settings_changed(), PurchaseFlowTests

### Community 47 - "json"
Cohesion: 0.06
Nodes (24): build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections(), _varints(), Command (+16 more)

### Community 48 - "Ingredient"
Cohesion: 0.06
Nodes (19): Command, Command, AtcCode, Meta, Ingredient, Meta, AtcCodeSerializer, Meta (+11 more)

### Community 49 - "FlashcardApiTests"
Cohesion: 0.08
Nodes (9): IngredientProfileSection, Meta, LessonDrugSectionSerializer, Meta, FlashcardApiTests, FlashcardLockedTests, _refresh_facts(), _rich_ingredient() (+1 more)

### Community 50 - "LessonTaxonomyTests"
Cohesion: 0.05
Nodes (9): ChapterProgress, Meta, ReadDrug, Meta, DrugSearchTests, _ingredient(), LessonTaxonomyFallbackTests, LessonTaxonomyTests (+1 more)

### Community 51 - "expo"
Cohesion: 0.06
Nodes (32): backgroundColor, foregroundImage, adaptiveIcon, allowBackup, blockedPermissions, package, projectId, typedRoutes (+24 more)

### Community 52 - "planning.py"
Cohesion: 0.08
Nodes (26): mark_drug_read(), StudyPlanItem, Meta, _chapter(), complete_item(), ensure_today_items(), _flatten(), _goal_items() (+18 more)

### Community 53 - "Article"
Cohesion: 0.06
Nodes (20): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label(), Article (+12 more)

### Community 54 - "common.tsx"
Cohesion: 0.09
Nodes (82): CalculatorDetail, CalculatorQuestion, bandFor(), Chip(), Collapse(), Explain(), Extra, Extras() (+74 more)

### Community 55 - "data_quality_center/tests.py"
Cohesion: 0.24
Nodes (6): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), word_diff(), CheckTests

### Community 56 - "offline/tests.py"
Cohesion: 0.06
Nodes (11): writing(), Command, rewrite_summaries(), CleanBoilerplateInPipelineTests, LoadAtcReferenceTests, _make_source_db(), ModelTests, StandardizePipelineUnitsTests (+3 more)

### Community 57 - "Article"
Cohesion: 0.04
Nodes (27): Command, CalculatorTag, Meta, export(), load(), Command, _DryRun, ReferenceImportCommand (+19 more)

### Community 58 - "test_phone_auth.py"
Cohesion: 0.09
Nodes (9): EmailOrUsernameBackend, Command, InvalidPhone, looks_like_phone(), normalize_phone(), PhoneField, NormalizePhoneTests, ProfileTests (+1 more)

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.12
Nodes (16): HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت, دادهٔ مرجع (UpToDate و Lexicomp), دیتابیس، کش و آمادگی, سایت (+8 more)

### Community 60 - "export"
Cohesion: 0.10
Nodes (7): Command, Command, export(), open_parts(), part_name(), _Parts, OpenfdaReferenceDbTests

### Community 61 - "files.web.ts"
Cohesion: 0.19
Nodes (9): file(), forget(), partSize(), readRange(), removeBuild(), removeOtherBuilds(), removePart(), snapshots (+1 more)

### Community 62 - "import_calculators.py"
Cohesion: 0.14
Nodes (12): standardize_fa_units(), Command, _error_checks_for(), _formula_strings_fa(), _import_categories(), _import_tags(), _questions_for(), _references_for() (+4 more)

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "Post"
Cohesion: 0.11
Nodes (4): CommentTests, DownloadAndMachineTests, make_post(), PostVisibilityTests

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (26): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+18 more)

### Community 68 - "migrate_uptodate_to_mysql.py"
Cohesion: 0.11
Nodes (6): Command, Command, ensure_title_search_index(), _has_title_search_index(), mysql_config(), MysqlTitleIndexTests

### Community 69 - "dependencies"
Cohesion: 0.07
Nodes (28): dependencies, axios, expo, expo-build-properties, expo-constants, expo-crypto, expo-file-system, expo-font (+20 more)

### Community 70 - "medscape/tests.py"
Cohesion: 0.11
Nodes (6): _disease_record(), _guideline_record(), ImportMedscapeArticlesTests, MedscapeApiTests, _write_diseases_tree(), _write_guidelines()

### Community 71 - "crypto.web.ts"
Cohesion: 0.21
Nodes (10): اجرای کامل با Docker, OfflineLicense, db(), idb(), keyring, openRecord(), openRecordBase64(), PackageKey (+2 more)

### Community 72 - "panel.js"
Cohesion: 0.16
Nodes (14): buildEditor(), align(), block(), exec(), sync(), toggleSource(), wrapBlock(), filterNav() (+6 more)

### Community 73 - "panel/views.py"
Cohesion: 0.05
Nodes (43): Command, Command, ActivityLog, Meta, Announcement, Meta, Category, Meta (+35 more)

### Community 74 - "اپ‌ها (`backend/apps/`)"
Cohesion: 0.07
Nodes (22): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, AdminAction, Meta (+14 more)

### Community 75 - "logging"
Cohesion: 0.10
Nodes (8): password_reset_url_for_user(), send_password_reset_email(), send_password_reset_emails_for_email(), send_password_reset_email_task(), get_request_id(), JsonFormatter, RequestContextFilter, enqueue()

### Community 76 - "SectionEdit"
Cohesion: 0.16
Nodes (6): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin, SectionEdit, Meta

### Community 77 - "views_account.py"
Cohesion: 0.12
Nodes (18): OneTimeCode, Meta, AccountForm, CodeForm, LoginForm, PasswordForm, PhoneForm, account() (+10 more)

### Community 80 - "test_onboarding_plan.py"
Cohesion: 0.18
Nodes (6): StudyPlan, get_plan(), _onboarding(), OnboardingPlanTests, PlanTodayApiTests, _two_chapter_topic()

### Community 81 - "LessonDetailScreen.tsx"
Cohesion: 0.30
Nodes (11): Badge(), joinOpenParens(), LessonBlock, LessonBody(), LessonLine, parenDepth(), parseLessonText(), sectionText() (+3 more)

### Community 82 - "config.py"
Cohesion: 0.11
Nodes (14): BillingConfig, current(), gateway_spec(), _gateways(), GatewaySpec, _load(), row(), access() (+6 more)

### Community 84 - "website_extras.py"
Cohesion: 0.15
Nodes (8): atc_groups(), feature_icon(), nav_on(), oneline(), person(), split_highlight(), split_lines(), آنچه کد انجام می‌دهد

### Community 85 - "dqc_extras.py"
Cohesion: 0.13
Nodes (16): ago(), get_item(), guest_access_on(), initial(), jdate(), num(), toman(), action_label() (+8 more)

### Community 86 - "clean_profile_boilerplate.py"
Cohesion: 0.14
Nodes (13): clean_text(), Command, cleaned(), is_hypersensitivity_boilerplate(), is_hypersensitivity_boilerplate_en(), is_negative_indication_en(), is_negative_indication_fa(), is_null_placeholder() (+5 more)

### Community 87 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.06
Nodes (9): build.sh script, configure_runtime(), validate_production_broker(), validate_production_cache(), validate_production_secret_key(), CorsPreflightTests, ProductionSecretKeyTests, DJANGO_SETTINGS_MODULE (+1 more)

### Community 88 - "porter.ts"
Cohesion: 0.23
Nodes (8): firstRule(), isVowelLetter(), porterStem(), Rule, STEP2, STEP3, STEP4, Word

### Community 89 - "billing/views.py"
Cohesion: 0.06
Nodes (35): FakeGateway, get_gateway(), start_payment(), Verification, is_guest(), CatalogSerializer, CheckoutSerializer, MyAccessSerializer (+27 more)

### Community 90 - "medscapeArticle.ts"
Cohesion: 0.20
Nodes (14): MedscapeBlock, MedscapeSection, countWords(), numberByDepth(), Numbered, readingMinutes(), blockText(), buildMedscapeModel() (+6 more)

### Community 91 - "offline/services.py"
Cohesion: 0.24
Nodes (7): has_paid_plan_with(), is_entitled(), is_guest(), issue_license(), license_days(), LicenseError, _wrap_for()

### Community 92 - "lessons/selectors.py"
Cohesion: 0.12
Nodes (12): AtcCategory, Meta, fold(), get_chapter(), l2_slug_index(), _l2_slug_index(), lesson_groups(), _rank() (+4 more)

### Community 93 - "Pharmexa — custom icon prompts"
Cohesion: 0.15
Nodes (12): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups, 9. App identity (optional) (+4 more)

### Community 94 - "offline/reader.ts"
Cohesion: 0.07
Nodes (40): Coding Style & Naming Conventions, پایهٔ Django, lexicompApi, uptodateApi, LexicompDrug, LexicompInteraction, OfflineDataset, OfflineManifest (+32 more)

### Community 96 - "6. Lesson study topics (52)"
Cohesion: 0.15
Nodes (13): 6. Lesson study topics (52), Cardiovascular & blood, Dermatology, Endocrine & metabolism, Gastrointestinal, Infectious disease, Miscellaneous, Musculoskeletal (+5 more)

### Community 97 - "files.ts"
Cohesion: 0.13
Nodes (18): downloader, DownloadEvents, PartJob, PartRef, tasks, buildDir(), closeHandles(), ensureBuildDir() (+10 more)

### Community 98 - "FlashcardFact"
Cohesion: 0.24
Nodes (3): FlashcardFact, Meta, Command

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

### Community 101 - "Command"
Cohesion: 0.11
Nodes (5): Command, _int(), _json_list(), _name_fa(), AtcSupplementTests

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
Cohesion: 0.05
Nodes (24): Media, Meta, AnnouncementForm, Meta, CategoryForm, Meta, MediaMetaForm, Meta (+16 more)

### Community 112 - "accounts/services.py"
Cohesion: 0.07
Nodes (33): SessionTokenAuthentication, Role, Meta, RoleAssignment, Meta, SecurityAuditEvent, Meta, SessionRefreshToken (+25 more)

### Community 113 - "۵. قرارداد API (نسخهٔ ۱)"
Cohesion: 0.11
Nodes (19): Lexicomp — `/lexicomp/` (ویژگی `lexicomp`), Medscape — `/medscape/` (ویژگی `medscape`), UpToDate — `/uptodate/` (ویژگی `uptodate`), آزمون — `/quiz/` (ویژگی `quiz`؛ پرچم `QUIZ_API_ENABLED`), برنامهٔ ساخته‌شده از آنبوردینگ, تغییر دادن API, داروها — `/drugs/` و `/atc/`, دانلود آفلاین — `/offline/` (+11 more)

### Community 114 - "topic_mastery"
Cohesion: 0.16
Nodes (7): slugs_for_topic(), topic_chapters(), topic_progress(), _flashcard_recall_for_slugs(), _quiz_accuracy_for_slugs(), topic_mastery(), TopicMasteryTests

### Community 115 - "۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی"
Cohesion: 0.12
Nodes (17): اطلاعات غیرمحرمانه‌ای که باید جایی ثبت باشد, بازیابی, بکاپ و بازیابی, حساب‌های سرویس, رازها و چیزهایی که باید امن نگه داشته شوند, رازهای فنی, شاخص‌هایی که مرتب دیده شوند, عیب‌یابی (+9 more)

### Community 116 - "tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, paths, strict, extends, include, expo/tsconfig.base

### Community 117 - "۱۲. سایت `pharmenta.ir` و پنل محتوا"
Cohesion: 0.14
Nodes (14): not_found(), آمار بازدید, حساب و خرید روی سایت, دارونامهٔ عمومی (`/drugs/`), رسانه, سئو, ساختار کد, صفحه‌های عمومی (+6 more)

### Community 119 - "App.tsx"
Cohesion: 0.08
Nodes (36): زبان، جهت و تم, App(), ThemedStatusBar(), OfflineDownloadButton(), OfflineSheet(), dismissedRecently(), Notes(), Offer (+28 more)

### Community 120 - "sw.js"
Cohesion: 0.38
Nodes (4): inScope(), referencedFiles(), SCOPE, storeShell()

### Community 122 - "HealthCheckTests"
Cohesion: 0.15
Nodes (3): HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests

### Community 125 - "LeitnerCardSerializer"
Cohesion: 0.18
Nodes (4): _card_back_fields(), DeckCardSerializer, LeitnerCardSerializer, Meta

### Community 126 - "otp.py"
Cohesion: 0.09
Nodes (17): LearnerProfile, account_for_signup(), _hash(), _minutes(), _new_code(), OtpError, request_code(), user_for_phone() (+9 more)

### Community 127 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.17
Nodes (10): PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa, 🎉 بازنویسی کامل شد, فاز ۰.۵ — حذف زیرساخت رهاشده ✅, فاز ۱ — دیتابیس دارویی ✅, فاز ۲ — قرارداد API + API دانش دارویی + onboarding ✅, فاز ۶ — uptodate + جمع‌بندی + انتشار (زیرفازی), پس از انتشار — حذف کدهای ATC نامرتبط با اندیکاسیون ✅ (برنچ `fix-chapter-indication-fit`), پس از انتشار — سایت و بلاگ `pharmenta.ir` + پنل مدیریت ✅ (+2 more)

### Community 128 - "accounts/permissions.py"
Cohesion: 0.31
Nodes (6): CanManagePlatformRoles, CanViewSecurityAudit, HasPlatformPermission, HasRecentStepUp, session_has_recent_step_up(), user_has_platform_permission()

### Community 134 - "Subscriber"
Cohesion: 0.25
Nodes (3): Subscriber, Meta, FormsTests

### Community 152 - "scripts"
Cohesion: 0.25
Nodes (8): scripts, android, build:web, ios, release, start, typecheck, web

### Community 182 - "۳. بک‌اند (Django)"
Cohesion: 0.12
Nodes (13): RequestIdMiddleware, SiteHostMiddleware, UpToDate و Lexicomp, افزودن یک قابلیت فروشی تازه, بستهٔ آفلاین (`apps.offline`), زنجیرهٔ middleware, صورتحساب و دسترسی (`apps.billing`), قواعد مشترک API (+5 more)

### Community 196 - "۷. کارهای فنی با معیار پذیرش"
Cohesion: 0.40
Nodes (3): PostQuerySet, سرعت و تجربهٔ موبایل, ۷. کارهای فنی با معیار پذیرش

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

- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `useTheme` to `accounts/services.py`, `App.tsx`, `CalculatorDetailScreen.tsx`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.164) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `AppText()` (e.g. with `زبان، جهت و تم` and `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅`) actually correct?**
  _`AppText()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-build-properties` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.037025316455696206 - nodes in this community are weakly interconnected._
- **Why does `UserSession` connect `accounts/services.py` to `WebsiteAuthTests`, `console/views.py`, `useTheme`, `اپ‌ها (`backend/apps/`)`, `UserSerializer`, `PlatformAPIError`, `config.py`, `accounts/views.py`, `test_phone_auth.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.0239880059970015 - nodes in this community are weakly interconnected._
- **Why does `اپ‌ها (`backend/apps/`)` connect `اپ‌ها (`backend/apps/`)` to `test_panel.py`, `console/views.py`, `Post`, `views_public.py`, `flashcards/views.py`, `UserSerializer`, `progress/services.py`, `billing/services.py`, `views_drugs.py`, `quiz/views.py`, `Calculator`, `SectionEditRequest`, `Ingredient`, `FlashcardApiTests`, `LessonTaxonomyTests`, `planning.py`, `Article`, `۳. بک‌اند (Django)`, `Article`, `panel/views.py`, `SectionEdit`, `views_account.py`, `config.py`, `lessons/selectors.py`, `FlashcardFact`, `Media`, `accounts/services.py`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._