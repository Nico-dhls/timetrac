# GUI Polish - Modern Refinement Design

## Goal

Comprehensive visual refresh of the TimeTrac GUI. Fix spacing inconsistencies, improve visual hierarchy, modernize the overall feel, and default to Duration time mode.

## Changes

### 1. Left Panel - Form Layout

- Remove card wrappers from PSP, Time, and Description sections.
- Use horizontal dividers (1px, border color) between logical sections instead.
- Consistent 20px spacing between sections, 8px between label and input.
- Section labels: 11px uppercase with letter-spacing for readability.
- Time section defaults to Duration mode (hours as number).
- Mode toggle becomes a segmented control: two buttons "Dauer" | "Zeitspanne" instead of a flat text button.
- Action buttons: all equal height (40px). Save button stretch factor 2, others stretch factor 1.
- Timer card stays at bottom with cleaner single-row layout.

### 2. Right Panel - Day View & Tree

- Replace parent/child tree with flat table rows. Each entry is one row: PSP, Leistungsart, Beschreibung, Zeit, Stunden.
- Group summary rows only appear when 2+ entries share the same PSP+Type+Desc key. Shown below the individual rows with a different background and bold total.
- Remove "Ubersicht" title (tabs already describe content).
- Move "Statistik" button into tab bar row, right-aligned, as a flat button.
- Copy buttons become a subtle toolbar row. "SAP ITP Export..." is the primary (accent) button; others are secondary.

### 3. Theme & Styling

- Title: 24px bold (from 22px).
- Section labels: 11px uppercase with letter-spacing 0.5px.
- Totals: 16px bold (from 15px).
- Button depth: reduce border-bottom from 3px to 2px for subtler press effect.
- Input fields: increase padding from 8px to 10px. Add subtle darker border-bottom for recessed feel.
- New `QFrame#divider` style: 1px height, border color, no margin.
- Tab bar: 10px vertical padding (from 8px), rounded top corners.

### 4. Default Time Mode

- Default `_time_mode` set to `TimeMode.DURATION` instead of `TimeMode.RANGE`.
- On startup: Duration widget visible, Range widget hidden.
- Mode button text starts as "Modus: Zeitspanne".
- `_reset_form()` resets to Duration mode.
- Timer still switches to Range mode when started (needs start/end times).

## Files Affected

- `timetrac/theme.py` - typography, button depth, input padding, divider style, tab bar
- `timetrac/main_window.py` - left panel layout, right panel layout, default time mode, button sizing
- `timetrac/widgets.py` - divider helper function
