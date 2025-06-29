# Technical Specification: Sutra - Multi-LLM Prompt Studio

Ved Mishra - June 2025 - Version: 1.0

## 1. Architecture Overview

Sutra will leverage a serverless, event-driven architecture hosted on Microsoft Azure. This approach minimizes operational overhead, scales automatically with demand, and ensures cost-effectiveness by implementing a pay-per-execution/consumption model. The design explicitly avoids persistent, high-cost services like Redis cache to adhere to budget constraints.

For the MVP, the application will be deployed as a single-region, single environment setup for simplicity and cost control. Azure Front Door will route traffic to this single Azure Functions App instance in the designated region.

**The architecture will consist of:**

- **Frontend:** A static web application for the user interface.
- **API Gateway:** A global entry point for secure, performant, and managed API traffic.
- **Backend:** Serverless functions for all API logic and LLM orchestration.
- **Database:** A serverless NoSQL document database for application data.
- **Identity:** Managed identity for user authentication.
- **Storage:** Blob storage for static assets and larger data files.

```
+-------------------+           +-----------------------+           +----------------------------+
| User Web Browser  |           | Azure Static Web Apps |           | Azure Front Door (Standard)|
| (Frontend)        | --------> | (Frontend Hosting)    | --------> | (Global LB, CDN, WAF)      |
|                   |           +-----------------------+           | (Single Entry Point)       |
|                   |                                               |                            |
|                   |                                               |                            |
|                   |                                               |       +--------------------+
|                   |                                               |       | Azure Functions    |
|                   |           +-------------------+               |-----> | (Backend API &     |
|                   | <-------- | Azure Active      |               |       |  Logic)            |
|                   |           | Directory B2C     |               |       +--------------------+
|                   |           | (Authentication)  |               |                |
+-------------------+           +-------------------+               |                V
                                                                    | Azure Cosmos DB (NoSQL)    |
                                                                    | (Serverless Database)      |
                                                                    +----------------------------+
                                                                                 |
                                                                                 V
                                                                    +----------------------------+
                                                                    | External LLM Providers     |
                                                                    | (OpenAI, Gemini, Claude)   |
                                                                    +----------------------------+
                                                                                 |
                                                                                 V
                                                                    +----------------------------+
                                                                    | Azure Blob Storage         |
                                                                    | (File Storage)             |
                                                                    +----------------------------+
```

---

## 2. Proposed Tech Stack (Azure Services)

### 2.1. Frontend Hosting & Framework

- **Azure Static Web Apps (ASWA):** For hosting the client-side application.
  - _Justification:_ Global distribution, custom domains, integrated CI/CD (GitHub Actions), automatic SSL, generous free tier.
- **Framework:** React with TypeScript (rich UI, strong typing).

### 2.2. Backend API & Logic

- **Azure Front Door (Standard Tier):** API Gateway and global entry point.
  - _Justification:_ Centralized security (WAF), performance (global load balancing, CDN caching), simplified API management, offsets compute costs.
- **Azure Functions:** Serverless backend logic, API endpoints, LLM orchestration.
  - _Justification:_ Pay-per-execution, auto-scaling, cost-effective.
  - **Runtime & Language:** Python 3.12.
  - **Use Cases:**
    - User authentication & authorization callbacks
    - CRUD for Prompts, Collections, Playbooks
    - Multi-LLM orchestration
    - Playbook execution
    - External integrations (future)

### 2.3. Database

- **Azure Cosmos DB (NoSQL API, Serverless Mode):**
  - _Justification:_ Pay-per-use, low-latency, flexible JSON document model.

### 2.4. Identity & Access Management

- **Microsoft Entra ID (vedid.onmicrosoft.com):** Sole authentication provider per Apps_Auth_Requirement.md
  - _Authority:_ `https://login.microsoftonline.com/vedid.onmicrosoft.com`
  - _Justification:_ Enterprise-grade security, mandatory domain-wide SSO, cost elimination of Auth0/Firebase (~$240-480/month), unified audit trails
- **VedUser Standard:** Mandatory unified user object across all Vedprakash applications
- **Authentication Libraries:**
  - Frontend: `@azure/msal-react` (required)
  - Backend: `msal` Python library with JWKS caching
- **Token Management:** JWT with automatic refresh, sessionStorage caching for SSO
- **Security Implementation:**
  - JWKS caching with 1-hour TTL (mandatory)
  - Complete security headers (CSP, HSTS, X-Frame-Options)
  - Standardized `extractStandardUser()` function
  - Bearer token validation with signature verification
- **Cross-Domain SSO:** Seamless authentication across sutra.vedprakash.net, vimarsh.vedprakash.net, vigor.vedprakash.net, pathfinder.vedprakash.net, carpool.vedprakash.net
- **Guest User System:** IP-based rate limiting (5 calls/day) with preserved trial experience

### 2.5. External LLM Integration

- **Direct API Calls:** Azure Functions make direct HTTP API calls to LLM providers (OpenAI, Gemini, Claude).
  - _Justification:_ Simple, avoids latency/cost of intermediaries. Users provide their own API keys.

### 2.6. File Storage

- **Azure Blob Storage:** For large files (chat histories, exports, assets).
  - _Justification:_ Low-cost, scalable, pay-per-GB.

### 2.7. Monitoring & Logging

- **Azure Application Insights with Adaptive Sampling:** Performance monitoring, distributed tracing, operational logging.
  - _Justification:_ Real-time insights, cost-effective telemetry.
- **Azure Monitor Logs (Log Analytics Workspace):** Centralized log collection and querying.
  - _Justification:_ Debugging, auditing, analytics.
- **Cost Management:** Short retention policy (e.g., 14 days), daily ingestion cap.
- **PII Redaction:** Redact/mask PII in logs before storage.
- **Contextual Logging:** Structured JSON logs with trace/correlation IDs, userId, etc.

