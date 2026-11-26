$ErrorActionPreference = 'Stop'
# 설치된 Visual Studio 환경을 현재 빌드 프로세스에만 적용한다.
$vswhere = 'C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe'
if (-not (Get-Command link.exe -ErrorAction SilentlyContinue)) {
    if (-not (Test-Path -LiteralPath $vswhere)) { throw 'Visual Studio C++ Build Tools가 필요합니다.' }
    $installPath = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if (-not $installPath) { throw '설치된 Visual Studio C++ 빌드 도구를 찾지 못했습니다.' }
    $devCmd = Join-Path $installPath 'Common7/Tools/VsDevCmd.bat'
    $buildEnvironment = & $env:ComSpec /d /c "`"$devCmd`" -arch=x64 -host_arch=x64 >nul && set"
    if ($LASTEXITCODE -ne 0) { throw 'Visual Studio 빌드 환경 로딩 실패' }
    foreach ($line in $buildEnvironment) {
        if ($line -match '^([^=]+)=(.*)$') { [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process') }
    }
}
$env:CARGO_HOME = 'E:/2026/개발 도구 및 캐시/Rust Astryx/cargo'
$env:RUSTUP_HOME = 'E:/2026/개발 도구 및 캐시/Rust Astryx/rustup'
# E에 보존된 SDK 라이브러리의 실제 경로를 사용한다. 전역 설정은 바꾸지 않는다.
$sdkLibraries = 'E:/2026/개발 도구 및 캐시/Rust Astryx/windows-sdk/x64/c'
if (Test-Path -LiteralPath "$sdkLibraries/um/x64/kernel32.Lib") {
    $env:LIB = "$sdkLibraries/um/x64;$sdkLibraries/ucrt/x64;$env:LIB"
}
& "$env:CARGO_HOME/bin/cargo.exe" build --release --manifest-path "$PSScriptRoot/../rust_money/Cargo.toml"
if ($LASTEXITCODE -ne 0) { throw 'Rust 빌드 실패. 기존 실행 파일로 대체하지 않습니다.' }
