# syntax=docker/dockerfile:1

# ── Stage 1: Build Frontend Assets ──────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency specifications
COPY package*.json ./

# Install dependencies (including devDependencies needed for build)
RUN npm ci --legacy-peer-deps

# Copy application source code
COPY . .

# Build production bundle
RUN npm run build

# ── Stage 2: Serve via Nginx ────────────────────────────────────────────────
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built static files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
# NOTE: use 127.0.0.1, not "localhost" — busybox wget resolves localhost to ::1
# (IPv6) first, while nginx only listens on IPv4 (listen 80), so the probe fails.
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
