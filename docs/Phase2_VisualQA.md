# Phase 2 Visual QA Evidence

Date: 2026-03-04 (America/New_York)
Scope: `DesignSystem/**`, `DesignSystemDemo/**`, `docs/**`

## 1) Build Validation

Commands executed:

```bash
xcodebuild -project DesignSystemDemo/DesignSystemDemo.xcodeproj -scheme DesignSystemDemo -destination 'generic/platform=iOS' build
xcodebuild -project DesignSystemDemo/DesignSystemDemo.xcodeproj -scheme DesignSystemDemo -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build
xcodebuild -project DesignSystemDemo/DesignSystemDemo.xcodeproj -scheme DesignSystemDemo -destination 'generic/platform=macOS' build
```

Result:
- iOS generic: PASS
- iOS simulator: PASS
- macOS generic: PASS

Note:
- `iPhone 16 Pro` is not available in this runtime list.
- Equivalent simulator used: `iPhone 17 Pro` (iOS 26.3).

## 2) iPhone Visual QA (Light/Dark + Dynamic Type)

Device:
- iPhone 17 Pro simulator (`ED4EFF46-EBC3-4141-8EA7-DA2A7FC8D902`)

QA matrix:
- Light mode + Dynamic Type default (`large`): PASS
- Dark mode + Dynamic Type default (`large`): PASS
- Light mode + Dynamic Type large (`extra-extra-large`): PASS
- Dark mode + Dynamic Type large (`extra-extra-large`): PASS

Evidence files:
- `docs/qa/phase2/iphone-light-dt-default.png`
- `docs/qa/phase2/iphone-dark-dt-default.png`
- `docs/qa/phase2/iphone-light-dt-large.png`
- `docs/qa/phase2/iphone-dark-dt-large.png`

## 3) macOS Visual QA (Light/Dark + Small/Large Window)

Method:
- Launch app with `-ApplePersistenceIgnoreState YES`.
- Set window frame defaults per case.
- Capture fullscreen evidence and persist per-case window bounds via CoreGraphics.

QA matrix:
- Light mode + Small window (`860x620`): PASS
- Light mode + Large window (`1280x860`): PASS
- Dark mode + Small window (`860x620`): PASS
- Dark mode + Large window (`1280x860`): PASS

Evidence files:
- `docs/qa/phase2/macos-light-window-small.png`
- `docs/qa/phase2/macos-light-window-large.png`
- `docs/qa/phase2/macos-dark-window-small.png`
- `docs/qa/phase2/macos-dark-window-large.png`
- `docs/qa/phase2/macos-window-matrix.log`

Window-matrix log contains the exact detected window bounds for each case.

## 4) Scope Validation

Validated sections in `GalleryView`:
- Tokens: colors, typography, spacing, radius, shadows/elevation, chart rules
- Components: `DSCard`, `DSMetricPill`, `DSSectionHeader`, `DSSegmentedControl`, `DSChartCard`, `DSRing`, `DSEmptyState`, `DSLoadingState`
- Compositions (sandbox only): metric/workout/calendar examples

Constraint respected:
- No feature screens (Home, Trends, Workouts, Calendar, Body) were added.

## 5) Summary

Phase 2 visual QA is complete for required scenarios:
- iPhone light/dark + dynamic type basic
- macOS light/dark + window small/large

All required build targets pass and evidence artifacts are stored under `docs/qa/phase2/`.
