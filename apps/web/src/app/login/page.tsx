'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { ApiClientError } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';

const loginSchema = z.object({
  email: z.string().email('Enter a valid email address.'),
  password: z.string().min(1, 'Password is required.'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('password_changed') === '1') {
        setInfoMessage(
          'Password updated and active sessions revoked. Sign in with your new password.',
        );
      }
    }
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (values: LoginFormValues) => {
    setErrorMessage(null);
    try {
      await login(values.email, values.password);
      router.push('/dashboard');
    } catch (err) {
      if (err instanceof ApiClientError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Unable to reach authentication service.');
      }
    }
  };

  return (
    <div className="flex min-h-screen flex-col justify-center bg-[#f8f9f7] px-6 py-12">
      <div className="mx-auto w-full max-w-md rounded-lg border border-slate-200 bg-white p-8">
        <div className="space-y-2">
          <Link href="/" className="text-sm font-semibold text-[#14532d] hover:underline">
            Nova AgriSense
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">Organization Sign In</h1>
          <p className="text-sm text-slate-600">
            Authenticate via FastAPI. Refresh tokens are stored in HttpOnly cookies only.
          </p>
        </div>

        {infoMessage && (
          <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-900">
            {infoMessage}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-slate-700">
              Email address
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              {...register('email')}
              className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-[#14532d] focus:outline-none focus:ring-2 focus:ring-[#14532d]/20"
            />
            {errors.email && (
              <p className="mt-1 text-xs text-red-700">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-slate-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              {...register('password')}
              className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-[#14532d] focus:outline-none focus:ring-2 focus:ring-[#14532d]/20"
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-700">{errors.password.message}</p>
            )}
          </div>

          {errorMessage && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-xs text-red-900">
              {errorMessage}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-lg bg-[#14532d] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#166534] disabled:opacity-60 transition-colors cursor-pointer"
          >
            {isSubmitting ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-slate-600">
          Need an account?{' '}
          <Link href="/register" className="font-semibold text-[#14532d] hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
