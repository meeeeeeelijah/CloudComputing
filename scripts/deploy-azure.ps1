<#
Phase 2 - Person 1: Azure setup and backend deployment.
Creates the resource group, storage account, blob container, dataset upload,
Flex Consumption Function App, app settings and CORS, then deploys and tests the function.

Run from the project root:
    powershell -ExecutionPolicy Bypass -File scripts\deploy-azure.ps1
Re-running is safe: names are reused from azure-deployment.json.
#>
param(
    [string]$ResourceGroup = "diet-analysis-rg",
    [string]$Location = "westus2",
    [string]$Suffix = "",
    [string]$ContainerName = "diet-data",
    [string]$BlobName = "All_Diets.csv",
    [string]$PythonVersion = "3.11"
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
$StateFile = Join-Path $ProjectRoot "azure-deployment.json"
$DatasetPath = Join-Path $ProjectRoot "data\$BlobName"

function Step([string]$Message) { Write-Host "`n==> $Message" -ForegroundColor Cyan }
function Fail([string]$Message) { Write-Host "`nERROR: $Message" -ForegroundColor Red; exit 1 }
function Invoke-Az {
    $output = & az @args
    if ($LASTEXITCODE -ne 0) { Fail "Azure CLI command failed: az $($args[0..2] -join ' ')" }
    return $output
}

Step "Checking tools"
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Fail "Azure CLI not found. Install it: winget install -e --id Microsoft.AzureCLI (then reopen PowerShell)"
}
$HasFunc = [bool](Get-Command func -ErrorAction SilentlyContinue)
if (-not (Test-Path $DatasetPath)) { Fail "Dataset not found at $DatasetPath" }
Write-Host "Azure CLI found. Functions Core Tools: $(if ($HasFunc) { 'found' } else { 'not found - will deploy with zip' })"

if (Test-Path $StateFile) {
    $state = Get-Content $StateFile -Raw | ConvertFrom-Json
    if (-not $Suffix) { $Suffix = $state.suffix }
}
if (-not $Suffix) {
    $Suffix = -join ((97..122) + (48..57) | Get-Random -Count 6 | ForEach-Object { [char]$_ })
}
$StorageAccount = "dietdata$Suffix"
$FunctionApp = "diet-analysis-func-$Suffix"
[ordered]@{ suffix = $Suffix; resourceGroup = $ResourceGroup; location = $Location; storageAccount = $StorageAccount; functionApp = $FunctionApp } |
    ConvertTo-Json | Set-Content -Path $StateFile -Encoding ASCII

Step "Signing in to Azure"
az account show -o none 2>$null
if ($LASTEXITCODE -ne 0) {
    az login -o none
    if ($LASTEXITCODE -ne 0) { Fail "Azure sign-in failed" }
}
$subscription = Invoke-Az account show --query "{name:name, id:id}" -o json | Out-String | ConvertFrom-Json
Invoke-Az account set --subscription $subscription.id -o none
Write-Host "Subscription: $($subscription.name) ($($subscription.id))"

Step "Registering resource providers (first run can take a few minutes)"
foreach ($ns in "Microsoft.Web", "Microsoft.App", "Microsoft.Storage", "Microsoft.Insights", "Microsoft.OperationalInsights") {
    Invoke-Az provider register --namespace $ns --wait -o none
    Write-Host "  $ns registered"
}

Step "Checking Flex Consumption support in $Location"
$flexRegions = Invoke-Az functionapp list-flexconsumption-locations --query "[].name" -o tsv
if ($flexRegions -notcontains $Location) {
    Fail "Region '$Location' does not support Flex Consumption. Re-run with -Location <region>. Supported: $($flexRegions -join ', ')"
}

Step "Creating resource group $ResourceGroup"
$existingRgLocation = az group show --name $ResourceGroup --query location -o tsv 2>$null
if ($LASTEXITCODE -eq 0 -and $existingRgLocation) {
    Write-Host "Already exists in $existingRgLocation (resources will still be created in $Location)"
} else {
    Invoke-Az group create --name $ResourceGroup --location $Location -o none
}

