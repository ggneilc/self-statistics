param (
    [string]$EnvName = $args[0]
)

if ($EnvName -eq "dev") {
    $env:DJANGO_SETTINGS_MODULE = "selfstats.settings.dev"
}
elseif ($EnvName -eq "prod") {
    $env:DJANGO_SETTINGS_MODULE = "selfstats.settings.prod"
}
else {
    Write-Host "Usage: .\load_env.ps1 dev|prod" -ForegroundColor Red
    exit 1
}

Write-Host "Environment loaded: $env:DJANGO_SETTINGS_MODULE" -ForegroundColor Green