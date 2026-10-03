#!/usr/bin/env bash
# Compile the generator's MotiveWave output for every recipe against BSV's javadoc-derived stubs.
# Needs node and javac (JDK 17+). Not a real SDK build. Usage: scripts/site/check_motivewave_stubs.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
JAVAC="${JAVAC:-javac}"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
mkdir -p "$T/gen/com/botshelfvampire/generated" "$T/out"
n=0
for r in "$ROOT"/trader-toolkit/recipes/*.json; do
  code="$(node "$ROOT/trader-toolkit/generator/render.mjs" "$r" --target motivewave)"
  cls="$(printf '%s\n' "$code" | sed -n 's/^public class \([A-Za-z0-9_]*\).*/\1/p')"
  printf '%s\n' "$code" > "$T/gen/com/botshelfvampire/generated/$cls.java"; n=$((n+1))
done
"$JAVAC" -Xlint:all,-rawtypes -Werror -d "$T/out" $(find "$ROOT/scripts/site/mw_stubs/com" "$T/gen" -name '*.java')
c=$(find "$T/out/com/botshelfvampire/generated" -name '*.class' ! -name '*$*' | wc -l)
echo "motivewave stub compile: recipes=$n classes=$c ok"
[ "$n" -eq "$c" ]
