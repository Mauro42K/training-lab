# Phase 4.4.1 — Source Precedence Calibration (Block 3)

## Status
- Date: 2026-03-11 (America/Mexico_City)
- Environment: staging database only
- Mode: read-only calibration
- Mutation: none

## Goal
- reduce noise from the duplicate audit
- isolate the source conflicts that actually matter
- prepare a human review sample to freeze source precedence for the next block

## Filter applied

Review set used in this block:
- `cluster_size = 2`
- `reasons = ["conflicting_source_bundle_id"]`
- no extra metric divergence reasons

This is the narrowest useful set for source precedence calibration because it excludes:
- clusters `> 2`
- distance/energy/hr conflicts
- cross-sport contamination

## Top source conflicts

Manual-review clusters from Block 2: `493`

Pure size-2 source-conflict clusters:
- `333`

Top pairs:
- `com.garmin.connect.mobile` vs `com.strava.stravaride`
  - clusters: `256`
  - `% of manual-review clusters`: `51.93%`
  - pure size-2 count: `256`
- `com.rungap.RunGap` vs `com.strava.stravaride`
  - clusters: `63`
  - `% of manual-review clusters`: `12.78%`
  - pure size-2 count: `63`
- `com.strava.stravaride` vs `com.zwift.Zwift`
  - clusters: `4`
  - `% of manual-review clusters`: `0.81%`
  - pure size-2 count: `4`
- `com.strava.stravaride` vs `com.zwift.ZwiftGame`
  - clusters: `3`
  - `% of manual-review clusters`: `0.61%`
  - pure size-2 count: `3`
- `com.WahooFitness.FisicaFitness` vs `com.strava.stravaride`
  - clusters: `2`
  - `% of manual-review clusters`: `0.41%`
  - pure size-2 count: `2`

Interpretation:
- Garmin vs Strava and RunGap vs Strava dominate the real decision surface
- together they account for `319 / 493` manual-review clusters (`64.71%`)
- the remaining pairs are materially smaller and can be reviewed after those two

## Human review sample prepared

Prepared review sample:
- `49` rows total
- `20` rows: Garmin vs Strava
- `20` rows: RunGap vs Strava
- `4` rows: Strava vs Zwift
- `3` rows: Strava vs ZwiftGame
- `2` rows: Wahoo vs Strava

Artifact:
- `docs/qa/phase4/artifacts/phase4_4_1_source_precedence_review_sample.csv`

Summary artifact:
- `docs/qa/phase4/artifacts/phase4_4_1_source_conflict_summary.json`

## Review sample columns

The sample CSV is side-by-side and intended for fast human winner review. It includes:
- `pair_rank`
- `source_pair`
- `cluster_id`
- `sport`
- `user_id`
- left/right:
  - `id`
  - `uuid`
  - `source_bundle_id`
  - `device_name`
  - `start`
  - `end`
  - `duration_sec`
  - `distance_m`
  - `energy_kcal`
  - `avg_hr_bpm`
  - `created_at`
  - `completeness_score`
- diff helpers:
  - `start_diff_sec`
  - `end_diff_sec`
  - `duration_diff_sec`
- `review_note`

This is enough to decide source precedence without opening the raw 530-cluster export first.

## Recommended next decision

Next gate should be:
1. review Garmin vs Strava sample
2. review RunGap vs Strava sample
3. freeze explicit source precedence rules for those pairs
4. then reevaluate how much of the 333 pure source-conflict clusters would move into auto-cleanup eligible

Current recommendation:
- do **not** revisit cleanup vs reload yet
- decide source precedence first
