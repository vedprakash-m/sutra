# Sutra Implementation Plan

> Systematic remediation and completion plan derived from comprehensive codebase audit against PRD, Tech Spec, and UX Spec.
> Organized by severity: showstoppers → security → functionality → hardening.

---

## Phase 0: Make It Run (Showstoppers)

These bugs cause import crashes, dead routes, or data model drift. The app literally cannot function until these are fixed.

### Task 0.1: Fix Broken Imports in Forge Endpoint Files
**Status:** ✅ Complete
**Severity:** SHOWSTOPPER — Every stage 2-5 endpoint crashes on import
**Resolution:** Fixed `LLMClient`→`LLMManager` imports and all instantiations (~13 occurrences), `QualityEngine`→`QualityAssessmentEngine`, `cost_tracking`→`cost_tracker`, replaced `sys.path.append` with proper `shared.` imports, moved `CodingAgentOptimizer` to correct module path in 4 files.

### Task 0.2: Fix Hardcoded Connection Strings
**Status:** ✅ Complete
**Resolution:** Replaced `COSMOS_CONNECTION_STRING = "your_cosmos_connection_string_here"` with `os.getenv("COSMOS_DB_CONNECTION_STRING", "")` in 4 files, added `import os` where missing.

### Task 0.3: Fix function.json Routing for All Forge Stages
**Status:** ✅ Complete
**Resolution:** Changed route from `forge/idea-refinement/{action:alpha?}/{project_id:alpha?}` to `forge/{action}/{sub_action?}/{project_id?}`, authLevel `"function"`→`"anonymous"`, added PUT/DELETE methods. Updated all 5 sub-endpoint dispatchers to read `sub_action` from route_params.

### Task 0.4: Fix Sync/Async Mismatches
**Status:** ✅ Complete
**Resolution:** Changed `def main` → `async def main` in technical_analysis_endpoints.py and implementation_playbook_endpoints.py. Removed `asyncio.run()` calls (2 occurrences) and replaced with `await`. Made `evaluate_architecture_endpoint` async.

### Task 0.5: Align ForgeStage Enum with Spec
**Status:** ✅ Complete
**Resolution:** Renamed ForgeStage enum: CONCEPTION→IDEA_REFINEMENT, VALIDATION→PRD_GENERATION, PLANNING→UX_REQUIREMENTS, IMPLEMENTATION→TECHNICAL_ANALYSIS, DEPLOYMENT→IMPLEMENTATION_PLAYBOOK. Renamed 5 dataclasses and 5 field names. Updated all references in forge_api/__init__.py and test files.

### Task 0.6: Fix ForgePage.tsx File Corruption
**Status:** ✅ Complete
**Resolution:** Removed corrupted header (lines 1-37), added proper `forgeApi` import, replaced hardcoded mockProjects with `forgeApi.getProjects()`, replaced mock loadProjectDetails with `forgeApi.getProject(id)`.

### Task 0.7: Fix Database Name Inconsistency
**Status:** ✅ Complete
**Resolution:** Changed `database.py` database_name from `"sutra"` to `"SutraDB"` for consistency.

---

## Phase 1: Secure It

### Task 1.1: Remove Debug Auth Endpoint
**Status:** ✅ Complete
**Resolution:** Deleted `api/debug_auth/` directory.

### Task 1.2: Remove Test Anonymous Endpoint
**Status:** ✅ Complete
**Resolution:** Deleted `api/test_anonymous/` directory.

### Task 1.3: Remove Guest Endpoints (Policy Violation)
**Status:** ✅ Complete
**Resolution:** Deleted `api/guest_api/` and `api/guest_llm_api/` directories. Removed `guest: guestApi` from frontend API export in `src/services/api.ts`.

### Task 1.4: Remove Test Function App Directories
**Status:** ✅ Complete
**Resolution:** Deleted `api/test_auth_decorator/`, `api/test_auth_token/`, `api/test_imports/`, `api/test_simple/`, and empty `api/llm_execute/`.

