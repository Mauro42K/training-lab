# Changelog

This project follows a simple SemVer-style changelog.

## v0.0.2 - 2026-03-05

- Phase 2 closed: Design System & Layout delivered and documented.
- Added `DesignSystemDemo` multiplatform runner for gallery validation on iOS + macOS.
- Finalized token system: `AppColors`, `AppTypography`, `AppSpacing`, `AppRadius`, `AppShadows`, `AppElevation`.
- Added chart styling source of truth (`AppChartStyle`) and chart container support.
- Component set closed for Phase 2: `DSCard`, `DSChartCard`, `DSRing`, `DSMetricPill`, `DSSectionHeader`, `DSSegmentedControl`, `DSEmptyState`, `DSLoadingState`.
- Visual QA matrix completed (light/dark + dynamic type basic + macOS window sizes) with evidence in `docs/Phase2_VisualQA.md` and `docs/qa/phase2/`.
- Implementation base reference: commit `3431927`; this release entry is the documentary closure.

## v0.0.1 - 2026-03-04

- Phase 1 documentation baseline completed: `docs/PRD.md`, `docs/DATA_SOURCES.md`, `docs/METRICS_CATALOG.md`, and `docs/GLOSARIO.md`.
- Versioning documentation added with this changelog and `metrics_model_version` set to `1`.

## v0.0.0 - 2026-03-04

- Initial bootstrap completed for Phase 0.
- Phase 0.1 patch closed with custom domain, TLS, baked deploy metadata, and GitHub Actions CI.