### 2.8. Continuous Integration/Continuous Deployment (CI/CD)

- **GitHub Actions:** Automated build, test, and deployment.
  - _Justification:_ Native ASWA integration, free tier, consistency.
- **Security Scanning:** SAST and dependency scanning in CI/CD.
- **Infrastructure as Code (IaC):** Bicep.
  - _Justification:_ Declarative syntax, native Azure support.

---

## 3. Data Models (Simplified)

All GUIDs are UUID v4. Timestamps are ISO 8601.

### 3.1. User Profile (`Users` Collection)

```json
{
  "id": "user_id_guid",
  "email": "user@example.com",
  "name": "John Doe",
  "teamId": "team_id_guid_optional",
  "role": "member",
  "userType": "registered" | "guest",
  "guestSessionData": {
    "sessionId": "guest_session_guid",
    "expiresAt": "2025-06-15T22:00:00Z",
    "usageCount": 3,
    "maxUsageCount": 5,
    "ipAddress": "192.168.1.1",
    "userAgent": "Mozilla/5.0...",
    "createdAt": "2025-06-14T22:00:00Z"
  },
  "llmApiKeys": {
    "openai": "kv-ref-to-secret",
    "google_gemini": "kv-ref-to-secret",
    "custom_endpoint_1": {
      "url": "https://api.custom.ai",
      "key": "kv-ref-to-secret"
    }
  },
  "createdAt": "2025-06-14T22:00:00Z",
  "updatedAt": "2025-06-14T22:00:00Z"
}
```

### 3.2. Prompt (`Prompts` Collection)

```json
{
  "id": "prompt_id_guid",
  "creatorId": "user_id_guid",
  "collectionId": "collection_id_guid",
  "currentVersionId": "version_id_guid",
  "name": "Marketing Email Draft",
  "description": "Template for new product launch emails.",
  "tags": ["marketing", "email", "template"],
  "visibility": "private" | "shared" | "public",
  "customVariables": {
    "product_name": { "type": "string", "label": "Product Name", "description": "Name of the product" },
    "target_audience": { "type": "dropdown", "options": ["SMEs", "Enterprises"], "label": "Target Audience" }
  },
  "createdAt": "2025-06-14T22:05:00Z",
  "updatedAt": "2025-06-14T22:05:00Z"
}
```

### 3.3. Prompt Version (`PromptVersions` Collection)

```json
{
  "id": "version_id_guid",
  "promptId": "prompt_id_guid",
  "versionNumber": 1,
  "promptText": "Act as a marketing expert for {{product_name}} targeting {{target_audience}}...",
  "contextDetails": {
    "intention": "Write a marketing email",
    "tone": "persuasive",
    "audience": "SMEs"
  },
  "llmEvaluations": [
    {
      "llm": "GPT-4o",
      "outputPreview": "Generated email body...",
      "score": "Good",
      "feedback": "Concise and engaging",
      "timestamp": "2025-06-14T22:10:00Z"
    }
  ],
  "createdAt": "2025-06-14T22:10:00Z"
}
```

### 3.4. Collection (`Collections` Collection)

```json
{
  "id": "collection_id_guid",
  "ownerId": "user_id_guid",
  "name": "My Marketing Prompts",
  "description": "Collection of prompts for marketing content.",
  "type": "private" | "shared_team" | "public_marketplace",
  "teamId": "team_id_guid_optional",
  "permissions": {
    "user_id_A": ["read", "write"],
    "team_role_agent": ["read", "execute"]
  },
  "createdAt": "2025-06-14T22:02:00Z",
  "updatedAt": "2025-06-14T22:02:00Z"
}
```

### 3.5. Playbook (`Playbooks` Collection)

```json
{
  "id": "playbook_id_guid",
  "creatorId": "user_id_guid",
  "name": "Customer Support Resolution Flow",
  "description": "Automated sequence for resolving common customer issues.",
  "visibility": "private" | "shared",
  "teamId": "team_id_guid_optional",
  "initialInputVariables": {
    "customer_name": { "type": "string", "label": "Customer Name" },
    "issue_summary": { "type": "text", "label": "Issue Summary" }
  },
  "steps": [
    {
      "stepId": "step1_guid",
      "type": "prompt",
      "promptId": "prompt_id_guid_fk",
      "explanationText": "This step generates the initial draft.",
      "outputParsingRules": {
        "regex": "Order ID: (\\d+)",
        "jsonPath": "$.order.id"
      },
      "variableMappings": {
        "extracted_order_id": "{{step1_guid.output.parsed.orderId}}"
      },
      "config": {
        "llm": "gemini-1.5-pro",
        "temperature": 0.7
      }
    }
    // ... more steps
  ],
  "createdAt": "2025-06-14T22:15:00Z",
  "updatedAt": "2025-06-14T22:15:00Z"
}
```

### 3.6. Playbook Execution Log (`PlaybookExecutions` Collection)

```json
{
  "id": "execution_id_guid",
  "playbookId": "playbook_id_guid",
  "userId": "user_id_guid",
  "status": "running" | "paused_for_review" | "completed" | "failed",
  "startTime": "2025-06-14T22:20:00Z",
  "endTime": "2025-06-14T22:25:00Z_optional",
  "initialInputs": { "customer_name": "Alice" },
  "stepLogs": [
    {
      "stepId": "step1_guid",
      "stepName": "Intro Email Generation",
      "status": "completed" | "failed" | "paused",
      "input": {
        "prompt_text": "Act as a sales agent...",
        "variables": { "product": "Sutra" }
      },
      "outputPreview": {
        "llm": "GPT-4o",
        "text": "Generated email preview...",
        "fullOutputRef": "blob_storage_url_optional",
        "score": "Good"
      },
      "error": "error_message_optional",
      "durationMs": 1500,
      "tokensConsumed": { "prompt": 100, "completion": 200 },
      "timestamp": "2025-06-14T22:21:00Z",
      "manualReview": {
        "reviewerId": "user_id_guid",
        "reviewedAt": "timestamp",
        "editedOutput": "user_modified_text_optional"
      }
    }
  ],
  "finalOutputRef": "blob_storage_url_final_output_optional",
  "auditTrail": [
    { "action": "playbook_started", "userId": "user_id_guid", "timestamp": "...", "logRef": "log_analytics_id_optional" },
    { "action": "manual_review_approved", "userId": "user_id_guid", "timestamp": "...", "logRef": "log_analytics_id_optional" }
  ]
}
```

