# Forge Module - Manual Testing Plan

**Date:** November 2, 2025  
**Test Phase:** Manual Integration Testing  
**Tester:** Development Team  
**Status:** 🔄 **READY TO EXECUTE**

---

## Executive Summary

This manual testing plan provides a comprehensive, step-by-step guide for validating the complete Forge workflow. The plan covers functional testing, integration testing, UI/UX validation, and performance assessment to ensure production readiness.

---

## 1. Test Environment Setup

### 1.1 Prerequisites Checklist

- [ ] Node.js v18+ installed
- [ ] Python 3.12 installed
- [ ] Azure Functions Core Tools v4 installed
- [ ] Git repository up to date (main branch)
- [ ] All dependencies installed (`npm install` + `pip install -r requirements.txt`)
- [ ] Environment variables configured (`.env` files)
- [ ] LLM API keys available (OpenAI, Anthropic, Google)

### 1.2 Start Development Servers

**Frontend Server:**
```bash
# Terminal 1: Start React development server
cd /Users/ved/Apps/sutra
npm run dev

# Expected output:
# ✓ Vite dev server running on http://localhost:3000
# ✓ Ready in ~2s
```

**Backend Server:**
```bash
# Terminal 2: Start Azure Functions local runtime
cd /Users/ved/Apps/sutra/api
func start

# Expected output:
# Azure Functions Core Tools
# Http Functions: [Multiple endpoints listed]
# Host started on http://localhost:7071
```

### 1.3 Verify Server Health

- [ ] Frontend: Navigate to http://localhost:3000 - should show login page
- [ ] Backend: Navigate to http://localhost:7071/api/health - should return `{"status": "healthy"}`
- [ ] Authentication: Login with test account - should redirect to dashboard

---

## 2. Test Scenarios

### Test Scenario 1: Complete 5-Stage Forge Workflow

**Objective:** Validate end-to-end workflow from idea refinement through implementation playbook

**Priority:** HIGH (Critical Path)  
**Duration:** 45-60 minutes  
**Prerequisites:** Clean database state, valid LLM API keys

#### Step 1.1: Create New Forge Project

**Action:**
1. Navigate to http://localhost:3000/forge
2. Click "Create New Project" button
3. Fill in project details:
   - Name: "Test SaaS Product - Manual Test"
   - Description: "A comprehensive project management tool for remote teams"
   - Initial Idea: "I want to build a SaaS platform that helps remote teams collaborate better with real-time updates, task management, and video conferencing integration"

**Expected Results:**
- [ ] Project creation form validates input
- [ ] Project saves successfully to database
- [ ] Redirect to Stage 1: Idea Refinement
- [ ] Project ID visible in URL: `/forge/[project-id]/idea`
- [ ] Stage progress indicator shows Stage 1 active, others locked

**Pass/Fail:** ______  
**Notes:** ________________________________

---

#### Step 1.2: Stage 1 - Idea Refinement

**Action:**
1. Review auto-generated analysis from initial idea
2. Click "Analyze Idea" button
3. Wait for multi-dimensional analysis to complete (15-30s)
4. Review analysis results:
   - Problem Clarity
   - Target Audience
   - Value Proposition
   - Market Viability
5. Answer systematic questions if prompted
6. Monitor quality score progress
7. Click "Complete Stage" when quality ≥ 75%

**Expected Results:**
- [ ] Loading indicator shows during analysis
- [ ] Analysis appears with 4 dimensions scored
- [ ] Quality score displays prominently
- [ ] Systematic questions appear if quality < 75%
- [ ] Quality score updates as questions answered
- [ ] "Complete Stage" button enabled at 75%+
- [ ] Stage completion modal shows summary
- [ ] Cost tracking updates with analysis cost

**Validation Points:**
- Quality score calculation: ______%
- Analysis completeness: All 4 dimensions present?
- Cost tracked: $______ for ______ tokens
- Time to complete: ______ seconds

**Pass/Fail:** ______  
**Notes:** ________________________________

---

#### Step 1.3: Stage 2 - PRD Generation

