# Run me when: I am on Windows (or want PowerShell) and I want an off-machine backup of plan work
# while ralph-looper runs, or after it stops. Same behavior as `ralph-pusher` (bash).
#
# It pushes only the plan branch (plan/<plan>) and the step branches (step/<plan>/*) to a remote.
# The agents and the driver have no credentials. YOU run this in your own shell. It never forces a push.
#
# Usage: ./ralph-pusher.ps1 -Repo PATH -Plan NAME [-Remote NAME] [-Interval SECONDS] [-Once]
# Stop it: create PUSHER-STOP in the work directory, or press Ctrl-C.
# Exit codes: 0 ok, 3 already running, 4 last push failed (with -Once).
#Requires -Version 7.0
[CmdletBinding()]
param(
    [string]$Repo = '.',
    [Parameter(Mandatory)][string]$Plan,
    [string]$Remote = 'origin',
    [int]$Interval = 45,
    [switch]$Once
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = (& git -C $Repo rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0) { exit 2 }
$Base = if ($env:RALPH_WORK) { $env:RALPH_WORK } else { Join-Path $HOME 'repo-work' }
$Work = Join-Path (Join-Path $Base (Split-Path -Leaf $RepoRoot)) $Plan
New-Item -ItemType Directory -Force -Path $Work | Out-Null
git -C $RepoRoot remote get-url $Remote *> $null
if ($LASTEXITCODE -ne 0) { Write-Error "ralph-pusher: no remote '$Remote' in $RepoRoot"; exit 2 }

try { $lock = [System.IO.File]::Open((Join-Path $Work '.pusher.lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
catch [System.IO.IOException] { Write-Error 'ralph-pusher: another pusher runs for this plan.'; exit 3 }

function Push-Once {
    $refs = @(git -C $RepoRoot for-each-ref --format='%(refname) %(objectname)' "refs/heads/plan/$Plan" "refs/heads/step/$Plan/")
    if ($refs.Count -eq 0) { Write-Host 'nothing to push (no plan branch yet)'; return 0 }
    $sha = [System.Security.Cryptography.SHA256]::HashData([System.Text.Encoding]::UTF8.GetBytes(($refs -join "`n")))
    $sig = [Convert]::ToHexString($sha)
    $sigFile = Join-Path $Work 'push.sig'
    if ((Test-Path $sigFile) -and ((Get-Content $sigFile -Raw).Trim() -eq $sig)) { return 0 }
    $specs = $refs | ForEach-Object { $r = ($_ -split ' ')[0]; "${r}:${r}" }
    $out = git -C $RepoRoot push --porcelain $Remote @specs 2> (Join-Path $Work 'push.err')
    $stamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    Set-Content (Join-Path $Work 'push.out') $out
    if ($LASTEXITCODE -eq 0) {
        Set-Content $sigFile $sig -NoNewline
        $msg = "$stamp ok $($specs.Count) refs to $Remote"
        Set-Content (Join-Path $Work 'push.status') $msg; Write-Host $msg
        return 0
    }
    $msg = "$stamp FAILED (see push.err)"
    Set-Content (Join-Path $Work 'push.status') $msg; Write-Host $msg
    return 4
}

try {
    while ($true) {
        if (Test-Path (Join-Path $Work 'PUSHER-STOP')) { Write-Host 'ralph-pusher: PUSHER-STOP found.'; exit 0 }
        $rc = Push-Once
        if ($Once) { exit $rc }
        Start-Sleep -Seconds $Interval
    }
} finally { $lock.Dispose() }
