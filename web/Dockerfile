FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# NEXT_PUBLIC_* встраиваются в сборку, поэтому передаются как build args.
ARG NEXT_PUBLIC_SITE_URL
ARG NEXT_PUBLIC_SITE_ENV
ARG NEXT_PUBLIC_CONTACT_EMAIL
ARG NEXT_PUBLIC_TELEGRAM_HANDLE
ARG NEXT_PUBLIC_TELEGRAM_CHANNEL
ARG NEXT_PUBLIC_PRIVACY_POLICY_VERSION
RUN npm run build

FROM node:22-alpine AS run
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
RUN adduser -S -u 10001 app
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public
USER app
EXPOSE 3000
CMD ["node", "server.js"]
