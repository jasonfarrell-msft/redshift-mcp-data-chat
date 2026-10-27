targetScope = 'resourceGroup'

resource account 'Microsoft.CognitiveServices/accounts@2026-09-01' existing = {
  name: 'foundry-sandbox-swc-mx01'
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2026-09-01' = {
  parent: account
  name: 'redshift-test-project'
  location: 'swedencentral'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: 'redshift-test-project'
    description: 'Synthetic Redshift metadata-only public POC'
  }
}

output projectId string = project.id
