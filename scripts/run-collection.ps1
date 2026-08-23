param([string]$ProjectDir = "D:\projects\sufeelec")
$mutex = New-Object System.Threading.Mutex($false, "Global\SUFElecCollection")
if (-not $mutex.WaitOne(0)) { Write-Host "已有采集任务运行，安全跳过本次执行"; exit 0 }
try {
  Set-Location $ProjectDir
  $python = (Get-Command python).Source
  if (-not $python) { throw "未找到 python" }
  & $python -m collector collect --slot now
  if ($LASTEXITCODE -ne 0) { throw "采集失败，退出码 $LASTEXITCODE" }
  & $python -m collector export
  if ($LASTEXITCODE -ne 0) { throw "导出失败，退出码 $LASTEXITCODE" }
  & $python scripts\validate_public.py
  if ($LASTEXITCODE -ne 0) { throw "公开数据校验失败，退出码 $LASTEXITCODE" }
  Write-Host "SUFElec collection/export/validation succeeded"
  exit 0
} catch {
  Write-Error $_
  exit 1
} finally { $mutex.ReleaseMutex(); $mutex.Dispose() }
