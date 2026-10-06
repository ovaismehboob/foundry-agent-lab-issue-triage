<#
.SYNOPSIS
  Creates app/.env.container for running the triage agent container locally (Module 6).

.DESCRIPTION
  A container can't use your Azure CLI sign-in. This script copies the non-secret settings from
  app/.env and adds two short-lived access tokens issued by `az account get-access-token`:
    LAB_DEV_TOKEN_FOUNDRY  (scope https://ai.azure.com/.default)
    LAB_DEV_TOKEN_SEARCH   (scope https://search.azure.com/.default, only if Module 5 is configured)

  The tokens expire (typically within 60-90 minutes). Run the script again when they expire.
  app/.env.container is excluded from Git and from the Docker build context. Delete it after the lab.
  Hosted agents in Foundry never use these tokens; they use their own agent identity.

.EXAMPLE
  ./scripts/new-container-env.ps1
#>
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path $root 'app/.env'
$target = Join-Path $root 'app/.env.container'

if (-not (Test-Path $source)) { throw "app/.env not found. Copy app/.env.example to app/.env and fill it in first." }

$lines = Get-Content $source | Where-Object { $_ -match '^\s*[A-Z0-9_]+=' -and $_ -notmatch '^\s*LAB_DEV_TOKEN_' }
$searchConfigured = $lines | Where-Object { $_ -match '^\s*AZURE_SEARCH_ENDPOINT=https://' }

Write-Host 'Requesting a short-lived token for Microsoft Foundry...'
$foundryToken = az account get-access-token --scope https://ai.azure.com/.default --query accessToken -o tsv
if (-not $foundryToken) { throw 'Could not get a token. Run az login and try again.' }
$output = @($lines) + "LAB_DEV_TOKEN_FOUNDRY=$foundryToken"

if ($searchConfigured) {
    Write-Host 'Requesting a short-lived token for Azure AI Search...'
    $searchToken = az account get-access-token --scope https://search.azure.com/.default --query accessToken -o tsv
    if ($searchToken) { $output += "LAB_DEV_TOKEN_SEARCH=$searchToken" }
}

# Values in a Docker --env-file are taken literally, so remove surrounding quotes.
$output = $output | ForEach-Object { $_ -replace '^([A-Z0-9_]+)="(.*)"$', '$1=$2' }
# Write UTF-8 without a byte-order mark (Docker would treat a BOM as part of the first variable name).
[System.IO.File]::WriteAllLines($target, [string[]]$output, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "Wrote app/.env.container (contains short-lived tokens - do not share or commit it)."
