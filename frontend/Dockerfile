# Multi-stage Dockerfile for React SPA Frontend
# Stage 1: Build static production bundle
FROM node:22-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* bun.lock* ./
RUN npm install --ignore-scripts

# Copy frontend source code and configuration
COPY index.html tsconfig.json vite.config.ts ./
COPY src/ ./src/

# Compile production assets into /app/dist
RUN npm run build

# Stage 2: High-performance lightweight Nginx server
FROM nginx:alpine

# Clean default configuration and html
RUN rm -rf /usr/share/nginx/html/*

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx reverse-proxy configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 3000
EXPOSE 3000

# Container health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
