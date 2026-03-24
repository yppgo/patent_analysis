param(
    [string[]]$Phases = @("external_q45", "main_q45"),
    [int]$PauseSeconds = 5
)

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $projectRoot

function Run-Phase {
    param(
        [string]$Name,
        [string[]]$CommandArgs
    )

    Write-Host ("=" * 80)
    Write-Host ("[{0}] START {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Name)
    Write-Host ("py " + ($CommandArgs -join " "))
    & py @CommandArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Phase failed: $Name (exit=$LASTEXITCODE)"
    }
    Write-Host ("[{0}] DONE  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Name)
}

foreach ($phase in $Phases) {
    switch ($phase) {
        "external_q45" {
            Run-Phase -Name $phase -CommandArgs @(
                "-3",
                "scripts/jos/run_repeated_batches.py",
                "--dataset", "main_data_security",
                "--modes", "G_react_single_agent,H_execution_feedback",
                "--question-indexes", "4,5",
                "--repeats", "5",
                "--output-dir", "outputs/repeated_experiments_external_main",
                "--pause-seconds", "$PauseSeconds"
            )
        }
        "main_q45" {
            Run-Phase -Name $phase -CommandArgs @(
                "-3",
                "scripts/jos/run_repeated_batches.py",
                "--dataset", "main_data_security",
                "--modes", "D_baseline0,A_template,B_data_aware,C_iterative,E_ablate_data,F_ablate_kg",
                "--question-indexes", "4,5",
                "--repeats", "5",
                "--output-dir", "outputs/repeated_experiments_full",
                "--pause-seconds", "$PauseSeconds"
            )
        }
        "subdomain_stability" {
            Run-Phase -Name $phase -CommandArgs @(
                "-3",
                "scripts/jos/run_repeated_batches.py",
                "--dataset", "transfer_iot_auto",
                "--modes", "D_baseline0,B_data_aware,C_iterative,H_execution_feedback",
                "--question-indexes", "1,2,3,4,5",
                "--repeats", "3",
                "--output-dir", "outputs/repeated_experiments_transfer_iot_auto",
                "--pause-seconds", "$PauseSeconds"
            )
        }
        default {
            throw "Unknown phase: $phase"
        }
    }
}

Write-Host ("=" * 80)
Write-Host ("[{0}] ALL REQUESTED PHASES COMPLETED" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
