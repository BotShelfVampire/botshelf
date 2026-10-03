# JForex API stubs (BSV, compile check only)

Minimal stand-ins written by BSV from the public JForex API javadoc signatures
(https://www.dukascopy.com/client/javadoc3/, API 2.13.99). They contain no Dukascopy code and do nothing at runtime.
`scripts/site/check_jforex_stubs.sh` compiles every generator `jforex` output against them
to catch Java syntax/type errors. Passing this check is NOT a JForex platform compile and NOT a strategy run.