### 3.7. Guest Session (`GuestSessions` Collection)

```json
{
  "id": "guest_session_guid",
  "sessionToken": "jwt_session_token",
  "userId": "guest_user_id_guid",
  "status": "active" | "expired" | "converted",
  "usageCount": 3,
  "maxUsageCount": 5,
  "ipAddress": "192.168.1.1",
  "userAgent": "Mozilla/5.0...",
  "geoLocation": {
    "country": "US",
    "region": "California"
  },
  "promptsCreated": ["prompt_id_1", "prompt_id_2"],
  "executionsPerformed": 3,
  "conversionTriggerShown": ["signup_modal", "usage_limit_warning"],
  "lastActivity": "2025-06-14T22:30:00Z",
  "createdAt": "2025-06-14T22:00:00Z",
  "expiresAt": "2025-06-15T22:00:00Z",
  "convertedUserId": "registered_user_id_guid_optional",
  "convertedAt": "2025-06-14T23:00:00Z_optional"
}
```

### 3.8. Guest Usage Analytics (`GuestAnalytics` Collection)

```json
{
  "id": "analytics_id_guid",
  "sessionId": "guest_session_guid",
  "eventType": "session_start" | "prompt_created" | "prompt_executed" | "conversion_trigger_shown" | "signup_clicked" | "session_expired",
  "eventData": {
    "promptId": "prompt_id_guid_optional",
    "llmProvider": "openai_optional",
    "executionTime": 1500,
    "conversionTriggerType": "usage_limit_optional"
  },
  "metadata": {
    "userAgent": "Mozilla/5.0...",
    "referrer": "https://example.com",
    "pageUrl": "/prompt-studio"
  },
  "timestamp": "2025-06-14T22:00:00Z"
}
```

````

---

## 4. API Endpoints (Examples)

All APIs are exposed via Azure Functions with HTTP triggers. Authentication uses AAD B2C tokens.

- `POST /api/prompts` – Create a new prompt
- `GET /api/prompts/{id}` – Get prompt details and current version
- `PUT /api/prompts/{id}` – Update prompt details (creates new version)
- `DELETE /api/prompts/{id}` – Delete a prompt
- `GET /api/prompts/{id}/versions` – Get all versions of a prompt (pagination)
- `POST /api/prompts/{id}/run` – Execute a specific prompt version against selected LLMs (Multi-LLM Compare)

  - **Request Body:**
    ```json
    {
      "versionId": "...",
      "llms": ["openai", "gemini"],
      "variables": { "product_name": "Sutra" },
      "outputFormat": "markdown"
    }
    ```
  - **Error Response:**
    ```json
    {
      "errorCode": "INVALID_LLM_KEY",
      "message": "Human-readable error message."
    }
    ```
  - **Success Response:**
    ```json
    { "llmOutputs": { "openai": { "text": "...", "score": "...", "format": "markdown" }, ... } }
    ```
  - **Input Validation:** Robust validation against schemas and types.

- `POST /api/collections` – Create a new collection
- `GET /api/collections` – Get user's/team's collections (pagination, filtering)
- `GET /api/collections/{id}/prompts` – Get prompts within a collection (pagination, filtering)
- `POST /api/playbooks` – Create a new playbook
- `GET /api/playbooks/{id}` – Get playbook details
- `POST /api/playbooks/{id}/run` – Execute a playbook (async)
  - **Request Body:**
    ```json
    { "initialInputs": { "customer_name": "Alice" } }
    ```
  - **Response:**
    ```json
    { "executionId": "...", "status": "running" }
    ```
- `GET /api/playbooks/executions/{id}` – Get real-time status and logs of a playbook execution
- `POST /api/playbooks/executions/{id}/continue` – Continue a paused playbook after manual review
- `POST /api/integrations/llm` – Connect LLM API key
  - **LLM Key Pre-validation:** Lightweight pre-validation call to LLM provider before storing in Key Vault.

### 4.1. Guest User API Endpoints

- `POST /api/guest/session` – Create a new guest session
  - **Request Body:**
    ```json
    {
      "userAgent": "Mozilla/5.0...",
      "referrer": "https://example.com",
      "timezone": "America/Los_Angeles"
    }
    ```
  - **Response:**
    ```json
    {
      "sessionToken": "jwt_session_token",
      "sessionId": "guest_session_guid",
      "expiresAt": "2025-06-15T22:00:00Z",
      "maxUsageCount": 5,
      "usageCount": 0
    }
    ```

- `GET /api/guest/session/{sessionId}` – Get guest session status and usage
  - **Response:**
    ```json
    {
      "sessionId": "guest_session_guid",
      "status": "active",
      "usageCount": 3,
      "maxUsageCount": 5,
      "expiresAt": "2025-06-15T22:00:00Z",
      "canCreatePrompts": true,
      "canExecutePrompts": true
    }
    ```

- `POST /api/guest/prompts` – Create a prompt as guest (rate limited)
  - **Rate Limiting:** 5 prompts per guest session
  - **Request Body:** Similar to regular prompt creation but with limited fields
  - **Response:** Includes conversion trigger when approaching limits