### Task 1.5: Fix CORS Configuration
**Status:** ✅ Complete
**Resolution:** Removed wildcard `Access-Control-Allow-Origin: *` from `security_headers()`. Added `get_allowed_origins()` with proper allowlist (production domain, localhost:5173/3000/4280, custom domain from env). Added `resolve_cors_origin(req)` that dynamically matches request Origin against allowlist. CORS headers set per-request in `rate_limit_middleware`. Added `Vary: Origin` header. Added OPTIONS preflight handling.

### Task 1.6: Apply Middleware to Endpoints
**Status:** ✅ Complete
**Resolution:** Applied `@enhanced_security_middleware` decorator to all 12 endpoint `main` functions (forge_api, admin_api, collections_api, cost_management_api, integrations_api, llm_execute_api, playbooks_api, role_management, user_management, getroles, anonymous_llm_api, integrations_api_fixed). Updated both `rate_limit_middleware` and `enhanced_security_middleware` to support async handlers via `asyncio.iscoroutinefunction()` check. Health endpoint already had it.

### Task 1.7: Standardize Auth Across All Forge Endpoints
**Status:** ✅ Complete
**Resolution:** Added `extract_user_info(req)` auth guard with 401 response to all 8 handler functions in `technical_analysis_endpoints.py`. Changed `user_id` source from body-provided `request_data.get("user_id")` to authenticated `user_info["user_id"]`. All other forge endpoints already had auth checks.

---

## Phase 2: Wire the Forge Pipeline

### Task 2.1: Wire ForgePage.tsx to forgeApi
**Status:** ✅ Complete (done as part of Task 0.6)
**Resolution:** Replaced `mockProjects` with `forgeApi.getProjects()` call. Replaced mock `loadProjectDetails` with `forgeApi.getProject(id)`. Added proper `forgeApi` import from `@/services/api`.

### Task 2.2: Wire ForgeProjectDetails to forgeApi
**Status:** ✅ Complete
**Resolution:** Added `forgeApi` import and `useCallback`. Wired `handleAdvanceStage` to call `forgeApi.advanceStage(projectId, nextStageId)` with proper error handling. Added `advanceStage` method to forgeApi in api.ts.

### Task 2.3: Wire IdeaRefinementStage to forgeApi
**Status:** ✅ Complete
**Resolution:** Added `forgeApi` import. Replaced 2 raw `fetch()` calls with `forgeApi.analyzeIdea()` and `forgeApi.getIdeaQualityAssessment()`. Auth headers now automatically included.

### Task 2.4: Wire PRDGeneration to forgeApi
**Status:** ✅ Complete
**Resolution:** Added `forgeApi` import. Replaced 6 raw `fetch()` calls with forgeApi methods: `extractRequirements`, `generateUserStories`, `prioritizeFeatures`, `generatePRDDocument`, `getPRDQualityAssessment`, `completePRDGeneration`. Added 2 missing methods to api.ts. Fixed URL mismatches (assessment, generate-document).

### Task 2.5: Wire UXRequirementsStage to forgeApi
**Status:** ✅ Complete
**Resolution:** Added `forgeApi` import. Replaced 7 raw `fetch()` calls. Fixed URL mismatches: `generate-user-journeys`→`map-user-journeys`, `accessibility-validation`→`check-accessibility`, `quality-assessment`→`assessment`, `generate-ux-document`→`generate-document`. Added `specifyInteractions` method to api.ts.

Also wired: `TechnicalAnalysisStage.tsx` (3 fetch→forgeApi) and `ImplementationPlaybookStage.tsx` (7 fetch→forgeApi). Fixed 4 URL mismatches in technical analysis forgeApi methods. Added 4 new api.ts methods (getConsensusModels, exportTechnicalAnalysis, createDeploymentGuide, validateContextIntegration).

### Task 2.6: Enforce Quality Gates
**Status:** ✅ Complete
**Resolution:** Enhanced `QualityGate.tsx` with `onPass`, `onBlock`, `allowOverride`, and `onOverride` callback props. Added `useEffect` to notify parent of gate status changes. Added expert override button UI (only shown when `allowOverride=true` and quality is below threshold). PRDGeneration and UXRequirementsStage already have quality threshold enforcement in their `completeStage` functions (check `canProceed` state before allowing completion).