Step "Creating storage account $StorageAccount"
az storage account show --name $StorageAccount --resource-group $ResourceGroup -o none 2>$null
if ($LASTEXITCODE -ne 0) {
    Invoke-Az storage account create --name $StorageAccount --resource-group $ResourceGroup `
        --location $Location --sku Standard_LRS --kind StorageV2 `
        --allow-blob-public-access false --min-tls-version TLS1_2 --https-only true -o none
} else {
    $saLocation = Invoke-Az storage account show --name $StorageAccount --resource-group $ResourceGroup --query location -o tsv
    Write-Host "Already exists in $saLocation"
}
$accountKey = Invoke-Az storage account keys list --account-name $StorageAccount --resource-group $ResourceGroup --query "[0].value" -o tsv
$connectionString = Invoke-Az storage account show-connection-string --name $StorageAccount --resource-group $ResourceGroup --query connectionString -o tsv

Step "Creating blob container '$ContainerName' and uploading the dataset"
$env:AZURE_STORAGE_ACCOUNT = $StorageAccount
$env:AZURE_STORAGE_KEY = $accountKey
Invoke-Az storage container create --name $ContainerName -o none
Invoke-Az storage blob upload --container-name $ContainerName --name $BlobName --file $DatasetPath --overwrite -o none
$blobSize = Invoke-Az storage blob show --container-name $ContainerName --name $BlobName --query "properties.contentLength" -o tsv
Remove-Item Env:AZURE_STORAGE_ACCOUNT, Env:AZURE_STORAGE_KEY
Write-Host "Uploaded $BlobName ($blobSize bytes) to $StorageAccount/$ContainerName"

Step "Creating Function App $FunctionApp (Flex Consumption, Python $PythonVersion)"
function Test-FunctionApp([int]$Tries = 1) {
    for ($i = 1; $i -le $Tries; $i++) {
        $names = az resource list --resource-group $ResourceGroup --resource-type Microsoft.Web/sites --query "[].name" -o tsv 2>$null
        if ($LASTEXITCODE -eq 0 -and (@($names) | ForEach-Object { "$_".Trim() }) -contains $FunctionApp) { return $true }
        if ($i -lt $Tries) { Start-Sleep -Seconds 15 }
    }
    return $false
}