- `POST /api/guest/prompts/{id}/run` – Execute a prompt as guest (rate limited)
  - **Rate Limiting:** 5 executions per guest session
  - **LLM Restrictions:** Limited to specific LLM providers with demo keys
  - **Response:** Includes usage count and conversion triggers

- `POST /api/guest/convert` – Convert guest session to registered user
  - **Request Body:**
    ```json
    {
      "sessionId": "guest_session_guid",
      "email": "user@example.com",
      "name": "John Doe",
      "password": "secure_password"
    }
    ```
  - **Response:**
    ```json
    {
      "userId": "new_user_id_guid",
      "migrationStatus": "completed",
      "migratedPrompts": ["prompt_id_1", "prompt_id_2"],
      "authToken": "jwt_auth_token"
    }
    ```

- `POST /api/admin/guest/analytics` – Get guest user analytics (admin only)
  - **Response:** Aggregated analytics on guest user behavior, conversion rates

### 4.2. Rate Limiting & Throttling

- **Guest User Limits:**
  - 5 prompt creations per session
  - 5 prompt executions per session
  - 24-hour session duration
  - IP-based rate limiting: 10 sessions per IP per day
- **Registered User Limits:**
  - 100 API calls per minute
  - 1000 prompt executions per day (configurable by plan)
- **Implementation:** Azure Front Door rate limiting + Function-level checks

---

## 5. Security Considerations

- **API Gateway (Azure Front Door Standard Tier):** First line of defense.
- **WAF:** Protection against common web vulnerabilities (SQLi, XSS) via custom rules.
- **DDoS Protection:** Basic volumetric attack protection.
- **Centralized Rate Limiting & Filtering:** Edge filtering/rate limiting reduces compute costs.
- **Authentication & Authorization:**
  - AAD B2C for user authentication.
  - Guest users receive temporary JWT tokens with limited claims and short expiration.
  - Azure Functions validate JWT tokens for all API access (signature, expiration, issuer/audience, claims).
  - **Dual Authentication System:**
    - **Registered Users:** Full AAD B2C integration with persistent identity
    - **Guest Users:** Temporary session-based authentication with usage tracking
  - **Role-Based Access Control (RBAC):**
    - **Roles:** Agent, Contributor, PromptManager, Admin, Guest (new)
    - **Guest Role Restrictions:** Read-only access to public content, limited creation rights
    - **Entity-Level RBAC:** Permissions (read, write, execute, manage) on Collections, Prompts, Playbooks.
    - **Guest Permissions:** Limited to personal temporary workspace with automatic cleanup
- **Data Encryption:**
  - At rest (Cosmos DB, Blob Storage) and in transit (HTTPS/TLS).
  - LLM API Keys stored in Azure Key Vault, accessed via Managed Identities.
  - Least privilege for Azure Functions.
- **Input Validation & Output Sanitization:**
  - Robust input validation (schema/type/length/regex).
  - Output sanitization (HTML escaping, PII redaction/masking).
- **Guest User Security:**
  - **Session-based Authentication:** JWT tokens for guest sessions with short expiration (24 hours)
  - **IP-based Rate Limiting:** Prevent abuse from single IP addresses
  - **Content Restrictions:** Guest users cannot access private/team content
  - **Data Isolation:** Guest user data is clearly marked and subject to automatic cleanup
  - **Abuse Prevention:** Monitoring for suspicious patterns, CAPTCHA for high-frequency requests
  - **Limited LLM Access:** Guest users restricted to demo LLM keys with usage quotas
  - **Session Cleanup:** Automatic deletion of expired guest sessions and associated data after 7 days
  - **Content Filtering & LLM Guardrails:**
    - **Input Validation:** Enhanced filtering for guest user prompts to prevent misuse
    - **Output Monitoring:** Automated scanning of LLM responses for inappropriate content
    - **Prompt Safety Checks:** Pre-execution validation against known harmful patterns
    - **Usage Pattern Analysis:** Machine learning models to detect and prevent abuse
    - **Content Moderation:** Integration with Azure Content Moderator for text analysis
    - **Compliance Controls:** Automatic logging and reporting of safety violations
- **Network Security:**
  - CORS configured to allow only frontend domain.
  - NSGs for VNet deployments (future consideration).

---

## 7. Guest User System Architecture

### 7.1. Technical Implementation Overview

The guest user system enables anonymous users to trial Sutra's core functionality without registration. This system balances user experience with security and cost control through careful technical implementation.

**Key Technical Components:**

- **Session Management:** JWT-based guest sessions with configurable expiration
- **Rate Limiting:** Multi-layer throttling (IP, session, resource-based)
- **Data Lifecycle:** Automatic cleanup of guest data after expiration
- **Conversion Pipeline:** Seamless migration from guest to registered user
- **Analytics Tracking:** Comprehensive guest user behavior analytics

### 7.2. Guest Session Lifecycle

````

1. Anonymous User Visits → 2. Guest Session Created → 3. Usage Tracking → 4. Conversion Triggers → 5. Session Expiry/Conversion

````

**Technical Flow:**

1. **Session Creation:**
   - Azure Function generates guest session with unique ID
   - JWT token issued with guest claims and expiration
   - Session metadata stored in Cosmos DB
   - Client receives session token for API authentication

2. **Usage Tracking:**
   - Each API call updates usage counters in real-time
   - Rate limiting enforced at Azure Front Door and Function levels
   - Analytics events captured for behavior analysis

3. **Conversion Triggers:**
   - Smart triggers based on usage patterns and limits
   - Progressive disclosure of premium features
   - Contextual upgrade prompts without disrupting workflow

4. **Data Migration:**
   - On conversion, guest data migrated to new user account
   - Seamless transition with data preservation
   - Session invalidation and cleanup

### 7.3. Rate Limiting Architecture

