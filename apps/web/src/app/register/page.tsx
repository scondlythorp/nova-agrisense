'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { ApiClientError, apiClient } from '@/lib/api-client';
import { useAuth } from '@/lib/auth-context';

const registerSchema = z.object({
  full_name: z.string().min(2, 'Full name must be at least 2 characters.'),
  email: z.string().email('Enter a valid email address.'),
  phone_number: z.string().max(32).optional(),
  password: z
    .string()
    .min(12, 'Password must be at least 12 characters.')
    .regex(/[a-z]/, 'Include at least one lowercase letter.')
    .regex(/[A-Z]/, 'Include at least one uppercase letter.')
    .regex(/\d/, 'Include at least one digit.'),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (values: RegisterFormValues) => {
    setErrorMessage(null);
    try {
      await apiClient.register({
        full_name: values.full_name,
        email: values.email,
        phone_number: values.phone_number || undefined,
        password: values.password,
      });
      await login(values.email, values.password);
      router.push('/dashboard');
    } catch (err) {
      if (err instanceof ApiClientError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Registration failed due to network or server unavailability.');
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
          <h1 className="text-2xl font-bold text-slate-900">Create Account</h1>
          <p className="text-sm text-slate-600">
            Register an individual account to create or join an agricultural organization.
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
          <div>
            <label htmlFor="full_name" className="block text-sm font-medium text-slate-700">
              Full name
            </label>
            <input
              id="full_name"
              type="text"
              {...register('full_name')}
              className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-[#14532d] focus:outline-none focus:ring-2 focus:ring-[#14532d]/20"
            />
            {errors.full_name && (
              <p className="mt-1 text-xs text-red-700">{errors.full_name.message}</p>
            )}
          </div>

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
            <label htmlFor="phone_number" className="block text-sm font-medium text-slate-700">
              Phone number (optional)
            </label>
            <input
              id="phone_number"
              type="tel"
              {...register('phone_number')}
              className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-[#14532d] focus:outline-none focus:ring-2 focus:ring-[#14532d]/20"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-slate-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="new-password"
              {...register('password')}
              className="mt-1.5 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-[#14532d] focus:outline-none focus:ring-2 focus:ring-[#14532d]/20"
            />
            <p className="mt-1 text-xs text-slate-500">
              Minimum 12 characters with uppercase, lowercase, and a number.
            </p>
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
            {isSubmitting ? 'Creating account...' : 'Register'}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-slate-600">
          Already registered?{' '}
          <Link href="/login" className="font-semibold text-[#14532d] hover:underline">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}
