"""Helper scripts and utilities for GCP auth module."""

# Script to extract project_id from credentials (service account key or WIF)
GET_PROJECT_ID_SCRIPT = '''
project_id=$(echo "$GCP_CREDENTIALS" | jq -r '.project_id // empty')
if [ -z "$project_id" ]; then
  sa_url=$(echo "$GCP_CREDENTIALS" | jq -r '.service_account_impersonation_url // empty')
  if [ -n "$sa_url" ]; then
    project_id=$(echo "$sa_url" | sed -n 's/.*@\\([^.]*\\)\\.iam\\.gserviceaccount\\.com.*/\\1/p')
  fi
fi
echo "$project_id"
'''
