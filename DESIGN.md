---
name: JobRun
description: Hebrew-first practice and founder workspaces with sage surfaces and deep-green emphasis.
colors:
  ink: "#172c27"
  muted: "#5f6e66"
  paper: "#f6f7f2"
  surface: "#fff"
  line: "#dce2d8"
  green: "#225d48"
  light: "#e8f0df"
  warm: "#f4eddb"
  danger: "#9c3434"
  primary-hover: "#194734"
  focus: "#b58a31"
  input-border: "#bcc9bf"
  sidebar: "#eef1e8"
  nav-active: "#dce7d2"
  badge: "#edf0e9"
  doing-bg: "#e3eeff"
  doing-text: "#204a80"
  blocked-bg: "#f9e7e0"
  blocked-text: "#8c3422"
  done-bg: "#e2efdb"
  done-text: "#285135"
  todo-bg: "#eeeee9"
  todo-text: "#5a6159"
typography:
  display:
    fontFamily: "Heebo, Arial, sans-serif"
    fontSize: "clamp(34px, 4vw, 58px)"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Heebo, Arial, sans-serif"
    fontSize: "32px"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Heebo, Arial, sans-serif"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: 1.4
  body:
    fontFamily: "Heebo, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "Heebo, Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 500
    lineHeight: 1.65
  code:
    fontFamily: "Consolas, monospace"
    fontSize: "14px"
    lineHeight: 1.7
rounded:
  badge: "5px"
  field: "7px"
  control: "8px"
  task: "9px"
  list: "10px"
  sheet: "12px"
spacing:
  control-gap: "8px"
  row-gap: "12px"
  field-gap: "16px"
  stack-gap: "18px"
  pane-gap: "24px"
  practice-gap: "26px"
  workspace-inset: "36px"
components:
  button-primary:
    backgroundColor: "{colors.green}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "9px 14px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
    textColor: "{colors.surface}"
  button-default:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "9px 14px"
  button-secondary:
    backgroundColor: "{colors.light}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "9px 14px"
  button-text:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "9px 14px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "10px 12px"
  nav-active:
    backgroundColor: "{colors.nav-active}"
    textColor: "#244733"
    rounded: "{rounded.control}"
    padding: "11px 13px"
  badge:
    backgroundColor: "{colors.badge}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.badge}"
    padding: "3px 9px"
  task-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.task}"
    padding: "16px"
  practice-sheet:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sheet}"
    padding: "28px"
---

# Design System: JobRun

## Overview

**Creative North Star: "Engineering working notebook / ledger"**

This is the implemented direction, chosen autonomously for the build; it is not a user-approved metaphor. Pale sage backgrounds, white working sheets, deep-green actions, and Heebo text support reading and writing in Hebrew and English. The visual system is shared by the practice and founder applications.

The interface concentrates detail inside question rows, task cards, and full-page work areas. Short labels, restrained borders, and visible keyboard focus organize routine actions without decorative imagery.

**Key Characteristics:**
- Hebrew-first typography with logical alignment for RTL and LTR.
- Sage surroundings and white working surfaces.
- Green primary actions and text-labelled status colors.
- Compact controls and responsive working panes.

Evidence: identical `apps/web/src/app/globals.css` and `apps/tasks/src/app/globals.css`, both app pages, and the authentication component. Product constraints come from `PRODUCT.md`; the provisional direction remains in `.impeccable/surfaces/apps-web-src-app-page-tsx.md`.

## Colors

The palette combines green-tinted neutrals with a dark action color and separate semantic status pairs.

### Primary
- **Green:** primary actions, selected self-assessment controls, progress, caret, and input focus.
- **Light:** secondary actions and selected segmented controls.
- **Primary hover:** deeper green for primary-button hover.

### Secondary
- **Warm:** pilot context notices.
- **Danger:** destructive text actions.
- **Doing, blocked, done, and todo pairs:** backgrounds and readable text for explicit status labels; blocked and high priority share the warm red pair.
- **Focus:** gold outline on keyboard-focused buttons and links.

### Neutral
- **Ink / muted:** principal content and supporting metadata.
- **Paper / surface / sidebar:** page, work area, and navigation backgrounds.
- **Line / input border:** group boundaries and field affordances.
- **Nav active / badge:** selected navigation and compact metadata backgrounds.

**The Labelled State Rule.** Status colors accompany written labels; keep the status meaning available in text.

## Typography

**Display Font:** Heebo with Arial and sans-serif fallbacks.
**Body Font:** Heebo with the same fallbacks.
**Label/Mono Font:** Heebo for labels; Consolas and monospace inside code blocks.

One family covers Hebrew and English, with weight and size establishing hierarchy. Tabular numerals align summary counts and question numbering.

