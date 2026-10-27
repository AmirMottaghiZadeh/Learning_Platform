# Graph Report - Learning Platform  (2026-10-26)

## Corpus Check
- 547 files · ~436,087 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 35 file(s) not represented in the graph (top: (none) 11, .ttf 7, .css 5)

## Summary
- 5370 nodes · 15381 edges · 213 communities (126 shown, 87 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1400 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fe49d2da`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- api/types.ts
- django_db
- test_panel.py
- console/views.py
- react
- Post
- Navigator.tsx
- views_public.py
- .reverse
- useLang
- flashcards/views.py
- useTheme
- uptodate/views.py
- LeitnerCard
- billing/tests.py
- MedscapeArticleScreen.tsx
- BottomNav.tsx
- Page
- ImportOpenfdaTests
- useLang
- PlatformAPIError
- forms_account.py
- drugs/reference_db.py
- calculatorEngine.ts
- accounts/checks.py
- quiz/views.py
- ScreenChrome.tsx
- lexicomp/services.py
- .request_code
- progress/services.py
- core/views.py
- lessons/views.py
- ApiTests
- store.ts
- errata.py
- data_quality_center/views.py
- panel/forms.py
- get_plan
- progress/admin.py
- Media
- uptodate/services.py
- DrugPageTests
- QuizApiTests
- builders.py
- progress/views.py
- release.mjs
- PurchaseFlowTests
- json
- drugs/serializers.py
- import_calculators.py
- LessonTaxonomyTests
- expo
- StudyPlanItem
- import_medscape_articles.py
- ResultCard
- django_urls
- manage/views.py
- برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای
- django_utils
- ۶. پیکربندی و متغیرهای محیطی
- offline/views.py
- files.web.ts
- decks.py
- throttling.py
- package.json
- FeedTests
- re
- ۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین
- ReferenceDbTests
- dependencies
- medscape/tests.py
- crypto.web.ts
- panel.js
- views_drugs.py
- HealthCheckTests
- celery_tasks.py
- data_quality_center/admin.py
- views_account.py
- TitleSearchTests
- ReviewTests
- common.tsx
- calculatorModel.ts
- Article
- UptodateTests
- fix_results
- dqc_extras.py
- file_urls
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- sqlite3
- billing/views.py
- Calculator
- make
- Ingredient
- Pharmexa — custom icon prompts
- ReleaseForm
- docs/README.md
- 6. Lesson study topics (52)
- files.ts
- previews.tsx
- site.js
- MedscapeApiTests
- uptodateLocal.ts
- downloader.web.ts
- ۲. راه‌اندازی محیط توسعه
- offline/reader.ts
- Redirect
- PackFormatTests
- Repository Guidelines
- BuildTests
- _updated_from_text
- website_extras.py
- StandardizeUnitsTests
- latest_manifest
- ۵. قرارداد API (نسخهٔ ۱)
- Command
- ۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی
- tsconfig.json
- migrate_uptodate_to_mysql.py
- django_apps
- CalculatorApiTests
- sw.js
- Command
- maintenance_urls.py
- PackageFileView
- pagination.py
- _SectionCard
- django_conf
- _nearest
- ReleaseCheckTests
- docker-start.sh
- billing/apps.py
- ImportCalculatorsTests
- .claude/CLAUDE.md
- StudyTopicsCoverageTests
- app.config.js
- .mcp.json
- SmsIrBackendTests
- enforcement.py
- bootstrap_superuser.py
- 0006_leitner_by_section.py
- AuthenticationSecurityTests
- calculators/apps.py
- data_quality_center/apps.py
- drugs/apps.py
- flashcards/apps.py
- lessons/apps.py
- lexicomp/apps.py
- offline/apps.py
- quiz/apps.py
- uptodate/apps.py
- website/apps.py
- GatewayPageTests
- PhaseTwoSessionSecurityTests
- LessonDetailScreen.tsx
- ۸. دیپلوی
- Section
- VisitorDay
- ۱. معرفی و معماری
- ۱۰. مرجع سریع دستورها
- ۱۱. مدیریت
- DateResult.tsx
- manage/apps.py
- medscape/apps.py
- مستندات فارمنتا
- فارمنتا (Pharmenta)

## God Nodes (most connected - your core abstractions)
1. `useTheme()` - 206 edges
2. `AppText()` - 194 edges
3. `useLang()` - 185 edges
4. `react` - 90 edges
5. `PlatformAPIError` - 83 edges
6. `Ingredient` - 81 edges
7. `react-native` - 80 edges
8. `useNav` - 67 edges
9. `Plan` - 58 edges
10. `Post` - 58 edges

## Surprising Connections (you probably didn't know these)
- `فاز ۰.۵ — حذف زیرساخت رهاشده ✅` --references--> `UserSession`  [INFERRED]
  PHASES.md → backend/apps/accounts/models.py
- `ورود و دسترسی` --references--> `SecurityAuditEvent`  [INFERRED]
  docs/11-admin-consoles.md → backend/apps/accounts/models.py
- `اعلانات اپ (`/manage/app/announcements/`)` --references--> `AnnouncementReceipt`  [INFERRED]
  docs/11-admin-consoles.md → backend/apps/announcements/models.py
- `۳d — بازنویسی `data_quality_center` ✅` --references--> `SectionEdit`  [INFERRED]
  PHASES.md → backend/apps/data_quality_center/models.py
- `دستورهای خودکار هنگام شروع` --references--> `AtcCategory`  [INFERRED]
  docs/07-data.md → backend/apps/drugs/models.py

## Import Cycles
- None detected.

## Communities (213 total, 87 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.03
Nodes (83): announcementsApi, offlineApi, quizApi, releaseApi, AnnouncementEvent, AnnouncementKind, AppReleaseInfo, AtcCode (+75 more)

### Community 1 - "django_db"
Cohesion: 0.02
Nodes (54): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+46 more)

### Community 2 - "test_panel.py"
Cohesion: 0.06
Nodes (17): StaffRole, Meta, post_link(), preview_token(), AdminTests, AuthorTests, AuthTests, InboxTests (+9 more)

### Community 3 - "console/views.py"
Cohesion: 0.03
Nodes (95): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, DiscountForm, FeatureEditForm (+87 more)

### Community 4 - "react"
Cohesion: 0.07
Nodes (50): ALPHABET, AlphabeticalArticleList(), buildOffsets(), groupAlphabetically(), Section, Bloom(), MeshBackground(), OfflineSheet() (+42 more)

### Community 5 - "Post"
Cohesion: 0.06
Nodes (56): ActivityLog, Meta, DailyStat, Meta, Post, Meta, PostRevision, Meta (+48 more)

### Community 6 - "Navigator.tsx"
Cohesion: 0.09
Nodes (82): قابلیت‌ها, افزودن صفحهٔ تازه, ناوبری, calculatorsApi, lessonsApi, meApi, LessonGroup, MedscapeKind (+74 more)

### Community 7 - "views_public.py"
Cohesion: 0.05
Nodes (52): site(), PostQuerySet, SiteSettings, Meta, article(), breadcrumbs(), editorial_team(), home_graph() (+44 more)

### Community 8 - ".reverse"
Cohesion: 0.06
Nodes (9): OnboardingTests, AccessTests, FeatureTests, PlanBuilderTests, UsersPageTests, AccessTests, render_links(), link() (+1 more)

### Community 9 - "useLang"
Cohesion: 0.09
Nodes (42): آنبوردینگ و برنامهٔ مطالعه, ارتباط با API و کش, دانلود آفلاین (`src/offline/`), زبان، جهت و تم, ساختار `frontend/src/`, شروع اپ, فلش‌کارت و جعبهٔ لایتنر, قواعد کدنویسی اپ (+34 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.07
Nodes (38): require_feature(), progress_map(), topic_meta(), TopicProgress, Meta, BoxCardSerializer, BoxReviewSerializer, BoxSummarySerializer (+30 more)

### Community 11 - "useTheme"
Cohesion: 0.08
Nodes (66): flashcardsApi, StudyPlanItem, describeInputs(), CardsFlow(), ChecklistFlow(), flowLayout, Choices(), FieldVariant (+58 more)

### Community 12 - "uptodate/views.py"
Cohesion: 0.30
Nodes (8): UptodateArticleSerializer, UptodateImageSerializer, UptodateSearchResultSerializer, UptodateTopicSerializer, ImageDetailView, _require_available(), TopicDetailView, TopicSearchView

### Community 13 - "LeitnerCard"
Cohesion: 0.08
Nodes (15): add_miss(), daily_minutes(), drawer_cards(), _exam_cap_days(), outcome(), overview(), previews(), review() (+7 more)

### Community 14 - "billing/tests.py"
Cohesion: 0.03
Nodes (25): SepGateway, ZarinpalGateway, ZibalGateway, _div(), _jal_cal(), _mod(), month_start(), to_gregorian() (+17 more)

### Community 15 - "MedscapeArticleScreen.tsx"
Cohesion: 0.09
Nodes (48): medscapeApi, MedscapeBlock, MedscapeSection, countMatches(), FindState, highlight(), ListMarker(), LTR (+40 more)

### Community 16 - "BottomNav.tsx"
Cohesion: 0.10
Nodes (29): اعلانات اپ, AnnouncementButton, AppAnnouncement, AnnouncementBox(), ANNOUNCEMENTS_KEY, Spotlight(), AnnouncementCard(), ICONS (+21 more)

### Community 17 - "Page"
Cohesion: 0.08
Nodes (6): clean_html(), _Cleaner, plain_text(), safe_url(), _Text, SanitizeTests

### Community 18 - "ImportOpenfdaTests"
Cohesion: 0.05
Nodes (12): IngredientProfileSectionInline, IngredientProfileSection, Meta, AtcSupplementTests, CleanBoilerplateInPipelineTests, DrugApiTests, ImportOpenfdaTests, LoadAtcReferenceTests (+4 more)

### Community 19 - "useLang"
Cohesion: 0.09
Nodes (50): DateInput(), DaysInput(), Field(), QuestionTitle(), CategoryPicker(), Chip(), ChipRow(), DateField() (+42 more)

### Community 20 - "PlatformAPIError"
Cohesion: 0.04
Nodes (66): Role, Meta, RoleAssignment, Meta, CanManagePlatformRoles, CanViewSecurityAudit, HasPlatformPermission, HasRecentStepUp (+58 more)

### Community 21 - "forms_account.py"
Cohesion: 0.22
Nodes (5): AccountForm, CodeForm, LoginForm, PasswordForm, PhoneForm

### Community 22 - "drugs/reference_db.py"
Cohesion: 0.10
Nodes (7): Command, Command, export(), open_parts(), part_name(), _Parts, OpenfdaReferenceDbTests

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.08
Nodes (54): useLiveScore(), buildHeuristicSeeds(), cartesian(), checkErrors(), classifyResultTone(), computeCalculator(), ComputeOptions, computeResultRanges() (+46 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.06
Nodes (36): BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, preview_selection(), best_score_pct_for_topic(), _finished_sessions(), _finished_topic_sessions(), topic_mastery_map() (+28 more)

### Community 26 - "ScreenChrome.tsx"
Cohesion: 0.07
Nodes (55): تور راهنما (`src/tour/`), TopInset, useBleedTop(), escape(), MediaContent, mediaPage(), MediaPageColors, page() (+47 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.08
Nodes (19): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, _categories_for_generics(), check_interactions(), close_all(), _conn(), _dir() (+11 more)

### Community 28 - ".request_code"
Cohesion: 0.17
Nodes (4): CodeRuleTests, PhoneAuthTestCase, ResetTests, SignUpTests

### Community 29 - "progress/services.py"
Cohesion: 0.07
Nodes (23): Migration, seed(), DailyStudy, Meta, dashboard(), _display_name(), _leitner_focus_row(), _mastery_pct() (+15 more)

### Community 30 - "core/views.py"
Cohesion: 0.14
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 31 - "lessons/views.py"
Cohesion: 0.04
Nodes (49): LessonDrugSerializer, ChapterProgress, Meta, ReadDrug, Meta, fold(), get_chapter(), get_lesson_drug() (+41 more)

### Community 33 - "store.ts"
Cohesion: 0.09
Nodes (53): OfflinePackageInfo, useOfflineBoot(), closeHandles(), partSize(), removeBuild(), removeOtherBuilds(), removePart(), closeReaders() (+45 more)

### Community 34 - "errata.py"
Cohesion: 0.09
Nodes (12): _fa_keys_standardized(), fix_questions(), fix_strings_fa(), renumber_from_one(), _stage_names_without_prefix(), _title_formula_as_result(), _with_choices(), apply_fixes() (+4 more)

### Community 35 - "data_quality_center/views.py"
Cohesion: 0.06
Nodes (52): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), warning_count(), word_diff(), section_state(), ReviewEvent (+44 more)

### Community 36 - "panel/forms.py"
Cohesion: 0.03
Nodes (51): Command, Command, Migration, Migration, Announcement, Meta, AppRelease, Meta (+43 more)

### Community 37 - "get_plan"
Cohesion: 0.11
Nodes (7): get_plan(), _onboarding(), OnboardingPlanTests, PlanTodayApiTests, MaintenancePlanAndApiTests, TopicMasteryTests, _two_chapter_topic()

### Community 38 - "progress/admin.py"
Cohesion: 0.53
Nodes (4): DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin

### Community 39 - "Media"
Cohesion: 0.07
Nodes (9): Media, Meta, Subscriber, Meta, CommentTests, DownloadAndMachineTests, FormsTests, make_post() (+1 more)

### Community 40 - "uptodate/services.py"
Cohesion: 0.14
Nodes (19): article_from_row(), _dir(), get_image(), get_topic(), is_available(), _is_word(), _mysql_conn(), _prefixed() (+11 more)

### Community 41 - "DrugPageTests"
Cohesion: 0.10
Nodes (4): DrugPageTests, SeedSeoContentTests, SiteIdentityTests, structured()

### Community 42 - "QuizApiTests"
Cohesion: 0.09
Nodes (3): QuizAccessTests, QuizApiTests, QuizLockedTests

### Community 43 - "builders.py"
Cohesion: 0.16
Nodes (10): build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections(), _varints(), pack_json() (+2 more)

### Community 44 - "progress/views.py"
Cohesion: 0.09
Nodes (28): Mistake, Meta, skip_item(), DashboardSerializer, FocusRowSerializer, FocusSessionSerializer, MistakeSerializer, Meta (+20 more)

### Community 45 - "release.mjs"
Cohesion: 0.09
Nodes (15): appJson, at, dryRun, file(), frontend, [kind, ...flags], lock, [major, minor, patch] (+7 more)

### Community 46 - "PurchaseFlowTests"
Cohesion: 0.07
Nodes (6): clear_cache(), _settings_changed(), GuestAccessTests, GuestConsoleTests, PurchaseFlowTests, WebsiteAuthTests

### Community 47 - "json"
Cohesion: 0.10
Nodes (10): Command, derive_key(), new_build_id(), open_sealed(), PackError, read_record(), seal(), secret() (+2 more)

### Community 48 - "drugs/serializers.py"
Cohesion: 0.10
Nodes (14): AtcCodeSerializer, Meta, IngredientDetailSerializer, Meta, IngredientListSerializer, Meta, LessonDrugSectionSerializer, Meta (+6 more)

### Community 49 - "import_calculators.py"
Cohesion: 0.14
Nodes (12): standardize_fa_units(), Command, _error_checks_for(), _formula_strings_fa(), _import_categories(), _import_tags(), _questions_for(), _references_for() (+4 more)

### Community 50 - "LessonTaxonomyTests"
Cohesion: 0.08
Nodes (4): DrugSearchTests, _ingredient(), LessonTaxonomyFallbackTests, LessonTaxonomyTests

### Community 51 - "expo"
Cohesion: 0.06
Nodes (32): backgroundColor, foregroundImage, adaptiveIcon, allowBackup, blockedPermissions, package, projectId, typedRoutes (+24 more)

### Community 52 - "StudyPlanItem"
Cohesion: 0.10
Nodes (15): StudyPlanItem, Meta, _chapter(), complete_item(), ensure_today_items(), _is_done_elsewhere(), plan_summary(), regenerate_items() (+7 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.16
Nodes (7): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label()

### Community 54 - "ResultCard"
Cohesion: 0.25
Nodes (30): Chip(), Collapse(), Explain(), Extras(), Hero(), Interpretation(), Ltr(), ResultCard() (+22 more)

### Community 55 - "django_urls"
Cohesion: 0.04
Nodes (36): AnnouncementEventView, AnnouncementListView, AnnouncementSerializer, as_item(), ButtonSerializer, EventSerializer, AnnouncementForm, Meta (+28 more)

### Community 56 - "manage/views.py"
Cohesion: 0.05
Nodes (51): wrapper(), format_date(), wrapper(), anyone(), can_enter(), has_site_role(), is_operator(), is_super() (+43 more)

### Community 57 - "برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای"
Cohesion: 0.12
Nodes (17): برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی, روش تبدیل پیشنهادها به کلمات کلیدی معتبر, ساخت Analytics از ابتدا, ساخت Search Console از ابتدا, منابع رسمی بررسی‌شده, چک‌لیست انتشار هر صفحه, ۱. نتیجهٔ بررسی واقعی سایت (+9 more)

### Community 58 - "django_utils"
Cohesion: 0.03
Nodes (36): SessionTokenAuthentication, SessionTokenAuthenticationScheme, LearnerProfile, UserSession, Meta, ProfileTests, BillingConfig, current() (+28 more)

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.10
Nodes (20): local(), open(), paint(), HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت (+12 more)

### Community 60 - "offline/views.py"
Cohesion: 0.10
Nodes (22): LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer, PackageFileUrlSerializer, PackageManifestSerializer, PackageUrlsRequestSerializer, PackageUrlsSerializer (+14 more)

### Community 61 - "files.web.ts"
Cohesion: 0.19
Nodes (9): file(), forget(), partSize(), readRange(), removeBuild(), removeOtherBuilds(), removePart(), snapshots (+1 more)

### Community 62 - "decks.py"
Cohesion: 0.12
Nodes (11): all_decks(), _carded_slugs(), _cards(), deck_cards(), deck_slugs(), next_topic(), _sections_by_slug(), add_quiz_miss() (+3 more)

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "package.json"
Cohesion: 0.03
Nodes (62): حساب و احراز هویت — `/auth/`, devDependencies, @types/react, typescript, main, name, private, scripts (+54 more)

### Community 65 - "FeedTests"
Cohesion: 0.17
Nodes (3): AdminTests, FeedTests, make()

### Community 66 - "re"
Cohesion: 0.21
Nodes (10): _adjective(), _chain(), _key(), _latin_quantity(), _spelling(), standardize_in(), standardize_units(), _symbol_of() (+2 more)

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (26): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+18 more)

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
Cohesion: 0.19
Nodes (11): buildEditor(), align(), block(), exec(), sync(), toggleSource(), wrapBlock(), loadPicker() (+3 more)

### Community 73 - "views_drugs.py"
Cohesion: 0.11
Nodes (16): fa(), _build_catalog(), catalog(), _drop_title(), drug_detail(), drug_index(), english_name(), fa_key() (+8 more)

### Community 74 - "HealthCheckTests"
Cohesion: 0.15
Nodes (3): HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests

### Community 75 - "celery_tasks.py"
Cohesion: 0.12
Nodes (3): PlatformTask, retry_delay_seconds(), configure_runtime()

### Community 76 - "data_quality_center/admin.py"
Cohesion: 0.27
Nodes (4): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin

### Community 77 - "views_account.py"
Cohesion: 0.13
Nodes (7): EmailOrUsernameBackend, InvalidPhone, looks_like_phone(), normalize_phone(), PhoneField, NormalizePhoneTests, _find_user()

### Community 78 - "TitleSearchTests"
Cohesion: 0.21
Nodes (3): build_title_index(), _title_words(), TitleSearchTests

### Community 79 - "ReviewTests"
Cohesion: 0.15
Nodes (3): ConsoleTestCase, DraftAndSubmitTests, ReviewTests

### Community 80 - "common.tsx"
Cohesion: 0.18
Nodes (18): bandFor(), Extra, fmt(), LEVEL_TONES, plain(), Tier, TierBar(), tiersTones() (+10 more)

### Community 81 - "calculatorModel.ts"
Cohesion: 0.11
Nodes (33): CalculatorDetail, CalculatorQuestion, ResultProps, LIST_FROM, FieldProps, FlowProps, StagingResult(), CalculatorAnswers (+25 more)

### Community 82 - "Article"
Cohesion: 0.03
Nodes (37): Command, export(), load(), Command, _DryRun, ReferenceImportCommand, dumps(), expected_count() (+29 more)

### Community 84 - "fix_results"
Cohesion: 0.21
Nodes (4): fix_results(), apply_fixes(), Migration, FormulaErrataTests

### Community 85 - "dqc_extras.py"
Cohesion: 0.13
Nodes (16): ago(), get_item(), guest_access_on(), initial(), jdate(), num(), toman(), action_label() (+8 more)

### Community 86 - "file_urls"
Cohesion: 0.18
Nodes (9): Command, cors_rule(), _request(), file_urls(), _on_download_host(), _prefix(), _read_manifest(), _s3() (+1 more)

### Community 87 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.07
Nodes (17): build.sh script, validate_production_broker(), validate_production_cache(), validate_production_secret_key(), CorsPreflightTests, ProductionSecretKeyTests, DJANGO_SETTINGS_MODULE, release.sh script (+9 more)

### Community 88 - "sqlite3"
Cohesion: 0.05
Nodes (22): open_for_import(), writing(), clean_text(), Command, cleaned(), is_hypersensitivity_boilerplate(), is_hypersensitivity_boilerplate_en(), is_negative_indication_en() (+14 more)

### Community 89 - "billing/views.py"
Cohesion: 0.04
Nodes (58): enabled_gateways(), FakeGateway, GatewayError, get_gateway(), _post_json(), start_payment(), Verification, UsageRecord (+50 more)

### Community 90 - "Calculator"
Cohesion: 0.12
Nodes (17): Calculator, Meta, CalculatorCategory, Meta, CalculatorTag, Meta, CalculatorCategorySerializer, Meta (+9 more)

### Community 91 - "make"
Cohesion: 0.11
Nodes (7): ActivityTests, HomeTests, make(), NavigationTests, SearchTests, ShellTests, SignInTests

### Community 92 - "Ingredient"
Cohesion: 0.03
Nodes (39): AtcCategoryAdmin, AtcCodeAdmin, IngredientAdmin, IngredientProfileSectionAdmin, Command, Command, AtcCategory, Meta (+31 more)

### Community 93 - "Pharmexa — custom icon prompts"
Cohesion: 0.15
Nodes (12): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups, 9. App identity (optional) (+4 more)

### Community 94 - "ReleaseForm"
Cohesion: 0.17
Nodes (4): ReleaseForm, Meta, JalaliDateTimeField, ReleaseFormTests

### Community 96 - "6. Lesson study topics (52)"
Cohesion: 0.15
Nodes (13): 6. Lesson study topics (52), Cardiovascular & blood, Dermatology, Endocrine & metabolism, Gastrointestinal, Infectious disease, Miscellaneous, Musculoskeletal (+5 more)

### Community 97 - "files.ts"
Cohesion: 0.13
Nodes (15): downloader, DownloadEvents, PartJob, PartRef, tasks, buildDir(), ensureBuildDir(), handles (+7 more)

### Community 98 - "previews.tsx"
Cohesion: 0.15
Nodes (35): Bands(), Check(), CheckDot(), Choice(), Drawers(), Flip(), Interaction(), kf() (+27 more)

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

### Community 101 - "uptodateLocal.ts"
Cohesion: 0.08
Nodes (38): lexicompApi, uptodateApi, LexicompDrug, LexicompInteraction, UptodateImage, cache, checkInteractions(), LexIndex (+30 more)

### Community 102 - "downloader.web.ts"
Cohesion: 0.20
Nodes (9): downloader, DownloadEvents, newWorker(), PartJob, PartRef, Run, runFor(), runs (+1 more)

### Community 103 - "۲. راه‌اندازی محیط توسعه"
Cohesion: 0.17
Nodes (12): اندروید و iOS, اپ (Expo), بک‌اند, تست بستهٔ آفلاین بدون باکت, تست و بررسی, روال کار با مخزن, ساخت دیتابیس و اجرای سرور, نسخهٔ وب (+4 more)

### Community 104 - "offline/reader.ts"
Cohesion: 0.18
Nodes (11): Coding Style & Naming Conventions, OfflineDataset, OfflineManifest, keyring, openRecord(), openRecordBase64(), PackageKey, sealed() (+3 more)

### Community 105 - "Redirect"
Cohesion: 0.07
Nodes (15): RequestIdMiddleware, SiteHostMiddleware, SiteMaintenanceMiddleware, Redirect, Meta, HostRoutingTests, UpToDate و Lexicomp, بستهٔ آفلاین (`apps.offline`) (+7 more)

### Community 106 - "PackFormatTests"
Cohesion: 0.23
Nodes (3): build_matches_dataset(), DownloadHostTests, PackFormatTests

### Community 107 - "Repository Guidelines"
Cohesion: 0.29
Nodes (6): Build, Test, and Development Commands, Commit & Pull Request Guidelines, Project Structure & Module Organization, Repository Guidelines, Security & Configuration Tips, Testing Guidelines

### Community 108 - "BuildTests"
Cohesion: 0.20
Nodes (4): BuildTests, _quiet(), _record(), snippet_source()

### Community 109 - "_updated_from_text"
Cohesion: 0.20
Nodes (4): _updated_from_html(), _updated_from_text(), HeaderTextTests, MysqlTitleSearchTests

### Community 110 - "website_extras.py"
Cohesion: 0.06
Nodes (26): ReviewForm, SectionEditForm, atc_groups(), feature_icon(), nav_on(), on_site(), oneline(), person() (+18 more)

### Community 112 - "latest_manifest"
Cohesion: 0.24
Nodes (4): clear_cache(), is_configured(), latest_manifest(), BucketManifestTests

### Community 113 - "۵. قرارداد API (نسخهٔ ۱)"
Cohesion: 0.09
Nodes (22): Lexicomp — `/lexicomp/` (ویژگی `lexicomp`), Medscape — `/medscape/` (ویژگی `medscape`), UpToDate — `/uptodate/` (ویژگی `uptodate`), آزمون — `/quiz/` (ویژگی `quiz`؛ پرچم `QUIZ_API_ENABLED`), برنامهٔ ساخته‌شده از آنبوردینگ, تغییر دادن API, جعبهٔ قدیمی, جعبهٔ لایتنر (+14 more)

### Community 115 - "۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی"
Cohesion: 0.12
Nodes (17): اطلاعات غیرمحرمانه‌ای که باید جایی ثبت باشد, بازیابی, بکاپ و بازیابی, حساب‌های سرویس, رازها و چیزهایی که باید امن نگه داشته شوند, رازهای فنی, شاخص‌هایی که مرتب دیده شوند, عیب‌یابی (+9 more)

### Community 116 - "tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, paths, strict, extends, include, expo/tsconfig.base

### Community 117 - "migrate_uptodate_to_mysql.py"
Cohesion: 0.14
Nodes (5): Command, ensure_title_search_index(), _has_title_search_index(), mysql_config(), MysqlTitleIndexTests

### Community 120 - "sw.js"
Cohesion: 0.38
Nodes (4): inScope(), referencedFiles(), SCOPE, storeShell()

### Community 123 - "PackageFileView"
Cohesion: 0.27
Nodes (3): local_dir(), local_file_for_token(), PackageFileView

### Community 125 - "_SectionCard"
Cohesion: 0.19
Nodes (3): _card_back_fields(), DeckCardSerializer, _SectionCard

### Community 126 - "django_conf"
Cohesion: 0.04
Nodes (52): OneTimeCode, Meta, SecurityAuditEvent, Meta, SessionRefreshToken, Meta, account_for_signup(), _hash() (+44 more)

### Community 127 - "_nearest"
Cohesion: 0.22
Nodes (5): _letters(), _max_typos(), _nearest(), _typo_distance(), TypoDistanceTests

### Community 132 - "ImportCalculatorsTests"
Cohesion: 0.16
Nodes (6): _with_unit(), _build_sqlite(), FaUnitsTests, ImportCalculatorsTests, _one_calculator(), QuestionUnitTests

### Community 156 - "enforcement.py"
Cohesion: 0.43
Nodes (4): _applies(), require_atc_content(), _require_content(), require_topic_content()

### Community 202 - "LessonDetailScreen.tsx"
Cohesion: 0.24
Nodes (14): SectionTone, Badge(), joinOpenParens(), LessonBlock, LessonBody(), LessonDetailScreen(), LessonLine, parenDepth() (+6 more)

### Community 204 - "۸. دیپلوی"
Cohesion: 0.12
Nodes (16): CI, امنیت و هشدار نصب, اپ اندروید و iOS, برگرداندن یک دیپلوی خراب, بک‌اند, جریان دیپلوی, حجم APK, راه‌اندازی از صفر (یک بار) (+8 more)

### Community 210 - "VisitorDay"
Cohesion: 0.24
Nodes (4): VisitorDay, Meta, UniqueVisitorTests, visit()

### Community 211 - "۱. معرفی و معماری"
Cohesion: 0.25
Nodes (8): دامنه‌ها و سرویس‌ها, ذخیره‌گاه‌های داده, ساختار مخزن, سرویس‌های بیرونی, فناوری‌ها, محصول, معماری, ۱. معرفی و معماری

### Community 212 - "۱۰. مرجع سریع دستورها"
Cohesion: 0.25
Nodes (8): اپ موبایل (EAS), تست و بررسی, توسعهٔ محلی, دستورهای مدیریتی Django (همه), دیپلوی و گیت, عیب‌یابی, پایپلاین study_content (بیرون از مخزن), ۱۰. مرجع سریع دستورها

### Community 213 - "۱۱. مدیریت"
Cohesion: 0.12
Nodes (16): ادمین Django (`/admin/`), اعلانات اپ (`/manage/app/announcements/`), خانه (`/manage/`), درگاه پرداخت و کلیدهای فروش, دسترسی مهمان, فروش و کاربران (`/manage/sales/`), مرکز کیفیت داده (`/manage/data/`), نشانی‌های قدیمی (+8 more)

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
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1726 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **87 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UserSession` connect `django_utils` to `console/views.py`, `PhaseTwoSessionSecurityTests`, `useLang`, `PurchaseFlowTests`, `PlatformAPIError`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`, `manage/views.py`, `django_conf`?**
  _High betweenness centrality (0.161) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `AppText()` (e.g. with `زبان، جهت و تم` and `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅`) actually correct?**
  _`AppText()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-build-properties` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.03447332421340629 - nodes in this community are weakly interconnected._
- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `useLang` to `django_utils`, `useTheme`, `Navigator.tsx`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.160) - this node is a cross-community bridge._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.021367521367521368 - nodes in this community are weakly interconnected._
- **Why does `اپ‌ها (`backend/apps/`)` connect `console/views.py` to `test_panel.py`, `Post`, `views_public.py`, `flashcards/views.py`, `ImportOpenfdaTests`, `PlatformAPIError`, `quiz/views.py`, `progress/services.py`, `lessons/views.py`, `data_quality_center/views.py`, `Media`, `StudyPlanItem`, `django_urls`, `django_utils`, `Article`, `billing/views.py`, `Calculator`, `Ingredient`, `Redirect`, `django_conf`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._