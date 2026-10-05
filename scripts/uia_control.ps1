param(
  [ValidateSet('inspect','find','invoke','focus','set-value')][string]$Action='inspect',
  [Parameter(Mandatory=$true)][long]$Handle,
  [Parameter(Mandatory=$true)][int]$ExpectedProcessId,
  [string]$Name='', [string]$AutomationId='', [string]$ControlType='',
  [string]$Value='', [ValidateRange(1,200)][int]$MaxNodes=100
)
$ErrorActionPreference='Stop'
$script:truncated=$false
try {
  if($Handle -le 0 -or $ExpectedProcessId -le 0){throw 'Exact window lock required.'}
  Add-Type -AssemblyName UIAutomationClient
  Add-Type -AssemblyName UIAutomationTypes
  if(-not ('OperatorUiaNative' -as [type])){Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class OperatorUiaNative {
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
}
'@}
  function Assert-Lock {
    $owner=[uint32]0
    [void][OperatorUiaNative]::GetWindowThreadProcessId([IntPtr]$Handle,[ref]$owner)
    if($owner -ne $ExpectedProcessId){throw 'Window ownership changed.'}
    if([OperatorUiaNative]::GetForegroundWindow().ToInt64() -ne $Handle){throw 'Foreground lock lost.'}
  }
  Assert-Lock
  $root=[Windows.Automation.AutomationElement]::FromHandle([IntPtr]$Handle)
  $walker=[Windows.Automation.TreeWalker]::ControlViewWalker
  $queue=New-Object 'System.Collections.Generic.Queue[System.Windows.Automation.AutomationElement]'
  $queue.Enqueue($root)
  $rows=@();$matches=@();$visited=0
  while($queue.Count -gt 0 -and $visited -lt $MaxNodes){
    $el=$queue.Dequeue();$visited++;$c=$el.Current
    if($c.ProcessId -ne $ExpectedProcessId){continue}
    $type=$c.ControlType.ProgrammaticName.Replace('ControlType.','')
    # Password elements expose neither names nor values through this helper.
    if(-not $c.IsPassword){
      $rows+= [ordered]@{Name=$c.Name;AutomationId=$c.AutomationId;ControlType=$type;
        ProcessId=$c.ProcessId;Enabled=$c.IsEnabled;
        Bounds=@($c.BoundingRectangle.X,$c.BoundingRectangle.Y,$c.BoundingRectangle.Width,$c.BoundingRectangle.Height)}
      if(($Name -or $AutomationId -or $ControlType) -and (!$Name -or $c.Name -ceq $Name) -and (!$AutomationId -or $c.AutomationId -ceq $AutomationId) -and (!$ControlType -or $type -eq $ControlType)){$matches+=,$el}
    }
    $child=$walker.GetFirstChild($el)
    while($null -ne $child -and ($queue.Count+$visited) -lt $MaxNodes){$queue.Enqueue($child);$child=$walker.GetNextSibling($child)}
    if($null -ne $child){$script:truncated=$true}
  }
  $incomplete=($queue.Count -gt 0 -or $script:truncated)
  if($Action -eq 'inspect'){
    [ordered]@{Handle=$Handle;ProcessId=$ExpectedProcessId;Elements=$rows;Truncated=[bool]$incomplete}|ConvertTo-Json -Depth 6 -Compress
  } elseif($Action -eq 'find'){
    $found=@($rows|Where-Object {(!$Name -or $_.Name -ceq $Name) -and (!$AutomationId -or $_.AutomationId -ceq $AutomationId) -and (!$ControlType -or $_.ControlType -eq $ControlType)})
    [ordered]@{Matches=$found;Truncated=[bool]$incomplete}|ConvertTo-Json -Depth 6 -Compress
  } else {
    if($incomplete -or $matches.Count -ne 1){throw 'Selector must identify exactly one control in a complete bounded tree.'}
    $target=$matches[0];Assert-Lock
    if(-not $target.Current.IsEnabled -or $target.Current.IsPassword){throw 'Control unavailable.'}
    switch($Action){
      'focus'{$target.SetFocus()}
      'invoke'{$pattern=$null;if(-not $target.TryGetCurrentPattern([Windows.Automation.InvokePattern]::Pattern,[ref]$pattern)){throw 'Invoke unsupported.'};$pattern.Invoke()}
      'set-value'{if($Value.Length -gt 16000){throw 'Value limit.'};$pattern=$null;if(-not $target.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$pattern)){throw 'Value unsupported.'};if($pattern.Current.IsReadOnly){throw 'Read only.'};$pattern.SetValue($Value);if($pattern.Current.Value -cne $Value){throw 'Value verification failed.'}}
    }
    Assert-Lock
    [ordered]@{Action=$Action;Handle=$Handle;ProcessId=$ExpectedProcessId;Completed=$true;NeedsFinalAppVerification=($Action -eq 'invoke')}|ConvertTo-Json -Compress
  }
} catch {
  [Console]::Error.WriteLine('UIA operation refused or failed; verify window lock, unique selector and provider support. No input values echoed.')
  exit 2
}
