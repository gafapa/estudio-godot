# Contracts

The Architect writes/updates contracts; the Producer approves/integrates them. Existing contract changes require an ADR, updated fixtures and all affected consumers identified.

Each boundary has docs/contracts/ documentation, a src/game/contracts/ type where useful, deterministic tests/fixtures/ and tests validating them. Integrate the contract before dependent implementation tickets.

Telemetry catalog: telemetry.md, implemented by M0-02.
