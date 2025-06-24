# Container Name Analysis and Fix Plan

## Problem Summary
The Users container was missing because of two issues:
1. **Infrastructure Gap**: The `persistent.bicep` file didn't define the Users container
2. **Case Mismatch**: Inconsistent container naming between infrastructure and application code

## Container Name Issues Discovered

### Infrastructure defines (in persistent.bicep):
- `prompts` (lowercase)
- `collections` (lowercase)  
- `playbooks` (lowercase)
- `usage` (lowercase)
- `config` (lowercase)
- `Users` (✅ NOW ADDED)

### Application code uses:
- `Prompts` (capital P) - used in collections_api
- `Collections` (capital C) - used in collections_api
- `Playbooks` (capital P) - used in playbooks_api
- `Users` (capital U) - used throughout user management
- `users` (lowercase u) - used in admin_api
- `SystemConfig` - used in admin_api (NOT DEFINED ANYWHERE)
- `executions` - used in playbooks_api (NOT DEFINED ANYWHERE)
- `AuditLog` - used in role_management (NOT DEFINED ANYWHERE)

### Non-existent method calls found:
- `get_users_container()` - FIXED ✅
- `get_prompts_container()` - FIXED ✅
- `get_collections_container()` - FIXED ✅
- `get_playbooks_container()` - used in playbooks_api
- `get_config_container()` - FIXED ✅
- `get_executions_container()` - used in playbooks_api

## Fix Plan

### 1. Infrastructure Updates (persistent.bicep)
- ✅ Add Users container (DONE)
- Add missing containers:
  - executions (for playbook execution tracking)
  - SystemConfig (for system configuration)
  - AuditLog (for audit logging)
- Fix case mismatches:
  - Change `prompts` → `Prompts`
  - Change `collections` → `Collections`  
  - Change `playbooks` → `Playbooks`

### 2. Application Code Fixes
- ✅ Fix admin_api non-existent method calls (DONE)
- Fix playbooks_api non-existent method calls
- Standardize container naming throughout codebase
- Fix case mismatches in existing container references

### 3. Database Migration
- The case changes will require data migration since container names are case-sensitive
- Need to consider if we should:
  - Update infrastructure to match current app naming (uppercase)
  - Update app code to match current infrastructure (lowercase)
  - Create migration scripts to move data between containers

## Recommended Approach
Since the application code mostly uses uppercase names and we've already created "Users" with uppercase, let's:
1. Update infrastructure to use uppercase container names
2. Add missing containers
3. Fix remaining method call issues
4. Test thoroughly

## Risk Assessment
- **HIGH**: Case mismatches mean app is likely not working with real containers
- **MEDIUM**: Missing containers cause runtime errors
- **LOW**: Method call fixes are straightforward

# Users Container Missing - Root Cause Analysis & Fix

## Root Cause
The Users container was missing due to **two critical infrastructure and code issues**:

### 1. Infrastructure Gap
**Problem**: The `infrastructure/persistent.bicep` file did not define the "Users" container.
**Impact**: Even though the application code tried to access "Users", the container didn't exist in Cosmos DB.

### 2. Systematic Case Mismatch Issues
**Problem**: Inconsistent container naming between infrastructure and application code.

**Infrastructure defined** (all lowercase):
- `prompts` ❌
- `collections` ❌
- `playbooks` ❌ 
- `usage` ✅ (still lowercase)
- `config` ✅ (still lowercase)

**Application code expected** (mixed case):
- `Prompts` ✅ (uppercase P)
- `Collections` ✅ (uppercase C)
- `Playbooks` ✅ (uppercase P)
- `Users` ✅ (uppercase U)
- `Executions` ❌ (not defined anywhere)
- `SystemConfig` ❌ (not defined anywhere)
- `AuditLog` ❌ (not defined anywhere)

### 3. Non-existent Method Calls
**Problem**: Application code called methods that didn't exist on DatabaseManager:
- ❌ `get_users_container()`
- ❌ `get_prompts_container()`
- ❌ `get_collections_container()`
- ❌ `get_playbooks_container()`
- ❌ `get_config_container()`
- ❌ `get_executions_container()`

**Should have been**: `get_container("ContainerName")`

## Fixes Applied

### ✅ Infrastructure Updates (persistent.bicep)
1. **Added missing Users container** with correct partition key (`/id`)
2. **Fixed case mismatches**:
   - `prompts` → `Prompts`
   - `collections` → `Collections`
   - `playbooks` → `Playbooks`
3. **Added missing containers**:
   - `Executions` (partition key: `/userId`)
   - `SystemConfig` (partition key: `/type`)  
   - `AuditLog` (partition key: `/userId`, 90-day TTL)

### ✅ Application Code Fixes
1. **Fixed admin_api** - replaced all non-existent method calls with `get_container()`
2. **Fixed playbooks_api** - replaced all non-existent method calls with `get_container()`
3. **Fixed prompts_api** - updated container names to use proper casing
4. **Standardized container names** throughout the codebase

### ✅ Method Call Corrections
- `get_users_container()` → `get_container("Users")`
- `get_prompts_container()` → `get_container("Prompts")`
- `get_collections_container()` → `get_container("Collections")`
- `get_playbooks_container()` → `get_container("Playbooks")`
- `get_config_container()` → `get_container("config")`
- `get_executions_container()` → `get_container("Executions")`

## Container Naming Convention Established
**Uppercase for primary entities**: Users, Prompts, Collections, Playbooks, Executions, SystemConfig, AuditLog
**Lowercase for system containers**: usage, config

## Why This Wasn't Caught Earlier
1. **Development mode**: The DatabaseManager returns mock data in development, masking missing containers
2. **Testing gaps**: Tests used mocks that didn't reflect the actual container structure
3. **Infrastructure-Application disconnect**: IaC was defined separately from application development

## Prevention Measures
1. **Infrastructure validation**: Ensure all containers referenced in code are defined in IaC
2. **Integration testing**: Test against real Cosmos DB containers, not just mocks
3. **Container naming standards**: Document and enforce consistent naming conventions
4. **Database initialization checks**: Add startup validation to ensure all required containers exist

## Next Steps
1. **Deploy updated infrastructure** to create missing containers with correct names
2. **Data migration** (if needed) from old lowercase containers to new uppercase ones
3. **Test all endpoints** to ensure container access works correctly
4. **Update documentation** with correct container names and conventions
