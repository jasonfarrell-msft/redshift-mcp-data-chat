targetScope = 'subscription'

@allowed(['bb4b2781-6739-4fa1-994e-4ad6ce55c59c'])
param approvedSubscription string = 'bb4b2781-6739-4fa1-994e-4ad6ce55c59c'

@allowed(['eastus2'])
param appLocation string = 'eastus2'

module project './chat-project.bicep' = {
  name: 'redshift-chat-project'
  scope: resourceGroup(approvedSubscription, 'rg-client-sandbox-eus2-mx01')
}

module app './chat-app.bicep' = {
  name: 'redshift-chat-app'
  scope: resourceGroup(approvedSubscription, 'rg-redshift-bs01')
  params: {
    appLocation: appLocation
  }
}

module consumer './chat-role.bicep' = {
  name: 'redshift-chat-consumer'
  scope: resourceGroup(approvedSubscription, 'rg-client-sandbox-eus2-mx01')
  params: {
    principalId: any(app.outputs.principalId)
  }
  dependsOn: [project]
}

output projectId string = project.outputs.projectId
output appId string = app.outputs.appId
output principalId string = app.outputs.principalId
output hostname string = app.outputs.hostname
output consumerRoleId string = consumer.outputs.assignmentId
output cognitiveServicesUserRoleId string = consumer.outputs.cognitiveServicesUserAssignmentId