### Hierarchy
- **Display:** authentication statement, using the frontmatter fluid ramp; mobile overrides to 38px.
- **Headline:** workspace heading, reducing to 27px at the mobile breakpoint.
- **Title:** section heading; practice answer headings use 20px.
- **Body:** default text, reducing to 14px on mobile. Practice prompts use 17px with 1.95 line height, then 16px on mobile.
- **Label:** badges and small metadata. Secondary utility copy commonly uses 13px and 14px.
- **Code:** left-to-right, horizontally scrollable code with the dedicated monospace role.

**The Direction-Aware Text Rule.** Use logical alignment for interface text and preserve explicit LTR treatment for code and email fields.

## Layout

The desktop shell has a sticky full-height 220px sidebar and flexible workspace. Content is centered within a 1550px maximum width, with the workspace inset from the token scale. The top bar is 76px high.

At 1150px and below, the sidebar becomes 180px, workspace padding becomes 25px, and the four-column board becomes two columns. At 760px and below, navigation becomes a wrapping top rail, the top bar becomes 58px, content padding becomes 24px 16px, and editor and practice panes stack. Search occupies its own toolbar row. At 430px and below, the board and paired fields become single-column and navigation can scroll horizontally.

Desktop editors pair a flexible main pane with a 320px detail pane (280px at the intermediate breakpoint). Practice uses equal columns. Authentication splits evenly between story and form, then stacks on mobile; the form is capped at 390px. Spacing is component-specific, not a fabricated universal grid.

## Elevation & Depth

Tonal surfaces and one-pixel boundaries establish most depth. Task cards add a very subtle soft shadow; sticky save controls use an almost opaque white surface. There are no hard offset shadows.

### Shadow Vocabulary
- **Task at rest:** `0 2px 3px #1a321407`.
- **Task hover:** `0 5px 13px #1a32140c`.
- **Field focus:** `0 0 0 3px #225d4818`, paired with the green field border.

**The Quiet Depth Rule.** Use the observed subtle card shadows for interactive task cards; working sheets rely on borders and tonal separation.

## Shapes

Small rounded rectangles distinguish controls, fields, badges, cards, lists, and sheets through the radius tokens. Avatar initials sit inside circles. The wordmark has a small green square rotated by -12 degrees. List rows have square internal edges inside a rounded outer container. Panels use one-pixel borders; empty board columns use dashed boundaries.

## Components

### Buttons

Compact, text-led controls. Primary, default, secondary, and text variants use the frontmatter values, with a 42px minimum height and 8px content gap. Primary buttons have weight 600. Default hover uses light green and border `#9daf9d`; primary hover uses the deeper action tone. Keyboard focus is a 3px gold outline with 3px offset. Disabled controls have opacity .55 and a wait cursor. Background and border transitions last .18s with ease timing.

### Chips

Small flat metadata badges use the label role. Semantic variants pair the recorded foreground and background colors with status words. Segmented buttons use a light selected background and weight 600; self-assessment selections use green with white text.

### Cards / Containers

Task cards have a minimum height of 134px, a `#d9e0d4` border, and subtle resting shadow; hover changes the border to `#839b78` and raises the soft shadow. Mobile padding is 12px. List containers use the list radius and shared divider color. Editor sheets use 26px padding; practice sheets use 28px. All reduce to 20px on mobile.

### Inputs / Fields

White fields use the recorded field radius and border, with green caret and focus border. Labels use weight 500 and a 6px gap. Textareas resize vertically and have 1.8 line height. Practice answers have a 320px minimum height, reduced to 250px on mobile. Error notices combine warm red text, border, background, and written error messages.

### Navigation

The side rail uses transparent resting items with active sage fill and weight 700. Navigation buttons align to the text start. On mobile their padding becomes 8px 10px, font size becomes 13px, and icons are hidden while labels remain. Lucide SVG icons accompany actions elsewhere.

### Working rows and save feedback

Questions use full-width button rows with aligned number, title, category, difficulty, and duration fields. Lower-priority columns progressively hide at the recorded breakpoints. Task editing retains a sticky bottom save bar and written save feedback. View transitions use 180ms; reduced-motion preferences disable animation and transition effects.

## Do's and Don'ts

### Do:
- **Do** preserve readable Hebrew and English through logical alignment and explicit code direction.
- **Do** pair semantic colors with written status labels.
- **Do** retain visible focus and the reduced-motion override.
- **Do** use the shared surface, spacing, and type roles across both applications.

### Don't:
- **Don't** remove labels when compact navigation hides its icons.
- **Don't** use the code font for ordinary interface text.
- **Don't** present this implementation assumption as a user-approved visual identity.
