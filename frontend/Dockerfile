# Task: T001, T004 (S005) — Multi-stage Docker build for frontend-spa
# Decision: D007 — Vite static + multi-stage Docker (node:alpine → nginx:alpine)
# Decision: D013 — Docker port frontend-spa = 8080:80

# Stage 1 — build
FROM node:20-alpine AS build
WORKDIR /app

# Accept VITE_API_BASE_URL as build arg (Vite bakes env vars at build time)
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Install deps first for layer cache optimization
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# Stage 2 — serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
