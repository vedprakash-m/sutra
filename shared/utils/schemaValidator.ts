/**
 * Schema Validator Utility - Simplified Version
 * Centralized validation for Sutra data models
 * Part of the systematic resolution for validation fragmentation
 */

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  data?: any;
}

export interface ValidationError {
  field: string;
  message: string;
  value?: any;
}

/**
 * Basic field validation functions
 */
export const validators = {
  required: (value: any, fieldName: string): string | null => {
    if (value === undefined || value === null || value === "") {
      return `${fieldName} is required`;
    }
    return null;
  },

  string: (
    value: any,
    fieldName: string,
    options: { minLength?: number; maxLength?: number } = {},
  ): string | null => {
    if (typeof value !== "string") {
      return `${fieldName} must be a string`;
    }
    if (options.minLength && value.length < options.minLength) {
      return `${fieldName} must be at least ${options.minLength} characters`;
    }
    if (options.maxLength && value.length > options.maxLength) {
      return `${fieldName} must be no more than ${options.maxLength} characters`;
    }
    return null;
  },

  email: (value: any, fieldName: string): string | null => {
    if (typeof value !== "string") {
      return `${fieldName} must be a string`;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      return `${fieldName} must be a valid email address`;
    }
    return null;
  },

  enum: (
    value: any,
    fieldName: string,
    allowedValues: any[],
  ): string | null => {
    if (!allowedValues.includes(value)) {
      return `${fieldName} must be one of: ${allowedValues.join(", ")}`;
    }
    return null;
  },

  number: (
    value: any,
    fieldName: string,
    options: { min?: number; max?: number } = {},
  ): string | null => {
    if (typeof value !== "number" || isNaN(value)) {
      return `${fieldName} must be a number`;
    }
    if (options.min !== undefined && value < options.min) {
      return `${fieldName} must be at least ${options.min}`;
    }
    if (options.max !== undefined && value > options.max) {
      return `${fieldName} must be no more than ${options.max}`;
    }
    return null;
  },

  integer: (
    value: any,
    fieldName: string,
    options: { min?: number; max?: number } = {},
  ): string | null => {
    if (!Number.isInteger(value)) {
      return `${fieldName} must be an integer`;
    }
    return validators.number(value, fieldName, options);
  },

  boolean: (value: any, fieldName: string): string | null => {
    if (typeof value !== "boolean") {
      return `${fieldName} must be a boolean`;
    }
    return null;
  },

  array: (
    value: any,
    fieldName: string,
    options: { minItems?: number; maxItems?: number } = {},
  ): string | null => {
    if (!Array.isArray(value)) {
      return `${fieldName} must be an array`;
    }
    if (options.minItems && value.length < options.minItems) {
      return `${fieldName} must have at least ${options.minItems} items`;
    }
    if (options.maxItems && value.length > options.maxItems) {
      return `${fieldName} must have no more than ${options.maxItems} items`;
    }
    return null;
  },

  objectId: (value: any, fieldName: string): string | null => {
    if (typeof value !== "string" || value.length === 0) {
      return `${fieldName} must be a non-empty string`;
    }
    return null;
  },

  timestamp: (value: any, fieldName: string): string | null => {
    if (typeof value === "string") {
      const date = new Date(value);
      if (isNaN(date.getTime())) {
        return `${fieldName} must be a valid ISO timestamp`;
      }
    } else if (!(value instanceof Date)) {
      return `${fieldName} must be a Date object or ISO timestamp string`;
    }
    return null;
  },
};

/**
 * Schema definitions for each entity type
 */
