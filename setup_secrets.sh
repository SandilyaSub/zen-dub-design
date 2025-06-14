#!/bin/bash
# Script to set up Google Secret Manager secrets for Indic-Translator

# Exit on error
set -e

# Project ID - replace with your actual project ID if different
PROJECT_ID="phonic-bivouac-272213"

echo "Setting up secrets for project: $PROJECT_ID"

# Create secrets if they don't exist
echo "Creating secrets..."
gcloud secrets create sarvam-api-key --project=$PROJECT_ID --replication-policy="automatic" || echo "Secret sarvam-api-key already exists"
gcloud secrets create gemini-api-key --project=$PROJECT_ID --replication-policy="automatic" || echo "Secret gemini-api-key already exists"
gcloud secrets create cartesia-api-key --project=$PROJECT_ID --replication-policy="automatic" || echo "Secret cartesia-api-key already exists"

# Prompt for API keys
read -p "Enter Sarvam API Key: " SARVAM_API_KEY
read -p "Enter Gemini API Key: " GEMINI_API_KEY
read -p "Enter Cartesia API Key: " CARTESIA_API_KEY

# Store secrets
echo "Storing secrets in Secret Manager..."
echo -n "$SARVAM_API_KEY" | gcloud secrets versions add sarvam-api-key --project=$PROJECT_ID --data-file=-
echo -n "$GEMINI_API_KEY" | gcloud secrets versions add gemini-api-key --project=$PROJECT_ID --data-file=-
echo -n "$CARTESIA_API_KEY" | gcloud secrets versions add cartesia-api-key --project=$PROJECT_ID --data-file=-

echo "Secrets stored successfully!"

# Get the service account used by Cloud Run
echo "Getting Cloud Run service account..."
SERVICE_ACCOUNT=$(gcloud run services describe indic-translator --region asia-south1 --project=$PROJECT_ID --format="value(spec.template.spec.serviceAccountName)")

# If no service account is assigned, create one
if [ -z "$SERVICE_ACCOUNT" ]; then
  echo "No service account found. Creating a new one..."
  SERVICE_ACCOUNT="indic-translator-sa@$PROJECT_ID.iam.gserviceaccount.com"
  gcloud iam service-accounts create indic-translator-sa --project=$PROJECT_ID
  
  # Assign the service account to Cloud Run service
  echo "Assigning service account to Cloud Run service..."
  gcloud run services update indic-translator --region asia-south1 --project=$PROJECT_ID --service-account $SERVICE_ACCOUNT
fi

echo "Using service account: $SERVICE_ACCOUNT"

# Grant access to secrets
echo "Granting Secret Manager access to service account..."
gcloud secrets add-iam-policy-binding sarvam-api-key \
  --project=$PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding gemini-api-key \
  --project=$PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding cartesia-api-key \
  --project=$PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"

echo "Setup complete! The Cloud Run service now has access to the secrets."
echo "Deploy your application to apply these changes."
