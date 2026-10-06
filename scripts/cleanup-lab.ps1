<#
.SYNOPSIS
  Deletes the dedicated lab resource group and verifies that its resources are gone (final cleanup).

.DESCRIPTION
  Deletes ONLY the resource group you name, after showing its contents and asking you to type the
  resource group name to confirm. Use this only for a resource group created for this lab.
  Deleting the resource group deletes every resource in it (Foundry resource and project, agents,
  model deployments, search service, storage account, container registry, Application Insights).

  Some resources are soft-deleted after deletion (for example Foundry / Azure AI Services accounts).
  The script lists soft-deleted Cognitive Services accounts so you can purge them if your policy allows.

.EXAMPLE
  ./scripts/cleanup-lab.ps1 -ResourceGroup rg-foundry-agent-lab
#>
[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$ResourceGroup)
$ErrorActionPreference = 'Stop'

$exists = az group exists --name $ResourceGroup
if ($exists -ne 'true') { Write-Host "Resource group '$ResourceGroup' does not exist. Nothing to delete."; exit 0 }

Write-Host "Resources in '$ResourceGroup':"
az resource list --resource-group $ResourceGroup --query "[].{name:name, type:type}" -o table

$answer = Read-Host "Type the resource group name '$ResourceGroup' to delete it and everything in it"
if ($answer -ne $ResourceGroup) { Write-Host 'Cancelled.'; exit 1 }

Write-Host 'Deleting (this can take several minutes)...'
az group delete --name $ResourceGroup --yes

if ((az group exists --name $ResourceGroup) -eq 'false') {
    Write-Host "Verified: resource group '$ResourceGroup' no longer exists."
} else {
    Write-Warning "Resource group '$ResourceGroup' still exists. Check the Azure portal for deletion errors."
}

Write-Host 'Soft-deleted Foundry / Cognitive Services accounts in this subscription (purge only lab accounts, if allowed):'
az cognitiveservices account list-deleted --query "[].{name:name, location:location, id:id}" -o table