**Action:**
1. Navigate to Stage 2 (click "Next Stage" or navigate to `/forge/[project-id]/prd`)
2. Verify Stage 1 context loaded (idea analysis visible in sidebar)
3. Click "Generate User Stories" button
4. Wait for user story generation (15-30s)
5. Review generated user stories
6. Click "Generate Requirements" button
7. Review extracted requirements
8. Click "Generate Acceptance Criteria" button
9. Review acceptance criteria for each user story
10. Monitor quality score (target: 80%+)
11. Export PRD as Markdown
12. Click "Complete Stage" when ready

**Expected Results:**
- [ ] Stage 1 context visible and accurate
- [ ] User stories generate with proper format (As a..., I want..., So that...)
- [ ] Requirements categorized (Functional, Non-functional, Technical)
- [ ] Acceptance criteria specific and testable
- [ ] Quality score updates after each generation
- [ ] Quality score reaches 80%+ threshold
- [ ] Export functionality works (Markdown file downloads)
- [ ] "Complete Stage" enabled at 80%+
- [ ] Stage 2 marked complete in progress indicator

**Validation Points:**
- User stories generated: ______ count
- Quality score: ______%
- Context from Stage 1 accurate? Yes/No
- Export file size: ______ KB
- Time to complete: ______ seconds

**Pass/Fail:** ______  
**Notes:** ________________________________

---

#### Step 1.4: Stage 3 - UX Requirements

**Action:**
1. Navigate to Stage 3: `/forge/[project-id]/ux`
2. Verify Stage 2 context loaded (user stories + requirements visible)
3. Click "Generate User Journeys" button
4. Wait for journey generation (20-40s)
5. Review user journeys:
   - Expand each journey step
   - Check for pain points identification
   - Validate touchpoint mapping
6. Click "Generate Wireframes" button
7. Select devices: Desktop, Tablet, Mobile
8. Review wireframe descriptions for each device
9. Click "Generate Component Specs" button
10. Review component specifications
11. Click "Validate Accessibility" button
12. Review WCAG 2.1 AA compliance results
13. Monitor quality scores (main: 85%+, accessibility: 90%+)
14. Export as PDF
15. Click "Complete Stage"

**Expected Results:**
- [ ] Stage 2 context loaded (user stories visible)
- [ ] User journeys generated with visual flow
- [ ] Journey steps expandable with details
- [ ] Wireframes generated for 3 devices
- [ ] Component specs detailed and consistent
- [ ] Accessibility validation shows WCAG results
- [ ] Quality score reaches 85%+
- [ ] Accessibility score reaches 90%+
- [ ] PDF export includes all sections
- [ ] Stage 3 marked complete

**Validation Points:**
- User journeys generated: ______ count
- Wireframes created: Desktop/Tablet/Mobile
- Component specs: ______ count
- WCAG compliance: ______%
- Main quality score: ______%
- Accessibility score: ______%
- Export PDF size: ______ KB
- Time to complete: ______ seconds

**Pass/Fail:** ______  
**Notes:** ________________________________

---

#### Step 1.5: Stage 4 - Technical Analysis

**Action:**
1. Navigate to Stage 4: `/forge/[project-id]/tech`
2. Verify Stage 3 context loaded (UX requirements visible)
3. Select LLM providers for multi-LLM analysis:
   - [ ] GPT-4
   - [ ] Claude 3.5 Sonnet
   - [ ] Gemini 1.5 Pro
4. Click "Analyze Architecture" button
5. Wait for multi-LLM analysis (30-60s)
6. Review individual LLM recommendations:
   - Architecture patterns
   - Technology stack
   - Scalability considerations
   - Security recommendations
7. Review consensus analysis:
   - Agreement areas
   - Disagreement points
   - Weighted recommendations
8. Click "Generate Risk Assessment" button
9. Review identified risks with mitigation strategies
10. Monitor quality scores (main: 85%+, soundness: 90%+)
11. Export analysis as JSON
12. Click "Complete Stage"

