# Build from monorepo root: docker build -f apps/web/Dockerfile .
FROM node:22-alpine AS deps
WORKDIR /repo/apps/web
COPY apps/web/package.json ./
RUN npm install

FROM node:22-alpine AS builder
WORKDIR /repo
COPY --from=deps /repo/apps/web/node_modules ./apps/web/node_modules
COPY packages ./packages
COPY apps/web ./apps/web
RUN mkdir -p /repo/apps/web/public && npm --prefix apps/web run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs

COPY --from=builder /repo/apps/web/public ./apps/web/public
COPY --from=builder --chown=nextjs:nodejs /repo/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /repo/apps/web/.next/static ./apps/web/.next/static

USER nextjs
EXPOSE 3000

CMD ["node", "apps/web/server.js"]
