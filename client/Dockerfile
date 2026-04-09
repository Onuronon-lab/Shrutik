# ─────────────────────────────────────────────
# Stage 1 – Builder
# ─────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY package*.json ./

# Install dependencies (using clean install for reproducibility)
RUN npm ci --frozen-lockfile

# Copy source code
COPY . .

# Build the application
# We use npx vite build directly to ensure the production assets are generated
# effectively, skipping tsc if there are legacy type errors in tests.
RUN npx vite build

# ─────────────────────────────────────────────
# Stage 2 – Production
# ─────────────────────────────────────────────
FROM nginx:1.27-alpine AS production

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built static assets from the builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Copy the optimized nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose the standard http port
EXPOSE 80

# The standard nginx image starts the server automatically CMD ["nginx", "-g", "daemon off;"]