### Task 2.7: Add Forge State Management with Zustand
**Status:** ✅ Complete
**Resolution:** Created `src/stores/forgeStore.ts` with Zustand. Store manages: projects list, current project, stage data (keyed by projectId+stageId), quality scores, loading/error states. Actions: `fetchProjects`, `setCurrentProject`, `updateStageData`, `updateQuality`, `canAdvanceStage` (enforces spec thresholds: 75/80/82/85/88%), `advanceStage`, `createProject`, `deleteProject`. Uses `zustand/middleware/persist` with sessionStorage for stage data and quality scores.

---

## Phase 3: Harden for Production

### Task 3.1: Enable Strict TypeScript
**Status:** ✅ Complete
**Resolution:** Changed `"strict": false` → `"strict": true` in tsconfig.json. Fixed 68 type errors across 7 forge components (ForgePage, IdeaRefinementStage, PRDGeneration, UXRequirementsStage, TechnicalAnalysisStage, ImplementationPlaybookStage, ProgressIndicator). Errors included wrong method names, snake_case→camelCase fixes, response type mismatches, and optional property guards.

### Task 3.2: Remove Unused Dependencies
**Status:** ✅ Complete
**Resolution:** Removed 5 unused packages from package.json: `@emotion/react`, `@emotion/styled`, `@mui/material`, `axios`, `date-fns`, `react-hook-form`. Verified `@headlessui/react` (used in VersionHistory, ImportModal) and `react-query` (App.tsx provider) are in use — kept.

### Task 3.3: Consolidate Database Usage
**Status:** ✅ Complete
**Resolution:** Created `api/shared/async_database.py` with `AsyncCosmosHelper` class and completed Forge migration across all 6 Forge endpoint files (including `api/forge_api/__init__.py`). Added `create_item()` helper and removed all `CosmosClient.from_connection_string` usage from Forge API paths.

### Task 3.4: Improve Test Coverage
**Status:** ✅ Complete
**Severity:** MEDIUM (resolved)
**Resolution:** Added comprehensive backend and frontend Forge test coverage.
**Files:**
- `api/shared/quality_engine_test.py`: 110 tests for all quality engine classes/methods, stage scoring, thresholds, gate decisions, confidence, and contextual validation
- `api/forge_api/forge_api_test.py`: 46 endpoint/integration-style tests covering auth guards, CRUD, stage advancement, artifacts, templates, DB helpers, routing, and access control
- `src/components/forge/__tests__/QualityGate.test.tsx`: quality gate rendering, callback, threshold, and expert override behavior
- `src/components/forge/__tests__/ProgressIndicator.test.tsx`: step-state and progress percentage rendering
- `src/components/forge/__tests__/LLMProviderSelector.test.tsx`: provider/model selection and store interaction
- `src/components/forge/__tests__/ForgeExportButton.test.tsx`: export format menu and download handling (blob + URL)
- `src/components/forge/__tests__/ForgeProjectCard.test.tsx`: card rendering, badges, tags, and selection behavior
- `src/components/forge/__tests__/ForgePage.test.tsx`: list/create/details flow, filtering, route/search-param behavior, and API error handling
- `src/components/forge/__tests__/ForgeProjectDetails.test.tsx`: stage orchestration view (overview/work/artifacts/collaboration/analytics), stage advancement behavior, and stage-specific work-surface rendering
- `src/stores/forgeStore.test.ts`: Zustand action/state tests for project loading, quality gates, stage advancement, CRUD, and LLM preference persistence behavior
- Verified targeted frontend/store suites: 76 passing
- Added scoped coverage workflow for Forge surfaces: `jest.forge.config.js` + `npm run test:coverage:forge`
- Expanded scoped coverage target to include `ForgeProjectDetails.tsx`; verification now passes thresholds with 8/8 suites and 85/85 tests
- Verified backend suites: 110 + 46 passing, plus existing regression suites passing (`api/test_forge_models.py`, `api/test_forge_e2e.py`, `api/test_idea_refinement.py`)

