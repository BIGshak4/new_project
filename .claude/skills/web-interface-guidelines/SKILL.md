---
name: web-interface-guidelines
description: Review UI code (React/Next, CSS) against Vercel's Web Interface Guidelines and report file:line findings. Use when asked to "review my UI", "check accessibility", "audit design", "review UX", or before a front-end commit in apps/web.
license: Rules file (references/command.md) MIT, Vercel Labs; wrapper written for JobRun. See LICENSE.
---
<!--
  Installed 2026-09-27 as a JobRun project skill.
  Rules: references/command.md is a verbatim copy of
         https://github.com/vercel-labs/web-interface-guidelines/blob/main/command.md
         (raw: https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md)
         Licence: MIT, Copyright (c) 2025 Vercel Labs; full text in LICENSE beside this file.
  Wrapper: modelled on https://github.com/vercel-labs/agent-skills/blob/main/skills/web-design-guidelines/SKILL.md,
         which fetches the rules at run time; this copy reads the vendored file so it works offline,
         and adds JobRun's own overrides (RTL, Hebrew, sentence case).
-->

# Web Interface Guidelines (JobRun copy)

Review files for compliance with Vercel's Web Interface Guidelines: accessibility, focus, forms,
animation, typography, content handling, performance, navigation state, touch, layout, i18n, hydration.

## How it works

1. Read `references/command.md` in this folder (the rules and the output format).
   If the network is available and the user asks for the latest rules, fetch
   `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md` instead.
2. Read the files the user named (or a pattern such as `apps/web/src/components/*.tsx`).
   With no files named, ask which to review.
3. Check every rule. Output terse `file:line - finding` lines grouped by file, exactly in the
   format the rules file shows. `✓ pass` for a clean file. No preamble.

## JobRun overrides (these win over the rules file)

- **Copy case:** sentence case for headings and buttons, not Title Case. Hebrew has no case;
  English follows the same sentence-case rule. See `docs/design-brief-2026-09-27.md`.
- **Direction:** the app is `dir="rtl"` by default with an English mode. Flag physical CSS
  properties (`margin-left`, `padding-right`, `left:`, `text-align: left`) where a logical one
  (`margin-inline-start`, `inset-inline-start`, `text-align: start`) is meant. Code blocks, email
  fields and URLs are the exceptions and must carry `dir="ltr"`.
- **Hebrew text:** every user-visible string exists in both languages (`t("he", "en")`);
  a hard-coded single-language string is a finding. Numbers and dates use `Intl` with
  `he-IL` / `en-GB`.
- **Motion:** the app already disables all animation under `prefers-reduced-motion: reduce`
  (globals.css); a new animation is fine as long as it uses `transform`/`opacity` and lists its
  properties (never `transition: all`).
- **Do not flag** the deliberate 3D button (`box-shadow: 0 5px 0` collapsing on `:active` with
  `translateY`), the 2 px borders, or the 24 px+ radii: they are the design language.
- **Scope:** visual and navigation code only. Never suggest changes to data flows, API calls,
  polling, idempotency keys or anything under `backend/`.
