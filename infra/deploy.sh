#!/usr/bin/env bash
#
# SpecterOps deploy script.
# Deploys the FastAPI backend to Google Cloud Run and the Vite frontend to
# Firebase Hosting. Run from the repository root: ./infra/deploy.sh
#
set -euo pipefail

PROJECT_ID="$(gcloud config get-value project 2>/dev/null)"
REGION="us-central1"
SERVICE_NAME="specterops"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  echo "❌ No GCP project configured. Run: gcloud config set project <PROJECT_ID>"
  exit 1
fi

: "${GEMINI_API_KEY:?Set GEMINI_API_KEY in your environment before deploying}"

echo "📦 Project:  ${PROJECT_ID}"
echo "🌎 Region:   ${REGION}"
echo "🚀 Service:  ${SERVICE_NAME}"
echo

# 1. Build the container image from the backend.
echo "🔨 Building container image…"
gcloud builds submit backend/ --tag "${IMAGE}"

# 2. Deploy to Cloud Run.
echo "🚀 Deploying to Cloud Run…"
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY},DEMO_MODE=true,GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"

# 3. Resolve the deployed URL.
BACKEND_URL="$(gcloud run services describe "${SERVICE_NAME}" \
  --platform managed --region "${REGION}" \
  --format 'value(status.url)')"

echo "✅ Backend deployed: ${BACKEND_URL}"

# 4. Wire the frontend to the backend URL.
echo "VITE_API_URL=${BACKEND_URL}" > frontend/.env.production
echo "📝 Wrote frontend/.env.production"

# 5. Build the frontend.
echo "🔨 Building frontend…"
( cd frontend && npm install && npm run build )

# 6. Deploy the frontend to Firebase Hosting if available.
FRONTEND_URL="(not deployed — firebase CLI not found)"
if command -v firebase >/dev/null 2>&1; then
  echo "🚀 Deploying frontend to Firebase Hosting…"
  firebase deploy --only hosting
  FRONTEND_URL="(see Firebase Hosting output above)"
else
  echo "ℹ️  firebase CLI not found — skipping frontend hosting deploy."
  echo "    Serve frontend/dist/ with any static host."
fi

echo
echo "────────────────────────────────────────────────"
echo "✅ SpecterOps deployed"
echo "   Backend:  ${BACKEND_URL}"
echo "   Frontend: ${FRONTEND_URL}"
echo "────────────────────────────────────────────────"
