#!/usr/bin/env bash
# Task: T005 (S005) — Build smoke test for admin-spa Docker packaging
# Usage: bash tests/admin-spa/S005.build.sh
# Make executable: chmod +x tests/admin-spa/S005.build.sh
#
# Verifies:
#   1. npm run build succeeds (TypeScript + Vite bundle)
#   2. docker build succeeds (multi-stage: node:20-alpine → nginx:alpine)
#
# Exit code: 0 = pass, non-zero = fail (set -e enforces fail-fast)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADMIN_SPA_DIR="$(cd "$SCRIPT_DIR/../../frontend/admin-spa" && pwd)"
IMAGE_TAG="admin-spa-smoke-test:latest"

echo "=== S005 Build Smoke Test ==="
echo "Admin SPA dir: $ADMIN_SPA_DIR"

# Step 1: npm run build
echo ""
echo "[1/2] Running npm run build..."
cd "$ADMIN_SPA_DIR"
npm run build
echo "✓ npm run build PASSED"

# Step 2: docker build
echo ""
echo "[2/2] Running docker build..."
docker build \
  --build-arg VITE_API_BASE_URL=http://localhost:8000 \
  -t "$IMAGE_TAG" \
  "$ADMIN_SPA_DIR"
echo "✓ docker build PASSED"

echo ""
echo "=== S005 Smoke Test PASSED ==="
echo "Image: $IMAGE_TAG"
echo "Run with: docker run -p 8081:80 $IMAGE_TAG"
