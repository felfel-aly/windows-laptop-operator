param(
    [Parameter(Mandatory=$true)][ValidateSet('list','find','activate','active')][string]$Action,
    [string]$Title = '',
    [long]$Handle = 0
)
$ErrorActionPreference = 'Stop'
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
using System.Collections.Generic;
public static class WinCtl {
  public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc cb, IntPtr p);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder s, int nMaxCount);
  [DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
  public static List<object> List() {
    var result = new List<object>();
    EnumWindows((h,p)=>{
      if(!IsWindowVisible(h)) return true;
      int len=GetWindowTextLength(h); if(len<=0) return true;
      var sb=new StringBuilder(len+1); GetWindowText(h,sb,sb.Capacity);
      uint pid; GetWindowThreadProcessId(h,out pid);
      result.Add(new {Handle=h.ToInt64(), Title=sb.ToString(), ProcessId=pid}); return true;
    }, IntPtr.Zero);
    return result;
  }
}
"@
$windows = @([WinCtl]::List())
switch ($Action) {
  'list' { $windows | ConvertTo-Json -Compress }
  'find' { @($windows | Where-Object { $_.Title -like "*$Title*" }) | ConvertTo-Json -Compress }
  'active' {
    $h=[WinCtl]::GetForegroundWindow().ToInt64()
    @($windows | Where-Object { $_.Handle -eq $h } | Select-Object -First 1) | ConvertTo-Json -Compress
  }
  'activate' {
    $target=$null
    if ($Handle -ne 0) { $target=$windows | Where-Object { $_.Handle -eq $Handle } | Select-Object -First 1 }
    elseif ($Title) { $candidates=@($windows | Where-Object { $_.Title -like "*$Title*" }); if($candidates.Count -ne 1){throw "Window title must be unique; use an exact handle."}; $target=$candidates[0] }
    if ($null -eq $target) { throw 'Target window not found.' }
    [void][WinCtl]::ShowWindowAsync([IntPtr]$target.Handle,9)
    Start-Sleep -Milliseconds 80
    if(-not [WinCtl]::SetForegroundWindow([IntPtr]$target.Handle)) { throw 'Failed to activate target window.' }
    Start-Sleep -Milliseconds 80
    $active=[WinCtl]::GetForegroundWindow().ToInt64()
    if($active -ne $target.Handle) { throw 'Target window did not become active.' }
    $target | ConvertTo-Json -Compress
  }
}
