# Design System — Phase 2

## Scope
Phase 2 defines the shared visual language and reusable primitives used by future feature screens.
This document is implementation-facing and maps directly to `DesignSystem/**`.

## Token Model

### Variables
Variables are scalar values reused directly in layout or geometry.

- Spacing: `AppSpacing` (`0, 4, 8, 12, 16, 24, 32, 40, 48, 64`)
- Radius: `AppRadius` (`0, 8, 12, 16, 20, 24`)
- Sizing: `AppSizing` for reusable dimensions (ring sizes, skeleton blocks, chart/card minimum heights)
- Stroke widths: `AppStrokeWidth` (`hairline`, `regular`)

### Styles
Styles combine one or more variables with semantic intent.

- Typography styles: `AppTypography` (`Display`, `Heading`, `Body`, `Button`, `Label`)
- Shadow styles: `AppShadows` (`card`, `dropdown`, `modal`)
- Elevation styles: `AppElevation` (surface + shadow mapping)
- Chart style rules: `AppChartStyle` (grid, axes, labels, series, interaction)

### Why this distinction matters
- Variables answer: "which raw measurement/value?"
- Styles answer: "which semantic visual role?"
- Components should consume styles first, then variables only when a style layer is not appropriate.

## Design Tokens

### Colors
Defined in `AppColors` with dynamic light/dark mappings.

- Background: `primary`, `elevated`
- Surface: `card`, `cardMuted`
- Text: `primary`, `secondary`, `inverse`
- Stroke: `subtle`, `strong`
- Accent: `blue`, `green`, `orange`, `red`, `purple`

### Typography
Defined in `AppTypography`.

- Display: `displayLarge`, `displayMedium`
- Heading: `headingH1`, `headingH2`, `headingH3`
- Body: `bodyLarge`, `bodyRegular`, `bodySmall`
- Button: `buttonMedium`
- Label: `labelSmall`

### Spacing and Radius
- Spacing scale: 0, 4, 8, 12, 16, 24, 32, 40, 48, 64
- Radius scale: 0, 8, 12, 16, 20, 24

### Shadows and Elevation
- Shadow/Card: used for standard cards
- Shadow/Dropdown: used for muted/dropdown surfaces
- Shadow/Modal: used for floating/modal surfaces
- Elevation maps each surface role to a shadow + surface color pair.

## Layout Rules

### Card Density
- Standard card internal padding: `AppSpacing.x16`
- Minimum card height: `AppSizing.cardMinHeight`
- Card radius: `AppRadius.large`
- Border width: `AppStrokeWidth.hairline`

### Section Spacing
- Section-to-section spacing in vertical stacks: `AppSpacing.x32`
- Card-to-card spacing in section groups: `AppSpacing.x16`
- Tight element spacing within cards: `AppSpacing.x8` or `AppSpacing.x12`

## Home Language

### Readiness Hero
- Home keeps a premium/editorial direction anchored in Figma, with the hero as the dominant surface.
- `Readiness` uses semantic theming by label, not a continuous score gradient:
  - `Ready` -> premium green
  - `Moderate` -> premium amber
  - `Recover` -> premium coral/red
  - `missing` -> neutral dark treatment without positive signaling
- Hero hierarchy is stable:
  - score first
  - label second
  - confidence and trust states as secondary support only

### Supporting Home Blocks
- Supporting blocks such as `Core Metrics` should stay in the same Home language without copying the hero treatment.
- Prefer shared primitives first:
  - `DSSectionHeader` for section hierarchy
  - `DSMetricSnapshotCard` for compact supporting metric groups
  - `DSCard` for supporting surfaces that do not need grouped metric tiles
  - `DSMetricPill` only for secondary trust/history signals
- Avoid introducing ad-hoc gradients, custom surface recipes, or bespoke shadows when an existing design-system primitive already matches the role.

## Navigation Patterns

### iPhone
- Primary navigation pattern: tab bar with top-level sections.
- In Phase 2, this is documented only; no feature tab screens are implemented.

### Mac
- Primary navigation pattern: split view with persistent sidebar + detail panel.
- In Phase 2, this is documented only; no feature split-view screen is implemented.

## Component Library
Implemented primitives:
- `DSCard`
- `DSMetricSnapshotCard`
- `DSMetricPill`
- `DSSectionHeader`
- `DSSegmentedControl`
- `DSChartCard`
- `DSRing`
- `DSEmptyState`
- `DSLoadingState`

All components must use Design System tokens/styles and avoid ad-hoc visual constants in component files.

## Chart Styling Rules v0.1
Defined in `DesignSystem/Charts/AppChartStyle.swift`.

### Grid
- Line color: `AppChartStyle.Grid.lineColor`
- Line width: `AppChartStyle.Grid.lineWidth`
- Default rows: `AppChartStyle.Grid.rowCount`

### Axes and Labels
- Axis label typography: `AppChartStyle.Axis.labelStyle`
- Axis label color: `AppChartStyle.Axis.labelColor`
- Value labels: `AppChartStyle.Label.valueStyle` + `valueColor`

### Series
- Primary/secondary/tertiary series colors from semantic accent tokens.
- Filled overlays use `fillOpacity` token for consistency.

### Interaction
- Highlight color: `AppChartStyle.Interaction.highlightColor`
- Highlight thickness: `highlightLineWidth`
- Marker corner radius: `markerRadius`

## Gallery and Demo App
- Gallery root: `GalleryView`
- Executable app: `DesignSystemDemo` (single multiplatform target)
- Supported validation platforms in Phase 2:
  - iOS (generic + iPhone simulator)
  - macOS (generic)
