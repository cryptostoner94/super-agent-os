FROM node:22-slim AS builder

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy only package files first for better caching
COPY frontend/next-app/package.json frontend/next-app/pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --ignore-scripts

# Copy the rest of the frontend code
COPY frontend/next-app/ .

# Build the Next.js app
# We pass the build-time env var if needed, but it's also set at runtime
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN pnpm build

# --- Runner Stage ---
FROM node:22-slim AS runner

WORKDIR /app

ENV NODE_ENV=production
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy built artifacts
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

CMD ["pnpm", "start", "-p", "3000"]
