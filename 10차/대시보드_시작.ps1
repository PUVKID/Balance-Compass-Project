$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonPath = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { $pythonPath = Join-Path $PSScriptRoot '../1차/.venv/Scripts/python.exe' }
if (-not (Test-Path -LiteralPath $pythonPath)) { throw '사용 안내에 따라 Python 환경을 먼저 준비해 주세요.' }
& $pythonPath -B -X utf8 "$PSScriptRoot/run_dashboard.py" @args
if ($LASTEXITCODE -ne 0) { throw '대시보드 실행에 실패했습니다. 입력 경로와 오류를 확인해 주세요.' }
