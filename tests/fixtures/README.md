# Synthetic fixtures only

The fixed two-panel markers, dialogue and source-role ledger currently live as constants in `src/biwoom_studio/core.py`. Tests materialize fresh copies under `output/mock-runs/`. This folder documents that test-only fixture boundary; no real ST-001 story is created. External fixture loading and YAML schemas are deferred to P1.
