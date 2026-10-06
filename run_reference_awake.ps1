$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$log = Join-Path $root 'qwen_testing\reference_bf16.log'

Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class ReferencePowerState {
    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint flags);
    public static void PreventSleep() { SetThreadExecutionState(0x80000001); }
    public static void Restore() { SetThreadExecutionState(0x80000000); }
}
'@

try {
    [ReferencePowerState]::PreventSleep()
    "Started: $(Get-Date -Format o)" | Tee-Object -FilePath $log
    & cmd.exe /c (Join-Path $root 'evaluate_qwen_reference.bat') 2>&1 | Tee-Object -FilePath $log -Append
    $exitCode = $LASTEXITCODE
}
finally {
    [ReferencePowerState]::Restore()
    "Finished: $(Get-Date -Format o)" | Tee-Object -FilePath $log -Append
}

exit $exitCode
