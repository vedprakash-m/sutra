# Technical Specification: Sutra - AI Operations Platform

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

---

## 5. Security Considerations

- **API Gateway (Azure Front Door Standard Tier):** First line of defense.
- **WAF:** Protection against common web vulnerabilities (SQLi, XSS) via custom rules.
- **DDoS Protection:** Basic volumetric attack protection.
- **Centralized Rate Limiting & Filtering:** Edge filtering/rate limiting reduces compute costs.
- **Authentication & Authorization:**
  - AAD B2C for user authentication.
  - Azure Functions validate JWT tokens for all API access (signature, expiration, issuer/audience, claims).
  - **Role-Based Access Control (RBAC):**
    - **Roles:** Agent, Contributor, PromptManager, Admin
    - **Entity-Level RBAC:** Permissions (read, write, execute, manage) on Collections, Prompts, Playbooks.
- **Data Encryption:**
  - At rest (Cosmos DB, Blob Storage) and in transit (HTTPS/TLS).
  - LLM API Keys stored in Azure Key Vault, accessed via Managed Identities.
  - Least privilege for Azure Functions.
- **Input Validation & Output Sanitization:**
  - Robust input validation (schema/type/length/regex).
  - Output sanitization (HTML escaping, PII redaction/masking).
- **Network Security:**
  - CORS configured to allow only frontend domain.
  - NSGs for VNet deployments (future consideration).

---

## 6. Cost Optimization Strategy (Serverless Focus)

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
- **Monitoring & Alerts:**
  - Azure Monitor, Application Insights with adaptive sampling.
  - Budgets and alerts in Azure Cost Management.
  - **Efficient Code:** Directly translates to cost savings.

---
