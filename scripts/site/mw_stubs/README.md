# MotiveWave SDK stubs (BSV, compile check only)

Minimal stand-ins written by BSV from the public MotiveWave SDK javadoc signatures
(https://www.motivewave.com/sdk/javadoc/). They contain no SDK code and do nothing at runtime.
`scripts/site/check_motivewave_stubs.sh` compiles every generator `motivewave` output against them
to catch Java syntax/type errors. Passing this check is NOT a real SDK build and NOT a MotiveWave load test.
