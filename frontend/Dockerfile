# ─────────────────────────────────────────────
# Stage 1 – Builder
# ─────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (better layer caching)
COPY package*.json ./
RUN npm ci --frozen-lockfile

# Build-time env (can be overridden with --build-arg)
ARG VITE_API_URL=https://api.shrutik.org
ENV VITE_API_URL=$VITE_API_URL

# Copy source and compile
COPY . .
RUN npx vite build

# ─────────────────────────────────────────────
# Stage 2 – Production image (nginx)
# ─────────────────────────────────────────────
FROM nginx:1.27-alpine AS production

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy compiled output from builder
COPY --from=builder /app/build /usr/share/nginx/html

# Custom nginx config for SPA (react-router fallback)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
