$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$log = Join-Path $root 'gemma_testing\gemma_baseline.log'

Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class GemmaPowerState {
    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint flags);
    public static void PreventSleep() { SetThreadExecutionState(0x80000001); }
    public static void Restore() { SetThreadExecutionState(0x80000000); }
}
'@

try {
    [GemmaPowerState]::PreventSleep()
    "Started: $(Get-Date -Format o)" | Tee-Object -FilePath $log
    & cmd.exe /c (Join-Path $root 'run_gemma_baseline.bat') 2>&1 | Tee-Object -FilePath $log -Append
    $exitCode = $LASTEXITCODE
}
finally {
    [GemmaPowerState]::Restore()
    "Finished: $(Get-Date -Format o)" | Tee-Object -FilePath $log -Append
}

exit $exitCode
