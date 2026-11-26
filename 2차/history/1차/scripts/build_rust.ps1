$ErrorActionPreference = 'Stop'
$env:CARGO_HOME = 'E:/2026/개발 도구 및 캐시/Rust Astryx/cargo'
$env:RUSTUP_HOME = 'E:/2026/개발 도구 및 캐시/Rust Astryx/rustup'
& "$env:CARGO_HOME/bin/cargo.exe" build --release --manifest-path "$PSScriptRoot/../rust_money/Cargo.toml"
if ($LASTEXITCODE -ne 0) { throw 'Rust 빌드 실패. 기존 실행 파일로 대체하지 않습니다.' }
