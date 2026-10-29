# Wardrobe design verification — 2026-10-29

## Overview

This is a scoped verification of the wardrobe extension in commit `599adef`, not a replacement design system. The incumbent authority remains `DESIGN.md` and `.impeccable/design.json`: Mineral light, optional dark Ion, Heebo, semantic colors, logical text alignment and restrained working surfaces. Those files were read and preserved. The surface contract is `.impeccable/surfaces/apps-web-src-app-games-shop-page-tsx.md`; `PRODUCT.md` supplies the Hebrew-first, bilingual and responsive product constraints.

The implementation realizes the contract through a physical Muxi stall, component-specific avatar geometry, technical printed shirts, an optional free first-use setup and inward-facing duel characters. The stall composition is local to this surface; it does not become the product-wide layout or a new visual world. No shipping raster was introduced: characters and shirt artwork are native SVG.

## Colors

Wardrobe, onboarding, navigation and duel details resolve the existing `paper`, `surface`, `surface-2`, `ink`, `muted`, `line`, `link`, `action` and `action-ink` semantic variables. Mineral supplies cool gray-green surfaces with plum text and purple actions; dark Ion supplies violet surfaces, light text, lilac links and amber actions. Written ownership, balance, loading, save and error messages accompany visual states.

Character colors remain the finite avatar catalog rather than new UI tokens. Shirt fabric, print ink, collar and seam colors belong to the illustration renderer. A scoped dark-theme outer rim separates limbs, feet, shirt outlines and pins from the dark surface; light mode makes the rim transparent. Face ink remains plum. These illustration colors and geometry are not additions to the global token registry.

## Typography

The surfaces inherit the Heebo stack through `--nf-ion`. Source samples show the shop headline at `clamp(32px,3.7vw,46px)` with weight 900 and line-height 1.15, collection/editor headings at `clamp(28px,3vw,36px)`, supporting text at 14–16px, and compact labels at 12–13px. Phone overrides reduce these roles locally. The welcome title uses `clamp(29px,3.5vw,44px)` and line-height 1.25. These are observed surface variations, not a replacement for the incumbent type ramp.

Technical shirt lettering stays LTR. The facing transform applies to anatomy while print lettering sits outside it, preventing reversed words on the opposing avatar. At avatar sizes of 180 or below, distinct compact print identifiers replace full jokes; the shop enlargement and optional duel details retain the complete artwork at reading size.

## Layout

The shop content caps at 1180px with a 90% width, widening to 92% on smaller screens. The desktop booth pairs Muxi and speech with a featured shirt and purchase controls. The collection uses three columns, then two below 800px. The editor changes from two columns to one below 800px. Below 570px, the booth stacks its merchant and featured merchandise, preserving the physical canopy/counter relationship. The top navigation wraps onto its own row on compact layouts.

The welcome view pairs a large preview and selectors, then stacks for phones. Its support control is in the header; the sibling floating support launcher is suppressed so it does not cover selectors. Duel shirt details use two columns and stack below 650px.

## Elevation & Depth

Interface panels primarily use semantic tonal separation and one-pixel borders, consistent with the incumbent Quiet Depth Rule. The merchandise SVG has a small diffuse drop shadow; the canopy, hanger, speech tail and counter establish the stall's physical composition. This local illustration treatment is not a new structural shadow rule for working panels.

## Shapes

The native character renderer combines rounded component-specific heads, tailored shirt bodies, a broad integrated neck seated behind the collar, articulated short limbs and expressive faces. AND, OR/XOR, MUX and D flip-flop retain their component silhouettes. The shop uses softened booth corners, rounded merchandise fields, pill filters and circular color selectors. These local shapes coexist with the incumbent product geometry.

## Components

- **Shop and prints:** four generic skins cost 20 coins each and six technical meme shirts cost 40. Shared SVG artwork covers negative feedback, terminal, binary, AND, 404 and resistor motifs. Full prints remain available through enlargement. Purchase, ownership, try-on and saved selection are distinct written states; purchase/equip feedback is driven by client results.
- **Saved identity and navigation:** `FeatureNav` provides labelled games/shop destinations plus the saved avatar. The shop header passes the server-loaded saved configuration rather than its unsaved editor draft. The authenticated workspace passes `profileAvatar` and hides its identity during active practice or the interview view. Workspace header integration was inspected in source and covered by the reported build, without a signed-in browser account.
- **Editor:** component and color controls expose selected state with `aria-pressed`; color buttons have accessible labels and a visible selected outline. Draft restoration uses an account-scoped session-storage key and validates the draft against loaded inventory. This is session draft continuity, separate from confirmed server persistence.
- **First use:** free component/color setup offers an explicit skip. The source completes onboarding through the client and keeps errors visible; preview changes alone do not establish a successful save.
- **Duels:** two avatars face inward according to interface direction, with print lettering unmirrored. Native `details`/`summary` exposes both full shirt designs optionally, rather than depending on compact artwork to carry tiny joke text.
- **Interaction:** sampled shop controls retain 44px minimum targets, semantic selected states and visible keyboard focus. This is source evidence, not a claim of a complete accessibility audit or physical-phone validation.

## Do's and Don'ts

- **Do** retain the incumbent Theme Continuity, Labelled State, Direction-Aware Text and Quiet Depth rules within their existing scope.
- **Do** keep compact identifiers and reading-size full prints as separate render modes of the same artwork.
- **Do** preserve anatomy/lettering transform separation and the dark-only silhouette rim.
- **Don't** promote the stall's canopy, physical counter, illustration palette or local radii into product-wide requirements.
- **Don't** treat simulated demo purchases, local captures or build success as evidence of two real authenticated users completing a deployed flow.

Evidence inspected: wardrobe styles, avatar geometry and print renderer, onboarding, feature navigation, workspace header styles, wardrobe draft handling, `app/page.tsx`, duel integration, `duel-looks.tsx` and `game-avatar.module.css`; incumbent `DESIGN.md`, its sidecar, `PRODUCT.md` and the surface contract. Representative final captures inspected in `.impeccable/review/wardrobe-v2/`: `desktop.png`, `mobile.png`, `duel-detail-mobile.png` and `welcome-mobile.png`. Earlier rack/editor supplements precede the rim fix and are not the final artifact authority.

The fresh finish review returned **ship for the three scored fixes only**: compact/full-print readability, dark-body separation and the welcome floating-help overlap were resolved, with no visible regressions identified in that batch. This is not whole-surface production approval. Parent-reported validation: 301 frontend tests passed; 1679 backend tests passed with 11 skipped, excluding live database/service/interview checks; production build passed. The database migration was applied after rollback-fixture/grant checks. Deployment remained pending at documentation time. Public demo UI was exercised; two real authenticated accounts were not exercised, and the authenticated workspace header has source/build evidence only.

Not canonized or repaired: incumbent dormant Workbench selectors, incomplete task sidecar snippets and unsampled local drift remain outside this ordinary extension; neither the global design files nor unrelated source/docs were rewritten to legitimize them.