**Multi-Layer Approach:**

1. **Azure Front Door Level:**
   - IP-based rate limiting (10 sessions per IP per day)
   - Geographic restrictions if needed
   - DDoS protection

2. **Azure Functions Level:**
   - Session-based limits (5 prompts, 5 executions)
   - Resource-specific throttling
   - Dynamic rate adjustment based on system load

3. **LLM API Level:**
   - Demo API keys with daily quotas
   - Fallback to cached responses for common queries
   - Cost protection mechanisms

### 7.4. Data Management & Privacy

**Guest Data Handling:**

- **Temporary Storage:** All guest data marked with TTL (Time To Live)
- **Automatic Cleanup:** Expired sessions cleaned up via Azure Functions timer trigger
- **Privacy Compliance:** Minimal data collection, no PII storage for guests
- **Data Isolation:** Guest and registered user data clearly separated

**Migration Strategy:**

```json
{
  "migrationProcess": {
    "step1": "Validate user registration data",
    "step2": "Create new registered user account",
    "step3": "Transfer guest prompts and collections",
    "step4": "Update ownership and permissions",
    "step5": "Invalidate guest session",
    "step6": "Send welcome email with migration summary"
  }
}
````

### 7.5. Monitoring & Analytics

**Guest User Metrics:**

- Session creation and conversion rates
- Usage patterns and feature adoption
- Geographic distribution and referral sources
- Technical performance and error rates

**Implementation:**

- Azure Application Insights for real-time monitoring
- Custom dashboards for guest user analytics
- Automated alerts for unusual patterns or system issues
- A/B testing framework for conversion optimization

### 7.6. Cost Optimization for Guest Users

**Resource Management:**

- **Shared LLM Keys:** Demo API keys shared across guest users with quotas
- **Response Caching:** Common prompts cached to reduce LLM API calls
- **Session Lifecycle:** Automatic cleanup prevents storage cost accumulation
- **Rate Limiting:** Prevents abuse and unexpected cost spikes

**Budget Controls:**

- Daily/monthly spending limits on demo LLM usage
- Real-time cost monitoring with automatic throttling
- Cost allocation tracking between guest and registered users

### 7.7. Frontend Integration

**Guest User Experience:**

- **Seamless Onboarding:** No registration required to start using core features
- **Progressive Disclosure:** Features and limitations revealed contextually
- **Usage Indicators:** Real-time display of remaining trial actions
- **Conversion Triggers:** Smart prompts for signup based on engagement

**Technical Implementation:**

```typescript
// Guest session management
interface GuestSession {
  sessionId: string;
  token: string;
  expiresAt: Date;
  usageCount: number;
  maxUsageCount: number;
  status: "active" | "expired" | "converted";
}

