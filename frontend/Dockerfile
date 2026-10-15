# ==========================================
# Stage 1: Build React + Vite SPA
# ==========================================
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies using pinned lockfile for reproducibility
COPY package.json package-lock.json ./
RUN npm ci

# Copy application source code and build production distribution
COPY . .
RUN npm run build

# ==========================================
# Stage 2: Serve via Production Nginx Web Server
# ==========================================
FROM nginx:1.27-alpine AS runner

# Remove default nginx static assets and configuration
RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf

# Copy custom reverse proxy & client-side routing configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose internal HTTP port
EXPOSE 80

# Health check to verify Nginx is actively serving index
HEALTHCHECK --interval=20s --timeout=3s --retries=3 \
  CMD wget -qO- http://localhost:80/ || exit 1

# Start Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
