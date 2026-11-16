import assert from 'node:assert/strict';
import test from 'node:test';
import { z } from 'zod';
import {
  apiClient,
  getActiveOrganizationId,
  getInMemoryAccessToken,
  getInMemoryCsrfToken,
  setActiveOrganizationId,
  setInMemoryAccessToken,
  setInMemoryCsrfToken,
} from '../src/lib/api-client';

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

const registerSchema = z.object({
  full_name: z.string().min(2),
  email: z.string().email(),
  password: z
    .string()
    .min(12)
    .regex(/[a-z]/)
    .regex(/[A-Z]/)
    .regex(/\d/),
});

test('login and register schemas enforce validation rules', () => {
  assert.equal(loginSchema.safeParse({ email: 'bad-email', password: 'abc' }).success, false);
  assert.equal(loginSchema.safeParse({ email: 'amina@coop.gm', password: '' }).success, false);
  assert.equal(
    loginSchema.safeParse({ email: 'amina@coop.gm', password: 'StrongAgriPass123' }).success,
    true,
  );
  assert.equal(
    registerSchema.safeParse({
      full_name: 'Amina Jallow',
      email: 'amina@coop.gm',
      password: 'short',
    }).success,
    false,
  );
  assert.equal(
    registerSchema.safeParse({
      full_name: 'Amina Jallow',
      email: 'amina@coop.gm',
      password: 'StrongAgriPass123',
    }).success,
    true,
  );
});

test('access token, CSRF token, and organization context stay strictly in memory', () => {
  setInMemoryAccessToken('jwt-access-sample');
  setInMemoryCsrfToken('csrf-sample');
  setActiveOrganizationId('org-uuid-1');

  assert.equal(getInMemoryAccessToken(), 'jwt-access-sample');
  assert.equal(getInMemoryCsrfToken(), 'csrf-sample');
  assert.equal(getActiveOrganizationId(), 'org-uuid-1');

  setInMemoryAccessToken(null);
  setInMemoryCsrfToken(null);
  setActiveOrganizationId(null);

  assert.equal(getInMemoryAccessToken(), null);
  assert.equal(getInMemoryCsrfToken(), null);
  assert.equal(getActiveOrganizationId(), null);
});

test('apiClient attaches Authorization, X-Organization-ID, retries once on 401 refresh, and clears on logout', async () => {
  const originalFetch = globalThis.fetch;
  const calls: Array<{ url: string; method: string; headers: Record<string, string> }> = [];

  try {
    globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? 'GET';
      const headers = (init?.headers as Record<string, string>) ?? {};
      calls.push({ url, method, headers });

      if (url.endsWith('/auth/login')) {
        return new Response(
          JSON.stringify({
            access_token: 'access-1',
            token_type: 'Bearer',
            expires_in: 900,
            csrf_token: 'csrf-1',
            user: {
              id: 'u1',
              email: 'amina@coop.gm',
              full_name: 'Amina Jallow',
              phone_number: null,
              is_active: true,
              is_verified: false,
              platform_role: null,
              last_login_at: null,
              created_at: '2026-11-14T00:00:00Z',
              memberships: [],
            },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        );
      }

      if (url.endsWith('/organizations/org-123/members')) {
        if (headers.Authorization === 'Bearer access-1') {
          return new Response(
            JSON.stringify({
              error: { code: 'invalid_token', message: 'Expired', request_id: 'r1' },
            }),
            { status: 401, headers: { 'Content-Type': 'application/json' } },
          );
        }
        return new Response(JSON.stringify([]), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      if (url.endsWith('/auth/refresh')) {
        return new Response(
          JSON.stringify({
            access_token: 'access-2',
            token_type: 'Bearer',
            expires_in: 900,
            csrf_token: 'csrf-2',
            user: {
              id: 'u1',
              email: 'amina@coop.gm',
              full_name: 'Amina Jallow',
              phone_number: null,
              is_active: true,
              is_verified: false,
              platform_role: null,
              last_login_at: null,
              created_at: '2026-11-14T00:00:00Z',
              memberships: [],
            },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        );
      }

      if (url.endsWith('/auth/logout')) {
        return new Response(JSON.stringify({ revoked: true, message: 'Session closed.' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      return new Response(JSON.stringify({}), { status: 404 });
    }) as typeof fetch;

    await apiClient.login({ email: 'amina@coop.gm', password: 'StrongAgriPass123' });
    assert.equal(getInMemoryAccessToken(), 'access-1');
    assert.equal(getInMemoryCsrfToken(), 'csrf-1');

    setActiveOrganizationId('org-123');
    const members = await apiClient.listMembers('org-123');
    assert.deepEqual(members, []);

    assert.equal(calls[1].headers['X-Organization-ID'], 'org-123');
    assert.equal(calls[2].url.endsWith('/auth/refresh'), true);
    assert.equal(calls[2].headers['X-CSRF-Token'], 'csrf-1');
    assert.equal(calls[3].headers.Authorization, 'Bearer access-2');

    await apiClient.logout();
    assert.equal(calls[4].headers['X-CSRF-Token'], 'csrf-2');
    assert.equal(getInMemoryAccessToken(), null);
    assert.equal(getInMemoryCsrfToken(), null);
    assert.equal(getActiveOrganizationId(), null);
  } finally {
    globalThis.fetch = originalFetch;
    setInMemoryAccessToken(null);
    setInMemoryCsrfToken(null);
    setActiveOrganizationId(null);
  }
});