export const schemas = {
  prompt: {
    required: ["id", "title", "description", "content", "userId", "createdAt"],
    fields: {
      id: { validator: "objectId" },
      title: { validator: "string", options: { minLength: 1, maxLength: 200 } },
      description: {
        validator: "string",
        options: { minLength: 1, maxLength: 1000 },
      },
      content: { validator: "string", options: { minLength: 1 } },
      userId: { validator: "objectId" },
      tags: { validator: "array", options: { maxItems: 10 } },
      isPublic: { validator: "boolean" },
      category: {
        validator: "enum",
        options: [
          "writing",
          "coding",
          "analysis",
          "creative",
          "business",
          "other",
        ],
      },
      createdAt: { validator: "timestamp" },
      updatedAt: { validator: "timestamp" },
      usageCount: { validator: "integer", options: { min: 0 } },
      version: { validator: "string" },
    },
  },

  collection: {
    required: ["id", "name", "description", "userId", "createdAt"],
    fields: {
      id: { validator: "objectId" },
      name: { validator: "string", options: { minLength: 1, maxLength: 100 } },
      description: {
        validator: "string",
        options: { minLength: 1, maxLength: 500 },
      },
      userId: { validator: "objectId" },
      prompts: { validator: "array" },
      isPublic: { validator: "boolean" },
      tags: { validator: "array", options: { maxItems: 10 } },
      category: {
        validator: "enum",
        options: ["personal", "team", "public", "template", "other"],
      },
      createdAt: { validator: "timestamp" },
      updatedAt: { validator: "timestamp" },
      promptCount: { validator: "integer", options: { min: 0 } },
    },
  },

  playbook: {
    required: ["id", "name", "description", "userId", "createdAt", "steps"],
    fields: {
      id: { validator: "objectId" },
      name: { validator: "string", options: { minLength: 1, maxLength: 100 } },
      description: {
        validator: "string",
        options: { minLength: 1, maxLength: 1000 },
      },
      userId: { validator: "objectId" },
      steps: { validator: "array", options: { minItems: 1 } },
      tags: { validator: "array", options: { maxItems: 10 } },
      category: {
        validator: "enum",
        options: [
          "automation",
          "analysis",
          "content",
          "customer_service",
          "development",
          "other",
        ],
      },
      isPublic: { validator: "boolean" },
      version: { validator: "string" },
      createdAt: { validator: "timestamp" },
      updatedAt: { validator: "timestamp" },
      executionCount: { validator: "integer", options: { min: 0 } },
      avgExecutionTime: { validator: "number", options: { min: 0 } },
    },
  },

  user: {
    required: ["id", "email", "role", "createdAt"],
    fields: {
      id: { validator: "objectId" },
      email: { validator: "email" },
      name: { validator: "string", options: { minLength: 1, maxLength: 100 } },
      role: { validator: "enum", options: ["admin", "user", "guest"] },
      permissions: { validator: "array" },
      createdAt: { validator: "timestamp" },
      updatedAt: { validator: "timestamp" },
      lastLoginAt: { validator: "timestamp" },
      isActive: { validator: "boolean" },
      emailVerified: { validator: "boolean" },
    },
  },

  cost: {
    required: [
      "id",
      "userId",
      "provider",
      "model",
      "requestId",
      "timestamp",
      "cost",
    ],
    fields: {
      id: { validator: "objectId" },
      userId: { validator: "objectId" },
      provider: {
        validator: "enum",
        options: ["openai", "anthropic", "google", "local"],
      },
      model: { validator: "string" },
      requestId: { validator: "objectId" },
      promptId: { validator: "objectId" },
      playbookId: { validator: "objectId" },
      timestamp: { validator: "timestamp" },
      cost: { validator: "number", options: { min: 0 } },
      inputTokens: { validator: "integer", options: { min: 0 } },
      outputTokens: { validator: "integer", options: { min: 0 } },
      totalTokens: { validator: "integer", options: { min: 0 } },
      requestDuration: { validator: "number", options: { min: 0 } },
      requestType: {
        validator: "enum",
        options: [
          "prompt_execution",
          "playbook_step",
          "test_execution",
          "api_call",
        ],
      },
      status: {
        validator: "enum",
        options: ["success", "error", "timeout", "cancelled"],
      },
      errorMessage: { validator: "string" },
    },
  },
};
/**
 * Validate data against a schema
 */
export function validateData(
  schemaName: keyof typeof schemas,
  data: any,
  partial = false,
): ValidationResult {
  const schema = schemas[schemaName];
  if (!schema) {
    return {
      isValid: false,
      errors: [`Unknown schema: ${schemaName}`],
    };
  }

  const errors: string[] = [];
  const validatedData: any = {};

  // Check required fields (only for non-partial validation)
  if (!partial) {
    for (const requiredField of schema.required) {
      if (!(requiredField in data)) {
        errors.push(`Missing required field: ${requiredField}`);
        continue;
      }
    }
  }

  // Validate each field that exists in the data
  for (const [fieldName, fieldValue] of Object.entries(data)) {
    const fieldSchema = schema.fields[fieldName];

    if (!fieldSchema) {
      // Field not in schema - skip or warn?
      continue;
    }

    const validatorName = fieldSchema.validator;
    const validatorOptions = fieldSchema.options;

    if (validatorName in validators) {
      const validator = validators[validatorName as keyof typeof validators];
      let error: string | null = null;

      // Handle different validator signatures
      if (validatorName === "enum" && validatorOptions) {
        error = (validator as any)(fieldValue, fieldName, validatorOptions);
      } else if (validatorOptions) {
        error = (validator as any)(fieldValue, fieldName, validatorOptions);
      } else {
        error = (validator as any)(fieldValue, fieldName);
      }

      if (error) {
        errors.push(error);
      } else {
        validatedData[fieldName] = fieldValue;
      }
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    data: errors.length === 0 ? validatedData : undefined,
  };
}

/**
 * Convenience validation functions
 */
export const validatePrompt = (data: any, partial = false) =>
  validateData("prompt", data, partial);
export const validateCollection = (data: any, partial = false) =>
  validateData("collection", data, partial);
export const validatePlaybook = (data: any, partial = false) =>
  validateData("playbook", data, partial);
export const validateUser = (data: any, partial = false) =>
  validateData("user", data, partial);
export const validateCost = (data: any, partial = false) =>
  validateData("cost", data, partial);

/**
 * Create validation middleware for Express.js
 */
export function createValidationMiddleware(
  schemaName: keyof typeof schemas,
  options: {
    validateBody?: boolean;
    validateQuery?: boolean;
    partial?: boolean;
  } = {},
) {
  return (req: any, res: any, next: any) => {
    const errors: string[] = [];

    if (options.validateBody && req.body) {
      const result = validateData(schemaName, req.body, options.partial);
      if (!result.isValid) {
        errors.push(`Body validation: ${result.errors.join(", ")}`);
      } else if (result.data) {
        req.body = result.data; // Use validated data
      }
    }

    if (options.validateQuery && req.query) {
      const result = validateData(schemaName, req.query, true); // Query params are always partial
      if (!result.isValid) {
        errors.push(`Query validation: ${result.errors.join(", ")}`);
      }
    }

    if (errors.length > 0) {
      return res.status(400).json({
        error: "Validation failed",
        details: errors,
      });
    }

    next();
  };
}

/**
 * Validation middleware creators
 */
export const createPromptValidation = (options = {}) =>
  createValidationMiddleware("prompt", options);
export const createCollectionValidation = (options = {}) =>
  createValidationMiddleware("collection", options);
export const createPlaybookValidation = (options = {}) =>
  createValidationMiddleware("playbook", options);
export const createUserValidation = (options = {}) =>
  createValidationMiddleware("user", options);
export const createCostValidation = (options = {}) =>
  createValidationMiddleware("cost", options);