**Expected Results:**
- [ ] Stage 3 context loaded
- [ ] Multi-LLM selector works correctly
- [ ] Each LLM provides independent analysis
- [ ] Consensus calculation displays weighted results
- [ ] Agreement/disagreement clearly visualized
- [ ] Risk assessment comprehensive
- [ ] Quality score reaches 85%+
- [ ] Architectural soundness reaches 90%+
- [ ] JSON export valid and complete
- [ ] Stage 4 marked complete

**Validation Points:**
- LLMs analyzed: ______ count
- Consensus agreements: ______ areas
- Consensus disagreements: ______ points
- Risks identified: ______ count
- Main quality score: ______%
- Soundness score: ______%
- Export JSON valid? Yes/No
- Time to complete: ______ seconds

**Pass/Fail:** ______  
**Notes:** ________________________________

---

#### Step 1.6: Stage 5 - Implementation Playbook

**Action:**
1. Navigate to Stage 5: `/forge/[project-id]/playbook`
2. Verify all previous stages' context loaded
3. Click "Compile Playbook" button
4. Wait for playbook compilation (20-40s)
5. Review compiled playbook sections:
   - Executive Summary
   - Architecture Overview (from Stage 4)
   - User Stories (from Stage 2)
   - UX Requirements (from Stage 3)
   - Technical Specifications
   - Implementation Roadmap
6. Click "Generate Coding Prompts" button
7. Review coding prompts for key features
8. Click "Generate Development Workflow" button
9. Review workflow phases and milestones
10. Monitor quality score (target: 85%+)
11. Test all export formats:
    - [ ] Export as JSON
    - [ ] Export as Markdown
    - [ ] Export as PDF
    - [ ] Export as ZIP (complete bundle)
12. Click "Complete Stage"

**Expected Results:**
- [ ] All stages' context integrated correctly
- [ ] Playbook compilation comprehensive
- [ ] All 6 sections present and detailed
- [ ] Coding prompts specific and actionable
- [ ] Development workflow realistic
- [ ] Quality score reaches 85%+
- [ ] JSON export valid
- [ ] Markdown export formatted correctly
- [ ] PDF export professional quality
- [ ] ZIP contains all formats + assets
- [ ] Stage 5 marked complete
- [ ] All stages show "Complete" status

**Validation Points:**
- Playbook sections: ______ count
- Coding prompts: ______ count
- Workflow phases: ______ count
- Quality score: ______%
- JSON export size: ______ KB
- Markdown export size: ______ KB
- PDF export size: ______ KB
- ZIP export size: ______ KB
- Time to complete: ______ seconds

**Pass/Fail:** ______  
**Notes:** ________________________________

---

### Test Scenario 2: Quality Gate Enforcement

**Objective:** Validate quality gates prevent progression with low-quality work

**Priority:** HIGH  
**Duration:** 15-20 minutes

#### Step 2.1: Create Low-Quality Idea

**Action:**
1. Create new project with minimal idea: "An app"
2. Try to complete Stage 1 without meeting 75% threshold

**Expected Results:**
- [ ] Quality score below 75%
- [ ] "Complete Stage" button disabled
- [ ] Warning message displayed
- [ ] Systematic questions prompted
- [ ] Cannot navigate to Stage 2

**Pass/Fail:** ______

---

#### Step 2.2: Test Each Stage's Quality Gate

**Action:**
Test quality gates for all stages:
- Stage 1: 75% minimum
- Stage 2: 80% minimum
- Stage 3: 85% + 90% accessibility
- Stage 4: 85% + 90% soundness
- Stage 5: 85% minimum

**Expected Results:**
- [ ] Each stage enforces its threshold
- [ ] Progress blocked until met
- [ ] Clear feedback on what's missing
- [ ] Improvement suggestions provided

**Pass/Fail:** ______

---

### Test Scenario 3: Context Preservation & Handoff

**Objective:** Verify data flows correctly between stages

**Priority:** HIGH  
**Duration:** 20-30 minutes

#### Step 3.1: Track Context Through Workflow