### Task 3.5: Remove Empty/Dead Code Directories
**Status:** ✅ Complete
**Resolution:** Deleted empty `api/llm_execute/` directory (Task 1.4). Deleted redundant `api/integrations_api_fixed/` — was a 183-line debug copy of the full 672-line `integrations_api/` with separate `/integrations-fixed/` route. No frontend references.

---

## Phase 4: Excellence (Spec Completion)

### Task 4.1: Implement Missing Routes
**Status:** ✅ Complete
**Files:**
- `src/App.tsx`: Added `/dashboard`, `/prompts`, `/collections/:id`, `/playbooks` routes
- Created `src/components/prompt/PromptsListPage.tsx`
- Created `src/components/playbooks/PlaybooksListPage.tsx`
- Created `src/components/collections/CollectionDetailPage.tsx`

### Task 4.2: Complete Quality Engine for Stages 2-5
**Status:** ✅ Complete
**Files:**
- `api/shared/quality_engine.py`: Added real content-based scoring for all 5 stages (16 new assessment methods)
- Added `implementation_playbook` stage metrics (context_integration, prompt_actionability, testing_completeness, deployment_readiness) and thresholds (min:88, rec:95)
- Added improvement suggestions for stages 2-5 (16 dimension-specific suggestions)
- Replaced generic string-length heuristic with structural content analysis

### Task 4.3: Complete Forge Stage Endpoint Logic
**Status:** ✅ Complete
**Files:**
- `api/forge_api/__init__.py`: Implemented 6 stubs (delete, analytics, artifacts, templates CRUD), added quality gate enforcement to `advance_project_stage`, imported QualityAssessmentEngine
- `api/forge_api/technical_analysis_endpoints.py`: Added missing `os` import, fixed `assess_quality()` → `calculate_quality_score()`
- `api/forge_api/implementation_playbook_endpoints.py`: Added `cost_tracker = CostTracker()` initialization
- `api/forge_api/prd_generation_endpoints.py`: Fixed container scope bug — moved all logic inside `async with` block
- `api/forge_api/ux_requirements_endpoints.py`: Fixed container scope bug — moved all logic inside `async with` block

### Task 4.4: Implement LLM Provider Selection UI
**Status:** ✅ Complete
**Spec:** Users should be able to select which LLM provider to use for each operation
**Files:**
- `src/types/forge.ts`: Added `LLMProviderName`, `LLMModelOption`, `LLMProviderInfo` types + `LLM_PROVIDERS` constant (OpenAI/Anthropic/Google with models)
- `src/stores/forgeStore.ts`: Added `selectedProvider`/`selectedModel` state + `setLLMProvider` action + persist preferences
- `src/components/forge/LLMProviderSelector.tsx`: NEW — provider tabs + model dropdown + cost tier indicator
- `src/components/forge/ForgeProjectDetails.tsx`: Wired `LLMProviderSelector` into work tab, replaced hardcoded `selectedLLM`
- `src/services/api.ts`: Added `getLLMPreferences()` helper, attached provider/model to all LLM-calling forge API methods

### Task 4.5: Implement Export Functionality
**Status:** ✅ Complete
**Spec:** Users should be able to export Forge artifacts in multiple formats
**Files:**
- Backend: `api/forge_api/implementation_playbook_endpoints.py` — already has `export_playbook_endpoint` supporting JSON/Markdown/PDF/ZIP + `export_to_markdown`, `export_to_pdf`, `export_to_zip_archive` helpers
- `src/types/forge.ts`: `ExportFormat`, `ExportRequest`, `ExportResponse` types already defined
- `src/services/api.ts`: `forgeApi.exportPlaybook()` already handles blob/JSON responses
- `src/components/forge/ForgeExportButton.tsx`: NEW — reusable export dropdown (format picker + download trigger)
- `src/components/forge/ForgeProjectDetails.tsx`: Wired `ForgeExportButton` into project header toolbar
- `src/components/forge/ImplementationPlaybookStage.tsx`: Already had inline export format selector + export action

---

## Progress Log

