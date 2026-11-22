# Run me when: I am on Windows (or want PowerShell) and I want to run, resume, pause or check the
# steps of a plan in a repository that uses the repo-template layout. Same behavior as `ralph-looper` (bash).
#
# Usage: ./ralph-looper.ps1 -Repo PATH -Plan NAME [-Agent claude|codex|copilot|local] [-Jobs N]
#                           [-OnLimit wait|handoff] [-MaxIterations N]
#        ./ralph-looper.ps1 -Repo PATH -Plan NAME -Status | -Pause | -Resume
#
# Needs: PowerShell 7, git, python (python or python3 on PATH), and the agent CLI.
# Work directory: $env:RALPH_WORK or $HOME/repo-work, then <repo>/<plan>/ (never inside the repo).
# Gate commands run with PowerShell by default. Set `gate_shell: bash` in plans/<plan>/loop.yaml
# for gates written for bash. AGENT_CMD (if set) runs with `pwsh -Command`; it reads the prompt on stdin.
# Exit codes: 0 all done, 3 already running, 10 stopped early, 11 blocked, 75 usage limit (handoff).
#Requires -Version 7.0
[CmdletBinding()]
param(
    [string]$Repo = '.',
    [Parameter(Mandatory)][string]$Plan,
    [string]$Agent = $(if ($env:RALPH_AGENT) { $env:RALPH_AGENT } else { 'claude' }),
    [int]$Jobs = 0,
    [ValidateSet('wait', 'handoff')][string]$OnLimit = 'wait',
    [int]$MaxIterations = 1000,
    [switch]$Status, [switch]$Pause, [switch]$Resume,
    [string]$Worker = ''    # internal: run one step in this process
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Here = Split-Path -Parent $PSCommandPath
$Pick = Join-Path $Here 'lib/pick_step.py'
$Usage = Join-Path $Here 'lib/usage.py'
$Py = (Get-Command python -ErrorAction SilentlyContinue) ?? (Get-Command python3 -ErrorAction SilentlyContinue)
if (-not $Py) { Write-Error 'ralph-looper: python not found on PATH'; exit 2 }
$Py = $Py.Source

function Git { & git @args; }
$RepoRoot = (& git -C $Repo rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0) { exit 2 }
$RepoName = Split-Path -Leaf $RepoRoot
$Base = if ($env:RALPH_WORK) { $env:RALPH_WORK } else { Join-Path $HOME 'repo-work' }
$Work = Join-Path (Join-Path $Base $RepoName) $Plan
$WT = Join-Path $Work 'worktrees'
$PWT = Join-Path $WT '_plan'
$Branch = "plan/$Plan"
$Ledger = Join-Path $Work 'ledger.jsonl'
foreach ($d in 'logs', 'results', 'attempts', 'worktrees') { New-Item -ItemType Directory -Force -Path (Join-Path $Work $d) | Out-Null }

function Say([string]$m) { $line = "ralph-looper: $m"; Write-Host $line; Add-Content -Path (Join-Path $Work 'driver.out') -Value $line }
function Say-Block([string]$text) { foreach ($l in ($text -split "`r?`n")) { Write-Host $l; Add-Content -Path (Join-Path $Work 'driver.out') -Value $l } }

function Invoke-Pick { & $Py -I $Pick @args }
function Get-Field([string]$file, [string]$key) { $r = Invoke-Pick field $file $key; if ($null -eq $r) { '' } else { ($r -join "`n").Trim() } }

if ($Pause) { New-Item -ItemType File -Force -Path (Join-Path $Work 'PAUSE') | Out-Null; Write-Host 'paused'; exit 0 }
if ($Resume) { Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $Work 'PAUSE'); Write-Host 'resumed'; exit 0 }

# ---- plan branch and its worktree ----
git -C $RepoRoot worktree prune
git -C $RepoRoot rev-parse -q --verify "refs/heads/$Branch" *> $null
if ($LASTEXITCODE -ne 0) { git -C $RepoRoot branch $Branch HEAD; if ($LASTEXITCODE -ne 0) { exit 2 } }
if (-not (Test-Path $PWT)) { git -C $RepoRoot worktree add -q $PWT $Branch; if ($LASTEXITCODE -ne 0) { exit 2 } }
$PlanDir = Join-Path (Join-Path $PWT 'plans') $Plan
if (-not (Test-Path (Join-Path $PlanDir 'steps'))) { Write-Error "ralph-looper: no $PlanDir/steps on branch $Branch"; exit 2 }

