# Wardrobe design verification — 2026-10-29

## Scope and authority

The wardrobe is an ordinary extension of the existing Mineral / Adaptive Ion system. `PRODUCT.md`, `DESIGN.md`, `.impeccable/design.json` and `.impeccable/surfaces/apps-web-src-app-games-shop-page-tsx.md` remain authoritative and unchanged by this pass. No new visual world, global token, reusable prohibition or registry entry is introduced. This record follows the scan guidance in `C:/Users/harel/.agents/skills/impeccable/reference/document.md`; it records the implementation rather than regenerating the incumbent system.

## Inherited system

- **Palette:** the shell, controls and shelf consume `paper`, `surface`, `surface-2`, `ink`, `muted`, `line`, `link`, `action`, `action-ink` and semantic feedback variables. Mineral supplies the light values through `mineral.css`; the same references retain existing dark Ion behavior. The finite avatar colors and skin gradients belong to the character renderer, not to a replacement interface palette.
- **Type:** the shell uses the incumbent `--nf-ion` Heebo stack. The local main heading is `clamp(32px,4.6vw,50px)`, weight 900, line-height 1.2; the shop heading is `clamp(28px,3.4vw,38px)`, weight 900. Supporting copy uses 17px and controls inherit the shell face. Mobile headings and labels reduce locally. These are surface adaptations, not changes to the global type ramp.
- **Named rules:** Theme Continuity is maintained by semantic variables and the existing theme toggle; Labelled State by written balance, ownership, wearing, purchase, save and error messages; Direction-Aware Text by the Hebrew/English `dir` switch and logical spacing; Quiet Depth by flat fills and thin borders without structural panel shadows.
- **Shape and interaction:** controls retain 7px corners, one-pixel boundaries, 44px minimum height and visible link-colored keyboard outlines. Selected component buttons use a written label, checkmark and `aria-pressed`; color buttons have accessible names, `aria-pressed` and a checkmark. Product state is written as well as outlined.
- **Layout:** the local content maximum is 1160px with a 90% width. The preview and editor form two columns; the shelf has three columns, two below 900px, with a single-column editor below 650px and a single-column shelf below 360px. The stage, 18px frame corners and 12px product corners are local composition details.

## Character and game integration

`LogicAvatar` renders native SVG from the selected AND, OR, XOR, MUX or D flip-flop component, one of six canonical colors, and Classic, Aurora, Circuit, Cosmic or Gold clothing. Every variant retains a face, short limbs and literal `Job_Run` shirt text. The technical silhouettes and skin gradients are native character material, compatible with the selected surface contract. They do not authorize gradients or illustration colors on general UI controls. D/Q notation and shirt lettering are small identity/technical artwork, not a new system display face.

The same renderer appears in the duel header, lobby, score and result views. `game-avatar.module.css` scopes the profile link and avatar layout. Avatar artwork uses its own fixed outline, shirt and skin colors; semantic theme inheritance describes the surrounding interface, not a recoloring of every SVG path.

No raster asset is shipped by this extension. Review PNGs are evidence captures, not runtime imagery. No raster provenance sidecar is required for the native SVG implementation.

## Evidence and limits

Source checked: `apps/web/src/components/wardrobe/{wardrobe.tsx,wardrobe.module.css,wardrobe-page.tsx,wardrobe-preview.tsx,logic-avatar.tsx,logic-avatar.module.css}`, `apps/web/src/components/duels/{duel-workspace.tsx,game-avatar.module.css}`, `apps/web/src/lib/{avatar-types.ts,avatar-catalog.json,avatar-demo.ts,avatar-api.ts}`, `apps/web/src/app/games/shop/page.tsx` and `apps/web/src/app/mineral.css`. The incumbent system and sidecar were sampled against these sources.

Local capture set: `.impeccable/review/wardrobe/{desktop-editor.png,desktop-shop.png,mobile-editor.png,mobile-controls.png,mobile-shop.png}`. This pass directly inspected `desktop-editor.png` and `mobile-shop.png`; the coordinating agent inspected the full viewport capture set. The screenshots show a labelled simulated shop, flat Mineral surfaces and responsive stacking. They do not establish authenticated production or physical-phone behavior.

The coordinating agent reports a local demo check of component/color saving and a 40-coin Aurora purchase followed by equipping. The demo client is explicitly session-local and does not write a real wallet. Backend authorization and purchase checks are recorded by the coordinating implementation work; database tests used rollback, migrations were applied live, and deployment was still pending when this record was written. Those reports are not independent production verification by this documentation pass. The finish review is separate from this inheritance check.

## Not canonized or repaired

The wardrobe primary action has a local 44px minimum inherited from its scoped button rule, while the incumbent global primary role records 46px. Scoped type sizes, character colors, illustration lettering, stage geometry and seller counter remain surface decisions, not new global rules. This documentation-only pass preserves source and registry files; it does not repair local drift or certify unsampled states. No kickers, glyph icons or hard offset shadows were found in the sampled wardrobe source.
