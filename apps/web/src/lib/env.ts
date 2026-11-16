import { z } from 'zod';

const envSchema = z.object({
  NEXT_PUBLIC_API_BASE_URL: z
    .string()
    .url()
    .default('http://localhost:8000/api/v1'),
  NEXT_PUBLIC_APP_NAME: z.string().min(1).default('Nova AgriSense'),
  NEXT_PUBLIC_DEFAULT_LOCALE: z.string().min(2).default('en'),
});

export const webEnv = envSchema.parse({
  NEXT_PUBLIC_API_BASE_URL:
    process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1',
  NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'Nova AgriSense',
  NEXT_PUBLIC_DEFAULT_LOCALE: process.env.NEXT_PUBLIC_DEFAULT_LOCALE || 'en',
});