function Get-Cfg([string]$key, [string]$default) {
    $f = Join-Path $PlanDir 'loop.yaml'
    if (Test-Path $f) {
        $m = Select-String -Path $f -Pattern "^$([regex]::Escape($key)):\s*(.*)$" | Select-Object -First 1
        if ($m) { $v = ($m.Matches[0].Groups[1].Value -replace '\s+#.*$', '').Trim().Trim('"'); if ($v) { return $v } }
    }
    return $default
}

if ($Status) {
    Invoke-Pick summary $PlanDir
    Write-Host "work dir: $Work"
    if (Test-Path (Join-Path $Work 'PAUSE')) { Write-Host 'PAUSED' }
    if (Test-Path $Ledger) { Get-Content $Ledger -Tail 3 | ForEach-Object { $_.Substring(0, [Math]::Min(300, $_.Length)) } }
    exit 0
}

$StepTimeoutMin = [int](Get-Cfg 'step_timeout_minutes' '45')
$GateTimeoutMin = [int](Get-Cfg 'gate_timeout_minutes' '15')
$MaxAttempts = [int](Get-Cfg 'max_attempts' '3')
$MaxUsd = [double](Get-Cfg 'max_usd' '0')
$MaxStepUsd = Get-Cfg 'max_step_usd' '6'
$GateShell = Get-Cfg 'gate_shell' 'pwsh'
if ($Jobs -le 0) { $Jobs = [int](Get-Cfg 'jobs' '1') }
$env:RALPH_AGENT = $Agent
foreach ($v in 'GH_TOKEN', 'GITHUB_TOKEN', 'GITLAB_TOKEN') { Remove-Item "Env:$v" -ErrorAction SilentlyContinue }
$env:GIT_TERMINAL_PROMPT = '0'

