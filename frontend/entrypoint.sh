#!/bin/sh
set -eu

cat > /app/dist/runtime-config.js <<EOF
window.__GOLDEN_TEA_CONFIG__ = {
  API_URL: "${VITE_API_URL:-/api}",
  DEMO_USER_ID: "${VITE_DEMO_USER_ID:-900000001}"
};
EOF

exec serve -s dist -l "${PORT:-3000}"

