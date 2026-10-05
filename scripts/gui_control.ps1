param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('probe','screenshot','move','click','scroll','type','keys','sequence')]
    [string]$Action,
    [int]$X = 0,
    [int]$Y = 0,
    [ValidateSet('left','right','middle')]
    [string]$Button = 'left',
    [ValidateRange(1,3)][int]$Count = 1,
    [int]$Delta = 0,
    [string]$Text = '',
    [string]$Keys = '',
    [string]$Path = '',
    [string]$SequenceJson = '',
    [long]$ExpectedHandle = 0,
    [int]$ExpectedProcessId = 0
)
$ErrorActionPreference='Stop'
if($Action -notin @('probe','screenshot') -and ($ExpectedHandle -le 0 -or $ExpectedProcessId -le 0)){
  [Console]::Error.WriteLine('Exact HWND and process lock required before input.'); exit 2
}
try {
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
if (-not ('GuiNative' -as [type])) {
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class GuiNative {
 [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X; public int Y; }
 [StructLayout(LayoutKind.Sequential)] public struct INPUT { public UInt32 type; public INPUTUNION U; }
 [StructLayout(LayoutKind.Explicit)] public struct INPUTUNION { [FieldOffset(0)] public KEYBDINPUT ki; [FieldOffset(0)] public MOUSEINPUT mi; }
 [StructLayout(LayoutKind.Sequential)] public struct KEYBDINPUT { public UInt16 wVk; public UInt16 wScan; public UInt32 dwFlags; public UInt32 time; public UIntPtr dwExtraInfo; }
 [StructLayout(LayoutKind.Sequential)] public struct MOUSEINPUT {public Int32 dx,dy;public UInt32 mouseData,dwFlags,time;public UIntPtr dwExtraInfo;}
 [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left,Top,Right,Bottom; }
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out RECT r);
 [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(POINT p);
 [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr h,uint f);
 public static long LockedHandle; public static uint LockedPid;
 public static void CheckLock(){uint p; GetWindowThreadProcessId(new IntPtr(LockedHandle),out p);if(LockedHandle==0 || p!=LockedPid || GetForegroundWindow().ToInt64()!=LockedHandle)throw new InvalidOperationException("Window lock lost");}
 public const UInt32 INPUT_KEYBOARD=1, KEYEVENTF_KEYUP=0x0002, KEYEVENTF_UNICODE=0x0004;
 public const UInt32 LDOWN=0x0002, LUP=0x0004, RDOWN=0x0008, RUP=0x0010, MDOWN=0x0020, MUP=0x0040, WHEEL=0x0800;
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int X,int Y);
 [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT point);
 [DllImport("user32.dll")] public static extern void mouse_event(UInt32 f,UInt32 dx,UInt32 dy,Int32 data,UIntPtr e);
 [DllImport("user32.dll",SetLastError=true)] public static extern UInt32 SendInput(UInt32 n, INPUT[] p, Int32 cb);
 public static void SendUnicode(string text){ foreach(char c in text){ CheckLock(); INPUT d=new INPUT(); d.type=INPUT_KEYBOARD; d.U.ki.wScan=c; d.U.ki.dwFlags=KEYEVENTF_UNICODE; INPUT u=d; u.U.ki.dwFlags=KEYEVENTF_UNICODE|KEYEVENTF_KEYUP; var a=new INPUT[]{d,u}; if(SendInput((UInt32)a.Length,a,Marshal.SizeOf(typeof(INPUT)))!=a.Length) throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error()); }}
}
"@
}
[GuiNative]::LockedHandle=$ExpectedHandle
[GuiNative]::LockedPid=$ExpectedProcessId
function Assert-Point([int]$px,[int]$py){
 $r=New-Object GuiNative+RECT
 if(-not [GuiNative]::GetWindowRect([IntPtr]$ExpectedHandle,[ref]$r)){throw 'Window bounds unavailable.'}
 if($px -lt $r.Left -or $px -ge $r.Right -or $py -lt $r.Top -or $py -ge $r.Bottom){throw 'Point outside locked window.'}
 $pt=New-Object GuiNative+POINT; $pt.X=$px;$pt.Y=$py
 $hit=[GuiNative]::WindowFromPoint($pt)
 if([GuiNative]::GetAncestor($hit,2).ToInt64() -ne $ExpectedHandle){throw 'Point occluded by another window.'}
}
function State { $p=New-Object GuiNative+POINT; [void][GuiNative]::GetCursorPos([ref]$p); $v=[System.Windows.Forms.SystemInformation]::VirtualScreen; [ordered]@{Interactive=[Environment]::UserInteractive;CursorX=$p.X;CursorY=$p.Y;ScreenX=$v.X;ScreenY=$v.Y;Width=$v.Width;Height=$v.Height} }
function Shot([string]$Target){ if(!$Target){throw 'Path required.'}; $f=[IO.Path]::GetFullPath($Target); [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($f))|Out-Null; $v=[System.Windows.Forms.SystemInformation]::VirtualScreen; $b=New-Object Drawing.Bitmap $v.Width,$v.Height; $g=[Drawing.Graphics]::FromImage($b); try{$g.CopyFromScreen($v.Left,$v.Top,0,0,$b.Size);$b.Save($f,[Drawing.Imaging.ImageFormat]::Png)}finally{$g.Dispose();$b.Dispose()}; $f }
function Click([string]$b,[int]$n){ switch($b){left{$d=[GuiNative]::LDOWN;$u=[GuiNative]::LUP}right{$d=[GuiNative]::RDOWN;$u=[GuiNative]::RUP}middle{$d=[GuiNative]::MDOWN;$u=[GuiNative]::MUP}}; for($i=0;$i-lt$n;$i++){[GuiNative]::CheckLock();[GuiNative]::mouse_event($d,0,0,0,[UIntPtr]::Zero);Start-Sleep -Milliseconds 25;[GuiNative]::mouse_event($u,0,0,0,[UIntPtr]::Zero);Start-Sleep -Milliseconds 45} }
function DoOp($o){
 if([string]$o.action -ne 'screenshot'){[GuiNative]::CheckLock()}
 if([string]$o.action -in @('move','click')){Assert-Point ([int]$o.x) ([int]$o.y)}
 if([string]$o.action -eq 'scroll'){$pos=New-Object GuiNative+POINT;[void][GuiNative]::GetCursorPos([ref]$pos);Assert-Point $pos.X $pos.Y}
 if([string]$o.action -eq 'type' -and ([string]$o.text).Length -gt 16000){throw 'Text limit.'}
 if([string]$o.action -eq 'keys' -and ([string]$o.keys).Length -gt 200){throw 'Key sequence limit.'}
 switch([string]$o.action){
 'move'{ if(-not [GuiNative]::SetCursorPos([int]$o.x,[int]$o.y)){throw 'SetCursorPos failed.'} }
 'click'{
   if($null -ne $o.PSObject.Properties['x'] -and $null -ne $o.PSObject.Properties['y']){ [void][GuiNative]::SetCursorPos([int]$o.x,[int]$o.y); Start-Sleep -Milliseconds 40 }
   $btn='left'; if($null -ne $o.PSObject.Properties['button'] -and $o.button){ $btn=[string]$o.button }
   $cnt=1; if($null -ne $o.PSObject.Properties['count'] -and $o.count){ $cnt=[int]$o.count }
   if($cnt -lt 1 -or $cnt -gt 3 -or $btn -notin @('left','right','middle')){throw 'Invalid click.'}; [GuiNative]::CheckLock(); Click $btn $cnt
 }
 'scroll'{[GuiNative]::mouse_event([GuiNative]::WHEEL,0,0,[int]$o.delta,[UIntPtr]::Zero)}
 'type'{[GuiNative]::SendUnicode([string]$o.text)}
 'keys'{[Windows.Forms.SendKeys]::SendWait([string]$o.keys)}
 'screenshot'{ return Shot([string]$o.path) }
 default{throw "Unknown sequence action: $($o.action)"}
}; if([string]$o.action -ne 'screenshot'){[GuiNative]::CheckLock()}; return $null }
switch($Action){
 'probe'{ State | ConvertTo-Json -Compress }
 'screenshot'{ [ordered]@{Screenshot=(Shot $Path);State=(State)} | ConvertTo-Json -Depth 4 -Compress }
 'move'{ DoOp ([pscustomobject]@{action='move';x=$X;y=$Y}); State | ConvertTo-Json -Compress }
 'click'{ DoOp ([pscustomobject]@{action='click';x=$X;y=$Y;button=$Button;count=$Count}); State | ConvertTo-Json -Compress }
 'scroll'{ DoOp ([pscustomobject]@{action='scroll';delta=$Delta}); State | ConvertTo-Json -Compress }
 'type'{ DoOp ([pscustomobject]@{action='type';text=$Text}); [ordered]@{Action='type';Completed=$true;Handle=$ExpectedHandle}|ConvertTo-Json -Compress }
 'keys'{ DoOp ([pscustomobject]@{action='keys';keys=$Keys}); [ordered]@{Action='keys';Completed=$true;Handle=$ExpectedHandle}|ConvertTo-Json -Compress }
 'sequence'{ if(!$SequenceJson){throw 'SequenceJson required.'}; $ops=@($SequenceJson|ConvertFrom-Json); if($ops.Count -gt 20){throw 'Sequence limited to 20 operations.'}; $shots=@(); foreach($o in $ops){$r=DoOp $o;if($r){$shots+=$r}}; [ordered]@{Operations=$ops.Count;Screenshots=$shots;State=(State)} | ConvertTo-Json -Depth 6 -Compress }
}

} catch {
 [Console]::Error.WriteLine('GUI action refused or failed; verify the exact window lock, input bounds and interactive desktop. No input text echoed.'); exit 2
}

