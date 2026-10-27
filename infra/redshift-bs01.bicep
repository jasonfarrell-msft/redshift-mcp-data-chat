targetScope = 'subscription'

// Use a deployment-specific template name to avoid unrelated subscription deployment names.
// Prerequisite creation surface for ARM validation/what-if; deploy/deploy.py remains the execution engine.
// Use only subscription bb4b2781-6739-4fa1-994e-4ad6ce55c59c, tenant e90bd921-0e00-4e6f-b87c-713670ee27bf.
resource resourceGroup 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: 'rg-redshift-bs01'
  location: 'brazilsouth'
}

module prerequisites './resources.bicep' = {
  name: 'redshift-prerequisites'
  scope: resourceGroup
}
