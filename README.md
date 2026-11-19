# Biwoom Webtoon Studio

Local-first experimental tooling for a webtoon production workflow. The repository contains **synthetic fixtures and safety checks**, not a production-ready automatic studio. Explicitly approved artwork is kept separately under `published/illustrations/`; private pilot materials remain excluded. Source, rights, artistic and doctrinal decisions remain human responsibilities.

## Run locally
Python 3.10+; verified on Python 3.13 with Pillow 12.2. Raster/composition tests require the optional `raster` dependency declared in pyproject.toml. No command installs packages or calls an external service. The Korean demonstration additionally requires the existing macOS Apple SD Gothic Neo font. It is not distributed here; unavailable font/glyphs fail closed.

From the repository root, without installing this package:
```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m biwoom_studio --help
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m biwoom_studio pipeline-demo
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m biwoom_studio korean-demo
```

Other synthetic commands: `demo`, `raster-demo`, `p4-demo`, `p3-start`, and `p3-resume <run_name>`. Each creates a fresh ignored output directory and preserves earlier runs. Tests also retain their output, so disk usage grows. `validate ST-NNN`, `preflight ST-NNN`, `status ST-NNN`, and `p2-demo ST-NNN` require a separately supplied local story bundle; private stories are intentionally absent from the public repository. P1 currently validates the EP01 ten-cut draft contract, not arbitrary episodes. Files ending in `.yaml` use JSON syntax (a YAML subset); a general YAML parser is not included.

## Implemented and tested
- Project confinement checks; safe relative paths; missing panels/source roles/approval guards.
- Draft source/storyboard validation and fixed offline SVG candidate generation with immutable revisions.
- Bounded synthetic QA/revision loop with paused, complete and stalled states; resume does not duplicate completed work.
- PNG/JPEG decoding, format/dimensions/hash verification and distinct manual review records.
- Exact image+dialogue binding, immutable synthetic offer snapshots, specific linked consent checks.
- SQLite atomic synthetic intent/receipt storage, restart replay, concurrent-process duplicate prevention, collision and interruption tests.
- Fixed-fixture vertical PNG/HTML preview, Korean measured eojeol wrapping, punctuation/overlap/clipping checks, private test ZIP manifest/hash/CRC verification.

`pipeline-demo` links synthetic offer → technical QA → fixed-fixture compatibility receipt → vertical composition → test-only ZIP. Korean lettering remains a separate demonstration. Real transport and final export gates remain blocked. API call count/cost zero describes these offline tests only, not actual production expense or human labor. No artistic quality score is inferred from unit tests.

## Important boundaries
Automatic fixture consent, supplied JSON booleans, matching hashes and unsigned user names **cannot authorize real production**. ProductionTransport and real approval import remain unavailable. G3.5 is exact current image+dialogue acceptance; G4 is a separate final episode review. Generic instructions to continue work are not either approval. Preview/test-only output is never a final release.

The optional local project `archive_reference` object has `path` (Studio-relative) and `sha256`. Preflight reports missing configuration or failed verification without guessing a private artifact path. It never imports approvals or rewrites story state.

Korean wrapping preserves space-delimited words and explicit newlines; an oversized word requires an explicit edit or wider balloon. Full typography, automatic visual/doctrinal review, live generation, production approval ingress, actual supervision integration and release orchestration are unimplemented. The SQLite receipt store is tested separately from later file outputs; the entire composition/export sequence is not one crash-atomic transaction. Path validation is an application check, not OS sandboxing.

Private story drafts, unapproved art, archives, local logs, credentials and workstation histories are not public inputs. `output/` is ignored; Git push/publication needs separate owner authorization. See `docs/workflow.md` and the versioned design for intended gates and future scope.
