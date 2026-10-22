# Graph Report - Learning Platform  (2026-10-22)

## Corpus Check
- 439 files · ~397,057 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 27 file(s) not represented in the graph (top: (none) 11, .ttf 7, .example 2)

## Summary
- 4022 nodes · 11350 edges · 182 communities (105 shown, 77 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 1048 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ee24605d`
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
- Article
- billing/views.py
- panel/forms.py
- GatewayError
- progress/tests.py
- Feature
- accounts/services.py
- billing/models.py
- views_account.py
- PlatformAPIError
- calculators/tests.py
- website/models.py
- calculatorEngine.ts
- django_apps
- quiz/views.py
- MedscapeArticleScreen.tsx
- lexicomp/views.py
- .request_code
- progress/views.py
- json
- LearnerProfile
- accounts/serializers.py
- Ingredient
- Calculator
- data_quality_center/services.py
- clean_html
- CalculatorDetailScreen.tsx
- accounts/views.py
- lessons/views.py
- data_quality_center/views.py
- lessons/selectors.py
- QuizApiTests
- UptodateArticleScreen.tsx
- billing/tests.py
- panel/views.py
- PurchaseFlowTests
- Mistake
- drugs/serializers.py
- LeitnerCard
- LessonTaxonomyTests
- expo
- planning.py
- import_medscape_articles.py
- VerdictResult.tsx
- config.py
- record_study
- core/views.py
- IngredientProfileSection
- common.tsx
- import_openfda.py
- 6. Lesson study topics (52)
- ResultCard
- throttling.py
- mark_drug_read
- دستورهای ایمپورت، اکسپورت و دیتابیس
- sms.py
- migrate_uptodate_to_mysql.py
- uptodate/services.py
- dependencies
- medscape/tests.py
- calculatorModel.ts
- panel.js
- DownloadAndMachineTests
- import_calculators.py
- core/tests.py
- SectionEdit
- برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای
- data_quality_center/tests.py
- ConsoleTestCase
- StudyTopicsCoverageTests
- uptodate/views.py
- WebsiteAuthTests
- UptodateTests
- ReferenceDbTests
- dqc_extras.py
- clean_profile_boilerplate.py
- PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa
- MedscapeApiTests
- website_extras.py
- ReviewTests
- _snippet
- mastery_selectors.py
- settings/base.py
- production.py
- سایت و بلاگ (pharmenta.ir) و پنل مدیریت
- jalali.ts
- send_password_reset_emails_for_email
- Command
- site.js
- LessonDetailScreen.tsx
- logging.py
- ImportOpenfdaTests
- website/__init__.py
- Section
- back.ts
- Pharmexa
- Repository Guidelines
- PlanSerializer
- _card_back_fields
- MaintenancePlanAndApiTests
- maintenance_urls.py
- uptodate/tests.py
- HostRoutingTests
- scripts
- tsconfig.json
- bootstrap_superuser.py
- RegisterSerializer
- Deploying the backend on Runflare (single container, no Redis)
- SessionSerializer
- Command
- 0005_atccode_name_fa.py
- QuizQuestionSerializer
- pagination.py
- data_quality_center/forms.py
- 0004_clear_rule_based_facts.py
- 0007_clear_rule_based_bank.py
- SiteHostMiddleware
- docker-start.sh
- ۴. نگهداری دادهٔ داروها
- CLAUDE.md
- .claude/CLAUDE.md
- study-content.md
- app.config.js
- .mcp.json

## God Nodes (most connected - your core abstractions)
1. `useTheme()` - 154 edges
2. `AppText()` - 146 edges
3. `useLang()` - 133 edges
4. `react` - 73 edges
5. `PlatformAPIError` - 71 edges
6. `react-native` - 64 edges
7. `Ingredient` - 63 edges
8. `useNav` - 56 edges
9. `LoadingState()` - 51 edges
10. `Post` - 48 edges

## Surprising Connections (you probably didn't know these)
- `فاز ۰.۵ — حذف زیرساخت رهاشده ✅` --references--> `UserSession`  [INFERRED]
  PHASES.md → backend/apps/accounts/models.py
- `۳d — بازنویسی `data_quality_center` ✅` --references--> `SectionEdit`  [INFERRED]
  PHASES.md → backend/apps/data_quality_center/models.py
- ``load_atc_reference`` --references--> `AtcCategory`  [INFERRED]
  docs/data-commands.md → backend/apps/drugs/models.py
- `۳a — جدول مرجع ATC + `apps.lessons` ✅` --references--> `AtcCategory`  [INFERRED]
  PHASES.md → backend/apps/drugs/models.py
- ``GET /lessons/chapters/{atc_code}/` — one chapter (ATC L2 subgroup)` --references--> `ReadDrug`  [INFERRED]
  docs/api-contract.md → backend/apps/lessons/models.py

## Import Cycles
- None detected.

## Communities (182 total, 77 thin omitted)

### Community 0 - "api/types.ts"
Cohesion: 0.03
Nodes (101): Auth & onboarding, API_BASE_URL, apiClient, ApiError, ApiErrorBody, AuthController, configureAuth(), RetryableConfig (+93 more)

### Community 1 - "django_db"
Cohesion: 0.03
Nodes (46): Migration, Migration, Migration, Migration, Migration, Migration, Migration, Migration (+38 more)

### Community 2 - "django_utils"
Cohesion: 0.05
Nodes (20): Comment, Meta, StaffRole, Meta, SiteTestCase, AdminTests, AuthorTests, AuthTests (+12 more)

### Community 3 - "console/views.py"
Cohesion: 0.05
Nodes (69): DiscountForm, FeatureEditForm, Meta, FeatureForm, Meta, latin_digits(), parse_amount(), parse_jalali() (+61 more)

### Community 4 - "react"
Cohesion: 0.08
Nodes (62): lessonsApi, meApi, medscapeApi, MedscapeKind, ALPHABET, AlphabeticalArticleList(), buildOffsets(), groupAlphabetically() (+54 more)

### Community 5 - "Post"
Cohesion: 0.07
Nodes (47): Post, Meta, PostRevision, Meta, Subscriber, Meta, orders(), plans() (+39 more)

### Community 6 - "useTheme"
Cohesion: 0.13
Nodes (81): Gate(), AppShell(), AuthLayout(), BottomNav(), GlassToggles(), HeaderMesh(), HelpSheet(), LoadFailed() (+73 more)

### Community 7 - "views_public.py"
Cohesion: 0.05
Nodes (44): site(), SiteMaintenanceMiddleware, Category, Meta, SiteSettings, Meta, Tag, Meta (+36 more)

### Community 8 - ".reverse"
Cohesion: 0.05
Nodes (10): AuthenticationSecurityTests, OnboardingTests, enabled_gateways(), wrapper(), DeleteUserTests, GatewayPageTests, PlanBuilderTests, UsersPageTests (+2 more)

### Community 9 - "package.json"
Cohesion: 0.04
Nodes (63): App(), devDependencies, @types/react, typescript, main, name, private, version (+55 more)

### Community 10 - "flashcards/views.py"
Cohesion: 0.06
Nodes (33): _applies(), _require_content(), require_feature(), require_topic_content(), all_decks(), _carded_slugs(), deck_slugs(), next_topic() (+25 more)

### Community 11 - "Article"
Cohesion: 0.05
Nodes (22): Command, Command, _DryRun, ReferenceImportCommand, Command, Command, Article, Meta (+14 more)

### Community 12 - "billing/views.py"
Cohesion: 0.06
Nodes (43): start_payment(), is_guest(), Order, Meta, CatalogSerializer, CheckoutSerializer, MyAccessSerializer, MyEntitlementSerializer (+35 more)

### Community 13 - "panel/forms.py"
Cohesion: 0.04
Nodes (34): Media, Meta, AnnouncementForm, Meta, CategoryForm, Meta, ContentBlockForm, Meta (+26 more)

### Community 14 - "GatewayError"
Cohesion: 0.06
Nodes (12): FakeGateway, GatewayError, get_gateway(), _post_json(), SepGateway, Verification, ZarinpalGateway, ZibalGateway (+4 more)

### Community 15 - "progress/tests.py"
Cohesion: 0.05
Nodes (12): Command, AtcCategory, Meta, AtcCode, Meta, AtcSupplementTests, DrugApiTests, LoadAtcReferenceTests (+4 more)

### Community 16 - "Feature"
Cohesion: 0.05
Nodes (19): Feature, Meta, UsageRecord, Meta, Access, check_feature(), content_lock(), effective_features() (+11 more)

### Community 17 - "accounts/services.py"
Cohesion: 0.07
Nodes (17): SessionTokenAuthentication, SessionTokenAuthenticationScheme, Role, Meta, SessionRefreshToken, Meta, UserSession, Meta (+9 more)

### Community 18 - "billing/models.py"
Cohesion: 0.06
Nodes (24): EntitlementAdmin, FeatureAdmin, OrderAdmin, PlanAdmin, PlanFeatureInline, PlanPriceInline, AdminAction, Meta (+16 more)

### Community 19 - "views_account.py"
Cohesion: 0.09
Nodes (28): OneTimeCode, Meta, SecurityAuditEvent, Meta, account_for_signup(), _hash(), OtpError, request_code() (+20 more)

### Community 20 - "PlatformAPIError"
Cohesion: 0.08
Nodes (27): LearnerProfileSerializer, Meta, LoginSerializer, OtpRequestSerializer, OtpVerifySerializer, PasswordSetSerializer, RefreshSessionSerializer, SessionRevokeSerializer (+19 more)

### Community 21 - "calculators/tests.py"
Cohesion: 0.08
Nodes (14): fix_questions(), fix_results(), renumber_from_one(), _stage_names_without_prefix(), _with_unit(), apply_fixes(), Migration, apply_fixes() (+6 more)

### Community 22 - "website/models.py"
Cohesion: 0.06
Nodes (20): Command, Announcement, Meta, AppRelease, Meta, ContentBlock, Meta, DownloadLink (+12 more)

### Community 23 - "calculatorEngine.ts"
Cohesion: 0.08
Nodes (47): buildHeuristicSeeds(), cartesian(), checkErrors(), classifyResultTone(), computeCalculator(), ComputeOptions, computeResultRanges(), computeTierBands() (+39 more)

### Community 24 - "django_apps"
Cohesion: 0.04
Nodes (14): AccountsConfig, sms_configured(), BillingConfig, CalculatorsConfig, DataQualityCenterConfig, DrugsConfig, FlashcardsConfig, LessonsConfig (+6 more)

### Community 25 - "quiz/views.py"
Cohesion: 0.10
Nodes (28): BankQuestionAdmin, QuizQuestionInline, QuizSessionAdmin, QuizAnswer, QuizQuestion, Meta, QuizSession, Meta (+20 more)

### Community 26 - "MedscapeArticleScreen.tsx"
Cohesion: 0.10
Nodes (42): MedscapeBlock, MedscapeSection, countMatches(), FindState, highlight(), ListMarker(), LTR, NumberedHeading() (+34 more)

### Community 27 - "lexicomp/views.py"
Cohesion: 0.08
Nodes (18): InteractionCheckRequestSerializer, LexicompDrugSerializer, LexicompInteractionSerializer, _categories_for_generics(), check_interactions(), close_all(), _conn(), _dir() (+10 more)

### Community 28 - ".request_code"
Cohesion: 0.11
Nodes (10): _error_message(), send_code(), _send_smsir(), SentCode, SmsSendError, CodeRuleTests, PhoneAuthTestCase, ResetTests (+2 more)

### Community 29 - "progress/views.py"
Cohesion: 0.10
Nodes (26): complete_item(), skip_item(), DashboardSerializer, FocusRowSerializer, FocusSessionSerializer, MistakeSerializer, Meta, NextChapterSerializer (+18 more)

### Community 30 - "json"
Cohesion: 0.08
Nodes (13): export(), load(), dumps(), expected_count(), loads(), open_for_import(), record_counts(), rows() (+5 more)

### Community 31 - "LearnerProfile"
Cohesion: 0.08
Nodes (14): EmailOrUsernameBackend, LearnerProfile, InvalidPhone, looks_like_phone(), normalize_phone(), PhoneField, NormalizePhoneTests, ProfileTests (+6 more)

### Community 32 - "accounts/serializers.py"
Cohesion: 0.07
Nodes (18): AuthTokenResponseSerializer, OnboardingSerializer, OtpRequestResponseSerializer, PasswordResetConfirmSerializer, PasswordResetRequestSerializer, PasswordResetResponseSerializer, UserSerializer, Meta (+10 more)

### Community 33 - "Ingredient"
Cohesion: 0.07
Nodes (19): Ingredient, Meta, FlashcardFactAdmin, LeitnerCardAdmin, FlashcardFact, Meta, slugs_for_topic(), ingredient_ids_for_selection() (+11 more)

### Community 34 - "Calculator"
Cohesion: 0.08
Nodes (18): Calculator, Meta, CalculatorCategory, Meta, CalculatorTag, Meta, CalculatorCategorySerializer, Meta (+10 more)

### Community 35 - "data_quality_center/services.py"
Cohesion: 0.10
Nodes (21): ReviewEvent, Meta, SectionEditRequest, Meta, approve(), _clean(), _client_ip(), _close() (+13 more)

### Community 36 - "clean_html"
Cohesion: 0.08
Nodes (6): clean_html(), _Cleaner, plain_text(), safe_url(), _Text, SanitizeTests

### Community 37 - "CalculatorDetailScreen.tsx"
Cohesion: 0.13
Nodes (33): calculatorsApi, CalculatorQuestion, describeInputs(), DateInput(), DaysInput(), Field(), QuestionTitle(), CardsFlow() (+25 more)

### Community 38 - "accounts/views.py"
Cohesion: 0.11
Nodes (22): RoleAssignment, Meta, CanManagePlatformRoles, CanViewSecurityAudit, HasPlatformPermission, HasRecentStepUp, RoleAssignmentCreateSerializer, RoleAssignmentRevokeSerializer (+14 more)

### Community 39 - "lessons/views.py"
Cohesion: 0.10
Nodes (20): require_atc_content(), get_chapter(), get_lesson_drug(), topics_for_chapter(), AtcGroupSerializer, ChapterDrugSerializer, ChapterProgressSerializer, ChapterProgressUpdateSerializer (+12 more)

### Community 40 - "data_quality_center/views.py"
Cohesion: 0.12
Nodes (25): warning_count(), section_state(), _diffs(), discard(), history(), _login_key(), login_view(), logout_view() (+17 more)

### Community 41 - "lessons/selectors.py"
Cohesion: 0.08
Nodes (17): _seed_candidates(), _with_enough_content(), ChapterProgress, Meta, ReadDrug, Meta, fold(), l2_slug_index() (+9 more)

### Community 42 - "QuizApiTests"
Cohesion: 0.09
Nodes (3): QuizAccessTests, QuizApiTests, QuizLockedTests

### Community 43 - "UptodateArticleScreen.tsx"
Cohesion: 0.12
Nodes (30): uptodateApi, countWords(), numberByDepth(), Numbered, readingMinutes(), ChromeButton(), LangToggleButton(), useDebounced() (+22 more)

### Community 44 - "billing/tests.py"
Cohesion: 0.12
Nodes (19): _div(), fa_digits(), format_date(), _jal_cal(), _mod(), month_start(), to_gregorian(), to_jalali() (+11 more)

### Community 45 - "panel/views.py"
Cohesion: 0.10
Nodes (20): ActivityLog, Meta, ContactMessage, Meta, DailyStat, Meta, VisitorDay, Meta (+12 more)

### Community 46 - "PurchaseFlowTests"
Cohesion: 0.09
Nodes (4): clear_cache(), GatewayChoiceTests, GuestAccessTests, PurchaseFlowTests

### Community 47 - "Mistake"
Cohesion: 0.10
Nodes (18): DailyStudyAdmin, LearnerProgressAdmin, MistakeAdmin, StudyPlanAdmin, DailyStudy, Meta, Mistake, Meta (+10 more)

### Community 48 - "drugs/serializers.py"
Cohesion: 0.09
Nodes (15): AtcCodeSerializer, Meta, IngredientDetailSerializer, Meta, IngredientListSerializer, Meta, LessonDrugSectionSerializer, Meta (+7 more)

### Community 49 - "LeitnerCard"
Cohesion: 0.10
Nodes (8): LeitnerCard, Meta, seed_deck(), FlashcardApiTests, FlashcardLockedTests, _refresh_facts(), _rich_ingredient(), TopicDeckTests

### Community 50 - "LessonTaxonomyTests"
Cohesion: 0.08
Nodes (4): DrugSearchTests, _ingredient(), LessonTaxonomyFallbackTests, LessonTaxonomyTests

### Community 51 - "expo"
Cohesion: 0.06
Nodes (31): backgroundColor, foregroundImage, adaptiveIcon, package, versionCode, projectId, typedRoutes, expo (+23 more)

### Community 52 - "planning.py"
Cohesion: 0.11
Nodes (17): due_card_count(), StudyPlanItem, Meta, ensure_today_items(), _flatten(), _goal_items(), _groups_by_topic(), _maintenance_items() (+9 more)

### Community 53 - "import_medscape_articles.py"
Cohesion: 0.11
Nodes (13): _clean_blocks(), _clean_sections(), _clean_text(), Command, _extract_latest_update(), ImageResolver, _specialty_label(), `GET /me/dashboard/` (+5 more)

### Community 54 - "VerdictResult.tsx"
Cohesion: 0.28
Nodes (24): bandAt(), Chip(), Explain(), Hero(), Ltr(), TierBar(), tiersTones(), toneOf() (+16 more)

### Community 55 - "config.py"
Cohesion: 0.10
Nodes (15): BillingConfig, current(), gateway_spec(), _gateways(), GatewaySpec, _load(), row(), _settings_changed() (+7 more)

### Community 56 - "record_study"
Cohesion: 0.08
Nodes (12): Migration, seed(), bump_mistake(), record_study(), _touch_streak(), MeApiTests, ProgressServiceTests, فاز ۳ — اپ‌های بک‌اند (زیرفازی) (+4 more)

### Community 57 - "core/views.py"
Cohesion: 0.14
Nodes (12): check_broker(), check_cache(), check_database(), probe(), _timed(), HealthCheckSerializer, HealthChecksSerializer, ReadinessCheckSerializer (+4 more)

### Community 58 - "IngredientProfileSection"
Cohesion: 0.09
Nodes (17): AtcCategoryAdmin, AtcCodeAdmin, IngredientAdmin, IngredientProfileSectionAdmin, IngredientProfileSectionInline, IngredientProfileSection, Meta, LearnerProgress (+9 more)

### Community 59 - "common.tsx"
Cohesion: 0.13
Nodes (22): CalculatorDetail, Extra, fmt(), LEVEL_TONES, ResultProps, Tone, toneOfLevel(), LIST_FROM (+14 more)

### Community 60 - "import_openfda.py"
Cohesion: 0.12
Nodes (5): Command, Command, _int(), _json_list(), _name_fa()

### Community 61 - "6. Lesson study topics (52)"
Cohesion: 0.08
Nodes (25): 1. Bottom navigation (5 tabs), 2. Dashboard: entry points (درِ ورودی مسیرها), 3. Education hub (inside آموزش), 4. Profile menu and stats, 5. Lesson categories (12 body systems), 6. Lesson study topics (52), 7. Calculator specialties (30), 8. Diseases & Conditions: top-level groups (+17 more)

### Community 62 - "ResultCard"
Cohesion: 0.23
Nodes (20): Collapse(), Extras(), hasPersian(), ResultCard(), RichLines(), Rows(), useShown(), DateResult() (+12 more)

### Community 63 - "throttling.py"
Cohesion: 0.11
Nodes (9): BurstRateThrottle, DistributedAnonRateThrottle, DistributedScopedRateThrottle, DistributedUserRateThrottle, _fail_closed_scopes(), SharedCacheThrottleMixin, SustainedRateThrottle, throttle_cache() (+1 more)

### Community 64 - "mark_drug_read"
Cohesion: 0.14
Nodes (9): mark_drug_read(), topic_progress(), _flashcard_recall_for_slugs(), _quiz_accuracy_for_slugs(), regenerate_items(), topic_mastery(), GoalPlanGenerationTests, TopicMasteryTests (+1 more)

### Community 65 - "دستورهای ایمپورت، اکسپورت و دیتابیس"
Cohesion: 0.08
Nodes (23): `backup_database`, `bootstrap_superuser`, `delete_guest_accounts`, `ensure_uptodate_search_index` — ایندکس جست‌وجوی عنوان آپ‌تودیت, `export_reference_db`, `import_calculators_db`، `import_guidelines_db`، `import_diseases_db`, `import_calculators` — ماشین‌حساب‌ها از پایپلاین ترجمه, `import_medscape_articles` — مقاله‌های بیماری و گایدلاین (+15 more)

### Community 66 - "sms.py"
Cohesion: 0.10
Nodes (3): PlatformTask, retry_delay_seconds(), configure_runtime()

### Community 67 - "migrate_uptodate_to_mysql.py"
Cohesion: 0.14
Nodes (5): Command, ensure_title_search_index(), _has_title_search_index(), mysql_config(), MysqlTitleIndexTests

### Community 68 - "uptodate/services.py"
Cohesion: 0.21
Nodes (13): _dir(), get_image(), get_topic(), is_available(), _mysql_conn(), search_topics(), _search_words(), _section_for() (+5 more)

### Community 69 - "dependencies"
Cohesion: 0.09
Nodes (22): dependencies, axios, expo, expo-font, @expo-google-fonts/vazirmatn, expo-linear-gradient, @expo/metro-runtime, expo-secure-store (+14 more)

### Community 70 - "medscape/tests.py"
Cohesion: 0.27
Nodes (5): _disease_record(), _guideline_record(), ImportMedscapeArticlesTests, _write_diseases_tree(), _write_guidelines()

### Community 71 - "calculatorModel.ts"
Cohesion: 0.16
Nodes (19): allWholeNumbers(), cache, classify(), classifyCalculator(), isNumeric(), LadderRung, majorityKind(), makeRandom() (+11 more)

### Community 72 - "panel.js"
Cohesion: 0.16
Nodes (14): buildEditor(), align(), block(), exec(), sync(), toggleSource(), wrapBlock(), filterNav() (+6 more)

### Community 73 - "DownloadAndMachineTests"
Cohesion: 0.15
Nodes (3): DownloadAndMachineTests, make_post(), PostVisibilityTests

### Community 74 - "import_calculators.py"
Cohesion: 0.20
Nodes (9): Command, _error_checks_for(), _formula_strings_fa(), _import_categories(), _import_tags(), _questions_for(), _references_for(), _results_for() (+1 more)

### Community 75 - "core/tests.py"
Cohesion: 0.13
Nodes (3): HealthCheckTests, OpenAPISchemaTests, ResponseCompressionTests

### Community 76 - "SectionEdit"
Cohesion: 0.16
Nodes (6): ReadOnlyAdmin, ReviewEventAdmin, SectionEditAdmin, SectionEditRequestAdmin, SectionEdit, Meta

### Community 77 - "برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای"
Cohesion: 0.12
Nodes (17): برنامهٔ سئوی فارمنتا برای داروسازان و مراجع علمی حرفه‌ای, تقویم پیشنهادی نخستین هشت محتوای تخصصی, روش تبدیل پیشنهادها به کلمات کلیدی معتبر, ساخت Analytics از ابتدا, ساخت Search Console از ابتدا, منابع رسمی بررسی‌شده, چک‌لیست انتشار هر صفحه, ۱. نتیجهٔ بررسی واقعی سایت (+9 more)

### Community 78 - "data_quality_center/tests.py"
Cohesion: 0.22
Nodes (6): _canonical(), _numbers(), numbers_missing_from_source(), run_checks(), word_diff(), CheckTests

### Community 80 - "StudyTopicsCoverageTests"
Cohesion: 0.12
Nodes (7): StudyTopicsCoverageTests, `GET /lessons/chapters/{atc_code}/` — one chapter (ATC L2 subgroup), `GET /lessons/drugs/{slug}/` — one drug's lesson, `GET /lessons/groups/` — the study tree with progress, `GET /lessons/search/?q=` — find a drug by name, Lessons — ✅ built (Phase 3a), `POST /lessons/chapters/{atc_code}/` — record progress

### Community 81 - "uptodate/views.py"
Cohesion: 0.30
Nodes (8): UptodateArticleSerializer, UptodateImageSerializer, UptodateSearchResultSerializer, UptodateTopicSerializer, ImageDetailView, _require_available(), TopicDetailView, TopicSearchView

### Community 85 - "dqc_extras.py"
Cohesion: 0.24
Nodes (9): action_label(), action_tone(), ago(), dict_get(), fa_digits(), percent(), status_label(), status_tone() (+1 more)

### Community 86 - "clean_profile_boilerplate.py"
Cohesion: 0.23
Nodes (8): clean_text(), Command, is_hypersensitivity_boilerplate(), is_hypersensitivity_boilerplate_en(), is_negative_indication_en(), is_negative_indication_fa(), is_null_placeholder(), _normalize()

### Community 87 - "PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa"
Cohesion: 0.14
Nodes (10): CorsPreflightTests, PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa, 🎉 بازنویسی کامل شد, فاز ۰.۵ — حذف زیرساخت رهاشده ✅, فاز ۲ — قرارداد API + API دانش دارویی + onboarding ✅, فاز ۶ — uptodate + جمع‌بندی + انتشار (زیرفازی), پس از انتشار — حذف کدهای ATC نامرتبط با اندیکاسیون ✅ (برنچ `fix-chapter-indication-fit`), پس از انتشار — سایت و بلاگ `pharmenta.ir` + پنل مدیریت ✅ (+2 more)

### Community 89 - "website_extras.py"
Cohesion: 0.19
Nodes (6): atc_groups(), feature_icon(), nav_on(), person(), split_highlight(), split_lines()

### Community 91 - "_snippet"
Cohesion: 0.18
Nodes (3): _snippet(), MysqlTitleSearchTests, SnippetTests

### Community 92 - "mastery_selectors.py"
Cohesion: 0.24
Nodes (5): best_score_pct_for_topic(), _finished_sessions(), _finished_topic_sessions(), topic_mastery_map(), weak_topics_count()

### Community 93 - "settings/base.py"
Cohesion: 0.17
Nodes (3): build.sh script, DJANGO_SETTINGS_MODULE, release.sh script

### Community 94 - "production.py"
Cohesion: 0.29
Nodes (4): validate_production_broker(), validate_production_cache(), validate_production_secret_key(), ProductionSecretKeyTests

### Community 95 - "سایت و بلاگ (pharmenta.ir) و پنل مدیریت"
Cohesion: 0.18
Nodes (7): آمار, اولین اجرا, جابه‌جایی دامنه‌ها (یک‌بار), خرید اشتراک روی سایت, رسانه, سایت و بلاگ (pharmenta.ir) و پنل مدیریت, نقش‌ها

### Community 96 - "jalali.ts"
Cohesion: 0.47
Nodes (11): BREAKS, d2g(), d2j(), div(), g2d(), isValidJalali(), j2d(), jalCal() (+3 more)

### Community 97 - "send_password_reset_emails_for_email"
Cohesion: 0.20
Nodes (5): password_reset_url_for_user(), send_password_reset_email(), send_password_reset_emails_for_email(), send_password_reset_email_task(), enqueue()

### Community 99 - "site.js"
Cohesion: 0.33
Nodes (9): answer(), countUp(), frame(), f(), next(), paint(), show(), toFa() (+1 more)

### Community 100 - "LessonDetailScreen.tsx"
Cohesion: 0.33
Nodes (10): LessonSection, joinOpenParens(), LessonBlock, LessonLine, parenDepth(), parseLessonText(), sectionText(), splitIssues() (+2 more)

### Community 101 - "logging.py"
Cohesion: 0.22
Nodes (4): get_request_id(), JsonFormatter, RequestContextFilter, RequestIdMiddleware

### Community 105 - "back.ts"
Cohesion: 0.29
Nodes (9): canGoBack(), goBackInApp(), installWebBackGuard(), Interceptor, interceptors, listeners, notify(), subscribeBackState() (+1 more)

### Community 106 - "Pharmexa"
Cohesion: 0.22
Nodes (9): Architecture, Backend, locally, Deploy, Docker (backend + db + redis + web frontend), Frontend, locally, Pharmexa, Running it, Tests (+1 more)

### Community 107 - "Repository Guidelines"
Cohesion: 0.25
Nodes (7): Build, Test, and Development Commands, Coding Style & Naming Conventions, Commit & Pull Request Guidelines, Project Structure & Module Organization, Repository Guidelines, Security & Configuration Tips, Testing Guidelines

### Community 108 - "PlanSerializer"
Cohesion: 0.29
Nodes (5): PlanFeatureItemSerializer, PlanPriceSerializer, Meta, PlanSerializer, Meta

### Community 115 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, android, build:web, ios, start, typecheck, web

### Community 116 - "tsconfig.json"
Cohesion: 0.29
Nodes (6): compilerOptions, paths, strict, extends, include, expo/tsconfig.base

### Community 118 - "RegisterSerializer"
Cohesion: 0.33
Nodes (3): RegisterSerializer, Meta, ensure_default_learner_role()

### Community 119 - "Deploying the backend on Runflare (single container, no Redis)"
Cohesion: 0.33
Nodes (5): Deploying the backend on Runflare (single container, no Redis), Environment variables, Loading calculators, guidelines and diseases, Loading the drug data, Verify

### Community 120 - "SessionSerializer"
Cohesion: 0.50
Nodes (3): SessionSerializer, Meta, SessionListView

### Community 130 - "۴. نگهداری دادهٔ داروها"
Cohesion: 0.67
Nodes (3): `apply_atc_supplement`, `clean_profile_boilerplate`, ۴. نگهداری دادهٔ داروها

## Knowledge Gaps
- **8 isolated node(s):** `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-splash-screen`, `react-dom`, `react-native-web` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1298 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **77 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UserSession` connect `accounts/services.py` to `accounts/serializers.py`, `console/views.py`, `accounts/views.py`, `useTheme`, `billing/models.py`, `views_account.py`, `PlatformAPIError`, `WebsiteAuthTests`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`, `config.py`, `SessionSerializer`, `IngredientProfileSection`, `LearnerProfile`?**
  _High betweenness centrality (0.241) - this node is a cross-community bridge._
- **What connects `DJANGO_SETTINGS_MODULE`, `@expo/metro-runtime`, `expo-splash-screen` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api/types.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.031122031122031123 - nodes in this community are weakly interconnected._
- **Why does `فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅` connect `useTheme` to `accounts/services.py`, `package.json`, `PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa`?**
  _High betweenness centrality (0.227) - this node is a cross-community bridge._
- **Should `django_db` be split into smaller, more focused modules?**
  _Cohesion score 0.02728937728937729 - nodes in this community are weakly interconnected._
- **Why does `AppText()` connect `useTheme` to `api/types.ts`, `react`, `CalculatorDetailScreen.tsx`, `LessonDetailScreen.tsx`, `package.json`, `UptodateArticleScreen.tsx`, `VerdictResult.tsx`, `MedscapeArticleScreen.tsx`, `common.tsx`, `ResultCard`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Should `django_utils` be split into smaller, more focused modules?**
  _Cohesion score 0.048514851485148516 - nodes in this community are weakly interconnected._