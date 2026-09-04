# Demo (3 minutes, mock mode)

1. Open dashboard — health READY (mock), 1 seeded verified run.
2. Repositories → New task with `/srv/sklab/repos/demo`.
3. Enter “Fix flaky auth timeout”, Plan → shows Hermes/free, AUTO gates.
4. Run → live logs stream; attempt 1 REJECT regression.
5. Retry evidence → attempt 2 ACCEPT 94/100.
6. Inspect patch diff, verification checks, history entry.