if (Test-FunctionApp) {
    Write-Host "Already exists"
} else {
    az functionapp create --name $FunctionApp --resource-group $ResourceGroup `
        --subscription $subscription.id --storage-account $StorageAccount `
        --flexconsumption-location $Location --runtime python --runtime-version $PythonVersion -o none

    if (-not (Test-FunctionApp -Tries 4)) {
        Write-Host "CLI create failed - creating with an ARM template instead" -ForegroundColor Yellow
        az deployment group create --resource-group $ResourceGroup --name "functionapp-$Suffix" `
            --template-file (Join-Path $PSScriptRoot "flex-functionapp.json") `
            --parameters functionAppName=$FunctionApp storageAccountName=$StorageAccount location=$Location pythonVersion=$PythonVersion `
            -o none
    }

    if (-not (Test-FunctionApp -Tries 4)) {
        Write-Host "`nCould not create the Function App automatically. Create it in the Azure portal:" -ForegroundColor Yellow
        Write-Host "  Function App > Create > Flex Consumption"
        Write-Host "  Resource group: $ResourceGroup"
        Write-Host "  Name:           $FunctionApp"
        Write-Host "  Region:         $Location"
        Write-Host "  Runtime:        Python $PythonVersion"
        Write-Host "  Storage tab:    use existing account $StorageAccount"
        Write-Host "Then run this script again - it will pick up from here." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "Created"
}

Step "Setting environment variables (app settings)"
$settingsFile = Join-Path $env:TEMP "diet-app-settings-$Suffix.json"
$settings = @(
    @{ name = "BLOB_CONNECTION_STRING"; value = $connectionString; slotSetting = $false },
    @{ name = "BLOB_CONTAINER"; value = $ContainerName; slotSetting = $false },
    @{ name = "BLOB_NAME"; value = $BlobName; slotSetting = $false },
    @{ name = "RESULTS_BLOB_NAME"; value = "results/diet_results.json"; slotSetting = $false }
)
try {
    [System.IO.File]::WriteAllText($settingsFile, (ConvertTo-Json -InputObject $settings))
    Invoke-Az functionapp config appsettings set --name $FunctionApp --resource-group $ResourceGroup --settings "@$settingsFile" -o none
} finally {
    Remove-Item $settingsFile -ErrorAction SilentlyContinue
}
Write-Host "BLOB_CONNECTION_STRING, BLOB_CONTAINER, BLOB_NAME, RESULTS_BLOB_NAME set"

Step "Enabling CORS for the dashboard"
$origins = Invoke-Az functionapp cors show --name $FunctionApp --resource-group $ResourceGroup --query "allowedOrigins" -o tsv
if ($origins -notcontains "*") {
    az functionapp cors add --name $FunctionApp --resource-group $ResourceGroup --allowed-origins '*' -o none
    if ($LASTEXITCODE -ne 0) { Fail "Could not enable CORS" }
}
Write-Host "Allowed origins: *"

Step "Deploying the function code (remote build)"
$deployed = $false
if ($HasFunc) {
    for ($attempt = 1; $attempt -le 2 -and -not $deployed; $attempt++) {
        func azure functionapp publish $FunctionApp --python
        if ($LASTEXITCODE -eq 0) { $deployed = $true }
        elseif ($attempt -eq 1) { Write-Host "Publish failed, retrying in 45 seconds..."; Start-Sleep -Seconds 45 }
    }
}
if (-not $deployed) {
    Write-Host "Deploying with zip package instead"
    $zipPath = Join-Path $env:TEMP "diet-function-$Suffix.zip"
    Remove-Item $zipPath -ErrorAction SilentlyContinue
    Compress-Archive -Path function_app.py, host.json, requirements.txt -DestinationPath $zipPath -ErrorAction Stop
    Invoke-Az functionapp deployment source config-zip --name $FunctionApp --resource-group $ResourceGroup `
        --src $zipPath --build-remote true -o none
    Remove-Item $zipPath -ErrorAction SilentlyContinue
}

$hostName = ""
for ($attempt = 1; $attempt -le 6 -and -not $hostName; $attempt++) {
    $hostName = az functionapp show --name $FunctionApp --resource-group $ResourceGroup `
        --query "defaultHostName || hostNames[0] || enabledHostNames[0] || properties.defaultHostName" -o tsv 2>$null
    if (-not $hostName) {
        $hostName = az resource show --resource-group $ResourceGroup --name $FunctionApp `
            --resource-type "Microsoft.Web/sites" --query "properties.defaultHostName || properties.hostNames[0]" -o tsv 2>$null
    }
    if ($hostName) { $hostName = "$hostName".Trim() } else { Start-Sleep -Seconds 10 }
}
if (-not $hostName) {
    Fail "Could not read the Function App host name. Copy 'Default domain' from the Function App Overview page in the portal; the URL is https://<default domain>/api/process-diet-data"
}
$FunctionUrl = "https://$hostName/api/process-diet-data"

Step "Testing $FunctionUrl"
$response = $null
for ($attempt = 1; $attempt -le 8 -and -not $response; $attempt++) {
    try {
        $response = Invoke-RestMethod -Uri $FunctionUrl -Method Get -TimeoutSec 120
    } catch {
        Write-Host "  Attempt $attempt failed ($($_.Exception.Message)). Waiting 20 seconds..."
        Start-Sleep -Seconds 20
    }
}

[ordered]@{
    suffix          = $Suffix
    subscription    = $subscription.name
    resourceGroup   = $ResourceGroup
    location        = $Location
    storageAccount  = $StorageAccount
    blobContainer   = $ContainerName
    datasetBlob     = $BlobName
    functionApp     = $FunctionApp
    functionUrl     = $FunctionUrl
    lastDeployedUtc = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json | Set-Content -Path $StateFile -Encoding ASCII

if (-not $response) {
    Fail "Function did not respond yet. Wait a few minutes and open $FunctionUrl in a browser. Details saved to azure-deployment.json"
}

Write-Host "`nResults:" -ForegroundColor Green
$rows = foreach ($p in $response.results.PSObject.Properties) {
    [pscustomobject]@{
        Diet      = $p.Name
        Protein_g = $p.Value.average_protein_g
        Carbs_g   = $p.Value.average_carbs_g
        Fat_g     = $p.Value.average_fat_g
        Recipes   = $p.Value.recipe_count
    }
}
$rows | Format-Table -AutoSize | Out-String -Width 120 | Write-Host
Write-Host "Server execution time: $($response.metadata.execution_time_ms) ms"

Write-Host "`n=========================================================" -ForegroundColor Green
Write-Host " DEPLOYED FUNCTION URL (give this to Person 3):" -ForegroundColor Green
Write-Host " $FunctionUrl" -ForegroundColor Yellow
Write-Host "=========================================================" -ForegroundColor Green
Write-Host "Resource group: $ResourceGroup | Storage: $StorageAccount | Function App: $FunctionApp"
Write-Host "Saved to azure-deployment.json"
