#!/usr/bin/env bash
# Compile the generator's ATAS output for every recipe against BSV's API-reference-derived stubs.
# Needs node and the .NET 8 SDK (dotnet). Not a real ATAS build. Usage: scripts/site/check_atas_stubs.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DOTNET="${DOTNET:-dotnet}"
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
mkdir -p "$T/gen"
n=0
for r in "$ROOT"/trader-toolkit/recipes/*.json; do
  code="$(node "$ROOT/trader-toolkit/generator/render.mjs" "$r" --target atas)"
  if printf '%s\n' "$code" | grep -qE 'OpenOrder|SubmitOrder|PlaceOrder|ChartStrategy|TradingManager'; then echo "order API used in $r"; exit 1; fi
  cls="$(printf '%s\n' "$code" | sed -n 's/^    public class \([A-Za-z0-9_]*\) : Indicator$/\1/p')"
  printf '%s\n' "$code" > "$T/gen/$cls.cs"; n=$((n+1))
done
cp "$ROOT/scripts/site/atas_stubs/AtasStubs.cs" "$T/"
cat > "$T/check.csproj" <<'P'
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <ImplicitUsings>disable</ImplicitUsings>
    <EnableDefaultCompileItems>true</EnableDefaultCompileItems>
  </PropertyGroup>
</Project>
P
"$DOTNET" build "$T/check.csproj" -nologo -v q -o "$T/out" > "$T/build.log" 2>&1 || { cat "$T/build.log"; exit 1; }
c=$(grep -c '^    public class Bsv' "$T"/gen/*.cs | awk -F: '{s+=$2} END {print s}')
echo "atas stub compile: recipes=$n classes=$c ok"
[ "$n" -eq "$c" ]
