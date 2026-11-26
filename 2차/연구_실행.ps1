$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:OMP_NUM_THREADS = '2'
$env:OPENBLAS_NUM_THREADS = '2'
$pythonPath = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { $pythonPath = Join-Path $PSScriptRoot '../1차/.venv/Scripts/python.exe' }
if (-not (Test-Path -LiteralPath $pythonPath)) { throw '사용 안내에 따라 Python 환경을 먼저 준비해 주세요.' }
& $pythonPath -B -X utf8 -m rentlab @args
if ($LASTEXITCODE -ne 0) { throw '연구 처리가 실패했습니다. 원본과 기존 결과는 보존합니다.' }
