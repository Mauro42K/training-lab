# Phase 2 — Design System & Layout Checklist

Status: COMPLETE
Goal: Establish a premium Apple-like visual language and reusable UI primitives before any feature screens are built.

This checklist is the tracking document for completing Phase 2 of Training Lab.
Figma is the design source of truth and the repository contains the executable DesignSystem implementation.

---

# 1. Design Tokens (Figma + Swift parity)

Objective: Every visual primitive exists both in Figma and in Swift with NO placeholders.

## Colors
- [x] Colors confirmed in Figma Tokens page
- [x] `AppColors.swift` matches Figma tokens
- [x] No TODO comments remaining

## Typography
- [x] All text styles defined in Figma as Text Styles
  - Display / Large
  - Display / Medium
  - Heading / H1
  - Heading / H2
  - Heading / H3
  - Body / Large
  - Body / Regular
  - Body / Small
  - Button / Medium
  - Label / Small
- [x] `AppTypography.swift` updated to match Figma
- [x] All TODO placeholders removed

## Spacing
- [x] Spacing scale confirmed
  - 0, 4, 8, 12, 16, 24, 32, 40, 48, 64
- [x] `AppSpacing.swift` matches token scale

## Radius
- [x] Radius tokens confirmed in Figma
  - 0, 8, 12, 16, 20, 24
- [x] `AppRadius.swift` matches token scale
- [x] No TODO placeholders

## Shadows / Elevation
- [x] Shadows confirmed in Figma
  - Card
  - Dropdown
  - Modal
- [x] `AppShadows.swift` matches tokens
- [x] `AppElevation.swift` correctly maps surfaces to shadows

Definition of Done (Tokens):
- No placeholders
- No TODO markers
- Full parity between Figma and Swift tokens

---

# 2. Layout Rules (Design Guidelines)

Objective: Define structural layout rules used across the app.

## Card Density
- [x] Standard card padding defined
- [x] Minimum card height defined
- [x] Card corner radius confirmed

## Section Spacing
- [x] Spacing between sections defined
- [x] Spacing between cards defined

## Navigation Patterns

### iPhone
- [x] Tab bar pattern documented

### Mac
- [x] Split view pattern documented

Definition of Done (Layout):
- Layout rules documented in docs/DesignSystem.md

---

# 3. Component Library

Objective: Implement reusable UI primitives.

## Core Components

### Card
- [x] `DSCard` implemented
- [x] Uses tokens only (no hardcoded values)
- [x] Supports elevation styles

### MetricPill
- [x] Implemented
- [x] Supports semantic colors

### SectionHeader
- [x] Title
- [x] Optional trailing action

### SegmentedControl
- [x] Wrapper around SwiftUI Picker
- [x] Styled using tokens

### ChartCard
- [x] Base container for charts
- [x] Uses card tokens

### Ring
- [x] Functional trim ring component
- [x] Token based styling

### EmptyState
- [x] Icon + message layout

### LoadingState
- [x] Skeleton placeholder

Definition of Done (Components):
- All components render correctly in Gallery
- No hardcoded visual values

---

# 4. Gallery / Sandbox

Objective: Visual playground for the design system.

`GalleryView.swift`

Sections included:

## Tokens
- [x] Color palette
- [x] Typography scale
- [x] Spacing examples
- [x] Radius examples
- [x] Shadow / elevation examples

## Components
- [x] Card
- [x] MetricPill
- [x] SectionHeader
- [x] SegmentedControl
- [x] ChartCard
- [x] Ring
- [x] EmptyState
- [x] LoadingState

## Compositions (Optional but recommended)
Examples inspired by Stitch screens:
- [x] Example metric card
- [x] Example workout card
- [x] Example calendar card

Definition of Done (Gallery):
- Gallery renders all tokens and components

---

# 5. Demo App (Multiplatform)

Objective: Provide an executable environment for validating the design system.

App name: `DesignSystemDemo`

Requirements:

- [x] SwiftUI multiplatform app created
- [x] iOS target
- [x] macOS target

Root View:

```
GalleryView()
```

Definition of Done (Demo App):
- App launches on iPhone simulator
- App launches on macOS

---

# 6. Visual QA

Objective: Ensure visual consistency across platforms.

## iPhone
- [x] Dark mode
- [x] Light mode
- [x] Dynamic Type default
- [x] Dynamic Type large

## Mac
- [x] Window small size
- [x] Window large size
- [x] Dark mode
- [x] Light mode

Artifacts:
- [x] QA evidence documented in `docs/Phase2_VisualQA.md`

Definition of Done (QA):
- All components visually validated on both platforms

---

# Phase 2 Completion Criteria

Phase 2 is considered COMPLETE when:

- [x] Tokens are finalized (no TODOs)
- [x] Component library implemented
- [x] Gallery renders all tokens and components
- [x] Demo app runs on iPhone and Mac
- [x] Visual QA completed

IMPORTANT:

No feature screens (Home, Trends, Workouts, Calendar, Body) should be built until Phase 2 is fully complete.

---

Next Step After Phase 2:

Phase 3 — Feature Screens

The screens designed in Stitch/Figma will then be implemented using the components defined in the DesignSystem.