# ---- agent command lines (an executable and an argument list) ----
function Get-AgentSpec([string]$agent, [string]$model, [string]$effort, [string]$prompt) {
    $allow = 'Read,Edit,Write,Glob,Grep,Bash(git:*),Bash(python:*),Bash(python3:*),Bash(pwsh:*),Bash(bash:*),Bash(ls:*),Bash(cat:*),Bash(grep:*),Bash(find:*),Bash(mkdir:*),Bash(cp:*),Bash(mv:*),Bash(rm:*),Bash(echo:*),Bash(test:*),Bash(pwd:*),Bash(cd:*)'
    switch ($agent) {
        'claude' {
            $a = @('-p', '--output-format', 'json')
            if ($model) { $a += @('--model', $model) }
            $a += @('--max-budget-usd', $MaxStepUsd, '--permission-mode', 'dontAsk', '--allowedTools', $allow,
                '--disallowedTools', 'Bash(git push:*)', 'Bash(gh:*)', 'Bash(curl:*)', 'Bash(wget:*)', 'Bash(ssh:*)')
            return @{ Exe = 'claude'; Args = $a; Stdin = $true }
        }
        'copilot' {
            $a = @('--no-auto-update', '--no-ask-user', '--assisted-approval', '--disable-builtin-mcps', '--output-format', 'json')
            if ($model) { $a += @('--model', $model) }
            if ($effort) { $a += @('--reasoning-effort', $effort) }
            $a += @('--allow-tool=shell(python)', '--allow-tool=shell(git)', '--allow-tool=shell(pwsh)', '--allow-tool=write',
                '--deny-tool=shell(git push)', '--deny-tool=shell(gh)', '--deny-tool=shell(curl)', '--deny-tool=shell(wget)', '--deny-tool=shell(ssh)',
                '--prompt', $prompt)
            return @{ Exe = 'copilot'; Args = $a; Stdin = $false }
        }
        'codex' {
            $a = @('exec')
            if ($model) { $a += @('-m', $model) }
            if ($effort) { $a += @('-c', "model_reasoning_effort=`"$effort`"") }
            $a += @('--approve-for-me', '--color', 'never', '--json', '-')
            return @{ Exe = 'codex'; Args = $a; Stdin = $true }
        }
        default { throw "ralph-looper: agent '$agent' is not available (the local agent is not built yet). Set AGENT_CMD." }
    }
}

# ---- run a process with stdin text, output files and a timeout. Returns the exit code (124 = timeout). ----
function Invoke-Timed([string]$exe, [string[]]$argList, [string]$cwd, [string]$stdin, [string]$outFile, [string]$errFile, [int]$timeoutMin) {
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $cmd = Get-Command $exe -ErrorAction SilentlyContinue
    $psi.FileName = if ($cmd) { $cmd.Source } else { $exe }
    foreach ($x in $argList) { $psi.ArgumentList.Add($x) }
    $psi.WorkingDirectory = $cwd
    $psi.RedirectStandardInput = $true; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $p = [System.Diagnostics.Process]::Start($psi)
    $o = $p.StandardOutput.ReadToEndAsync(); $e = $p.StandardError.ReadToEndAsync()
    if ($stdin) { $p.StandardInput.Write($stdin) }
    $p.StandardInput.Close()
    $rc = 0
    if (-not $p.WaitForExit($timeoutMin * 60000)) { $p.Kill($true); $p.WaitForExit(); $rc = 124 } else { $rc = $p.ExitCode }
    [System.IO.File]::WriteAllText($outFile, $o.GetAwaiter().GetResult())
    [System.IO.File]::WriteAllText($errFile, $e.GetAwaiter().GetResult())
    return $rc
}

# ---- an exclusive file lock. The OS frees it if the process dies. ----
function Lock-File([string]$path, [int]$waitSeconds) {
    $deadline = (Get-Date).AddSeconds($waitSeconds)
    while ($true) {
        try { return [System.IO.File]::Open($path, 'OpenOrCreate', 'ReadWrite', 'None') }
        catch [System.IO.IOException] { if ((Get-Date) -gt $deadline) { return $null }; Start-Sleep -Milliseconds 200 }
    }
}
function With-Lock([string]$path, [scriptblock]$body) {
    $fs = Lock-File $path 600
    if (-not $fs) { throw "could not get lock $path" }
    try { & $body } finally { $fs.Dispose() }
}

function Get-StepFile([string]$root, [string]$sid) { Join-Path $root "plans/$Plan/steps/$sid.md" }
function Get-Spent { $t = 0.0; if (Test-Path $Ledger) { foreach ($l in Get-Content $Ledger) { if ($l.Trim()) { $r = $l | ConvertFrom-Json; if ($r.cost_usd) { $t += [double]$r.cost_usd } } } }; '{0:N4}' -f $t }
function Read-Attempts([string]$sid) { $f = Join-Path $Work "attempts/$sid"; if (Test-Path $f) { [int](Get-Content $f -Raw) } else { 0 } }

# ---- run one step ----
function Invoke-Step([string]$sid) {
    $swt = Join-Path $WT $sid
    $br = "step/$Plan/$sid"
    $buf = [System.Collections.Generic.List[string]]::new()
    $res = Join-Path $Work "results/$sid"
    if (-not (Test-Path $swt)) {
        git -C $RepoRoot worktree add -q -B $br $swt $Branch
        if ($LASTEXITCODE -ne 0) { Set-Content $res 'fail'; return }
        $buf.Add("starting step $sid (new worktree)")
    } else { $buf.Add("resuming step $sid (worktree exists: previous run stopped)") }
    $sfile = Get-StepFile $swt $sid
    $tier = Get-Field $sfile 'tier'; if (-not $tier) { $tier = 'standard' }
    $attempts = Read-Attempts $sid
    if ($attempts -ge 1) { $tier = 'standard' }
    $model = Get-Cfg "${Agent}_model_$tier" ''
    $effort = Get-Cfg "${Agent}_effort_$tier" ''
    $env:RALPH_STEP = $sid; $env:RALPH_PLAN = $Plan; $env:RALPH_MODEL = $model; $env:RALPH_EFFORT = $effort; $env:RALPH_TIER = $tier
    $buf.Add("step=$sid agent=$Agent tier=$tier model=$(if ($model) { $model } else { 'cli-default' }) effort=$(if ($effort) { $effort } else { 'default' }) attempts=$attempts")

    $promptText = (Get-Content (Join-Path $Here 'lib/PROMPT.md') -Raw).Replace('{{PLAN}}', $Plan).Replace('{{STEP}}', $sid)
    Set-Content -Path (Join-Path $Work "logs/prompt-$sid.md") -Value $promptText
    $stamp = Get-Date -Format 'yyyyMMddTHHmmss'
    $out = Join-Path $Work "logs/$sid-$stamp.json"
    $headBefore = (git -C $swt rev-parse HEAD).Trim()
    $t0 = Get-Date
    if ($env:AGENT_CMD) { $rc = Invoke-Timed 'pwsh' @('-NoProfile', '-Command', $env:AGENT_CMD) $swt $promptText $out "$out.err" $StepTimeoutMin }
    else {
        $spec = Get-AgentSpec $Agent $model $effort $promptText
        $rc = Invoke-Timed $spec.Exe $spec.Args $swt $(if ($spec.Stdin) { $promptText } else { '' }) $out "$out.err" $StepTimeoutMin
    }
    $secs = [int]((Get-Date) - $t0).TotalSeconds
    $ublock = & $Py -I $Usage --agent $Agent --out $out --ledger $Ledger --rc $rc --seconds $secs --step $sid --tier $tier --model $model --effort $effort --head-before $headBefore --cwd $swt
    $buf.Add(($ublock -join "`n"))
    if ($ublock -match '(?m)^outcome: limit') { Set-Content $res 'limit'; $buf -join "`n"; return }

    # ---- verify: the driver runs the gate itself. It does not trust the agent. ----
    $gate = Get-Field $sfile 'gate'
    $gateOut = Join-Path $Work "logs/gate-$sid.out"
    $gateOk = $false
    if ($gate) {
        $gargs = if ($GateShell -eq 'bash') { @('bash', '-c', $gate) } else { @('pwsh', '-NoProfile', '-Command', $gate) }
        $grc = Invoke-Timed $gargs[0] $gargs[1..($gargs.Count - 1)] $swt '' $gateOut "$gateOut.err" $GateTimeoutMin
        $gateOk = ($grc -eq 0)
    }
    if ($gateOk) {
        Invoke-Pick set $sfile status done
        Invoke-Pick set $sfile claimed_by "$Agent $(if ($model) { $model } else { 'cli-default' })"
        Invoke-Pick set $sfile claimed_at (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        Invoke-Pick set $sfile evidence "gate passed $((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')) (driver-verified)"
        git -C $swt add -A; git -C $swt commit -q -m "plan($Plan): $sid done"
        $state = @{ merged = $false }
        With-Lock (Join-Path $Work 'merge.lock') {
            git -C $PWT merge --no-ff -q -m "plan($Plan): merge $sid" $br 2>> (Join-Path $Work 'logs/merge.err')
            if ($LASTEXITCODE -eq 0) { $state.merged = $true } else { git -C $PWT merge --abort 2>$null }
        }
        if ($state.merged) {
            git -C $RepoRoot worktree remove --force $swt; git -C $RepoRoot branch -q -D $br
            Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $Work "attempts/$sid")
            Set-Content $res 'done'; $buf.Add("result: $sid done (gate passed, merged into $Branch)")
        } else {
            Set-Content (Join-Path $Work "attempts/$sid") ($attempts + 1); Set-Content $res 'fail'
            $buf.Add("result: $sid MERGE CONFLICT (see logs/merge.err); worktree kept")
        }
    } else {
        Set-Content (Join-Path $Work "attempts/$sid") ($attempts + 1); Set-Content $res 'fail'
        $buf.Add("result: $sid gate FAILED (rc=$rc, attempt $($attempts + 1)/$MaxAttempts; see logs/gate-$sid.out)")
        if (($attempts + 1) -ge $MaxAttempts) {
            Invoke-Pick set (Get-StepFile $PWT $sid) status blocked
            With-Lock (Join-Path $Work 'merge.lock') { git -C $PWT add -A; git -C $PWT commit -q -m "plan($Plan): $sid blocked after $MaxAttempts attempts" }
            $buf.Add("result: $sid marked blocked")
        }
    }
    $buf -join "`n"
}

if ($Worker) { Invoke-Step $Worker; exit 0 }

# ---- single instance: the lock handle is not inherited by child processes ----
$LockHandle = Lock-File (Join-Path $Work '.lock') 0
if (-not $LockHandle) { Write-Error "ralph-looper: another loop runs for $RepoName/$Plan (lock held)."; exit 3 }

Say "start: repo=$RepoName plan=$Plan agent=$Agent jobs=$Jobs work=$Work"
$iter = 0; $stall = 0; $result = 0
while ($true) {
    if (Test-Path (Join-Path $Work 'PAUSE')) { Say 'PAUSE found. Run -Resume.'; $result = 10; break }
    if (Test-Path (Join-Path $Work 'STOP')) { Say 'STOP found.'; $result = 10; break }
    if ($iter -ge $MaxIterations) { Say 'iteration budget reached'; $result = 10; break }
    if ($MaxUsd -gt 0 -and [double](Get-Spent) -ge $MaxUsd) { Say "cost cap reached (`$$MaxUsd)"; $result = 10; break }

    # steps whose worktree exists and that are not done on the plan branch: resume first
    $active = @()
    foreach ($d in Get-ChildItem -Directory $WT) {
        if ($d.Name -eq '_plan') { continue }
        $st = Get-Field (Get-StepFile $PWT $d.Name) 'status'
        if ($st -eq 'done') { git -C $RepoRoot worktree remove --force $d.FullName; git -C $RepoRoot branch -q -D "step/$Plan/$($d.Name)" 2>$null; continue }
        if ($st -eq 'blocked') { continue }
        $active += $d.Name
    }
    $active = @($active | Select-Object -First $Jobs)
    $batch = @($active)
    if ($batch.Count -lt $Jobs) {
        foreach ($line in @(Invoke-Pick ready $PlanDir --max $Jobs --active ($active -join ','))) {
            if ($line) { $batch += ($line | ConvertFrom-Json).id }
        }
    }
    if ($batch.Count -eq 0) {
        $summary = Invoke-Pick summary $PlanDir; $code = $LASTEXITCODE
        Say "no step to run: $summary"
        if ($code -eq 0) { Say 'ALL STEPS DONE'; $result = 0 } else { Say 'BLOCKED or waiting'; $result = 11 }
        break
    }

    $iter++
    Say "batch ${iter}: $($batch -join ' ')"
    $procs = @{}
    foreach ($sid in $batch) {
        $logf = Join-Path $Work "logs/worker-$sid.out"
        $procs[$sid] = Start-Process -FilePath 'pwsh' -PassThru -NoNewWindow -RedirectStandardOutput $logf -ArgumentList @(
            '-NoProfile', '-File', "`"$PSCommandPath`"", '-Repo', "`"$RepoRoot`"", '-Plan', $Plan, '-Agent', $Agent, '-Jobs', $Jobs, '-Worker', $sid)
    }
    foreach ($sid in $batch) { $procs[$sid].WaitForExit() }
    $limited = $false; $progressed = $false
    foreach ($sid in $batch) {
        $logf = Join-Path $Work "logs/worker-$sid.out"
        if (Test-Path $logf) { Say-Block (Get-Content $logf -Raw) }
        $rf = Join-Path $Work "results/$sid"
        $r = if (Test-Path $rf) { (Get-Content $rf -Raw).Trim() } else { '' }
        if ($r -eq 'limit') { $limited = $true }
        if ($r -eq 'done') { $progressed = $true }
    }
    Say "batch $iter finished; spent `$$(Get-Spent)"
    if ($limited) {
        if ($OnLimit -eq 'handoff') { Say "$Agent hit a usage limit. Run again with another agent: -Agent claude|codex|copilot"; $result = 75; break }
        $remaining = if ($env:LIMIT_SLEEP_SECS) { [int]$env:LIMIT_SLEEP_SECS } else { 900 }
        Say "usage limit: sleeping ${remaining}s"
        while ($remaining -gt 0 -and -not (Test-Path (Join-Path $Work 'PAUSE')) -and -not (Test-Path (Join-Path $Work 'STOP'))) { Start-Sleep -Seconds 5; $remaining -= 5 }
        $iter--; continue
    }
    if ($progressed) { $stall = 0 } else { $stall++ }
    if ($stall -ge 6) { Say "stall breaker: $stall batches without progress"; $result = 11; break }
    Start-Sleep -Seconds 1
}
Say "finished (exit $result). spent `$$(Get-Spent). log: $(Join-Path $Work 'driver.out')"
$LockHandle.Dispose()
exit $result
