# Graph Report - Learning Platform  (2026-10-23)

## Corpus Check
- 486 files · ~387,302 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 32 file(s) not represented in the graph (top: (none) 11, .ttf 7, .woff2 4)

## Summary
- 4604 nodes · 12978 edges · 224 communities (126 shown, 98 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1199 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fc5ff298`
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
- calculators/reference_db.py
- billing/views.py
- panel/forms.py
- GatewayError
- ImportOpenfdaTests
- billing/tests.py
- accounts/permissions.py
- اپ‌ها (`backend/apps/`)
- django_conf
- accounts/views.py
- calculators/tests.py
- website/models.py
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
- data_quality_center/views.py
- .post
- CalculatorDetailScreen.tsx
- offline/views.py
- MaintenancePlanAndApiTests
- Post
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
- VerdictResult.tsx
- calculatorModel.ts
- progress/selectors.py
- Article
- test_phone_auth.py
- ۶. پیکربندی و متغیرهای محیطی
- drugs/admin.py
- 6. Lesson study topics (52)
- files.ts
- throttling.py
- django_utils
- crypto.web.ts
- logging
- ۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین
- uptodate/services.py
- dependencies
- medscape/tests.py
- ۲. راه‌اندازی محیط توسعه
- panel.js
- test_public.py
- LearnerProfile
- core/tests.py
- SectionEdit
- common.tsx
- views_account.py
- ConsoleTestCase
- StudyTopicsCoverageTests
- LessonDetailScreen.tsx
- ResultProps
- UptodateTests
- ReferenceDbTests
- website_extras.py
- clean_profile_boilerplate.py
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- porter.ts
- storage.py
- ReferenceImportCommand
- guest.py
- DrugPageTests
- builders.py
- offline/reader.ts
- docs/README.md
- views_drugs.py
- import_calculators.py
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
- OfflinePackageCard.tsx
- clean_html
- Role
- 0003_about_contact_text.py
- offline/tests.py
- ۵. قرارداد API (نسخهٔ ۱)
- برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای
- ۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی
- tsconfig.json
- ۱۲. سایت `pharmenta.ir` و پنل محتوا
- django_apps
- accounts/services.py
- sw.js
- Command
- CalculatorApiTests
- Command
- pagination.py
- send_password_reset_emails_for_email
- forms_account.py
- PhaseTwoSessionSecurityTests
- ReviewTests
- docker-start.sh
- billing/apps.py
- QuizAccessTests
- .claude/CLAUDE.md
- jalali.ts
- app.config.js
- .mcp.json
- ۳. بک‌اند (Django)
- GatewayPageTests
- downloader.ts
- SiteMaintenanceMiddleware
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
- SessionTokenAuthentication
- UsersPageTests
- AccessTests
- ۴. اپ (Expo — اندروید، iOS و وب)
- GuestSessionView
- ۸. دیپلوی
- Media
- SmsIrBackendTests
- PlanBuilderTests
- progress/admin.py
- oneline
- AlphabeticalArticleList.tsx
- ۱. معرفی و معماری
- ۱۰. مرجع سریع دستورها
- کنسول فروش (`/ops/`)
- django
- 0005_atccode_name_fa.py
- SiteHostMiddleware
- flashcards/admin.py
- EmailOrUsernameBackend
- AccessTests
- DateResult.tsx
- مستندات فارمنتا
- فارمنتا (Pharmenta)

## God Nodes (most connected - your core abstractions)
1. `useTheme()` - 162 edges
2. `AppText()` - 153 edges
3. `useLang()` - 143 edges
4. `PlatformAPIError` - 79 edges
5. `react` - 78 edges
6. `Ingredient` - 68 edges
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
- `ایمپورت از منبع خام (روی لپ‌تاپ)` --references--> `ArticleImage`  [INFERRED]
  docs/07-data.md → backend/apps/medscape/models.py
- `رسانه` --references--> `Media`  [INFERRED]
  docs/12-website.md → backend/apps/website/models.py

## Import Cycles
- None detected.

## Communities (224 total, 98 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.03
Nodes (87): حساب و احراز هویت — `/auth/`, flashcardsApi, guestApi, quizApi, AtcCode, AtcGroup, AuthTokenResponse, BoxSummary (+79 more)

### Community 1 - "django_db"
Cohesion: 0.03
Nodes (50): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+42 more)

### Community 2 - "test_panel.py"
Cohesion: 0.10
Nodes (12): StaffRole, Meta, SiteTestCase, AuthorTests, AuthTests, CommercePagesTests, InboxTests, make_user() (+4 more)

### Community 3 - "console/views.py"
Cohesion: 0.05
Nodes (69): DiscountForm, FeatureEditForm, Meta, FeatureForm, Meta, latin_digits(), parse_amount(), parse_jalali() (+61 more)

### Community 4 - "react"
Cohesion: 0.08
Nodes (63): calculatorsApi, meApi, medscapeApi, MedscapeKind, TopInset, useBleedTop(), SCREEN_TO_TAB, TAB_META (+55 more)

### Community 5 - "Post"
Cohesion: 0.07
Nodes (45): ActivityLog, Meta, Comment, Meta, ContactMessage, Meta, orders(), plans() (+37 more)

### Community 6 - "useTheme"
Cohesion: 0.14
Nodes (75): قابلیت‌ها, قواعد کدنویسی اپ, HelpSheet(), LoadFailed(), AppText(), Card(), iconFor(), IconImage() (+67 more)

### Community 7 - "views_public.py"
Cohesion: 0.05
Nodes (58): Announcement, Meta, Category, Meta, DailyStat, Meta, SiteSettings, Meta (+50 more)

### Community 8 - ".reverse"
Cohesion: 0.08
Nodes (6): AuthenticationSecurityTests, OnboardingTests, wrapper(), render_links(), link(), search()

### Community 9 - "package.json"
Cohesion: 0.03
Nodes (96): زبان، جهت و تم, ساختار `frontend/src/`, شروع اپ, App(), Gate(), main, name, private (+88 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.07
Nodes (33): deck_slugs(), next_topic(), progress_map(), topic_meta(), LeitnerCard, Meta, TopicProgress, Meta (+25 more)

### Community 11 - "calculators/reference_db.py"
Cohesion: 0.08
Nodes (15): export(), load(), Command, dumps(), expected_count(), loads(), record_counts(), rows() (+7 more)

### Community 12 - "billing/views.py"
Cohesion: 0.07
Nodes (33): is_guest(), Order, Meta, CatalogSerializer, CheckoutSerializer, MyAccessSerializer, MyEntitlementSerializer, Meta (+25 more)

### Community 13 - "panel/forms.py"
Cohesion: 0.05
Nodes (30): AnnouncementForm, Meta, CategoryForm, Meta, ContentBlockForm, Meta, DownloadLinkForm, Meta (+22 more)

### Community 14 - "GatewayError"
Cohesion: 0.05
Nodes (14): FakeGateway, GatewayError, get_gateway(), _post_json(), SepGateway, start_payment(), Verification, ZarinpalGateway (+6 more)

### Community 15 - "ImportOpenfdaTests"
Cohesion: 0.07
Nodes (6): AtcSupplementTests, DrugApiTests, ImportOpenfdaTests, LoadAtcReferenceTests, _make_source_db(), ModelTests

### Community 16 - "billing/tests.py"
Cohesion: 0.05
Nodes (29): UsageRecord, Meta, Access, BillingError, check_feature(), content_lock(), effective_features(), take() (+21 more)

### Community 17 - "accounts/permissions.py"
Cohesion: 0.11
Nodes (15): RoleAssignment, Meta, CanManagePlatformRoles, CanViewSecurityAudit, HasPlatformPermission, HasRecentStepUp, RoleAssignmentCreateSerializer, RoleAssignmentRevokeSerializer (+7 more)

### Community 18 - "اپ‌ها (`backend/apps/`)"
Cohesion: 0.09
Nodes (19): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, DiscountCode, Meta (+11 more)

### Community 19 - "django_conf"
Cohesion: 0.09
Nodes (23): OneTimeCode, Meta, account_for_signup(), _hash(), _new_code(), OtpError, request_code(), user_for_phone() (+15 more)

### Community 20 - "accounts/views.py"
Cohesion: 0.10
Nodes (33): AuthTokenResponseSerializer, LoginSerializer, OtpRequestResponseSerializer, OtpRequestSerializer, OtpVerifySerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, PasswordResetResponseSerializer (+25 more)

### Community 21 - "calculators/tests.py"
Cohesion: 0.10
Nodes (11): fix_questions(), fix_results(), renumber_from_one(), _stage_names_without_prefix(), _with_unit(), apply_fixes(), Migration, apply_fixes() (+3 more)

### Community 22 - "website/models.py"
Cohesion: 0.05
Nodes (20): site(), Command, Command, AppRelease, Meta, ContentBlock, Meta, DownloadLink (+12 more)

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.08
Nodes (52): CalculatorErrorCheck, CalculatorResultDef, filled(), num(), useLiveScore(), buildHeuristicSeeds(), cartesian(), classifyResultTone() (+44 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.07
Nodes (36): BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, preview_selection(), best_score_pct_for_topic(), _finished_sessions(), _finished_topic_sessions(), topic_mastery_map() (+28 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.06
Nodes (71): MedscapeBlock, MedscapeSection, countMatches(), FindState, highlight(), ListMarker(), LTR, NumberedHeading() (+63 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.11
Nodes (16): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, _categories_for_generics(), check_interactions(), _conn(), _dir(), _exceptions_for_monographs() (+8 more)

### Community 28 - ".request_code"
Cohesion: 0.17
Nodes (5): CodeRuleTests, PhoneAuthTestCase, ProfileTests, ResetTests, SignUpTests

### Community 29 - "progress/views.py"
Cohesion: 0.10
Nodes (26): Mistake, Meta, DashboardSerializer, FocusRowSerializer, FocusSessionSerializer, MistakeSerializer, Meta, NextChapterSerializer (+18 more)

### Community 30 - "core/views.py"
Cohesion: 0.14
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 31 - "lessons/views.py"
Cohesion: 0.10
Nodes (20): LessonDrugSerializer, get_chapter(), _topic_lookup(), topics_for_chapter(), AtcGroupSerializer, ChapterDrugSerializer, ChapterProgressSerializer, ChapterProgressUpdateSerializer (+12 more)

### Community 33 - "store.ts"
Cohesion: 0.15
Nodes (33): offlineApi, removeOtherBuilds(), closeReaders(), bootOffline(), cancel(), currentUserId(), DatasetState, download() (+25 more)

### Community 34 - "Calculator"
Cohesion: 0.12
Nodes (17): Calculator, Meta, CalculatorCategory, Meta, CalculatorTag, Meta, CalculatorCategorySerializer, Meta (+9 more)

### Community 35 - "data_quality_center/views.py"
Cohesion: 0.05
Nodes (54): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), warning_count(), word_diff(), section_state(), ReviewEvent (+46 more)

### Community 36 - ".post"
Cohesion: 0.12
Nodes (4): AdminTests, MediaTests, PostTests, url()

### Community 37 - "CalculatorDetailScreen.tsx"
Cohesion: 0.13
Nodes (33): describeInputs(), DateInput(), DaysInput(), Field(), QuestionTitle(), CardsFlow(), ChecklistFlow(), flowLayout (+25 more)

### Community 38 - "offline/views.py"
Cohesion: 0.11
Nodes (17): build_matches_dataset(), LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer, PackageFileUrlSerializer, PackageManifestSerializer, PackageUrlsRequestSerializer (+9 more)

### Community 39 - "MaintenancePlanAndApiTests"
Cohesion: 0.09
Nodes (7): Migration, seed(), bump_mistake(), MaintenancePlanAndApiTests, MeApiTests, ProgressServiceTests, ۳c — `apps.flashcards` + `apps.quiz` (ساخته‌شده، پشت فلگ خاموش) ✅

### Community 40 - "Post"
Cohesion: 0.17
Nodes (18): Post, Meta, PostRevision, Meta, _bulk(), _editable(), post_delete(), post_duplicate() (+10 more)

### Community 41 - "Ingredient"
Cohesion: 0.03
Nodes (45): _DryRun, Command, Command, AtcCategory, Meta, AtcCode, Meta, Ingredient (+37 more)

### Community 43 - "sources.ts"
Cohesion: 0.10
Nodes (27): lexicompApi, uptodateApi, LexicompDrug, LexicompInteraction, UptodateImage, cache, checkInteractions(), LexIndex (+19 more)

### Community 44 - "billing/tests.py"
Cohesion: 0.16
Nodes (17): _div(), fa_digits(), format_date(), _jal_cal(), _mod(), month_start(), to_gregorian(), to_jalali() (+9 more)

### Community 45 - "VisitorDay"
Cohesion: 0.20
Nodes (5): VisitorDay, Meta, _unique_series(), UniqueVisitorTests, visit()

### Community 46 - "PurchaseFlowTests"
Cohesion: 0.09
Nodes (3): clear_cache(), _settings_changed(), PurchaseFlowTests

### Community 47 - "pack.py"
Cohesion: 0.06
Nodes (15): Command, derive_key(), new_build_id(), open_sealed(), PackError, read_record(), seal(), secret() (+7 more)

### Community 48 - "drugs/serializers.py"
Cohesion: 0.10
Nodes (14): AtcCodeSerializer, Meta, IngredientDetailSerializer, Meta, IngredientListSerializer, Meta, LessonDrugSectionSerializer, Meta (+6 more)

### Community 49 - "FlashcardApiTests"
Cohesion: 0.11
Nodes (5): FlashcardApiTests, FlashcardLockedTests, _refresh_facts(), _rich_ingredient(), TopicDeckTests

### Community 50 - "LessonTaxonomyTests"
Cohesion: 0.08
Nodes (4): DrugSearchTests, _ingredient(), LessonTaxonomyFallbackTests, LessonTaxonomyTests

### Community 51 - "expo"
Cohesion: 0.06
Nodes (31): backgroundColor, foregroundImage, adaptiveIcon, package, versionCode, projectId, typedRoutes, expo (+23 more)

### Community 52 - "planning.py"
Cohesion: 0.06
Nodes (29): mark_drug_read(), topic_chapters(), topic_progress(), StudyPlan, StudyPlanItem, Meta, complete_item(), ensure_today_items() (+21 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.16
Nodes (7): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label()

### Community 54 - "VerdictResult.tsx"
Cohesion: 0.29
Nodes (24): bandFor(), Explain(), Hero(), Interpretation(), Ltr(), ResultCard(), showTierBar(), TierBar() (+16 more)

### Community 55 - "calculatorModel.ts"
Cohesion: 0.15
Nodes (23): plain(), StagingResult(), allWholeNumbers(), cache, classify(), classifyCalculator(), isNumeric(), LadderRung (+15 more)

### Community 56 - "progress/selectors.py"
Cohesion: 0.14
Nodes (16): due_card_count(), lesson_groups(), _subgroup(), DailyStudy, Meta, dashboard(), _display_name(), _leitner_focus_row() (+8 more)

### Community 57 - "Article"
Cohesion: 0.11
Nodes (14): Command, Article, Meta, ArticleImage, ArticleDetailSerializer, Meta, ArticleImageSerializer, Meta (+6 more)

### Community 58 - "test_phone_auth.py"
Cohesion: 0.16
Nodes (6): InvalidPhone, looks_like_phone(), normalize_phone(), PhoneField, NormalizePhoneTests, _find_user()

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.12
Nodes (16): HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت, دادهٔ مرجع (UpToDate و Lexicomp), دیتابیس، کش و آمادگی, سایت (+8 more)

### Community 60 - "drugs/admin.py"
Cohesion: 0.27
Nodes (5): AtcCategoryAdmin, AtcCodeAdmin, IngredientAdmin, IngredientProfileSectionAdmin, IngredientProfileSectionInline

### Community 61 - "6. Lesson study topics (52)"
Cohesion: 0.06
Nodes (34): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 6. Lesson study topics (52), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups (+26 more)

### Community 62 - "files.ts"
Cohesion: 0.28
Nodes (12): buildDir(), closeHandles(), ensureBuildDir(), handles, partFile(), partPath(), partSize(), readRange() (+4 more)

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "django_utils"
Cohesion: 0.05
Nodes (31): SessionTokenAuthenticationScheme, SessionRefreshToken, Meta, UserSession, Meta, BillingConfig, current(), enabled_gateways() (+23 more)

### Community 65 - "crypto.web.ts"
Cohesion: 0.23
Nodes (9): اجرای کامل با Docker, db(), idb(), keyring, openRecord(), openRecordBase64(), PackageKey, rsaPair() (+1 more)

### Community 66 - "logging"
Cohesion: 0.09
Nodes (6): PlatformTask, retry_delay_seconds(), get_request_id(), JsonFormatter, RequestContextFilter, configure_runtime()

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (24): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+16 more)

### Community 68 - "uptodate/services.py"
Cohesion: 0.15
Nodes (16): article_from_row(), _dir(), get_image(), get_topic(), is_available(), _mysql_conn(), search_topics(), _search_words() (+8 more)

### Community 69 - "dependencies"
Cohesion: 0.05
Nodes (36): dependencies, axios, expo, expo-crypto, expo-file-system, expo-font, @expo-google-fonts/vazirmatn, expo-linear-gradient (+28 more)

### Community 70 - "medscape/tests.py"
Cohesion: 0.27
Nodes (5): _disease_record(), _guideline_record(), ImportMedscapeArticlesTests, _write_diseases_tree(), _write_guidelines()

### Community 71 - "۲. راه‌اندازی محیط توسعه"
Cohesion: 0.17
Nodes (12): اندروید و iOS, اپ (Expo), بک‌اند, تست بستهٔ آفلاین بدون باکت, تست و بررسی, روال کار با مخزن, ساخت دیتابیس و اجرای سرور, نسخهٔ وب (+4 more)

### Community 72 - "panel.js"
Cohesion: 0.16
Nodes (14): buildEditor(), align(), block(), exec(), sync(), toggleSource(), wrapBlock(), filterNav() (+6 more)

### Community 73 - "test_public.py"
Cohesion: 0.06
Nodes (10): Redirect, Meta, Subscriber, Meta, CommentTests, DownloadAndMachineTests, FormsTests, HostRoutingTests (+2 more)

### Community 74 - "LearnerProfile"
Cohesion: 0.11
Nodes (10): LearnerProfile, LearnerProfileSerializer, Meta, OnboardingSerializer, PasswordSetSerializer, UserSerializer, Meta, MeView (+2 more)

### Community 75 - "core/tests.py"
Cohesion: 0.12
Nodes (3): HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests

### Community 76 - "SectionEdit"
Cohesion: 0.27
Nodes (4): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin

### Community 77 - "common.tsx"
Cohesion: 0.19
Nodes (23): Chip(), Collapse(), Extra, Extras(), fmt(), LEVEL_TONES, RichLines(), Tier (+15 more)

### Community 78 - "views_account.py"
Cohesion: 0.10
Nodes (5): active_entitlements(), maintenance_response(), account(), logout_view(), _meta()

### Community 81 - "LessonDetailScreen.tsx"
Cohesion: 0.29
Nodes (11): lessonsApi, LessonSection, joinOpenParens(), LessonBlock, LessonLine, parenDepth(), parseLessonText(), sectionText() (+3 more)

### Community 82 - "ResultProps"
Cohesion: 0.27
Nodes (10): CalculatorDetail, CalculatorQuestion, ResultProps, LIST_FROM, FieldProps, FlowProps, CalculatorAnswers, ComputedResult (+2 more)

### Community 85 - "website_extras.py"
Cohesion: 0.19
Nodes (6): atc_groups(), feature_icon(), nav_on(), person(), split_highlight(), split_lines()

### Community 86 - "clean_profile_boilerplate.py"
Cohesion: 0.23
Nodes (8): clean_text(), Command, is_hypersensitivity_boilerplate(), is_hypersensitivity_boilerplate_en(), is_negative_indication_en(), is_negative_indication_fa(), is_null_placeholder(), _normalize()

### Community 87 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.07
Nodes (17): build.sh script, validate_production_broker(), validate_production_cache(), validate_production_secret_key(), CorsPreflightTests, ProductionSecretKeyTests, DJANGO_SETTINGS_MODULE, release.sh script (+9 more)

### Community 88 - "porter.ts"
Cohesion: 0.23
Nodes (8): firstRule(), isVowelLetter(), porterStem(), Rule, STEP2, STEP3, STEP4, Word

### Community 89 - "storage.py"
Cohesion: 0.14
Nodes (12): Command, cors_rule(), _request(), file_urls(), is_configured(), latest_manifest(), local_dir(), local_file_for_token() (+4 more)

### Community 90 - "ReferenceImportCommand"
Cohesion: 0.11
Nodes (5): Command, ReferenceImportCommand, open_for_import(), Command, Command

### Community 91 - "guest.py"
Cohesion: 0.11
Nodes (17): _applies(), require_atc_content(), _require_content(), require_feature(), require_topic_content(), _first_message(), _message_from_data(), _normalize_code() (+9 more)

### Community 92 - "DrugPageTests"
Cohesion: 0.12
Nodes (3): DrugPageTests, SiteIdentityTests, structured()

### Community 93 - "builders.py"
Cohesion: 0.16
Nodes (10): build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections(), _varints(), pack_json() (+2 more)

### Community 94 - "offline/reader.ts"
Cohesion: 0.14
Nodes (15): Coding Style & Naming Conventions, پایهٔ Django, OfflineDataset, OfflineLicense, OfflineManifest, keyring, openRecord(), openRecordBase64() (+7 more)

### Community 96 - "views_drugs.py"
Cohesion: 0.12
Nodes (11): _build_catalog(), _drop_title(), english_name(), fa_key(), _group_code(), _group_titles(), grouped(), _in_scope() (+3 more)

### Community 97 - "import_calculators.py"
Cohesion: 0.20
Nodes (9): Command, _error_checks_for(), _formula_strings_fa(), _import_categories(), _import_tags(), _questions_for(), _references_for(), _results_for() (+1 more)

### Community 98 - "django_core_management_base"
Cohesion: 0.08
Nodes (8): Command, Command, ensure_title_search_index(), _has_title_search_index(), mysql_config(), _make_snapshot(), MysqlTitleIndexTests, MysqlTitleSearchTests

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

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

### Community 108 - "OfflinePackageCard.tsx"
Cohesion: 0.14
Nodes (23): OfflinePackageInfo, OfflineDownloadButton(), OfflineSheet(), ERROR_TEXT, LOGO, NAME, OfflinePackageCard(), PHASE_TEXT (+15 more)

### Community 109 - "clean_html"
Cohesion: 0.08
Nodes (6): clean_html(), _Cleaner, plain_text(), safe_url(), _Text, SanitizeTests

### Community 110 - "Role"
Cohesion: 0.15
Nodes (8): Role, Meta, RoleSerializer, Meta, ensure_default_learner_role(), PhaseTwoAuthorizationTests, RoleListView, نقش‌ها و رویدادهای امنیتی

### Community 112 - "offline/tests.py"
Cohesion: 0.10
Nodes (10): close_all(), LexicompApiTests, _make_snapshot(), has_paid_plan_with(), is_entitled(), is_guest(), issue_license(), license_days() (+2 more)

### Community 113 - "۵. قرارداد API (نسخهٔ ۱)"
Cohesion: 0.12
Nodes (17): Lexicomp — `/lexicomp/` (ویژگی `lexicomp`), Medscape — `/medscape/` (ویژگی `medscape`), UpToDate — `/uptodate/` (ویژگی `uptodate`), آزمون — `/quiz/` (ویژگی `quiz`؛ پرچم `QUIZ_API_ENABLED`), تغییر دادن API, داروها — `/drugs/` و `/atc/`, دانلود آفلاین — `/offline/`, درس‌نامه — `/lessons/` (ویژگی `lessons`) (+9 more)

### Community 114 - "برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای"
Cohesion: 0.12
Nodes (17): برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی, روش تبدیل پیشنهادها به کلمات کلیدی معتبر, ساخت Analytics از ابتدا, ساخت Search Console از ابتدا, منابع رسمی بررسی‌شده, چک‌لیست انتشار هر صفحه, ۱. نتیجهٔ بررسی واقعی سایت (+9 more)

### Community 115 - "۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی"
Cohesion: 0.12
Nodes (17): اطلاعات غیرمحرمانه‌ای که باید جایی ثبت باشد, بازیابی, بکاپ و بازیابی, حساب‌های سرویس, رازها و چیزهایی که باید امن نگه داشته شوند, رازهای فنی, شاخص‌هایی که مرتب دیده شوند, عیب‌یابی (+9 more)

### Community 116 - "tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, paths, strict, extends, include, expo/tsconfig.base

### Community 117 - "۱۲. سایت `pharmenta.ir` و پنل محتوا"
Cohesion: 0.18
Nodes (11): not_found(), آمار بازدید, حساب و خرید روی سایت, دارونامهٔ عمومی (`/drugs/`), رسانه, ساختار کد, صفحه‌های عمومی, محتوای شروع (+3 more)

### Community 119 - "accounts/services.py"
Cohesion: 0.17
Nodes (19): SecurityAuditEvent, Meta, assign_platform_role(), hash_session_token(), issue_user_session(), IssuedSession, _new_token(), record_security_event() (+11 more)

### Community 120 - "sw.js"
Cohesion: 0.38
Nodes (4): inScope(), referencedFiles(), SCOPE, storeShell()

### Community 123 - "Command"
Cohesion: 0.21
Nodes (4): Command, _int(), _json_list(), _name_fa()

### Community 125 - "send_password_reset_emails_for_email"
Cohesion: 0.15
Nodes (5): password_reset_url_for_user(), send_password_reset_email(), send_password_reset_emails_for_email(), send_password_reset_email_task(), enqueue()

### Community 126 - "forms_account.py"
Cohesion: 0.22
Nodes (5): AccountForm, CodeForm, LoginForm, PasswordForm, PhoneForm

### Community 134 - "jalali.ts"
Cohesion: 0.47
Nodes (11): BREAKS, d2g(), d2j(), div(), g2d(), isValidJalali(), j2d(), jalCal() (+3 more)

### Community 182 - "۳. بک‌اند (Django)"
Cohesion: 0.25
Nodes (8): UpToDate و Lexicomp, افزودن یک قابلیت فروشی تازه, بستهٔ آفلاین (`apps.offline`), صورتحساب و دسترسی (`apps.billing`), قواعد مشترک API, قواعد کدنویسی بک‌اند, کار پس‌زمینه, ۳. بک‌اند (Django)

### Community 184 - "downloader.ts"
Cohesion: 0.20
Nodes (6): downloader, DownloadEvents, PartJob, PartRef, tasks, @kesha-antonov/react-native-background-downloader

### Community 185 - "SiteMaintenanceMiddleware"
Cohesion: 0.22
Nodes (4): RequestIdMiddleware, SiteMaintenanceMiddleware, زنجیرهٔ middleware, پیکربندی (`backend/config/`)

### Community 196 - "SessionTokenAuthentication"
Cohesion: 0.25
Nodes (5): SessionTokenAuthentication, احراز هویت و حساب, ثبت‌نام و ورود, رمز عبور, نشست و توکن

### Community 202 - "۴. اپ (Expo — اندروید، iOS و وب)"
Cohesion: 0.29
Nodes (8): ارتباط با API و کش, افزودن صفحهٔ تازه, دانلود آفلاین (`src/offline/`), ناوبری, وب‌اپ و PWA, پیکربندی اپ بومی, ۴. اپ (Expo — اندروید، iOS و وب), ScreenKey

### Community 204 - "۸. دیپلوی"
Cohesion: 0.18
Nodes (11): CI, اپ اندروید و iOS, برگرداندن یک دیپلوی خراب, بک‌اند, جریان دیپلوی, راه‌اندازی از صفر (یک بار), سرویس‌های رانفلر, وب‌اپ (+3 more)

### Community 208 - "progress/admin.py"
Cohesion: 0.53
Nodes (4): DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin

### Community 209 - "oneline"
Cohesion: 0.33
Nodes (5): oneline(), آنچه کد انجام می‌دهد, سئو, محتوای اولیه: `seed_seo_content`, کارهای Search Console بعد از هر تغییر بزرگ

### Community 210 - "AlphabeticalArticleList.tsx"
Cohesion: 0.47
Nodes (5): ALPHABET, AlphabeticalArticleList(), buildOffsets(), groupAlphabetically(), Section

### Community 211 - "۱. معرفی و معماری"
Cohesion: 0.25
Nodes (8): دامنه‌ها و سرویس‌ها, ذخیره‌گاه‌های داده, ساختار مخزن, سرویس‌های بیرونی, فناوری‌ها, محصول, معماری, ۱. معرفی و معماری

### Community 212 - "۱۰. مرجع سریع دستورها"
Cohesion: 0.25
Nodes (8): اپ موبایل (EAS), تست و بررسی, توسعهٔ محلی, دستورهای مدیریتی Django (همه), دیپلوی و گیت, عیب‌یابی, پایپلاین study_content (بیرون از مخزن), ۱۰. مرجع سریع دستورها

### Community 213 - "کنسول فروش (`/ops/`)"
Cohesion: 0.22
Nodes (9): ادمین Django (`/admin/`), درگاه پرداخت و کلیدهای فروش, دسترسی مهمان, مرکز کیفیت داده (`/ops/data-quality/`), ویژگی‌ها, پلن‌ها و محصول‌ها, کاربران, کنسول فروش (`/ops/`) (+1 more)

### Community 224 - "DateResult.tsx"
Cohesion: 0.48
Nodes (6): hasPersian(), Rows(), DateResult(), useDateFormat(), parseAge(), parseDateText()

### Community 226 - "مستندات فارمنتا"
Cohesion: 0.50
Nodes (4): سندهای دیگر مخزن, فهرست, قرارداد نگهداری این مستندات, مستندات فارمنتا

### Community 230 - "فارمنتا (Pharmenta)"
Cohesion: 0.67
Nodes (3): شروع سریع, فارمنتا (Pharmenta), مستندات

## Knowledge Gaps
- **8 isolated node(s):** `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-splash-screen`, `react-dom`, `react-native-web` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1503 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **98 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `package.json` to `django_utils`, `useTheme`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.152) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `PlatformAPIError` (e.g. with `LoginView` and `OtpVerifyView`) actually correct?**
  _`PlatformAPIError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-splash-screen` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.034868421052631576 - nodes in this community are weakly interconnected._
- **Why does `UserSession` connect `django_utils` to `console/views.py`, `SessionTokenAuthentication`, `WebsiteAuthTests`, `package.json`, `LearnerProfile`, `accounts/views.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`, `accounts/services.py`, `test_phone_auth.py`, `.request_code`, `PhaseTwoSessionSecurityTests`?**
  _High betweenness centrality (0.147) - this node is a cross-community bridge._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.025688073394495414 - nodes in this community are weakly interconnected._
- **Why does `اپ‌ها (`backend/apps/`)` connect `django_utils` to `test_panel.py`, `console/views.py`, `views_public.py`, `flashcards/views.py`, `billing/views.py`, `billing/tests.py`, `accounts/permissions.py`, `اپ‌ها (`backend/apps/`)`, `django_conf`, `website/models.py`, `quiz/views.py`, `Calculator`, `data_quality_center/views.py`, `Post`, `Ingredient`, `۳. بک‌اند (Django)`, `progress/selectors.py`, `Article`, `Media`, `Role`, `accounts/services.py`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._