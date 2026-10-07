<#
.SYNOPSIS
  Grants the hosted agent's identity read access to the Foundry IQ knowledge base (Module 7, optional).

.DESCRIPTION
  A hosted agent gets its own Microsoft Entra agent identity. It can call models in its project by default,
  but it needs explicit roles to use your Azure AI Search knowledge base. This script assigns two
  least-privilege built-in roles on the lab search service only:
    - Search Index Data Reader (query indexes and retrieve from knowledge bases)
    - Reader (read object definitions; the Agent Framework provider reads the knowledge base definition)

  Run it only against the lab search service you created for this workshop.
  You need Owner or User Access Administrator (or another role with
  Microsoft.Authorization/roleAssignments/write) on the search service.

.PARAMETER AgentPrincipalId
  Object (principal) ID of the hosted agent identity. Find it in the Foundry portal on the agent's YAML/details
  view (instance identity principal ID), or in the output of `azd ai agent show`.

.PARAMETER SearchServiceName
  Name of the lab Azure AI Search service.

.PARAMETER ResourceGroup
  Lab resource group that contains the search service.

.EXAMPLE
  ./deployment/assign-hosted-agent-roles.ps1 -AgentPrincipalId 00000000-0000-0000-0000-000000000000 `
      -SearchServiceName srchtriagelab01 -ResourceGroup rg-foundry-agent-lab
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)][string]$AgentPrincipalId,
    [Parameter(Mandatory = $true)][string]$SearchServiceName,
    [Parameter(Mandatory = $true)][string]$ResourceGroup
)
$ErrorActionPreference = 'Stop'

$scope = az search service show --name $SearchServiceName --resource-group $ResourceGroup --query id -o tsv
if (-not $scope) { throw "Search service '$SearchServiceName' not found in resource group '$ResourceGroup'." }

if ($PSCmdlet.ShouldProcess($SearchServiceName, "Assign 'Search Index Data Reader' and 'Reader' to $AgentPrincipalId")) {
    # Search Index Data Reader: query indexes and retrieve from knowledge bases.
    # Reader: read object definitions (the Agent Framework provider reads the knowledge base definition first).
    foreach ($role in @('Search Index Data Reader', 'Reader')) {
        az role assignment create `
            --assignee-object-id $AgentPrincipalId `
            --assignee-principal-type ServicePrincipal `
            --role $role `
            --scope $scope | Out-Null
        Write-Host "Assigned '$role' on $SearchServiceName."
    }
    Write-Host 'Role assignments can take a few minutes to apply.'
}
