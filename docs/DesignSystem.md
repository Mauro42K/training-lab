# Design System

## Scope
This document defines the shared visual language, reusable primitives, and implementation rules used by Training Lab screens.
It is implementation-facing and maps directly to `DesignSystem/**`.

The Design System is the source of truth for:
- tokens
- semantic styles
- reusable UI primitives
- Home composition rules
- chart language
- gallery validation patterns

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
- Semantic readiness accents already approved for Home:
  - `green` for `Ready`
  - `amber/orange` for `Moderate`
  - `coral/red` for `Recover`
  - neutral dark treatment for `missing`

### Typography
Defined in `AppTypography`.

- Display: `displayLarge`, `displayMedium`
- Heading: `headingH1`, `headingH2`, `headingH3`
- Body: `bodyLarge`, `bodyRegular`, `bodySmall`
- Button: `buttonMedium`
- Label: `labelSmall`

### Spacing and Radius
- Spacing scale: `0, 4, 8, 12, 16, 24, 32, 40, 48, 64`
- Radius scale: `0, 8, 12, 16, 20, 24`

### Shadows and Elevation
- Flat surfaces are the default for integrated Home blocks that should read as part of the canvas rather than as floating cards.
- In flat Home panels, internal metric and explainability clusters should prefer embedded content, subtle separators, and reduced inner chrome over nested card surfaces.
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

### General Home Hierarchy
Home follows a premium/editorial hierarchy.
The order of visual importance is:
1. `Readiness Hero`
2. `Drivers / Explainability`
3. `Core Metrics`
4. `Load Trend`
5. `Trend Card`

Each block must preserve its semantic role and must not visually impersonate another block.

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
- Hero-specific rule:
  - the hero owns the atmospheric treatment
  - supporting blocks must not copy the hero surface treatment

### Drivers / Explainability
- `Drivers` exist to explain **why** `Readiness` moved.
- The visible v1 scope is intentionally limited to:
  - primary drivers: `Sleep`, `HRV`, `RHR`
  - secondary context: `Exertion`
- `Movement` and `secondary strength context` are not part of the visible v1 explainability surface.
- Drivers must preserve semantic hierarchy:
  - primary drivers carry more visual weight
  - secondary context is quieter and clearly subordinate
- Explainability states:
  - `measured` is the default and should feel trustworthy but not loud
  - `estimated`, `proxy`, and `missing` use lightweight status treatment
  - non-measured states must never read as if they were fully measured signals
- Copy rule:
  - short reasons must stay short, readable, and non-technical
  - avoid dense paragraphs or laboratory-style phrasing

### Core Metrics
- `Core Metrics` are a compact Home context block, not a mini dashboard.
- The visible metrics are:
  - `7-Day Load`
  - `Fitness`
  - `Fatigue`
- `Core Metrics` must feel clearly subordinate to the hero and more compact than the trend card.
- The block should feel information-rich but visually calm.
- Trust/history treatment must stay secondary and never compete with the values.

### Trend / Load Blocks
- `Load Trend` and `Load vs Capacity` belong to the load domain, not the readiness domain.
- They must remain visually and semantically separate from Hero and Drivers.
- Do not reuse trend grammar to explain readiness.

### Supporting Home Blocks
- Supporting blocks should stay in the same Home language without copying the hero treatment.
- Prefer shared primitives first:
  - `DSSectionHeader` for section hierarchy
  - `DSMetricSnapshotCard` for compact supporting metric groups
  - `DSExplainabilityCard` for readiness-style primary drivers plus quieter secondary context
  - `DSCard` for supporting surfaces that do not need grouped metric tiles
  - `DSMetricPill` only for secondary trust/history/status signals
- Avoid introducing ad-hoc gradients, custom surface recipes, or bespoke shadows when an existing design-system primitive already matches the role.

### Governance Rule for Home
Before creating a new Home block or changing an existing one, implementation must answer:
1. Which primitive already owns this pattern?
2. Which tokens/styles govern it?
3. Why is a new primitive necessary if one does not already exist?

If a suitable primitive is missing, extend the Design System first, then implement the feature with that primitive.
Do not build Home UI from local one-off recipes when a reusable system pattern is appropriate.

## Navigation Patterns

### iPhone
- Primary navigation pattern: tab bar with top-level sections.
- In current phases, Home is being hosted in the temporary validation surface while product sections continue evolving.

### Mac
- Primary navigation pattern: split view with persistent sidebar + detail panel.
- macOS remains a valid visual QA surface for Home hierarchy and supporting blocks.

## Component Library
Implemented primitives include:
- `DSCard`
- `DSMetricSnapshotCard`
- `DSExplainabilityCard`
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
- Gallery is not only a demo surface; it is also the visual contract for reusable primitives.
- New reusable Home primitives should be represented in Gallery whenever they become part of the supported system language.

### Supported validation platforms
- iOS (generic + iPhone simulator)
- macOS (generic)

## Implementation Rule
When a feature introduces a reusable pattern, the expected order is:
1. define or extend the primitive in `DesignSystem/**`
2. expose/validate it in Gallery if it is reusable language
3. document the rule here in `docs/DesignSystem.md`
4. then consume it in feature code

This keeps Home and future screens governed by the system instead of drifting into custom UI per phase.
