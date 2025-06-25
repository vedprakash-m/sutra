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

- **Azure Active Directory B2C (AAD B2C):** User identities and authentication.
  - _Justification:_ Secure, scalable, cost-effective, managed.
- **Alternative (Enterprise):** Azure AD for SSO in enterprise deployments.

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

## 8. Cost Optimization Strategy (Serverless Focus)

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
- **Guest User Cost Controls:**
  - **Shared Demo LLM Keys:** Controlled quotas across all guest users
  - **Automatic Session Cleanup:** Prevents storage cost accumulation
  - **Rate Limiting:** Multi-layer protection against cost spikes
  - **Usage Analytics:** Track cost per guest vs. conversion value
  - **Response Caching:** Common guest queries cached to reduce LLM API costs
- **Monitoring & Alerts:**
  - Azure Monitor, Application Insights with adaptive sampling.
  - Budgets and alerts in Azure Cost Management.
  - **Guest-specific alerts:** Monitor guest user LLM usage and conversion costs
  - **Efficient Code:** Directly translates to cost savings.

---
