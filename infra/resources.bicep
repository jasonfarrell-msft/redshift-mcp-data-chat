targetScope = 'resourceGroup'

var location = 'brazilsouth'
var acrPullRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')

// Public endpoints are approved synthetic-POC exceptions, not production network defaults.
resource registry 'Microsoft.ContainerRegistry/registries@2025-11-01' = {
  name: 'acrredshiftbs01bb4b2781'
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    anonymousPullEnabled: false
    publicNetworkAccess: 'Enabled'
    roleAssignmentMode: 'LegacyRegistryPermissions'
    policies: {
      azureADAuthenticationAsArmPolicy: {
        status: 'enabled'
      }
    }
  }
}

resource imagePullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: 'umi-redshift-imagepull-mx01'
  location: location
  properties: {}
}

resource imagePullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, imagePullIdentity.id, acrPullRoleId)
  scope: registry
  properties: {
    roleDefinitionId: acrPullRoleId
    principalId: imagePullIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource vault 'Microsoft.KeyVault/vaults@2026-05-15' = {
  name: 'kv-redshift-bs01'
  location: location
  properties: {
    tenantId: 'e90bd921-0e00-4e6f-b87c-713670ee27bf'
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    enablePurgeProtection: true
    softDeleteRetentionInDays: 90
    publicNetworkAccess: 'Enabled'
    accessPolicies: []
  }
}

resource environment 'Microsoft.App/managedEnvironments@2026-07-01' = {
  name: 'cae-redshift-bs01'
  location: location
  properties: {
    // Empty profiles select Consumption-only, not a workload-profiles environment.
    // No VNet, infrastructure RG, network resources or Log Analytics workspace.
    workloadProfiles: []
    appLogsConfiguration: {
      destination: null
    }
  }
}

// App creation awaits the real immutable image digest/bootstrap. System identity,
// secret upload, secret-scoped RBAC and Key Vault references are later imperative
// stages in deploy/deploy.py, not validated by this prerequisite-only template.