// Client-side rate limiting
const checkUsageLimit = (session: GuestSession, action: string) => {
  if (session.usageCount >= session.maxUsageCount) {
    showConversionModal("usage_limit_reached");
    return false;
  }
  return true;
};
```

**State Management:**

- Local storage for session persistence
- Real-time usage tracking with server sync
- Offline capability for prompt editing
- Seamless transition to authenticated state

**UI/UX Components:**

- Guest user banner with trial status
- Progressive conversion modals
- Usage limit warnings and notifications
- Instant access CTAs throughout the interface

---

## 8. AI Cost Management & Automation System

### 8.1. Architecture Overview

The AI Cost Management system provides comprehensive real-time budget tracking, automated cost controls, and predictive analytics for LLM usage across the platform. This system ensures cost transparency for users while providing robust administrative controls and automated safeguards.

**Core Components:**

- **Real-time Budget Tracking Engine**
- **Automated Cost Control System**
- **Predictive Analytics Pipeline**
- **Multi-tier Budget Enforcement**
- **Smart Model Selection Engine**
- **Cost Allocation & Billing Integration**

### 8.2. Data Models for Cost Management

#### 8.2.1. Budget Configuration (`BudgetConfigs` Collection)

```json
{
  "id": "budget_config_guid",
  "entityType": "user" | "team" | "guest_cohort" | "system",
  "entityId": "user_id_guid_or_team_id_guid",
  "name": "Monthly AI Budget",
  "budgetPeriod": "daily" | "weekly" | "monthly" | "quarterly",
  "budgetAmount": 100.00,
  "currency": "USD",
  "alertThresholds": [50, 75, 90, 95],
  "autoActions": {
    "75": ["email_alert", "dashboard_notification"],
    "90": ["restrict_expensive_models"],
    "95": ["pause_all_executions", "admin_alert"],
    "100": ["suspend_access", "emergency_alert"]
  },
  "modelRestrictions": {
    "gpt-4": { "maxCostPerCall": 0.50 },
    "claude-3-opus": { "maxCostPerCall": 0.75 },
    "fallbackModel": "gpt-3.5-turbo"
  },
  "rolloverPolicy": "reset" | "carry_forward",
  "isActive": true,
  "createdAt": "2025-06-14T22:00:00Z",
  "updatedAt": "2025-06-14T22:00:00Z"
}
```

#### 8.2.2. Real-time Usage Tracking (`UsageMetrics` Collection)

```json
{
  "id": "usage_metric_guid",
  "entityType": "user" | "team" | "guest_session",
  "entityId": "user_id_guid",
  "budgetConfigId": "budget_config_guid",
  "timeWindow": "2025-06-14T00:00:00Z_to_2025-06-14T23:59:59Z",
  "currentSpend": 45.67,
  "projectedSpend": 52.34,
  "budgetUtilization": 0.4567,
  "executionCount": 127,
  "modelUsage": {
    "gpt-4": { "calls": 23, "cost": 12.45, "tokens": 15420 },
    "gpt-3.5-turbo": { "calls": 89, "cost": 8.90, "tokens": 45600 },
    "claude-3-haiku": { "calls": 15, "cost": 3.75, "tokens": 8900 }
  },
  "costBreakdown": {
    "inputTokens": 25.30,
    "outputTokens": 18.45,
    "apiCalls": 1.92
  },
  "lastUpdated": "2025-06-14T22:30:00Z",
  "alertsTriggered": ["50_percent_warning"],
  "restrictionsActive": []
}
```

#### 8.2.3. Cost Prediction Data (`CostPredictions` Collection)

```json
{
  "id": "prediction_guid",
  "entityId": "user_id_guid",
  "predictionType": "daily" | "weekly" | "monthly",
  "predictionDate": "2025-06-15T00:00:00Z",
  "basedOnDays": 7,
  "historicalAverage": 12.45,
  "trendAdjustment": 1.15,
  "seasonalityFactor": 1.02,
  "predictedSpend": 14.55,
  "confidenceInterval": {
    "lower": 11.20,
    "upper": 17.90
  },
  "factorsConsidered": [
    "historical_usage",
    "day_of_week_pattern",
    "recent_trend",
    "user_behavior_change"
  ],
  "recommendedBudget": 18.00,
  "alertLevel": "medium",
  "createdAt": "2025-06-14T23:00:00Z"
}
```

#### 8.2.4. Cost Control Actions (`CostActions` Collection)

```json
{
  "id": "action_guid",
  "entityId": "user_id_guid",
  "actionType": "model_restriction" | "execution_pause" | "alert_sent" | "auto_fallback",
  "triggerReason": "budget_threshold_90",
  "triggerValue": 90.5,
  "actionDetails": {
    "restrictedModels": ["gpt-4", "claude-3-opus"],
    "fallbackModel": "gpt-3.5-turbo",
    "pauseDuration": "until_budget_reset",
    "notificationsSent": ["email", "dashboard", "admin_alert"]
  },
  "executedAt": "2025-06-14T22:35:00Z",
  "executedBy": "system" | "admin_user_id",
  "status": "active" | "resolved" | "overridden",
  "resolvedAt": "2025-06-15T08:00:00Z_optional",
  "resolution": "budget_reset" | "admin_override" | "manual_resolution"
}
```

### 8.3. Real-time Budget Tracking Implementation

#### 8.3.1. Cost Calculation Engine

```python
# Azure Function: Real-time cost tracking
class CostTracker:
    def __init__(self, cosmos_client, cache_client):
        self.cosmos_client = cosmos_client
        self.cache_client = cache_client
        self.model_pricing = self._load_model_pricing()

    async def track_execution_cost(self, execution_data):
        """Track cost in real-time as LLM executions complete"""
        cost_breakdown = self._calculate_cost(execution_data)

        # Update real-time metrics
        await self._update_usage_metrics(
            execution_data.user_id,
            cost_breakdown
        )

        # Check budget thresholds
        usage_status = await self._check_budget_status(
            execution_data.user_id
        )

        # Trigger automated actions if needed
        if usage_status.threshold_exceeded:
            await self._trigger_cost_controls(
                execution_data.user_id,
                usage_status
            )

        return cost_breakdown

    def _calculate_cost(self, execution_data):
        """Calculate precise cost based on model, tokens, and pricing"""
        model = execution_data.model
        input_tokens = execution_data.prompt_tokens
        output_tokens = execution_data.completion_tokens

        pricing = self.model_pricing[model]

        input_cost = (input_tokens / 1000) * pricing["input_cost_per_1k"]
        output_cost = (output_tokens / 1000) * pricing["output_cost_per_1k"]

        return {
            "total_cost": input_cost + output_cost,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "model": model,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens
            }
        }
```

#### 8.3.2. Budget Monitoring Service

```python
class BudgetMonitor:
    async def check_pre_execution_budget(self, user_id, estimated_cost):
        """Check budget before allowing execution"""
        current_usage = await self._get_current_usage(user_id)
        budget_config = await self._get_budget_config(user_id)

        projected_total = current_usage.current_spend + estimated_cost
        utilization = projected_total / budget_config.budget_amount

        if utilization >= 1.0:
            return {"allowed": False, "reason": "budget_exceeded"}

        if utilization >= 0.95:
            # Suggest cheaper model
            cheaper_model = self._suggest_cheaper_model(execution_request)
            return {
                "allowed": True,
                "warning": "budget_critical",
                "suggestion": cheaper_model
            }

        return {"allowed": True}

    async def _suggest_cheaper_model(self, execution_request):
        """Smart model selection based on budget constraints"""
        current_model = execution_request.model
        prompt_complexity = self._analyze_prompt_complexity(
            execution_request.prompt
        )

        # Model selection logic based on complexity and cost
        if prompt_complexity == "simple" and current_model == "gpt-4":
            return {
                "suggested_model": "gpt-3.5-turbo",
                "cost_savings": "~75%",
                "quality_impact": "minimal"
            }

        return None
