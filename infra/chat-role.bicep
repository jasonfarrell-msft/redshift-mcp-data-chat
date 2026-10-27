targetScope = 'resourceGroup'

@allowed(['ebcf9b66-cca4-46a6-a344-3f100ea7eb0d'])
param principalId string

@description('Keep true for the full template. False permits an incremental Cognitive Services User assignment-only deployment without updating the existing Consumer assignment.')
param includeConsumerAssignment bool = true

var consumerId = 'eed3b665-ab3a-47b6-8f48-c9382fb1dad6'
var cognitiveServicesUserId = 'a97b65f3-24c7-4388-baec-2e87135dc908'
var appId = resourceId(subscription().subscriptionId, 'rg-redshift-bs01', 'Microsoft.Web/sites', 'app-redshift-chat-bs01-bb4b2781')

resource account 'Microsoft.CognitiveServices/accounts@2026-09-01' existing = {
  name: 'foundry-sandbox-swc-mx01'
}
resource project 'Microsoft.CognitiveServices/accounts/projects@2026-09-01' existing = {
  parent: account
  name: 'redshift-test-project'
}
resource consumer 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (includeConsumerAssignment) {
  name: guid(project.id, appId, consumerId)
  scope: project
  properties: {
    principalId: principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', consumerId)
  }
}

resource cognitiveServicesUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(project.id, appId, cognitiveServicesUserId)
  scope: project
  properties: {
    principalId: principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesUserId)
  }
}

output assignmentId string = extensionResourceId(project.id, 'Microsoft.Authorization/roleAssignments', guid(project.id, appId, consumerId))
output cognitiveServicesUserAssignmentId string = cognitiveServicesUser.id
