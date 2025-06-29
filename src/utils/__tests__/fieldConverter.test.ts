import {
  toSnakeCase,
  toCamelCase,
  convertObjectToSnakeCase,
  convertObjectToCamelCase,
  convertWithFieldMappings,
  FIELD_MAPPINGS,
} from "../fieldConverter";

describe("fieldConverter", () => {
  describe("toSnakeCase", () => {
    it("should convert camelCase to snake_case", () => {
      expect(toSnakeCase("userName")).toBe("user_name");
      expect(toSnakeCase("userId")).toBe("user_id");
      expect(toSnakeCase("isPublic")).toBe("is_public");
      expect(toSnakeCase("createdAt")).toBe("created_at");
      expect(toSnakeCase("totalSpent")).toBe("total_spent");
    });

    it("should handle single words", () => {
      expect(toSnakeCase("user")).toBe("user");
      expect(toSnakeCase("id")).toBe("id");
      expect(toSnakeCase("name")).toBe("name");
    });

    it("should handle multiple capital letters", () => {
      expect(toSnakeCase("XMLHttpRequest")).toBe("_x_m_l_http_request");
      expect(toSnakeCase("HTMLElement")).toBe("_h_t_m_l_element");
      expect(toSnakeCase("APIKey")).toBe("_a_p_i_key");
    });

    it("should handle empty string", () => {
      expect(toSnakeCase("")).toBe("");
    });

    it("should handle already snake_case strings", () => {
      expect(toSnakeCase("user_name")).toBe("user_name");
      expect(toSnakeCase("created_at")).toBe("created_at");
    });
  });

  describe("toCamelCase", () => {
    it("should convert snake_case to camelCase", () => {
      expect(toCamelCase("user_name")).toBe("userName");
      expect(toCamelCase("user_id")).toBe("userId");
      expect(toCamelCase("is_public")).toBe("isPublic");
      expect(toCamelCase("created_at")).toBe("createdAt");
      expect(toCamelCase("total_spent")).toBe("totalSpent");
    });

    it("should handle single words", () => {
      expect(toCamelCase("user")).toBe("user");
      expect(toCamelCase("id")).toBe("id");
      expect(toCamelCase("name")).toBe("name");
    });

    it("should handle multiple underscores", () => {
      expect(toCamelCase("some_very_long_field_name")).toBe(
        "someVeryLongFieldName",
      );
      expect(toCamelCase("xml_http_request")).toBe("xmlHttpRequest");
      expect(toCamelCase("html_element")).toBe("htmlElement");
    });

    it("should handle empty string", () => {
      expect(toCamelCase("")).toBe("");
    });

    it("should handle already camelCase strings", () => {
      expect(toCamelCase("userName")).toBe("userName");
      expect(toCamelCase("createdAt")).toBe("createdAt");
    });

    it("should handle leading underscores", () => {
      expect(toCamelCase("_private_field")).toBe("PrivateField");
      expect(toCamelCase("__internal_method")).toBe("_InternalMethod");
    });
  });

  describe("convertObjectToSnakeCase", () => {
    it("should convert simple object keys to snake_case", () => {
      const input = {
        userName: "john",
        userId: 123,
        isPublic: true,
        createdAt: "2023-01-01",
      };

      const expected = {
        user_name: "john",
        user_id: 123,
        is_public: true,
        created_at: "2023-01-01",
      };

      expect(convertObjectToSnakeCase(input)).toEqual(expected);
    });

    it("should handle nested objects", () => {
      const input = {
        userProfile: {
          firstName: "John",
          lastName: "Doe",
          accountSettings: {
            isPrivate: true,
            emailNotifications: false,
          },
        },
        metaData: {
          createdAt: "2023-01-01",
          updatedAt: "2023-01-02",
        },
      };

      const expected = {
        user_profile: {
          first_name: "John",
          last_name: "Doe",
          account_settings: {
            is_private: true,
            email_notifications: false,
          },
        },
        meta_data: {
          created_at: "2023-01-01",
          updated_at: "2023-01-02",
        },
      };

      expect(convertObjectToSnakeCase(input)).toEqual(expected);
    });

    it("should handle arrays of objects", () => {
      const input = {
        userList: [
          { userName: "john", userId: 1 },
          { userName: "jane", userId: 2 },
        ],
        metaTags: ["tag1", "tag2", "tag3"],
      };

      const expected = {
        user_list: [
          { user_name: "john", user_id: 1 },
          { user_name: "jane", user_id: 2 },
        ],
        meta_tags: ["tag1", "tag2", "tag3"],
      };

      expect(convertObjectToSnakeCase(input)).toEqual(expected);
    });

    it("should handle arrays of primitives", () => {
      const input = {
        stringArray: ["a", "b", "c"],
        numberArray: [1, 2, 3],
        booleanArray: [true, false, true],
      };

      const expected = {
        string_array: ["a", "b", "c"],
        number_array: [1, 2, 3],
        boolean_array: [true, false, true],
      };

      expect(convertObjectToSnakeCase(input)).toEqual(expected);
    });

    it("should handle Date objects", () => {
      const date = new Date("2023-01-01");
      const input = {
        createdAt: date,
        userInfo: {
          lastLogin: date,
        },
      };

      const expected = {
        created_at: date,
        user_info: {
          last_login: date,
        },
      };

      expect(convertObjectToSnakeCase(input)).toEqual(expected);
    });

    it("should handle null and undefined values", () => {
      const input = {
        userName: null,
        userId: undefined,
        isActive: true,
      };

      const expected = {
        user_name: null,
        user_id: undefined,
        is_active: true,
      };

      expect(convertObjectToSnakeCase(input)).toEqual(expected);
    });

    it("should handle non-object inputs", () => {
      expect(convertObjectToSnakeCase(null as any)).toBe(null);
      expect(convertObjectToSnakeCase(undefined as any)).toBe(undefined);
      expect(convertObjectToSnakeCase("string" as any)).toBe("string");
      expect(convertObjectToSnakeCase(123 as any)).toBe(123);
      expect(convertObjectToSnakeCase(true as any)).toBe(true);
    });

    it("should handle arrays directly", () => {
      const input = [
        { userName: "john", userId: 1 },
        { userName: "jane", userId: 2 },
      ];

      const expected = [
        { user_name: "john", user_id: 1 },
        { user_name: "jane", user_id: 2 },
      ];

      expect(convertObjectToSnakeCase(input)).toEqual(expected);
    });

    it("should handle mixed arrays with objects and primitives", () => {
      const input = [
        { userName: "john" },
        "simpleString",
        123,
        { userInfo: { isActive: true } },
      ];

      const expected = [
        { user_name: "john" },
        "simpleString",
        123,
        { user_info: { is_active: true } },
      ];

      expect(convertObjectToSnakeCase(input)).toEqual(expected);
    });
  });

  describe("convertObjectToCamelCase", () => {
    it("should convert simple object keys to camelCase", () => {
      const input = {
        user_name: "john",
        user_id: 123,
        is_public: true,
        created_at: "2023-01-01",
      };

      const expected = {
        userName: "john",
        userId: 123,
        isPublic: true,
        createdAt: "2023-01-01",
      };

      expect(convertObjectToCamelCase(input)).toEqual(expected);
    });

    it("should handle nested objects", () => {
      const input = {
        user_profile: {
          first_name: "John",
          last_name: "Doe",
          account_settings: {
            is_private: true,
            email_notifications: false,
          },
        },
        meta_data: {
          created_at: "2023-01-01",
          updated_at: "2023-01-02",
        },
      };

      const expected = {
        userProfile: {
          firstName: "John",
          lastName: "Doe",
          accountSettings: {
            isPrivate: true,
            emailNotifications: false,
          },
        },
        metaData: {
          createdAt: "2023-01-01",
          updatedAt: "2023-01-02",
        },
      };

      expect(convertObjectToCamelCase(input)).toEqual(expected);
    });

    it("should handle arrays of objects", () => {
      const input = {
        user_list: [
          { user_name: "john", user_id: 1 },
          { user_name: "jane", user_id: 2 },
        ],
        meta_tags: ["tag1", "tag2", "tag3"],
      };

      const expected = {
        userList: [
          { userName: "john", userId: 1 },
          { userName: "jane", userId: 2 },
        ],
        metaTags: ["tag1", "tag2", "tag3"],
      };

      expect(convertObjectToCamelCase(input)).toEqual(expected);
    });

    it("should handle Date objects", () => {
      const date = new Date("2023-01-01");
      const input = {
        created_at: date,
        user_info: {
          last_login: date,
        },
      };

      const expected = {
        createdAt: date,
        userInfo: {
          lastLogin: date,
        },
      };

      expect(convertObjectToCamelCase(input)).toEqual(expected);
    });

    it("should handle null and undefined values", () => {
      const input = {
        user_name: null,
        user_id: undefined,
        is_active: true,
      };

      const expected = {
        userName: null,
        userId: undefined,
        isActive: true,
      };

      expect(convertObjectToCamelCase(input)).toEqual(expected);
    });

    it("should handle non-object inputs", () => {
      expect(convertObjectToCamelCase(null as any)).toBe(null);
      expect(convertObjectToCamelCase(undefined as any)).toBe(undefined);
      expect(convertObjectToCamelCase("string" as any)).toBe("string");
      expect(convertObjectToCamelCase(123 as any)).toBe(123);
      expect(convertObjectToCamelCase(true as any)).toBe(true);
    });

    it("should handle arrays directly", () => {
      const input = [
        { user_name: "john", user_id: 1 },
        { user_name: "jane", user_id: 2 },
      ];

      const expected = [
        { userName: "john", userId: 1 },
        { userName: "jane", userId: 2 },
      ];

      expect(convertObjectToCamelCase(input)).toEqual(expected);
    });
  });

  describe("FIELD_MAPPINGS", () => {
    it("should contain expected field mappings", () => {
      expect(FIELD_MAPPINGS.owner_id).toBe("userId");
      expect(FIELD_MAPPINGS.created_at).toBe("createdAt");
      expect(FIELD_MAPPINGS.updated_at).toBe("updatedAt");
      expect(FIELD_MAPPINGS.user_id).toBe("userId");
      expect(FIELD_MAPPINGS.prompt_id).toBe("promptId");
      expect(FIELD_MAPPINGS.collection_id).toBe("collectionId");
      expect(FIELD_MAPPINGS.playbook_id).toBe("playbookId");
      expect(FIELD_MAPPINGS.is_public).toBe("isPublic");
      expect(FIELD_MAPPINGS.usage_count).toBe("usageCount");
      expect(FIELD_MAPPINGS.total_spent).toBe("totalSpent");
      expect(FIELD_MAPPINGS.input_tokens).toBe("inputTokens");
      expect(FIELD_MAPPINGS.output_tokens).toBe("outputTokens");
    });

    it("should be a readonly constant", () => {
      // Test that it's a const object with expected properties
      expect(typeof FIELD_MAPPINGS).toBe("object");
      expect(FIELD_MAPPINGS.user_id).toBe("userId");
      expect(FIELD_MAPPINGS.created_at).toBe("createdAt");
    });
  });

  describe("convertWithFieldMappings", () => {
    it("should convert to snake_case using explicit mappings", () => {
      const input = {
        userId: 123,
        createdAt: "2023-01-01",
        isPublic: true,
        totalSpent: 100.5,
        customField: "value",
      };

      const expected = {
        user_id: 123,
        created_at: "2023-01-01",
        is_public: true,
        total_spent: 100.5,
        custom_field: "value", // Falls back to automatic conversion
      };

      expect(convertWithFieldMappings(input, "toSnakeCase")).toEqual(expected);
    });

    it("should convert to camelCase using explicit mappings", () => {
      const input = {
        user_id: 123,
        created_at: "2023-01-01",
        is_public: true,
        total_spent: 100.5,
        custom_field: "value",
      };

      const expected = {
        userId: 123,
        createdAt: "2023-01-01",
        isPublic: true,
        totalSpent: 100.5,
        customField: "value", // Falls back to automatic conversion
      };

      expect(convertWithFieldMappings(input, "toCamelCase")).toEqual(expected);
    });

    it("should handle nested objects with field mappings", () => {
      const input = {
        userId: 123,
        userProfile: {
          createdAt: "2023-01-01",
          isPublic: false,
          metaData: {
            totalSpent: 50.25,
            inputTokens: 1000,
          },
        },
      };

      const expected = {
        user_id: 123,
        user_profile: {
          created_at: "2023-01-01",
          is_public: false,
          meta_data: {
            total_spent: 50.25,
            input_tokens: 1000,
          },
        },
      };

      expect(convertWithFieldMappings(input, "toSnakeCase")).toEqual(expected);
    });

    it("should handle arrays of objects with field mappings", () => {
      const input = {
        users: [
          { userId: 1, createdAt: "2023-01-01", isPublic: true },
          { userId: 2, createdAt: "2023-01-02", isPublic: false },
        ],
        totalSpent: 200.75,
      };

      const expected = {
        users: [
          { user_id: 1, created_at: "2023-01-01", is_public: true },
          { user_id: 2, created_at: "2023-01-02", is_public: false },
        ],
        total_spent: 200.75,
      };

      expect(convertWithFieldMappings(input, "toSnakeCase")).toEqual(expected);
    });

    it("should handle Date objects with field mappings", () => {
      const date = new Date("2023-01-01");
      const input = {
        createdAt: date,
        userId: 123,
        settings: {
          updatedAt: date,
          isPublic: true,
        },
      };

      const expected = {
        created_at: date,
        user_id: 123,
        settings: {
          updated_at: date,
          is_public: true,
        },
      };

      expect(convertWithFieldMappings(input, "toSnakeCase")).toEqual(expected);
    });

    it("should handle non-object inputs with field mappings", () => {
      expect(convertWithFieldMappings(null as any, "toSnakeCase")).toBe(null);
      expect(convertWithFieldMappings(undefined as any, "toCamelCase")).toBe(
        undefined,
      );
      expect(convertWithFieldMappings("string" as any, "toSnakeCase")).toBe(
        "string",
      );
      expect(convertWithFieldMappings(123 as any, "toCamelCase")).toBe(123);
    });

    it("should handle arrays directly with field mappings", () => {
      const input = [
        { userId: 1, createdAt: "2023-01-01" },
        { userId: 2, isPublic: true },
      ];

      const expected = [
        { user_id: 1, created_at: "2023-01-01" },
        { user_id: 2, is_public: true },
      ];

      expect(convertWithFieldMappings(input, "toSnakeCase")).toEqual(expected);
    });

    it("should prefer explicit mappings over automatic conversion", () => {
      const input = {
        userId: 123, // Should use mapping: user_id
        customUserId: 456, // Should use automatic conversion: custom_user_id
      };

      const result = convertWithFieldMappings(input, "toSnakeCase");
      expect(result.user_id).toBe(123); // Explicit mapping
      expect(result.custom_user_id).toBe(456); // Automatic conversion
    });

    it("should handle complex nested structures with mixed field types", () => {
      const input = {
        userId: 123,
        pagination: {
          currentPage: 1,
          totalPages: 10,
          hasNext: true,
          hasPrev: false,
        },
        costs: [
          {
            totalSpent: 50.25,
            inputTokens: 1000,
            outputTokens: 500,
            requestDuration: 1.5,
          },
        ],
        customMetrics: {
          averageScore: 8.5,
          maxAttempts: 3,
        },
      };

      const result = convertWithFieldMappings(input, "toSnakeCase");

      expect(result.user_id).toBe(123);
      expect(result.pagination.current_page).toBe(1);
      expect(result.pagination.total_pages).toBe(10);
      expect(result.pagination.has_next).toBe(true);
      expect(result.pagination.has_prev).toBe(false);
      expect(result.costs[0].total_spent).toBe(50.25);
      expect(result.costs[0].input_tokens).toBe(1000);
      expect(result.costs[0].output_tokens).toBe(500);
      expect(result.costs[0].request_duration).toBe(1.5);
      expect(result.custom_metrics.average_score).toBe(8.5);
      expect(result.custom_metrics.max_attempts).toBe(3);
    });
  });

  describe("round-trip conversion", () => {
    it("should maintain data integrity in round-trip conversions", () => {
      const original = {
        userId: 123,
        userName: "john",
        userProfile: {
          firstName: "John",
          lastName: "Doe",
          isActive: true,
          settings: {
            emailNotifications: true,
            darkMode: false,
          },
        },
        posts: [
          { postId: 1, title: "Hello World", isPublished: true },
          { postId: 2, title: "TypeScript Tips", isPublished: false },
        ],
      };

      // Convert to snake_case and back to camelCase
      const snakeCase = convertObjectToSnakeCase(original);
      const backToCamelCase = convertObjectToCamelCase(snakeCase);

      expect(backToCamelCase).toEqual(original);
    });

    it("should maintain data integrity with field mappings in round-trip", () => {
      const original = {
        userId: 123,
        createdAt: "2023-01-01",
        isPublic: true,
        totalSpent: 100.5,
        userProfile: {
          updatedAt: "2023-01-02",
          inputTokens: 1000,
        },
      };

      // Convert using field mappings and back
      const snakeCase = convertWithFieldMappings(original, "toSnakeCase");
      const backToCamelCase = convertWithFieldMappings(
        snakeCase,
        "toCamelCase",
      );

      expect(backToCamelCase).toEqual(original);
    });
  });
});
