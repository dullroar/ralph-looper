# Run me when: I am on Windows (or want PowerShell) and I want to run, resume, pause or check the
# steps of a plan in a repository that uses the repo-template layout. Same behavior as `ralph-looper` (bash).
#
# Usage: ./ralph-looper.ps1 -Repo PATH -Plan NAME [-Agent claude|codex|copilot|local] [-Jobs N]
#                           [-OnLimit wait|handoff] [-MaxIterations N]
#        ./ralph-looper.ps1 -Repo PATH -Plan NAME -Status | -Pause | -Resume
#        ./ralph-looper.ps1 -Capabilities   (print the supported features, one a line)
#
# A step can name its executor in front matter: `agent:` (claude, codex, copilot, local, script,
# operator), `fallback:` and `run:` (for script steps). See docs/routing.md. The driver reads
# gate, touches, agent, fallback and run from the plan branch, and rejects changes outside touches.
#
# Needs: PowerShell 7, git, python (python or python3 on PATH), and the agent CLI.
# Work directory: $env:RALPH_WORK or $HOME/repo-work, then <repo>/<plan>/ (never inside the repo).
# Gate commands run with PowerShell by default. Set `gate_shell: bash` in plans/<plan>/loop.yaml
# for gates written for bash. The `run:` command of a script step uses the same shell.
# AGENT_CMD (if set) replaces the command of the -Agent executor. AGENT_CMD_<NAME> (for example
# AGENT_CMD_CODEX) replaces the command of one named agent. Both run with `pwsh -Command` and read
# the prompt on stdin. The local agent: LOCAL_AGENT_CMD (a command and arguments, separated by
# spaces) if set, else `local-coder-agent` on PATH. It gets the same arguments as claude.
# Exit codes: 0 all done, 3 already running, 10 stopped early, 11 blocked, 12 waiting for operator,
#             75 usage limit (handoff).
#Requires -Version 7.0
[CmdletBinding()]
param(
    [string]$Repo = '.',
    [string]$Plan = '',
    [string]$Agent = $(if ($env:RALPH_AGENT) { $env:RALPH_AGENT } else { 'claude' }),
    [int]$Jobs = 0,
    [ValidateSet('wait', 'handoff')][string]$OnLimit = 'wait',
    [int]$MaxIterations = 1000,
    [switch]$Status, [switch]$Pause, [switch]$Resume, [switch]$Capabilities,
    [string]$Worker = ''    # internal: run one step in this process
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($Capabilities) {
    'step-agent', 'operator-step', 'script-step', 'local-agent', 'gate-from-plan-branch', 'touches-enforced' | ForEach-Object { Write-Output $_ }
    exit 0
}
if (-not $Plan) { Write-Error 'ralph-looper: -Plan is required'; exit 2 }
if ($Agent -notin 'claude', 'codex', 'copilot', 'local') { Write-Error "ralph-looper: unknown -Agent '$Agent'"; exit 2 }

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
foreach ($d in 'logs', 'results', 'attempts', 'worktrees', 'base', 'spec') { New-Item -ItemType Directory -Force -Path (Join-Path $Work $d) | Out-Null }

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
    foreach ($w in @(Invoke-Pick waiting $PlanDir)) { if ($w) { Write-Host "waiting for operator: $w (see plans/$Plan/steps/$w.md)" } }
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
function Get-ClaudeArgs([string]$model) {
    $allow = 'Read,Edit,Write,Glob,Grep,Bash(git:*),Bash(python:*),Bash(python3:*),Bash(pwsh:*),Bash(bash:*),Bash(ls:*),Bash(cat:*),Bash(grep:*),Bash(find:*),Bash(mkdir:*),Bash(cp:*),Bash(mv:*),Bash(rm:*),Bash(echo:*),Bash(test:*),Bash(pwd:*),Bash(cd:*)'
    $a = @('-p', '--output-format', 'json')
    if ($model) { $a += @('--model', $model) }
    $a += @('--max-budget-usd', $MaxStepUsd, '--permission-mode', 'dontAsk', '--allowedTools', $allow,
        '--disallowedTools', 'Bash(git push:*)', 'Bash(gh:*)', 'Bash(curl:*)', 'Bash(wget:*)', 'Bash(ssh:*)')
    return $a
}

# An override command for an executor: AGENT_CMD_<NAME>, then AGENT_CMD for the -Agent executor.
# AGENT_CMD stays in the environment: the worker processes read it too.
function Get-Override([string]$name) {
    $v = [Environment]::GetEnvironmentVariable('AGENT_CMD_' + ($name.ToUpperInvariant() -replace '[^A-Z0-9]', '_'))
    if ($v) { return $v }
    if ($name -eq $Agent -and $env:AGENT_CMD) { return $env:AGENT_CMD }
    return ''
}
function Test-AgentKnown([string]$name) { $name -in 'claude', 'codex', 'copilot', 'local', 'script', 'operator' }
function Test-CanRun([string]$name) {
    if (-not (Test-AgentKnown $name)) { return $false }
    if (Get-Override $name) { return $true }
    switch ($name) {
        { $_ -in 'script', 'operator' } { return $true }
        'local' { return [bool]($env:LOCAL_AGENT_CMD -or (Get-Command local-coder-agent -ErrorAction SilentlyContinue)) }
        default { return [bool](Get-Command $name -ErrorAction SilentlyContinue) }
    }
}

function Get-AgentSpec([string]$agent, [string]$model, [string]$effort, [string]$prompt) {
    switch ($agent) {
        'claude' { return @{ Exe = 'claude'; Args = (Get-ClaudeArgs $model); Stdin = $true } }
        'local' {
            if ($env:LOCAL_AGENT_CMD) {
                $parts = @($env:LOCAL_AGENT_CMD -split '\s+' | Where-Object { $_ })
                return @{ Exe = $parts[0]; Args = @(@($parts | Select-Object -Skip 1) + (Get-ClaudeArgs $model)); Stdin = $true }
            }
            if (Get-Command local-coder-agent -ErrorAction SilentlyContinue) {
                return @{ Exe = 'local-coder-agent'; Args = (Get-ClaudeArgs $model); Stdin = $true }
            }
            throw "ralph-looper: the 'local' agent needs LOCAL_AGENT_CMD or 'local-coder-agent' on PATH"
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
        default { throw "ralph-looper: agent '$agent' has no command" }
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

# ---- helpers for one step ----
function Get-StepRel([string]$sid) { "plans/$Plan/steps/$sid.md" }

# Run a gate or a `run:` command with the gate shell. Returns the exit code (124 = timeout).
function Invoke-Shell([string]$command, [string]$cwd, [string]$outFile, [int]$timeoutMin) {
    $gargs = if ($GateShell -eq 'bash') { @('bash', '-c', $command) } else { @('pwsh', '-NoProfile', '-Command', $command) }
    return Invoke-Timed $gargs[0] $gargs[1..($gargs.Count - 1)] $cwd '' $outFile "$outFile.err" $timeoutMin
}

# Save the step file of commit $startRev to $spec. Returns $true on success.
function Save-Spec([string]$startRev, [string]$rel, [string]$spec) {
    if (-not $startRev) { return $false }
    $text = & git -C $RepoRoot show "${base}:$rel" 2>$null
    if ($LASTEXITCODE -ne 0) { return $false }
    Set-Content -Path $spec -Value $text
    return $true
}

function Merge-Step([string]$sid, [string]$br) {
    $state = @{ merged = $false }
    With-Lock (Join-Path $Work 'merge.lock') {
        git -C $PWT merge --no-ff -q -m "plan($Plan): merge $sid" $br 2>> (Join-Path $Work 'logs/merge.err') | Out-Null
        if ($LASTEXITCODE -eq 0) { $state.merged = $true } else { git -C $PWT merge --abort 2>$null | Out-Null }
    } | Out-Null
    return $state.merged
}

function Remove-StepWorktree([string]$sid) {
    git -C $RepoRoot worktree remove --force (Join-Path $WT $sid) 2>$null
    git -C $RepoRoot branch -q -D "step/$Plan/$sid" 2>$null
    Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $Work "base/$sid")
}

function Write-ScriptLedger([string]$sid, [int]$rc, [int]$secs, [string]$tier, [int]$attempt) {
    $rec = [ordered]@{ ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'); step = $sid; agent = 'script'; route = 'script'; attempt = $attempt; gate = 'none'
        exit_code = $rc; seconds = $secs; tier = $tier; model_requested = ''; effort_requested = ''
        cost_usd = 0.0; cost_est_usd = 0.0; ai_credits = 0; tok_fresh_in = 0; tok_cache_read = 0
        tok_cache_write = 0; tok_out = 0; tok_reasoning = 0; api_calls = 0; model_reported = ''
        models_all = @(); model_mismatch = $false; usage_limited = $false }
    Add-Content -Path $Ledger -Value ($rec | ConvertTo-Json -Compress)
}

# Count a failed attempt. Block the step after MaxAttempts.
function Register-Failure([string]$sid, [int]$attempts, [System.Collections.Generic.List[string]]$buf, [string]$message) {
    Set-Content (Join-Path $Work "attempts/$sid") ($attempts + 1); Set-Content (Join-Path $Work "results/$sid") 'fail'
    $buf.Add("result: $message")
    if (($attempts + 1) -ge $MaxAttempts) {
        $rel = Get-StepRel $sid
        Invoke-Pick set (Join-Path $PWT $rel) status blocked
        With-Lock (Join-Path $Work 'merge.lock') { git -C $PWT add -- $rel; git -C $PWT commit -q -m "plan($Plan): $sid blocked after $MaxAttempts attempts" }
        $buf.Add("result: $sid marked blocked")
    }
}

# ---- operator step: no agent. Run the gate in a fresh worktree. A failed gate is not an attempt. ----
function Invoke-Operator([string]$sid) {
    $swt = Join-Path $WT $sid; $br = "step/$Plan/$sid"; $rel = Get-StepRel $sid
    $res = Join-Path $Work "results/$sid"; $spec = Join-Path $Work "spec/$sid.md"
    if (Test-Path $swt) { Remove-StepWorktree $sid }
    $startRev = (git -C $RepoRoot rev-parse $Branch).Trim()
    if (-not (Save-Spec $startRev $rel $spec)) { Set-Content $res 'fail'; "result: $sid has no step file on $Branch"; return }
    $gate = Get-Field $spec 'gate'
    git -C $RepoRoot worktree add -q -B $br $swt $startRev
    if ($LASTEXITCODE -ne 0) { Set-Content $res 'fail'; return }
    Set-Content (Join-Path $Work "base/$sid") $startRev
    "checking operator step $sid"
    $ok = $false
    if ($gate) { $ok = ((Invoke-Shell $gate $swt (Join-Path $Work "logs/gate-$sid.out") $GateTimeoutMin) -eq 0) }
    if ($ok) {
        $sfile = Join-Path $swt $rel
        Invoke-Pick set $sfile status done
        Invoke-Pick set $sfile claimed_by operator
        Invoke-Pick set $sfile claimed_at (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        Invoke-Pick set $sfile evidence "gate passed $((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')) (operator step, driver-verified)"
        git -C $swt add -- $rel; git -C $swt commit -q -m "plan($Plan): $sid done (operator)"
        if (Merge-Step $sid $br) {
            Remove-StepWorktree $sid; Set-Content $res 'done'
            "result: $sid done (operator gate passed, merged into $Branch)"
        } else {
            Remove-StepWorktree $sid; Set-Content $res 'wait'
            "result: $sid MERGE CONFLICT (see logs/merge.err)"
        }
    } else {
        Remove-StepWorktree $sid; Set-Content $res 'wait'
        "waiting for operator: $sid (see plans/$Plan/steps/$sid.md)"
    }
}

# ---- run one step ----
function Invoke-Step([string]$sid) {
    $swt = Join-Path $WT $sid
    $br = "step/$Plan/$sid"
    $rel = Get-StepRel $sid
    $spec = Join-Path $Work "spec/$sid.md"
    $buf = [System.Collections.Generic.List[string]]::new()
    $res = Join-Path $Work "results/$sid"
    $attempts = Read-Attempts $sid
    # The driver-owned keys come from the plan commit from which the step worktree started.
    if (Test-Path $swt) {
        $bf = Join-Path $Work "base/$sid"
        $startRev = if (Test-Path $bf) { (Get-Content $bf -Raw).Trim() } else { '' }
        if (-not $startRev) { $startRev = "$(git -C $RepoRoot merge-base $br $Branch 2>$null)".Trim() }
    } else { $startRev = (git -C $RepoRoot rev-parse $Branch).Trim() }
    if (-not (Save-Spec $startRev $rel $spec)) { Set-Content $res 'fail'; "result: $sid has no step file at the plan commit $startRev"; return }
    $fmAgent = Get-Field $spec 'agent'; $fallback = Get-Field $spec 'fallback'
    $exe = if ($fmAgent) { $fmAgent } else { $Agent }
    if ($fallback -and ($attempts -ge 1 -or -not (Test-CanRun $exe))) { $exe = $fallback }
    if (-not (Test-CanRun $exe)) { Set-Content $res 'unavailable'; "waiting: agent $exe not available (step $sid not started)"; return }
    if ($exe -eq 'operator') { Invoke-Operator $sid; return }

    if (-not (Test-Path $swt)) {
        git -C $RepoRoot worktree add -q -B $br $swt $startRev
        if ($LASTEXITCODE -ne 0) { Set-Content $res 'fail'; return }
        Set-Content (Join-Path $Work "base/$sid") $startRev
        $buf.Add("starting step $sid (new worktree)")
    } else { $buf.Add("resuming step $sid (worktree exists: previous run stopped)") }
    $sfile = Join-Path $swt $rel
    $tier = Get-Field $spec 'tier'; if (-not $tier) { $tier = 'standard' }
    if ($attempts -ge 1) { $tier = 'standard' }
    $model = ''; $effort = ''
    if ($exe -ne 'script') { $model = Get-Cfg "${exe}_model_$tier" ''; $effort = Get-Cfg "${exe}_effort_$tier" '' }
    $env:RALPH_STEP = $sid; $env:RALPH_PLAN = $Plan; $env:RALPH_MODEL = $model; $env:RALPH_EFFORT = $effort; $env:RALPH_TIER = $tier
    $env:RALPH_STEP_AGENT = $exe
    $buf.Add("step=$sid agent=$exe tier=$tier model=$(if ($model) { $model } else { 'cli-default' }) effort=$(if ($effort) { $effort } else { 'default' }) attempts=$attempts")

    $stamp = Get-Date -Format 'yyyyMMddTHHmmss'
    $out = Join-Path $Work "logs/$sid-$stamp.json"
    $headBefore = (git -C $swt rev-parse HEAD).Trim()
    $t0 = Get-Date
    if ($exe -eq 'script') {
        # ---- script step: a deterministic command. No model call. ----
        $runCmd = Get-Field $spec 'run'
        if ($runCmd) { $rc = Invoke-Shell $runCmd $swt $out $StepTimeoutMin }
        else { Set-Content "$out.err" 'script step has no run: command'; $rc = 2 }
        $secs = [int]((Get-Date) - $t0).TotalSeconds
        Write-ScriptLedger $sid $rc $secs $tier ($attempts + 1)
        $buf.Add("--- usage: step=$sid agent=script ---"); $buf.Add("time: ${secs}s  exit_code: $rc"); $buf.Add('cost: usd=0 (no model)')
    } else {
        $promptText = (Get-Content (Join-Path $Here 'lib/PROMPT.md') -Raw).Replace('{{PLAN}}', $Plan).Replace('{{STEP}}', $sid)
        Set-Content -Path (Join-Path $Work "logs/prompt-$sid.md") -Value $promptText
        $override = Get-Override $exe
        if ($override) { $rc = Invoke-Timed 'pwsh' @('-NoProfile', '-Command', $override) $swt $promptText $out "$out.err" $StepTimeoutMin }
        else {
            $spec2 = Get-AgentSpec $exe $model $effort $promptText
            $rc = Invoke-Timed $spec2.Exe $spec2.Args $swt $(if ($spec2.Stdin) { $promptText } else { '' }) $out "$out.err" $StepTimeoutMin
        }
        $secs = [int]((Get-Date) - $t0).TotalSeconds
        $ublock = & $Py -I $Usage --agent $exe --out $out --ledger $Ledger --rc $rc --seconds $secs --step $sid --tier $tier --model $model --effort $effort --route $exe --attempt ($attempts + 1) --head-before $headBefore --cwd $swt
        $buf.Add(($ublock -join "`n"))
        if ($ublock -match '(?m)^outcome: limit') { Set-Content $res 'limit'; $buf -join "`n"; return }
    }

    # ---- verify: the driver checks the scope and runs the gate itself. It does not trust the agent. ----
    $changed = @(Invoke-Pick same $spec $sfile)
    if ($LASTEXITCODE -ne 0) {
        Register-Failure $sid $attempts $buf "$sid changed its own gate or scope (keys: $(($changed | Where-Object { $_ }) -join ', '))"
        $buf -join "`n"; return
    }
    $gate = Get-Field $spec 'gate'
    $gateOk = $false
    if ($gate) { $gateOk = ((Invoke-Shell $gate $swt (Join-Path $Work "logs/gate-$sid.out") $GateTimeoutMin) -eq 0) }
    & $Py -I $Usage --record-gate $(if ($gateOk) { 'pass' } else { 'fail' }) --ledger $Ledger --step $sid --route $exe --attempt ($attempts + 1) *> $null
    if (-not $gateOk) {
        Register-Failure $sid $attempts $buf "$sid gate FAILED (rc=$rc, attempt $($attempts + 1)/$MaxAttempts; see logs/gate-$sid.out)"
        $buf -join "`n"; return
    }
    $scopeErr = Join-Path $Work "logs/scope-$sid.out"
    $allowed = @(& $Py -I $Pick scope $swt $startRev $spec $rel 2> $scopeErr)
    if ($LASTEXITCODE -ne 0) {
        $bad = @(Get-Content $scopeErr | ForEach-Object { $_ -replace '^outside touches: ', '' }) -join ' '
        Register-Failure $sid $attempts $buf "$sid changed files outside touches: $bad"
        $buf -join "`n"; return
    }
    Invoke-Pick set $sfile status done
    Invoke-Pick set $sfile claimed_by "$exe $(if ($model) { $model } else { 'cli-default' })"
    Invoke-Pick set $sfile claimed_at (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    Invoke-Pick set $sfile evidence "gate passed $((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')) (driver-verified)"
    $env:GIT_LITERAL_PATHSPECS = '1'
    git -C $swt add -A -- $rel @($allowed | Where-Object { $_ })
    Remove-Item Env:GIT_LITERAL_PATHSPECS
    # Secret guard: the commits the agent made and the staged files. A finding fails the attempt. Nothing is merged.
    $guardOut = Join-Path $Work "logs/secret-guard-$sid.out"
    $guard = Join-Path $Here 'scripts/secret_guard.py'
    $guardCopy = Join-Path $Work "spec/guard-$sid.py"
    $guardText = & git -C $RepoRoot show "${startRev}:scripts/secret_guard.py" 2>$null
    if ($LASTEXITCODE -eq 0) { Set-Content -Path $guardCopy -Value $guardText; $guard = $guardCopy }
    $env:SECRET_GUARD = Join-Path $Here 'scripts/secret_guard.py'
    & $Py -I $guard --root $swt --staged *> $guardOut
    $guardRc = $LASTEXITCODE
    if ($guardRc -eq 0) { & $Py -I $guard --root $swt --range "$startRev..HEAD" *>> $guardOut; $guardRc = $LASTEXITCODE }
    if ($guardRc -ne 0) {
        git -C $swt reset -q --hard $startRev; git -C $swt clean -qfd
        Register-Failure $sid $attempts $buf "$sid secret guard FAILED (see logs/secret-guard-$sid.out)"
        $buf -join "`n"; return
    }
    git -C $swt commit -q -m "plan($Plan): $sid done"
    if (Merge-Step $sid $br) {
        Remove-StepWorktree $sid
        Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $Work "attempts/$sid")
        Set-Content $res 'done'; $buf.Add("result: $sid done (gate passed, merged into $Branch)")
    } else {
        Set-Content (Join-Path $Work "attempts/$sid") ($attempts + 1); Set-Content $res 'fail'
        $buf.Add("result: $sid MERGE CONFLICT (see logs/merge.err); worktree kept")
    }
    $buf -join "`n"
}

if ($Worker) { Invoke-Step $Worker; exit 0 }

# ---- single instance: the lock handle is not inherited by child processes ----
$LockHandle = Lock-File (Join-Path $Work '.lock') 0
if (-not $LockHandle) { Write-Error "ralph-looper: another loop runs for $RepoName/$Plan (lock held)."; exit 3 }

Say "start: repo=$RepoName plan=$Plan agent=$Agent jobs=$Jobs work=$Work"
$iter = 0; $stall = 0; $result = 0
$skip = @(); $waitingOps = @()   # steps not to start again in this run: operator steps that wait, agents not available
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
        if ($d.Name -in $skip) { continue }
        $active += $d.Name
    }
    $active = @($active | Select-Object -First $Jobs)
    $batch = @($active)
    if ($batch.Count -lt $Jobs) {
        foreach ($line in @(Invoke-Pick ready $PlanDir --max $Jobs --active ($active -join ',') --skip ($skip -join ','))) {
            if ($line) { $batch += ($line | ConvertFrom-Json).id }
        }
    }
    if ($batch.Count -eq 0) {
        $summary = Invoke-Pick summary $PlanDir; $code = $LASTEXITCODE
        Say "no step to run: $summary"
        if ($code -eq 0) { Say 'ALL STEPS DONE'; $result = 0 }
        elseif ($waitingOps.Count -gt 0 -or $code -eq 12) { Say "WAITING FOR OPERATOR: $($waitingOps -join ' ') (do the action, then run again)"; $result = 12 }
        else { Say 'BLOCKED or waiting'; $result = 11 }
        break
    }

    $iter++
    Say "batch ${iter}: $($batch -join ' ')"
    $procs = @{}
    foreach ($sid in $batch) {
        $logf = Join-Path $Work "logs/worker-$sid.out"
        Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $Work "results/$sid")
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
        if ($r -eq 'wait') { $skip += $sid; $waitingOps += $sid }
        if ($r -eq 'unavailable') { $skip += $sid }
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