| Date | Tasks Completed | Notes |
|------|----------------|-------|
| Session 1 | Phase 0 (0.1-0.7) | All showstoppers fixed: imports, connection strings, routing, async, enums, ForgePage corruption, DB name |
| Session 1 | Phase 1 (1.1-1.7) | Security hardened: removed 9 debug/test/guest dirs, dynamic CORS, middleware applied to all 12 endpoints, auth standardized |
| Session 1 | Task 2.1 | ForgePage wired to forgeApi (done as part of 0.6) |
| Session 1 | Task 3.5 (partial) | Empty llm_execute dir removed |
| Session 1 | Phase 2 (2.1-2.7) | All Forge components wired to forgeApi (24 fetch→forgeApi), URL mismatches fixed, QualityGate enhanced, Zustand store created |
| Session 2 | Task 3.1 | Enabled strict TypeScript — fixed 68 type errors across 7 forge components |
| Session 2 | Task 3.2 | Removed 5 unused npm packages |
| Session 2 | Task 3.3 | Created async_database.py — AsyncCosmosHelper for forge endpoint DB consolidation |
| Session 3 | Task 3.5 | Deleted redundant api/integrations_api_fixed/ (183-line debug copy) |
| Session 3 | Task 4.1 | Added 4 missing routes (/dashboard, /prompts, /collections/:id, /playbooks) + 3 new page components |
| Session 3 | Task 4.2 | Quality engine: 16 new assessment methods for stages 2-5, 16 improvement suggestions, replaced string-length heuristic |
| Session 3 | Task 4.3 | Fixed 5 runtime crash bugs (missing import, wrong method, uninitialized var, 2 container scope bugs), quality gate in advance-stage, 6 stub implementations |
| Session 3 | Task 4.4 | LLM provider selection: types, store state, LLMProviderSelector component, wired to ForgeProjectDetails + API methods |
| Session 3 | Task 4.5 | Export UI: ForgeExportButton component (JSON/MD/PDF/ZIP dropdown), wired to project toolbar |
| Session 4 | Tech debt remediation | Removed duplicate `save_implementation_playbook`; fixed `LLMManager.execute_prompt()` signature mismatch via provider auto-resolution; standardized Forge container name to `ForgeProjects`; migrated 5/6 Forge files to `AsyncCosmosHelper`; fixed frontend→backend LLM field mapping mismatch |
| Session 5 | Task 3.3 completion + backend tests | Completed `AsyncCosmosHelper` migration in `api/forge_api/__init__.py` (0 remaining `CosmosClient.from_connection_string` in Forge API); added `create_item()` helper; discovered and fixed nested enum serialization bug in `ForgeProject.to_dict()` and artifact enum serialization in `add_project_artifact`; added 110 quality-engine tests + 46 forge-api tests |
| Session 5 | Task 3.4 completion (frontend/store) | Added Forge frontend/store tests for `ForgePage`, `ForgeProjectCard`, `LLMProviderSelector`, `ForgeExportButton`, `QualityGate`, `ProgressIndicator`, and `forgeStore`; targeted Jest verification: 76 passing |
| Session 6 | Verification hardening pass | Re-ran targeted Forge frontend/store suites: 7/7 suites, 76/76 tests passing; captured coverage run for same suites (strong Forge/store coverage, global thresholds still fail due whole-repo coverage policy and many untested non-Forge modules) |
| Session 7 | Coverage hardening (scoped) | Added `jest.forge.config.js` and `test:coverage:forge` script to enforce strict coverage on tested Forge surfaces without weakening global suite policy; verification result: 7/7 suites, 76/76 tests, scoped coverage 85.43% statements / 74% branches / 87.5% functions / 85.77% lines |
| Session 8 | ForgeProjectDetails hardening | Added `src/components/forge/__tests__/ForgeProjectDetails.test.tsx` covering tab flows, stage advancement, and stage-specific work rendering; updated scoped coverage to include `ForgeProjectDetails.tsx`; verification: 8/8 suites, 85/85 tests, scoped coverage 82.55% statements / 82.19% branches / 75.51% functions / 83.89% lines |
