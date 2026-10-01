[CmdletBinding()]
param(
    [string]$BasePath = 'D:\Daten\git',
    [string]$RepoName = 'aoostar-truenas-lcd',
    [ValidateSet('public','private')]
    [string]$Visibility = 'public',
    [switch]$ForceReplace,
    [switch]$SkipWorkflowWait
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

function Require-Command {
    param([Parameter(Mandatory=$true)][string]$Name)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) { throw "Required command '$Name' was not found in PATH." }
    return $cmd
}

function Invoke-Git {
    param([Parameter(Mandatory=$true)][string[]]$GitArgs)
    & git @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw "git $($GitArgs -join ' ') failed with exit code $LASTEXITCODE."
    }
}

function Copy-ProjectFiles {
    param(
        [Parameter(Mandatory=$true)][string]$Source,
        [Parameter(Mandatory=$true)][string]$Destination
    )
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    Get-ChildItem -Force $Source | Where-Object { $_.Name -ne '.git' } | ForEach-Object {
        Copy-Item -Recurse -Force $_.FullName $Destination
    }
}

Write-Host 'AOOSTAR TrueNAS LCD - GitHub bootstrap' -ForegroundColor Cyan
Require-Command -Name 'git' | Out-Null

$ScriptRoot = (Resolve-Path (Split-Path -Parent $MyInvocation.MyCommand.Path)).Path
$Target = Join-Path $BasePath $RepoName
New-Item -ItemType Directory -Force -Path $BasePath | Out-Null

# A previous interrupted run may already have created only .git in the target.
# Preserve that repository and copy/update the project files around it.
$SameLocation = $false
if (Test-Path $Target) {
    $TargetResolved = (Resolve-Path $Target).Path
    $SameLocation = ($ScriptRoot.TrimEnd('\') -ieq $TargetResolved.TrimEnd('\'))
}

if (-not $SameLocation) {
    if ((Test-Path $Target) -and $ForceReplace) {
        Write-Host "Replacing target project directory: $Target" -ForegroundColor Yellow
        Remove-Item -Recurse -Force $Target
    }
    Copy-ProjectFiles -Source $ScriptRoot -Destination $Target
}

Set-Location $Target

$gh = Get-Command 'gh' -ErrorAction SilentlyContinue
if ($gh) {
    & gh auth status
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'GitHub CLI is installed but not authenticated. Starting login...' -ForegroundColor Yellow
        & gh auth login
        if ($LASTEXITCODE -ne 0) { throw 'GitHub CLI authentication failed.' }
    }
    $GitHubUser = ((& gh api user --jq '.login') | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $GitHubUser) { throw 'Could not determine the GitHub username.' }
} else {
    Write-Host 'GitHub CLI (gh) is not installed. Git itself cannot create a GitHub repository.' -ForegroundColor Yellow
    Write-Host 'Install it with: winget install --id GitHub.cli' -ForegroundColor Yellow
    $GitHubUser = Read-Host 'Enter your exact GitHub username so the TrueNAS YAML can be prepared'
    if (-not $GitHubUser) { throw 'GitHub username is required.' }
}

$GitHubUserLower = $GitHubUser.ToLowerInvariant()
$yamlPath = Join-Path $Target 'truenas-app.yaml'
$yaml = Get-Content -Raw $yamlPath
$yaml = $yaml.Replace('GITHUB_USER', $GitHubUserLower)
# Also repair/rewrite an already customized image line on repeated runs.
$yaml = $yaml -replace 'ghcr\.io/[^/]+/aoostar-truenas-lcd:latest', "ghcr.io/$GitHubUserLower/aoostar-truenas-lcd:latest"
Set-Content -Path $yamlPath -Value $yaml -Encoding UTF8

if (-not (Test-Path (Join-Path $Target '.git'))) {
    Invoke-Git -GitArgs @('init')
}
Invoke-Git -GitArgs @('branch','-M','main')
Invoke-Git -GitArgs @('add','-A')

& git diff --cached --quiet
$DiffExit = $LASTEXITCODE
if ($DiffExit -eq 1) {
    Invoke-Git -GitArgs @('commit','-m','Initial TrueNAS SCALE port with GHCR build')
} elseif ($DiffExit -eq 0) {
    Write-Host 'No new files to commit.' -ForegroundColor DarkGray
} else {
    throw "git diff --cached --quiet failed with exit code $DiffExit."
}

if ($gh) {
    & gh repo view "$GitHubUser/$RepoName" *> $null
    $RepoExists = ($LASTEXITCODE -eq 0)

    if (-not $RepoExists) {
        Write-Host "Creating GitHub repository $GitHubUser/$RepoName ($Visibility)..." -ForegroundColor Cyan
        & gh repo create "$GitHubUser/$RepoName" "--$Visibility" --source . --remote origin --push
        if ($LASTEXITCODE -ne 0) { throw 'GitHub repository creation/push failed.' }
    } else {
        $origin = (& git remote get-url origin 2>$null | Out-String).Trim()
        if (-not $origin) {
            Invoke-Git -GitArgs @('remote','add','origin',"https://github.com/$GitHubUser/$RepoName.git")
        }
        Invoke-Git -GitArgs @('push','-u','origin','main')
    }

    if (-not $SkipWorkflowWait) {
        Write-Host 'Waiting for the GHCR build workflow to appear...' -ForegroundColor Cyan
        $RunId = $null
        for ($i = 0; $i -lt 12 -and -not $RunId; $i++) {
            Start-Sleep -Seconds 5
            $RunId = ((& gh run list --workflow 'docker-publish.yml' --limit 1 --json databaseId --jq '.[0].databaseId' 2>$null) | Out-String).Trim()
        }
        if ($RunId) {
            Write-Host "Watching workflow run $RunId..." -ForegroundColor Cyan
            & gh run watch $RunId --exit-status
            if ($LASTEXITCODE -ne 0) {
                Write-Host 'The Docker build failed. Show the failed log with:' -ForegroundColor Red
                Write-Host "  gh run view $RunId --log-failed"
                exit 2
            }
        } else {
            Write-Host 'No workflow run appeared within 60 seconds. The repository was pushed successfully.' -ForegroundColor Yellow
            Write-Host 'Check GitHub -> Actions, or run: gh run list --workflow docker-publish.yml'
        }
    }

    Write-Host ''
    Write-Host 'SUCCESS' -ForegroundColor Green
    Write-Host "Repository: https://github.com/$GitHubUser/$RepoName"
    Write-Host "Container:  ghcr.io/$GitHubUserLower/$RepoName`:latest"
    Write-Host "TrueNAS YAML: $yamlPath"
    Write-Host ''
    Write-Host 'Next: TrueNAS -> Apps -> Discover Apps -> menu -> Install via YAML' -ForegroundColor Cyan
} else {
    Write-Host ''
    Write-Host 'Local repository is ready, but no GitHub repository was created because gh is missing.' -ForegroundColor Yellow
    Write-Host "Project: $Target"
    Write-Host 'After installing GitHub CLI, run this script again from the package.'
}
