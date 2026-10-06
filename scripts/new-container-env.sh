#!/usr/bin/env bash
# Creates app/.env.container for running the triage agent container locally (Module 6).
# Same behaviour as new-container-env.ps1: copies non-secret settings from app/.env and adds
# short-lived access tokens from `az account get-access-token`. Tokens expire; rerun when needed.
# app/.env.container is excluded from Git and from the Docker build context. Delete it after the lab.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
source_file="$root/app/.env"
target_file="$root/app/.env.container"

if [[ ! -f "$source_file" ]]; then
  echo "app/.env not found. Copy app/.env.example to app/.env and fill it in first." >&2
  exit 1
fi

grep -E '^[A-Z0-9_]+=' "$source_file" | grep -v '^LAB_DEV_TOKEN_' | sed -E 's/^([A-Z0-9_]+)="(.*)"$/\1=\2/' > "$target_file"

echo "Requesting a short-lived token for Microsoft Foundry..."
echo "LAB_DEV_TOKEN_FOUNDRY=$(az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv)" >> "$target_file"

if grep -qE '^AZURE_SEARCH_ENDPOINT=https://' "$source_file"; then
  echo "Requesting a short-lived token for Azure AI Search..."
  echo "LAB_DEV_TOKEN_SEARCH=$(az account get-access-token --scope https://search.azure.com/.default --query accessToken -o tsv)" >> "$target_file"
fi

chmod 600 "$target_file"
echo "Wrote app/.env.container (contains short-lived tokens - do not share or commit it)."
