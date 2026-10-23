# Graph Report - Learning Platform  (2026-10-23)

## Corpus Check
- 486 files · ~386,764 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 32 file(s) not represented in the graph (top: (none) 11, .ttf 7, .woff2 4)

## Summary
- 4601 nodes · 12953 edges · 194 communities (114 shown, 80 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1199 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fa027c47`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- api/types.ts
- django_db
- django_utils
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
- clear_cache
- Command
- store.ts
- Calculator
- data_quality_center/services.py
- console/forms.py
- CalculatorDetailScreen.tsx
- offline/views.py
- PaymentGateway
- data_quality_center/views.py
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
- progress/tests.py
- Article
- views_account.py
- ۶. پیکربندی و متغیرهای محیطی
- IngredientProfileSection
- 6. Lesson study topics (52)
- files.ts
- throttling.py
- config.py
- crypto.web.ts
- logging
- ۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین
- uptodate/services.py
- dependencies
- medscape/tests.py
- ۲. راه‌اندازی محیط توسعه
- panel.js
- DownloadAndMachineTests
- LearnerProfile
- core/tests.py
- SectionEdit
- common.tsx
- data_quality_center/tests.py
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
- PlanSerializer
- offline/reader.ts
- docs/README.md
- session.ts
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
- _Cleaner
- 0003_about_contact_text.py
- django_conf
- ۵. قرارداد API (نسخهٔ ۱)
- ۹. نگهداری: مانیتورینگ، بکاپ، رازها و عیب‌یابی
- tsconfig.json
- ۱۲. سایت `pharmenta.ir` و پنل محتوا
- django_apps
- accounts/services.py
- sw.js
- Command
- CalculatorApiTests
- pagination.py
- docker-start.sh
- billing/apps.py
- .claude/CLAUDE.md
- app.config.js
- .mcp.json
- SiteHostMiddleware
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
- `۳a — جدول مرجع ATC + `apps.lessons` ✅` --references--> `AtcCategory`  [INFERRED]
  PHASES.md → backend/apps/drugs/models.py
- `ایمپورت از منبع خام (روی لپ‌تاپ)` --references--> `ArticleImage`  [INFERRED]
  docs/07-data.md → backend/apps/medscape/models.py

## Import Cycles
- None detected.

## Communities (194 total, 80 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.04
Nodes (74): حساب و احراز هویت — `/auth/`, flashcardsApi, guestApi, quizApi, AtcCode, AtcGroup, AuthTokenResponse, BoxSummary (+66 more)

### Community 1 - "django_db"
Cohesion: 0.02
Nodes (51): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+43 more)

### Community 2 - "django_utils"
Cohesion: 0.05
Nodes (19): StaffRole, Meta, SiteTestCase, AdminTests, AuthorTests, AuthTests, CommercePagesTests, InboxTests (+11 more)

### Community 3 - "console/views.py"
Cohesion: 0.07
Nodes (56): FeatureEditForm, Meta, PlanBasicsForm, Meta, access(), _active_entitlements_qs(), _active_q(), audit() (+48 more)

### Community 4 - "react"
Cohesion: 0.07
Nodes (70): authApi, calculatorsApi, meApi, medscapeApi, ALPHABET, AlphabeticalArticleList(), buildOffsets(), groupAlphabetically() (+62 more)

### Community 5 - "Post"
Cohesion: 0.05
Nodes (62): maintenance_response(), ActivityLog, Meta, Comment, Meta, ContactMessage, Meta, PostRevision (+54 more)

### Community 6 - "useTheme"
Cohesion: 0.10
Nodes (93): قابلیت‌ها, ساختار `frontend/src/`, SectionTone, BottomNav(), HelpSheet(), LoadFailed(), AppText(), Button() (+85 more)

### Community 7 - "views_public.py"
Cohesion: 0.05
Nodes (58): site(), SiteMaintenanceMiddleware, DailyStat, Meta, SiteSettings, Meta, plans(), article() (+50 more)

### Community 8 - ".reverse"
Cohesion: 0.05
Nodes (10): AuthenticationSecurityTests, OnboardingTests, wrapper(), GatewayPageTests, PlanBuilderTests, UsersPageTests, AccessTests, render_links() (+2 more)

### Community 9 - "package.json"
Cohesion: 0.03
Nodes (87): ارتباط با API و کش, افزودن صفحهٔ تازه, دانلود آفلاین (`src/offline/`), زبان، جهت و تم, شروع اپ, قواعد کدنویسی اپ, ناوبری, وب‌اپ و PWA (+79 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.06
Nodes (38): _applies(), require_atc_content(), _require_content(), require_feature(), require_topic_content(), deck_slugs(), next_topic(), progress_map() (+30 more)

### Community 11 - "calculators/reference_db.py"
Cohesion: 0.06
Nodes (17): Command, export(), load(), Command, _DryRun, dumps(), expected_count(), loads() (+9 more)

### Community 12 - "billing/views.py"
Cohesion: 0.07
Nodes (34): is_guest(), Order, Meta, CatalogSerializer, CheckoutSerializer, MyAccessSerializer, MyFeatureSerializer, OrderSerializer (+26 more)

### Community 13 - "panel/forms.py"
Cohesion: 0.04
Nodes (22): Media, Meta, AnnouncementForm, Meta, MediaMetaForm, Meta, PageForm, Meta (+14 more)

### Community 14 - "GatewayError"
Cohesion: 0.06
Nodes (12): FakeGateway, GatewayError, get_gateway(), SepGateway, start_payment(), Verification, ZarinpalGateway, ZibalGateway (+4 more)

### Community 15 - "ImportOpenfdaTests"
Cohesion: 0.05
Nodes (10): Command, _int(), _json_list(), _name_fa(), AtcSupplementTests, DrugApiTests, ImportOpenfdaTests, LoadAtcReferenceTests (+2 more)

### Community 16 - "billing/tests.py"
Cohesion: 0.05
Nodes (26): Entitlement, Meta, MyEntitlementSerializer, Meta, Access, active_entitlements(), check_feature(), content_lock() (+18 more)

### Community 17 - "accounts/permissions.py"
Cohesion: 0.16
Nodes (10): CanManagePlatformRoles, CanViewSecurityAudit, HasPlatformPermission, HasRecentStepUp, RoleAssignmentCreateSerializer, RoleAssignmentSerializer, Meta, session_has_recent_step_up() (+2 more)

### Community 18 - "اپ‌ها (`backend/apps/`)"
Cohesion: 0.06
Nodes (25): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, AdminAction, Meta (+17 more)

### Community 19 - "django_conf"
Cohesion: 0.11
Nodes (15): account_for_signup(), _hash(), _new_code(), OtpError, request_code(), user_for_phone(), verify_code(), ensure_default_learner_role() (+7 more)

### Community 20 - "accounts/views.py"
Cohesion: 0.07
Nodes (41): AuthTokenResponseSerializer, LoginSerializer, OtpRequestResponseSerializer, OtpRequestSerializer, OtpVerifySerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, PasswordResetResponseSerializer (+33 more)

### Community 21 - "calculators/tests.py"
Cohesion: 0.10
Nodes (11): fix_questions(), fix_results(), renumber_from_one(), _stage_names_without_prefix(), _with_unit(), apply_fixes(), Migration, apply_fixes() (+3 more)

### Community 22 - "website/models.py"
Cohesion: 0.03
Nodes (48): Command, Command, AppRelease, Meta, Category, Meta, ContentBlock, Meta (+40 more)

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.08
Nodes (52): CalculatorErrorCheck, CalculatorResultDef, filled(), num(), useLiveScore(), buildHeuristicSeeds(), cartesian(), classifyResultTone() (+44 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.05
Nodes (42): slugs_for_topic(), BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, ingredient_ids_for_selection(), preview_selection(), sample_bank_questions(), _sample_rows() (+34 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.06
Nodes (60): MedscapeBlock, MedscapeSection, countMatches(), FindState, highlight(), ListMarker(), LTR, NumberedHeading() (+52 more)

### Community 27 - "lexicomp/services.py"
Cohesion: 0.08
Nodes (18): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, _categories_for_generics(), check_interactions(), close_all(), _conn(), _dir() (+10 more)

### Community 28 - ".request_code"
Cohesion: 0.07
Nodes (23): CodeRuleTests, PhoneAuthTestCase, ProfileTests, ResetTests, SignUpTests, SmsIrBackendTests, برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی (+15 more)

### Community 29 - "progress/views.py"
Cohesion: 0.07
Nodes (36): topic_progress(), DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin, Mistake, Meta, StudyPlan (+28 more)

### Community 30 - "core/views.py"
Cohesion: 0.14
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 31 - "clear_cache"
Cohesion: 0.12
Nodes (4): clear_cache(), _settings_changed(), GuestAccessTests, GuestConsoleTests

### Community 33 - "store.ts"
Cohesion: 0.12
Nodes (40): offlineApi, OfflinePackageInfo, closeReaders(), localReader(), bootOffline(), cancel(), currentUserId(), DatasetState (+32 more)

### Community 34 - "Calculator"
Cohesion: 0.15
Nodes (13): Calculator, Meta, CalculatorCategory, Meta, CalculatorCategorySerializer, Meta, CalculatorDetailSerializer, Meta (+5 more)

### Community 35 - "data_quality_center/services.py"
Cohesion: 0.10
Nodes (22): ReviewEvent, Meta, SectionEditRequest, Meta, approve(), _clean(), _client_ip(), _close() (+14 more)

### Community 36 - "console/forms.py"
Cohesion: 0.17
Nodes (6): DiscountForm, FeatureForm, Meta, latin_digits(), parse_amount(), parse_jalali()

### Community 37 - "CalculatorDetailScreen.tsx"
Cohesion: 0.10
Nodes (46): describeInputs(), DateInput(), DaysInput(), Field(), QuestionTitle(), CardsFlow(), ChecklistFlow(), flowLayout (+38 more)

### Community 38 - "offline/views.py"
Cohesion: 0.08
Nodes (24): build_matches_dataset(), LicenseRequestSerializer, LicenseSerializer, OfflinePackageSerializer, PackageFileSerializer, PackageFileUrlSerializer, PackageManifestSerializer, PackageUrlsRequestSerializer (+16 more)

### Community 39 - "PaymentGateway"
Cohesion: 0.17
Nodes (10): gateway(), gateway_edit(), _gateway_facts(), _gateway_state(), _masked(), _site_callback(), _site_url(), _tristate() (+2 more)

### Community 40 - "data_quality_center/views.py"
Cohesion: 0.12
Nodes (25): warning_count(), section_state(), _diffs(), discard(), history(), _login_key(), login_view(), logout_view() (+17 more)

### Community 41 - "Ingredient"
Cohesion: 0.03
Nodes (50): AtcCategoryAdmin, AtcCodeAdmin, IngredientAdmin, IngredientProfileSectionAdmin, Command, Command, AtcCategory, Meta (+42 more)

### Community 42 - "QuizApiTests"
Cohesion: 0.09
Nodes (3): QuizAccessTests, QuizApiTests, QuizLockedTests

### Community 43 - "sources.ts"
Cohesion: 0.08
Nodes (30): Coding Style & Naming Conventions, پایهٔ Django, lexicompApi, uptodateApi, LexicompDrug, LexicompInteraction, UptodateArticle, UptodateImage (+22 more)

### Community 44 - "billing/tests.py"
Cohesion: 0.16
Nodes (16): _div(), fa_digits(), format_date(), _jal_cal(), _mod(), month_start(), to_gregorian(), to_jalali() (+8 more)

### Community 45 - "VisitorDay"
Cohesion: 0.24
Nodes (4): VisitorDay, Meta, UniqueVisitorTests, visit()

### Community 47 - "pack.py"
Cohesion: 0.06
Nodes (24): build_lexicomp(), build_uptodate(), _info_version(), _porter_terms(), _ro(), _top_sections(), _varints(), Command (+16 more)

### Community 48 - "drugs/serializers.py"
Cohesion: 0.12
Nodes (11): AtcCodeSerializer, Meta, IngredientDetailSerializer, Meta, IngredientListSerializer, Meta, LessonDrugSerializer, LessonSectionSerializer (+3 more)

### Community 49 - "FlashcardApiTests"
Cohesion: 0.07
Nodes (10): FlashcardFactAdmin, LeitnerCardAdmin, FlashcardFact, Meta, FlashcardApiTests, FlashcardLockedTests, _refresh_facts(), _rich_ingredient() (+2 more)

### Community 50 - "LessonTaxonomyTests"
Cohesion: 0.08
Nodes (4): DrugSearchTests, _ingredient(), LessonTaxonomyFallbackTests, LessonTaxonomyTests

### Community 51 - "expo"
Cohesion: 0.06
Nodes (31): backgroundColor, foregroundImage, adaptiveIcon, package, versionCode, projectId, typedRoutes, expo (+23 more)

### Community 52 - "planning.py"
Cohesion: 0.05
Nodes (26): ChapterProgress, Meta, mark_drug_read(), ensure_today_items(), _flashcard_recall_for_slugs(), _flatten(), _goal_items(), _groups_by_topic() (+18 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.16
Nodes (7): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label()

### Community 54 - "VerdictResult.tsx"
Cohesion: 0.29
Nodes (24): bandFor(), Explain(), Hero(), Interpretation(), Ltr(), ResultCard(), showTierBar(), TierBar() (+16 more)

### Community 55 - "calculatorModel.ts"
Cohesion: 0.15
Nodes (23): plain(), StagingResult(), allWholeNumbers(), cache, classify(), classifyCalculator(), isNumeric(), LadderRung (+15 more)

### Community 56 - "progress/tests.py"
Cohesion: 0.06
Nodes (25): Migration, seed(), due_card_count(), DailyStudy, Meta, LearnerProgress, dashboard(), _display_name() (+17 more)

### Community 57 - "Article"
Cohesion: 0.13
Nodes (13): Article, Meta, ArticleImage, ArticleDetailSerializer, Meta, ArticleImageSerializer, Meta, ArticleListSerializer (+5 more)

### Community 58 - "views_account.py"
Cohesion: 0.06
Nodes (25): EmailOrUsernameBackend, OneTimeCode, Meta, InvalidPhone, looks_like_phone(), normalize_phone(), PhoneField, NormalizePhoneTests (+17 more)

### Community 59 - "۶. پیکربندی و متغیرهای محیطی"
Cohesion: 0.12
Nodes (16): HTTPS، CORS و CSRF, اپ (فرانت‌اند), ایمیل, بستهٔ آفلاین, حساب و احراز هویت, دادهٔ مرجع (UpToDate و Lexicomp), دیتابیس، کش و آمادگی, سایت (+8 more)

### Community 60 - "IngredientProfileSection"
Cohesion: 0.15
Nodes (7): IngredientProfileSectionInline, IngredientProfileSection, Meta, LessonDrugSectionSerializer, Meta, ProfileSectionSerializer, Meta

### Community 61 - "6. Lesson study topics (52)"
Cohesion: 0.06
Nodes (34): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 6. Lesson study topics (52), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups (+26 more)

### Community 62 - "files.ts"
Cohesion: 0.13
Nodes (19): downloader, DownloadEvents, PartJob, PartRef, tasks, buildDir(), closeHandles(), ensureBuildDir() (+11 more)

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "config.py"
Cohesion: 0.10
Nodes (13): BillingConfig, current(), enabled_gateways(), gateway_spec(), _gateways(), GatewaySpec, _load(), row() (+5 more)

### Community 65 - "crypto.web.ts"
Cohesion: 0.21
Nodes (10): اجرای کامل با Docker, OfflineLicense, db(), idb(), keyring, openRecord(), openRecordBase64(), PackageKey (+2 more)

### Community 66 - "logging"
Cohesion: 0.06
Nodes (11): password_reset_url_for_user(), send_password_reset_email(), send_password_reset_emails_for_email(), send_password_reset_email_task(), PlatformTask, retry_delay_seconds(), get_request_id(), JsonFormatter (+3 more)

### Community 67 - "۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین"
Cohesion: 0.08
Nodes (24): `apply_atc_supplement`, `clean_profile_boilerplate`, CORS و بررسی باکت, `ensure_uptodate_search_index`, `import_openfda`, Lexicomp, `migrate_uptodate_to_mysql`, UpToDate (+16 more)

### Community 68 - "uptodate/services.py"
Cohesion: 0.13
Nodes (17): article_from_row(), _dir(), get_image(), get_topic(), is_available(), _mysql_conn(), search_topics(), _search_words() (+9 more)

### Community 69 - "dependencies"
Cohesion: 0.06
Nodes (33): dependencies, axios, expo, expo-crypto, expo-file-system, expo-font, @expo-google-fonts/vazirmatn, expo-linear-gradient (+25 more)

### Community 70 - "medscape/tests.py"
Cohesion: 0.27
Nodes (5): _disease_record(), _guideline_record(), ImportMedscapeArticlesTests, _write_diseases_tree(), _write_guidelines()

### Community 71 - "۲. راه‌اندازی محیط توسعه"
Cohesion: 0.17
Nodes (12): اندروید و iOS, اپ (Expo), بک‌اند, تست بستهٔ آفلاین بدون باکت, تست و بررسی, روال کار با مخزن, ساخت دیتابیس و اجرای سرور, نسخهٔ وب (+4 more)

### Community 72 - "panel.js"
Cohesion: 0.16
Nodes (14): buildEditor(), align(), block(), exec(), sync(), toggleSource(), wrapBlock(), filterNav() (+6 more)

### Community 73 - "DownloadAndMachineTests"
Cohesion: 0.07
Nodes (9): Announcement, Meta, Post, Meta, search(), plain_text(), DownloadAndMachineTests, make_post() (+1 more)

### Community 74 - "LearnerProfile"
Cohesion: 0.13
Nodes (9): LearnerProfile, LearnerProfileSerializer, Meta, OnboardingSerializer, UserSerializer, Meta, active_role_keys(), MeView (+1 more)

### Community 75 - "core/tests.py"
Cohesion: 0.15
Nodes (3): HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests

### Community 76 - "SectionEdit"
Cohesion: 0.16
Nodes (6): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin, SectionEdit, Meta

### Community 77 - "common.tsx"
Cohesion: 0.19
Nodes (23): Chip(), Collapse(), Extra, Extras(), fmt(), LEVEL_TONES, RichLines(), Tier (+15 more)

### Community 78 - "data_quality_center/tests.py"
Cohesion: 0.24
Nodes (6): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), word_diff(), CheckTests

### Community 79 - "ConsoleTestCase"
Cohesion: 0.15
Nodes (3): ConsoleTestCase, DraftAndSubmitTests, ReviewTests

### Community 81 - "LessonDetailScreen.tsx"
Cohesion: 0.33
Nodes (10): lessonsApi, joinOpenParens(), LessonBlock, LessonLine, parenDepth(), parseLessonText(), sectionText(), splitIssues() (+2 more)

### Community 82 - "ResultProps"
Cohesion: 0.27
Nodes (10): CalculatorDetail, CalculatorQuestion, ResultProps, LIST_FROM, FieldProps, FlowProps, CalculatorAnswers, ComputedResult (+2 more)

### Community 85 - "website_extras.py"
Cohesion: 0.15
Nodes (8): atc_groups(), feature_icon(), nav_on(), oneline(), person(), split_highlight(), split_lines(), آنچه کد انجام می‌دهد

### Community 86 - "clean_profile_boilerplate.py"
Cohesion: 0.23
Nodes (8): clean_text(), Command, is_hypersensitivity_boilerplate(), is_hypersensitivity_boilerplate_en(), is_negative_indication_en(), is_negative_indication_fa(), is_null_placeholder(), _normalize()

### Community 87 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.05
Nodes (18): build.sh script, validate_production_broker(), validate_production_cache(), validate_production_secret_key(), CorsPreflightTests, ProductionSecretKeyTests, DJANGO_SETTINGS_MODULE, release.sh script (+10 more)

### Community 88 - "porter.ts"
Cohesion: 0.23
Nodes (8): firstRule(), isVowelLetter(), porterStem(), Rule, STEP2, STEP3, STEP4, Word

### Community 89 - "storage.py"
Cohesion: 0.09
Nodes (15): _post_json(), ReviewForm, SectionEditForm, Command, cors_rule(), _request(), file_urls(), is_configured() (+7 more)

### Community 90 - "ReferenceImportCommand"
Cohesion: 0.15
Nodes (4): ReferenceImportCommand, open_for_import(), Command, Command

### Community 91 - "guest.py"
Cohesion: 0.09
Nodes (18): create_guest(), end_guest_sessions(), guests(), GuestSessionView, GuestStatusView, GuestAccount, _first_message(), _message_from_data() (+10 more)

### Community 92 - "DrugPageTests"
Cohesion: 0.12
Nodes (3): DrugPageTests, SiteIdentityTests, structured()

### Community 93 - "PlanSerializer"
Cohesion: 0.29
Nodes (5): PlanFeatureItemSerializer, PlanPriceSerializer, Meta, PlanSerializer, Meta

### Community 94 - "offline/reader.ts"
Cohesion: 0.20
Nodes (11): OfflineDataset, OfflineManifest, keyring, openRecord(), openRecordBase64(), PackageKey, sealed(), Locator (+3 more)

### Community 96 - "session.ts"
Cohesion: 0.29
Nodes (5): get(), KEYS, sessionStore, StoredSession, expo-secure-store

### Community 97 - "import_calculators.py"
Cohesion: 0.20
Nodes (9): Command, _error_checks_for(), _formula_strings_fa(), _import_categories(), _import_tags(), _questions_for(), _references_for(), _results_for() (+1 more)

### Community 98 - "django_core_management_base"
Cohesion: 0.09
Nodes (7): Command, Command, ensure_title_search_index(), _has_title_search_index(), mysql_config(), MysqlTitleIndexTests, MysqlTitleSearchTests

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
Cohesion: 0.12
Nodes (30): OfflineDownloadButton(), OfflineSheet(), ERROR_TEXT, LOGO, NAME, OfflinePackageCard(), PHASE_TEXT, canGoBack() (+22 more)

### Community 112 - "django_conf"
Cohesion: 0.15
Nodes (3): writing(), _make_snapshot(), _make_snapshot()

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

### Community 119 - "accounts/services.py"
Cohesion: 0.06
Nodes (32): SessionTokenAuthentication, SessionTokenAuthenticationScheme, Role, Meta, RoleAssignment, Meta, SecurityAuditEvent, Meta (+24 more)

### Community 120 - "sw.js"
Cohesion: 0.38
Nodes (4): inScope(), referencedFiles(), SCOPE, storeShell()

### Community 122 - "CalculatorApiTests"
Cohesion: 0.13
Nodes (5): CalculatorTag, Meta, CalculatorTagSerializer, Meta, CalculatorApiTests

### Community 182 - "SiteHostMiddleware"
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
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1502 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **80 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `useTheme` to `package.json`, `accounts/services.py`, `react`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `PlatformAPIError` (e.g. with `LoginView` and `OtpVerifyView`) actually correct?**
  _`PlatformAPIError` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-splash-screen` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.0393028024606972 - nodes in this community are weakly interconnected._
- **Why does `UserSession` connect `accounts/services.py` to `console/views.py`, `WebsiteAuthTests`, `useTheme`, `django_conf`, `اپ‌ها (`backend/apps/`)`, `accounts/views.py`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`, `views_account.py`, `guest.py`, `.request_code`, `clear_cache`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.021891010712622262 - nodes in this community are weakly interconnected._
- **Why does `اپ‌ها (`backend/apps/`)` connect `اپ‌ها (`backend/apps/`)` to `django_utils`, `console/views.py`, `views_public.py`, `flashcards/views.py`, `billing/views.py`, `panel/forms.py`, `billing/tests.py`, `website/models.py`, `quiz/views.py`, `Calculator`, `data_quality_center/services.py`, `PaymentGateway`, `Ingredient`, `FlashcardApiTests`, `planning.py`, `SiteHostMiddleware`, `progress/tests.py`, `Article`, `views_account.py`, `IngredientProfileSection`, `config.py`, `DownloadAndMachineTests`, `SectionEdit`, `guest.py`, `accounts/services.py`, `CalculatorApiTests`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._