**Action:**
1. Complete Stage 1 with specific idea details
2. Verify Stage 2 references Stage 1 analysis
3. Verify Stage 3 references Stage 2 user stories
4. Verify Stage 4 references Stage 3 UX requirements
5. Verify Stage 5 integrates all previous stages

**Expected Results:**
- [ ] Stage 1 data visible in Stage 2
- [ ] Stage 2 data visible in Stage 3
- [ ] Stage 3 data visible in Stage 4
- [ ] Stage 4 data visible in Stage 5
- [ ] Stage 5 shows complete context
- [ ] No data loss between stages
- [ ] Context accurate and relevant

**Validation Points:**
- Stage 1→2 handoff: ______ data points transferred
- Stage 2→3 handoff: ______ data points transferred
- Stage 3→4 handoff: ______ data points transferred
- Stage 4→5 handoff: ______ data points transferred

**Pass/Fail:** ______

---

### Test Scenario 4: Stage Navigation & Routing

**Objective:** Validate navigation controls and URL routing

**Priority:** MEDIUM  
**Duration:** 15-20 minutes

#### Step 4.1: Test Navigation Controls

**Action:**
1. Test "Next Stage" button functionality
2. Test "Previous Stage" button functionality
3. Test direct URL navigation to each stage
4. Test breadcrumb navigation
5. Test stage locking (can't access incomplete stages)
6. Test stage unlocking (after completion)

**Expected Results:**
- [ ] "Next" navigates to next stage if unlocked
- [ ] "Previous" navigates to completed stages
- [ ] Direct URLs redirect if stage locked
- [ ] Breadcrumbs show correct hierarchy
- [ ] Locked stages show lock icon
- [ ] Completed stages show checkmark
- [ ] Current stage highlighted

**Pass/Fail:** ______

---

### Test Scenario 5: Cost Tracking & Budget

**Objective:** Verify real-time cost tracking across workflow

**Priority:** MEDIUM  
**Duration:** 10-15 minutes

#### Step 5.1: Monitor Cost Throughout Workflow

**Action:**
1. Note starting cost: $______
2. Complete Stage 1, note cost: $______
3. Complete Stage 2, note cost: $______
4. Complete Stage 3, note cost: $______
5. Complete Stage 4, note cost: $______
6. Complete Stage 5, note cost: $______
7. Verify cost breakdown by:
   - LLM provider
   - Stage
   - Operation type

**Expected Results:**
- [ ] Cost updates after each operation
- [ ] Cost displays in header/sidebar
- [ ] Breakdown shows provider distribution
- [ ] Breakdown shows stage distribution
- [ ] Total cost matches sum of operations
- [ ] Warning if approaching budget limit

**Validation Points:**
- Stage 1 cost: $______
- Stage 2 cost: $______
- Stage 3 cost: $______
- Stage 4 cost: $______
- Stage 5 cost: $______
- Total cost: $______
- OpenAI cost: $______
- Anthropic cost: $______
- Google cost: $______

**Pass/Fail:** ______

---

### Test Scenario 6: Export Functionality

**Objective:** Test all export formats and verify quality

**Priority:** MEDIUM  
**Duration:** 20-25 minutes

#### Step 6.1: Test Stage-Specific Exports

**Action:**
Test exports for each stage:
- Stage 1: JSON export
- Stage 2: Markdown export
- Stage 3: PDF export
- Stage 4: JSON export
- Stage 5: All 4 formats + ZIP

**Expected Results:**
- [ ] JSON files valid and parseable
- [ ] Markdown files properly formatted
- [ ] PDF files professional quality
- [ ] ZIP contains all files
- [ ] File names descriptive
- [ ] Downloads work in all browsers

**Validation Points:**
- JSON valid? Yes/No
- Markdown formatted? Yes/No
- PDF readable? Yes/No
- ZIP complete? Yes/No

**Pass/Fail:** ______

---

### Test Scenario 7: Error Handling & Recovery

**Objective:** Validate graceful error handling and user feedback

**Priority:** MEDIUM  
**Duration:** 15-20 minutes

#### Step 7.1: Test API Failure Scenarios

**Action:**
1. Disconnect internet during LLM operation
2. Simulate API rate limit (if possible)
3. Test with invalid API keys
4. Test with extremely long inputs
5. Test rapid clicking/spamming buttons

**Expected Results:**
- [ ] Network errors show user-friendly message
- [ ] Retry option available
- [ ] Rate limit errors handled gracefully
- [ ] Invalid API key errors clear
- [ ] Long inputs validated/truncated
- [ ] Button spam prevented (loading states)
- [ ] No crashes or blank screens
- [ ] Progress saved before errors

**Pass/Fail:** ______

---

## 3. UI/UX Testing

### 3.1 Responsive Design Testing

**Test on Devices:**
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

**Validation Points:**
- [ ] Layout adapts correctly
- [ ] Navigation accessible
- [ ] Text readable (no overflow)
- [ ] Buttons clickable
- [ ] Forms usable

---

### 3.2 Accessibility Testing

**Action:**
1. Test keyboard navigation (Tab, Enter, Esc)
2. Test with screen reader (if available)
3. Check color contrast
4. Test focus management

**Expected Results:**
- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible
- [ ] Logical tab order
- [ ] ARIA labels present
- [ ] Color contrast WCAG AA compliant

**Pass/Fail:** ______

---

### 3.3 User Experience Testing

**Evaluation Criteria:**
- [ ] Clear instructions at each stage
- [ ] Helpful error messages
- [ ] Progress indicators visible
- [ ] Loading states informative
- [ ] Animations smooth
- [ ] No jarring transitions
- [ ] Consistent UI patterns

**Pass/Fail:** ______

---

## 4. Performance Testing

### 4.1 Page Load Times

**Action:**
Measure load times for each stage:
- Stage 1: ______ ms
- Stage 2: ______ ms
- Stage 3: ______ ms
- Stage 4: ______ ms
- Stage 5: ______ ms

**Target:** < 2000ms for first contentful paint

**Pass/Fail:** ______

---

### 4.2 API Response Times

**Action:**
Measure response times for key operations:
- Analyze Idea: ______ ms
- Generate User Stories: ______ ms
- Generate User Journeys: ______ ms
- Analyze Architecture: ______ ms
- Compile Playbook: ______ ms

**Target:** < 30000ms for LLM operations

**Pass/Fail:** ______

---

## 5. Bug Tracking Template

### Bug Report Format

**Bug ID:** ______  
**Date Found:** ______  
**Severity:** Critical / High / Medium / Low  
**Stage:** ______  
**Description:** ______________________________  
**Steps to Reproduce:**
1. ______
2. ______
3. ______

**Expected Behavior:** ______________________________  
**Actual Behavior:** ______________________________  
**Screenshots/Logs:** ______________________________  
**Assigned To:** ______  
**Status:** Open / In Progress / Fixed / Closed  

---

## 6. Test Summary Report

### 6.1 Test Execution Summary

**Test Date:** ______  
**Tester:** ______  
**Total Scenarios:** 7  
**Scenarios Passed:** ______  
**Scenarios Failed:** ______  
**Pass Rate:** ______%

---

### 6.2 Critical Issues Found

| Issue ID | Severity | Stage | Description | Status |
|----------|----------|-------|-------------|--------|
| _______ | _______ | _____ | ___________ | ______ |
| _______ | _______ | _____ | ___________ | ______ |
| _______ | _______ | _____ | ___________ | ______ |

---

### 6.3 Recommendations

**Immediate Actions Required:**
- ______________________________
- ______________________________

**Enhancements Suggested:**
- ______________________________
- ______________________________

---

### 6.4 Sign-Off

**Tester Signature:** ______________________  
**Date:** ______________________  
**Approved for Staging:** Yes / No / Conditional  
**Comments:** ______________________________

---

**Next Steps:**
1. Address critical bugs
2. Retest failed scenarios
3. Document all fixes
4. Prepare for staging deployment

---

**Document Version:** 1.0  
**Last Updated:** November 2, 2025  
**Owner:** Development Team
