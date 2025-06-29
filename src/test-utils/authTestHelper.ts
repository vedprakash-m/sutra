import { VedUser } from "../types/auth";

/**
 * Test helper for mocking authentication states
 */
export class AuthTestHelper {
  private static originalFetch: any;

  static mockUnauthenticatedUser() {
    global.fetch = jest.fn((url: string) => {
      if (url.includes("/.auth/me")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ clientPrincipal: null }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    }) as jest.Mock;
  }

  static mockAuthenticatedUser(user: Partial<VedUser> = {}) {
    const defaultUser: VedUser = {
      id: "test-user-id",
      email: "test@example.com",
      name: "Test User",
      givenName: "Test",
      familyName: "User",
      permissions: ["user"],
      vedProfile: {
        profileId: "test-user-id",
        subscriptionTier: "free",
        appsEnrolled: ["sutra"],
        preferences: {},
      },
      ...user,
    };

    global.fetch = jest.fn((url: string) => {
      if (url.includes("/.auth/me")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              clientPrincipal: {
                identityProvider: "aad",
                userId: defaultUser.id,
                userDetails: defaultUser.email,
                userRoles: defaultUser.permissions,
                claims: [
                  { typ: "name", val: defaultUser.name },
                  { typ: "email", val: defaultUser.email },
                ],
              },
            }),
        });
      }
      if (url.includes("/getroles")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ roles: defaultUser.permissions }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    }) as jest.Mock;
  }

  static mockAdminUser() {
    this.mockAuthenticatedUser({
      id: "admin-user-id",
      email: "admin@example.com",
      name: "Admin User",
      permissions: ["admin"],
      vedProfile: {
        profileId: "admin-user-id",
        subscriptionTier: "premium",
        appsEnrolled: ["sutra"],
        preferences: {},
      },
    });
  }

  static cleanup() {
    jest.clearAllMocks();
    if (this.originalFetch) {
      global.fetch = this.originalFetch;
    }
  }

  static setup() {
    this.originalFetch = global.fetch;
  }
}