```

### 8.4. Automated Cost Control System

#### 8.4.1. Multi-tier Enforcement

**Tier 1: Preventive Controls (Pre-execution)**

- Budget validation before each LLM call
- Smart model suggestion based on remaining budget
- Cost estimation with user confirmation for expensive requests

**Tier 2: Real-time Controls (During execution)**

- Streaming cost monitoring for long-running requests
- Automatic request termination if cost exceeds limits
- Dynamic model switching for multi-step playbooks

**Tier 3: Reactive Controls (Post-threshold)**

- Immediate restriction of expensive models
- Automatic pause of all executions
- Admin alerts and manual override capabilities

#### 8.4.2. Implementation Architecture

```python
class AutomatedCostControls:
    def __init__(self):
        self.control_policies = {
            50: [self._send_warning_alert],
            75: [self._restrict_premium_models, self._increase_monitoring],
            90: [self._pause_expensive_operations, self._admin_alert],
            95: [self._emergency_pause, self._executive_alert],
            100: [self._suspend_access, self._escalate_to_billing]
        }

    async def execute_threshold_actions(self, user_id, threshold, usage_data):
        """Execute automated actions when budget thresholds are crossed"""
        actions = self.control_policies.get(threshold, [])

        action_results = []
        for action in actions:
            try:
                result = await action(user_id, usage_data)
                action_results.append(result)

                # Log action for audit trail
                await self._log_cost_action(user_id, threshold, action.__name__, result)

            except Exception as e:
                await self._log_action_error(user_id, action.__name__, str(e))

        return action_results

    async def _restrict_premium_models(self, user_id, usage_data):
        """Restrict access to expensive models"""
        restricted_models = ["gpt-4", "claude-3-opus", "gemini-pro"]
        fallback_model = "gpt-3.5-turbo"

        # Update user's model access
        await self._update_model_restrictions(
            user_id,
            restricted_models,
            fallback_model
        )

        return {
            "action": "model_restriction",
            "restricted": restricted_models,
            "fallback": fallback_model,
            "timestamp": datetime.utcnow()
        }
```

### 8.5. Predictive Analytics Pipeline

#### 8.5.1. Usage Pattern Analysis

```python
class CostPredictionEngine:
    def __init__(self, ml_client):
        self.ml_client = ml_client
        self.prediction_models = self._load_prediction_models()

    async def generate_predictions(self, user_id, prediction_horizon="monthly"):
        """Generate cost predictions using historical data and ML models"""

        # Gather historical usage data
        historical_data = await self._get_historical_usage(
            user_id,
            lookback_days=30
        )

        # Feature engineering
        features = self._extract_features(historical_data)

        # Generate predictions
        predictions = {}

        # Trend-based prediction
        predictions["trend"] = self._calculate_trend_prediction(features)

        # Seasonal pattern prediction
        predictions["seasonal"] = self._calculate_seasonal_prediction(features)

        # ML model prediction
        predictions["ml"] = await self._ml_prediction(features)

        # Ensemble prediction
        final_prediction = self._ensemble_prediction(predictions)

        return {
            "predicted_spend": final_prediction["amount"],
            "confidence_interval": final_prediction["confidence"],
            "risk_level": self._assess_risk_level(final_prediction),
            "recommendations": self._generate_recommendations(final_prediction)
        }

    def _generate_recommendations(self, prediction):
        """Generate actionable recommendations based on predictions"""
        recommendations = []

        if prediction["risk_level"] == "high":
            recommendations.extend([
                "Consider setting a lower monthly budget",
                "Review usage of expensive models (GPT-4, Claude-3-Opus)",
                "Enable automatic model fallback",
                "Set up additional budget alerts at 60% and 80%"
            ])

        if prediction["efficiency_score"] < 0.7:
            recommendations.extend([
                "Optimize prompts to reduce token usage",
                "Use more cost-effective models for simple tasks",
                "Implement prompt caching for repeated queries"
            ])

        return recommendations
```

### 8.6. API Endpoints for Cost Management

#### 8.6.1. Budget Management APIs

```python
# Cost Management API Endpoints

@app.route('/api/budget/config', methods=['POST'])
async def create_budget_config(request):
    """Create or update budget configuration"""
    data = await request.json()

    budget_config = {
        "entityType": data["entityType"],
        "entityId": data["entityId"],
        "budgetAmount": data["budgetAmount"],
        "budgetPeriod": data["budgetPeriod"],
        "alertThresholds": data.get("alertThresholds", [50, 75, 90, 95]),
        "autoActions": data.get("autoActions", {}),
        "modelRestrictions": data.get("modelRestrictions", {})
    }

    # Validate and save
    result = await budget_service.create_config(budget_config)
    return json_response(result)

@app.route('/api/budget/usage/<entity_id>', methods=['GET'])
async def get_current_usage(entity_id):
    """Get real-time budget usage"""
    usage_data = await cost_tracker.get_current_usage(entity_id)

    return json_response({
        "currentSpend": usage_data.current_spend,
        "budgetAmount": usage_data.budget_amount,
        "utilization": usage_data.utilization,
        "projectedSpend": usage_data.projected_spend,
        "remainingBudget": usage_data.remaining_budget,
        "daysRemaining": usage_data.days_remaining,
        "alertLevel": usage_data.alert_level,
        "restrictionsActive": usage_data.restrictions_active
    })

@app.route('/api/budget/predictions/<user_id>', methods=['GET'])
async def get_cost_predictions(user_id):
    """Get cost predictions and recommendations"""
    predictions = await prediction_engine.generate_predictions(user_id)

    return json_response({
        "predictions": predictions,
        "recommendations": predictions["recommendations"],
        "riskAssessment": predictions["risk_level"]
    })

@app.route('/api/cost/estimate', methods=['POST'])
async def estimate_execution_cost(request):
    """Estimate cost before execution"""
    data = await request.json()

    estimate = await cost_estimator.estimate_cost(
        model=data["model"],
        prompt=data["prompt"],
        max_tokens=data.get("max_tokens", 1000)
    )

    return json_response({
        "estimatedCost": estimate.total_cost,
        "breakdown": estimate.breakdown,
        "budgetImpact": estimate.budget_impact,
        "alternatives": estimate.cheaper_alternatives
    })
```

### 8.7. Frontend Integration

#### 8.7.1. Real-time Budget Display

```typescript
// Budget tracking component
interface BudgetStatus {
  currentSpend: number;
  budgetAmount: number;
  utilization: number;
  alertLevel: 'safe' | 'warning' | 'critical' | 'exceeded';
  restrictionsActive: string[];
  timeRemaining: string;
}

