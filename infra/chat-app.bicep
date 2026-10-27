targetScope = 'resourceGroup'

@allowed(['eastus2'])
param appLocation string = 'eastus2'

// Provider inventory on 2026-10-26 advertises 2026-08-01 GA; local schemas can lag.
resource plan 'Microsoft.Web/serverfarms@2026-08-01' = {
  name: 'asp-redshift-chat-bs01'
  location: appLocation
  kind: 'linux'
  sku: {
    name: 'B1'
    tier: 'Basic'
    capacity: 1
  }
  properties: {
    reserved: true
  }
}

resource app 'Microsoft.Web/sites@2026-08-01' = {
  name: 'app-redshift-chat-bs01-bb4b2781'
  location: appLocation
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    clientAffinityEnabled: false
    publicNetworkAccess: 'Enabled'
    siteConfig: {
      linuxFxVersion: 'NODE|24-lts'
      alwaysOn: true
      minTlsVersion: '1.2'
      scmMinTlsVersion: '1.2'
      ftpsState: 'Disabled'
      http20Enabled: true
      appCommandLine: 'npm start'
      healthCheckPath: '/healthz'
    }
  }
}

resource scm 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2026-08-01' = {
  parent: app
  name: 'scm'
  properties: {
    allow: false
  }
}

resource ftp 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2026-08-01' = {
  parent: app
  name: 'ftp'
  properties: {
    allow: false
  }
}

output appId string = app.id
output principalId string = app.identity.principalId
output hostname string = app.properties.defaultHostName
