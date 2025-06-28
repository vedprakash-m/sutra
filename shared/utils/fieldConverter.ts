/**
 * Field Converter Utility
 * Handles automated conversion between snake_case (backend) and camelCase (frontend)
 * Part of the systematic resolution for data model inconsistency
 */

export type CaseConvention = 'snake_case' | 'camelCase';

/**
 * Convert a string from camelCase to snake_case
 */
export function toSnakeCase(str: string): string {
  return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
}

/**
 * Convert a string from snake_case to camelCase
 */
export function toCamelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

/**
 * Convert object keys from camelCase to snake_case
 */
export function convertObjectToSnakeCase<T extends Record<string, any>>(obj: T): Record<string, any> {
  if (!obj || typeof obj !== 'object') {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map(item => convertObjectToSnakeCase(item));
  }

  const converted: Record<string, any> = {};
  
  for (const [key, value] of Object.entries(obj)) {
    const snakeKey = toSnakeCase(key);
    
    if (value && typeof value === 'object' && !Array.isArray(value) && !(value instanceof Date)) {
      converted[snakeKey] = convertObjectToSnakeCase(value);
    } else if (Array.isArray(value)) {
      converted[snakeKey] = value.map(item => 
        typeof item === 'object' && item !== null ? convertObjectToSnakeCase(item) : item
      );
    } else {
      converted[snakeKey] = value;
    }
  }
  
  return converted;
}

/**
 * Convert object keys from snake_case to camelCase
 */
export function convertObjectToCamelCase<T extends Record<string, any>>(obj: T): Record<string, any> {
  if (!obj || typeof obj !== 'object') {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map(item => convertObjectToCamelCase(item));
  }

  const converted: Record<string, any> = {};
  
  for (const [key, value] of Object.entries(obj)) {
    const camelKey = toCamelCase(key);
    
    if (value && typeof value === 'object' && !Array.isArray(value) && !(value instanceof Date)) {
      converted[camelKey] = convertObjectToCamelCase(value);
    } else if (Array.isArray(value)) {
      converted[camelKey] = value.map(item => 
        typeof item === 'object' && item !== null ? convertObjectToCamelCase(item) : item
      );
    } else {
      converted[camelKey] = value;
    }
  }
  
  return converted;
}

/**
 * Mapping of common field names between conventions
 */
export const FIELD_MAPPINGS = {
  // Timestamp fields
  'created_at': 'createdAt',
  'updated_at': 'updatedAt',
  'last_login_at': 'lastLoginAt',
  'last_request_at': 'lastRequestAt',
  
  // ID fields
  'user_id': 'userId',
  'owner_id': 'userId', // Legacy mapping
  'prompt_id': 'promptId',
  'collection_id': 'collectionId',
  'playbook_id': 'playbookId',
  'request_id': 'requestId',
  
  // Status fields
  'is_public': 'isPublic',
  'is_active': 'isActive',
  'email_verified': 'emailVerified',
  
  // Count fields
  'usage_count': 'usageCount',
  'prompt_count': 'promptCount',
  'execution_count': 'executionCount',
  'total_requests': 'totalRequests',
  'monthly_requests': 'monthlyRequests',
  
  // Cost fields
  'total_spent': 'totalSpent',
  'monthly_spent': 'monthlySpent',
  'monthly_budget': 'monthlyBudget',
  'daily_requests': 'dailyRequests',
  'input_tokens': 'inputTokens',
  'output_tokens': 'outputTokens',
  'total_tokens': 'totalTokens',
  'request_duration': 'requestDuration',
  'request_type': 'requestType',
  'error_message': 'errorMessage',
  'max_tokens': 'maxTokens',
  'max_tokens_per_request': 'maxTokensPerRequest',
  
  // Execution fields
  'avg_execution_time': 'avgExecutionTime',
  'next_steps': 'nextSteps',
  'error_handling': 'errorHandling',
  'retry_count': 'retryCount',
  'fallback_step_id': 'fallbackStepId',
  'continue_on_error': 'continueOnError',
  'transform_type': 'transformType',
  'default_value': 'defaultValue',
  'default_provider': 'defaultProvider',
  'default_model': 'defaultModel',
  'budget_alerts': 'budgetAlerts',
  'execution_alerts': 'executionAlerts'
} as const;

