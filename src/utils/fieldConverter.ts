/**
 * Field Converter for Frontend API Service
 * Handles conversion between camelCase (frontend) and snake_case (backend)
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
 * Common field mappings for backward compatibility
 */
export const FIELD_MAPPINGS = {
  // Legacy mappings that might exist in data
  'owner_id': 'userId',
  'created_at': 'createdAt',
  'updated_at': 'updatedAt',
  'user_id': 'userId',
  'prompt_id': 'promptId',
  'collection_id': 'collectionId',
  'playbook_id': 'playbookId',
  'is_public': 'isPublic',
  'usage_count': 'usageCount',
  'prompt_count': 'promptCount',
  'execution_count': 'executionCount',
  'avg_execution_time': 'avgExecutionTime',
  
  // Pagination fields
  'current_page': 'currentPage',
  'total_pages': 'totalPages',
  'total_count': 'totalCount',
  'has_next': 'hasNext',
  'has_prev': 'hasPrev',
  
  // Cost fields
  'total_spent': 'totalSpent',
  'monthly_spent': 'monthlySpent',
  'monthly_budget': 'monthlyBudget',
  'input_tokens': 'inputTokens',
  'output_tokens': 'outputTokens',
  'total_tokens': 'totalTokens',
  'request_duration': 'requestDuration',
  'request_type': 'requestType',
  'error_message': 'errorMessage'
} as const;

/**
 * Convert object using explicit field mappings for accuracy
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