const BudgetTracker: React.FC = () => {
  const [budgetStatus, setBudgetStatus] = useState<BudgetStatus | null>(null);

  useEffect(() => {
    // Real-time budget monitoring
    const interval = setInterval(async () => {
      const status = await api.getBudgetStatus();
      setBudgetStatus(status);
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const getBudgetColor = (utilization: number) => {
    if (utilization >= 1.0) return 'red';
    if (utilization >= 0.9) return 'orange';
    if (utilization >= 0.75) return 'yellow';
    return 'green';
  };

  return (
    <div className="budget-tracker">
      <div className="budget-bar">
        <div
          className="budget-progress"
          style={{
            width: `${Math.min(budgetStatus?.utilization * 100, 100)}%`,
            backgroundColor: getBudgetColor(budgetStatus?.utilization || 0)
          }}
        />
      </div>
      <div className="budget-details">
        <span>${budgetStatus?.currentSpend} / ${budgetStatus?.budgetAmount}</span>
        <span>{budgetStatus?.timeRemaining} remaining</span>
      </div>
      {budgetStatus?.restrictionsActive.length > 0 && (
        <div className="budget-restrictions">
          Restrictions: {budgetStatus.restrictionsActive.join(', ')}
        </div>
      )}
    </div>
  );
};
```

#### 8.7.2. Cost Preview Integration

```typescript
// Pre-execution cost preview
const CostPreview: React.FC<{prompt: string, model: string}> = ({ prompt, model }) => {
  const [costEstimate, setCostEstimate] = useState(null);
  const [alternatives, setAlternatives] = useState([]);

  useEffect(() => {
    const estimateCost = async () => {
      const estimate = await api.estimateExecutionCost({
        prompt,
        model,
        max_tokens: 1000
      });

      setCostEstimate(estimate);
      setAlternatives(estimate.alternatives);
    };

    estimateCost();
  }, [prompt, model]);

  return (
    <div className="cost-preview">
      <div className="estimated-cost">
        Estimated cost: ${costEstimate?.estimatedCost}
      </div>

      {alternatives.length > 0 && (
        <div className="cost-alternatives">
          <h4>Cheaper alternatives:</h4>
          {alternatives.map(alt => (
            <div key={alt.model} className="alternative">
              <span>{alt.model}: ${alt.cost}</span>
              <span className="savings">Save {alt.savings}%</span>
            </div>
          ))}
        </div>
      )}

      <div className="budget-impact">
        Budget impact: {costEstimate?.budgetImpact}%
      </div>
    </div>
  );
};
```

### 8.8. Administrative Controls

#### 8.8.1. Admin Dashboard Features

- **Global Budget Overview**: System-wide cost tracking and trends
- **User Budget Management**: Set and modify individual/team budgets
- **Cost Analytics**: Detailed breakdowns by user, model, and time period
- **Alert Management**: Configure and monitor automated alerts
- **Emergency Controls**: Manual override capabilities for critical situations

#### 8.8.2. Reporting and Analytics

```python
class CostAnalytics:
    async def generate_cost_report(self, entity_type, time_period):
        """Generate comprehensive cost analytics report"""

        report_data = {
            "summary": await self._get_cost_summary(entity_type, time_period),
            "trends": await self._analyze_cost_trends(entity_type, time_period),
            "model_breakdown": await self._get_model_usage_breakdown(entity_type, time_period),
            "user_rankings": await self._get_top_users_by_cost(time_period),
            "efficiency_metrics": await self._calculate_efficiency_metrics(entity_type, time_period),
            "predictions": await self._get_future_projections(entity_type),
            "recommendations": await self._generate_cost_optimization_recommendations(entity_type)
        }

        return report_data
```

## 9. Cost Optimization Strategy (Enhanced Serverless Focus)

- **Azure Functions (Consumption Plan):** Pay for execution time/memory and executions. Scales to zero when idle.
- **Cold Start Mitigation:** Acceptable trade-off for lower cost.
  - **Warm-up HTTP Trigger:** Timer Function pings critical APIs to keep warm.
  - **Efficient Code:** Optimize for speed and minimal memory.
- **Azure Cosmos DB (Serverless):** Pay-per-operation, no minimum throughput.
  - **Query Optimization:** Efficient queries, indexing, partitioning.
- **Azure Static Web Apps:** Free tier for basic hosting.
- **Azure Blob Storage:** Low-cost, scalable object storage.
  - **Data Lifecycle Management:** Move old outputs/logs to archive or delete per retention policy.
- **Azure Front Door (Standard):** Base fee offset by reduced compute/egress costs.
- **No Persistent Caching (Redis):** No fixed-cost caching.
  - **Alternative Caching:** Client-side, in-memory, and efficient indexing.
- **Enhanced Guest User Cost Controls:**
  - **Shared Demo LLM Keys:** Controlled quotas across all guest users
  - **Automatic Session Cleanup:** Prevents storage cost accumulation
  - **Rate Limiting:** Multi-layer protection against cost spikes
  - **Usage Analytics:** Track cost per guest vs. conversion value
  - **Response Caching:** Common guest queries cached to reduce LLM API costs
  - **Smart Model Selection:** Automatic fallback to cheaper models for guests
- **AI Cost Management Integration:**
  - **Real-time Cost Monitoring:** Live tracking of LLM usage costs
  - **Predictive Budget Analytics:** ML-powered cost forecasting
  - **Automated Cost Controls:** Multi-tier enforcement with smart fallbacks
  - **Cost Allocation Tracking:** Detailed attribution across users and teams
- **Monitoring & Alerts:**
  - Azure Monitor, Application Insights with adaptive sampling.
  - Budgets and alerts in Azure Cost Management.
  - **AI-specific alerts:** Monitor LLM usage patterns and cost anomalies
  - **Guest-specific alerts:** Monitor guest user LLM usage and conversion costs
  - **Efficient Code:** Directly translates to cost savings.

---