/**
 * Convert object using explicit field mappings for better accuracy
 */
export function convertWithFieldMappings(
  obj: Record<string, any>, 
  direction: 'toSnakeCase' | 'toCamelCase'
): Record<string, any> {
  if (!obj || typeof obj !== 'object') {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map(item => convertWithFieldMappings(item, direction));
  }

  const converted: Record<string, any> = {};
  const mappings = direction === 'toSnakeCase' 
    ? Object.fromEntries(Object.entries(FIELD_MAPPINGS).map(([k, v]) => [v, k]))
    : FIELD_MAPPINGS;
  
  for (const [key, value] of Object.entries(obj)) {
    // Use explicit mapping if available, otherwise use automatic conversion
    const convertedKey = mappings[key as keyof typeof mappings] || 
      (direction === 'toSnakeCase' ? toSnakeCase(key) : toCamelCase(key));
    
    if (value && typeof value === 'object' && !Array.isArray(value) && !(value instanceof Date)) {
      converted[convertedKey] = convertWithFieldMappings(value, direction);
    } else if (Array.isArray(value)) {
      converted[convertedKey] = value.map(item => 
        typeof item === 'object' && item !== null 
          ? convertWithFieldMappings(item, direction) 
          : item
      );
    } else {
      converted[convertedKey] = value;
    }
  }
  
  return converted;
}

/**
 * Middleware for Express.js to automatically convert request/response data
 */
export function createFieldConverterMiddleware() {
  return {
    // Convert incoming request data from camelCase to snake_case
    convertRequest: (req: any, res: any, next: any) => {
      if (req.body) {
        req.body = convertWithFieldMappings(req.body, 'toSnakeCase');
      }
      if (req.query) {
        req.query = convertWithFieldMappings(req.query, 'toSnakeCase');
      }
      next();
    },

    // Convert outgoing response data from snake_case to camelCase
    convertResponse: (req: any, res: any, next: any) => {
      const originalJson = res.json;
      
      res.json = function(data: any) {
        const convertedData = convertWithFieldMappings(data, 'toCamelCase');
        return originalJson.call(this, convertedData);
      };
      
      next();
    }
  };
}

/**
 * Validation helper to check for field naming consistency
 */
export function validateFieldNaming(obj: Record<string, any>): {
  isConsistent: boolean;
  convention: CaseConvention | 'mixed';
  issues: string[];
} {
  const keys = Object.keys(obj);
  const snakeKeys = keys.filter(key => key.includes('_'));
  const camelKeys = keys.filter(key => /[A-Z]/.test(key));
  
  const issues: string[] = [];
  
  if (snakeKeys.length > 0 && camelKeys.length > 0) {
    issues.push(`Mixed naming conventions detected: ${snakeKeys.length} snake_case, ${camelKeys.length} camelCase`);
    return {
      isConsistent: false,
      convention: 'mixed',
      issues
    };
  }
  
  if (snakeKeys.length > camelKeys.length) {
    return {
      isConsistent: true,
      convention: 'snake_case',
      issues
    };
  } else {
    return {
      isConsistent: true,
      convention: 'camelCase',
      issues
    };
  }
}

/**
 * Debug utility to show field conversion mapping
 */
export function debugFieldConversion(obj: Record<string, any>): void {
  console.log('🔍 Field Conversion Debug:');
  console.log('Original:', obj);
  console.log('To Snake Case:', convertWithFieldMappings(obj, 'toSnakeCase'));
  console.log('To Camel Case:', convertWithFieldMappings(obj, 'toCamelCase'));
  console.log('Validation:', validateFieldNaming(obj));
}
