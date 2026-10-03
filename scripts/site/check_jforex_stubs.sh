#!/usr/bin/env bash
# Compile the generator's JForex output for every recipe against BSV's javadoc-derived stubs.
# Needs node and javac (JDK 17+). Not a real JForex compile. Usage: scripts/site/check_jforex_stubs.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
JAVAC="${JAVAC:-javac}"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
mkdir -p "$T/gen" "$T/out"
n=0
for r in "$ROOT"/trader-toolkit/recipes/*.json; do
  code="$(node "$ROOT/trader-toolkit/generator/render.mjs" "$r" --target jforex)"
  if printf '%s\n' "$code" | grep -q 'getEngine\|submitOrder'; then echo "order API used in $r"; exit 1; fi
  cls="$(printf '%s\n' "$code" | sed -n 's/^public class \([A-Za-z0-9_]*\).*/\1/p')"
  printf '%s\n' "$code" > "$T/gen/$cls.java"; n=$((n+1))
done
"$JAVAC" -Xlint:all,-rawtypes,-serial -Werror -d "$T/out" $(find "$ROOT/scripts/site/jf_stubs/com" "$T/gen" -name '*.java')
c=$(find "$T/out" -maxdepth 1 -name 'Bsv*.class' ! -name '*$*' | wc -l)
echo "jforex stub compile: recipes=$n classes=$c ok"
[ "$n" -eq "$c" ]
