# Games, avatars and Muxi's shop rollout

The user authorized publishing the game after viewing its preview on 29 October 2026 and requested persistent user customization and a cosmetic-only shop. This supersedes the earlier local-only rollout status in `games-integration.md`; it does not attest expert correctness review.

## Content

Fifty source-linked quiz variants are enabled for the authorized pilot. Each has release metadata `basis: user_authorized_pilot_release` and `professional_review: pending`. The forty older independent drafts remain excluded. The UI identifies game content as a pilot with professional review pending. Original fundamentals and their review metadata were not altered.

## Avatars and prices

Free components: AND, OR, XOR, MUX and D flip-flop. Six free colors. Every character retains `Job_Run` branding. Classic is free; Aurora, Circuit, Cosmic and Gold each cost **20 coins**. Six original meme shirts each cost **40 coins**: Negative Feedback, Works on My Machine, Binary People, Gate Keeper, Sleep Not Found and Resistance Is Futile. Existing ownership and past charges are retained. Skins are permanent cosmetics, do not affect scoring and cannot be purchased or redeemed for cash. The skin shop does not expose the older daily-question top-up item.

`/games/shop` saves the authenticated user's selection and buys skins through the backend. `/games/preview/shop` is explicitly simulated and never writes to an account. The same preview tab retains its demo selection on returning to the game.

The API validates catalog IDs, ownership and prices. Avatar saves and purchases share the existing per-user coin lock with duel stakes. Purchase ownership and the ledger debit commit atomically; duplicate buys do not charge twice. Participants' visible avatar configuration is exposed through authorized duel views, without their inventory or balances.

The revised shop is Muxi's booth with a canopy, counter, changing dialogue, shirt rack, print close-up and free editor. Saved avatars and games/shop links appear inside the signed-in top bar; the avatar is hidden during a practice question or mock interview. Duel lobby and result avatars face inward without reversing their prints.

`POST /v1/me/avatar/onboarding` records an optional free component/color choice or an empty-body skip. It preserves owned/equipped skins and does not charge coins. The first-use gate does not interrupt focused practice or a duel invitation. `/games/preview/welcome` demonstrates this step without an account. Shop drafts use account-specific session storage, while ownership and saved configuration remain server-controlled.

## Database operations

Applied through the project connector after a transaction/rollback dry run: existing `coins` and `duels` schemas and new `game_avatars`. New local avatar migration was created using Supabase CLI (`20261029132230_game_avatars.sql`). Billing remains unapplied.

The revision migration `20261029141030_avatar_shirt_catalog_and_onboarding.sql` was also applied through the connector after a rollback dry run with transient fixtures. It expands the fixed skin constraints and adds `onboarding_completed`: true for existing avatar rows, false by default for new rows. The dry run accepted all 11 skins, rejected unowned/unknown skins, retained prior inventory and confirmed unchanged grants/RLS. Post-apply checks confirmed the false default, RLS enabled, no anonymous read and no authenticated update privilege.

Verified all three tables have RLS, no anonymous read grant and no browser insert/update grant. A rolled-back two-user test confirmed own avatar visibility and other-user isolation. The `duel` table intentionally has no browser RLS policy: its browser privileges are revoked and access goes through the authenticated API. The advisor's informational no-policy finding is expected for that design; its pre-existing password-protection warning is outside this rollout.

The local direct database verification script could not connect because its stored database password is invalid. No credentials were changed. Connector-based schema/permission tests and the automated service/API tests provide the available evidence; direct database application-flow testing remains a separate limit.

## Deployment

Frontend deploys from `master` to `https://jobrun-practice.netlify.app`; backend deploys from the same Git push to `https://jobrun-api.onrender.com`. Verify the exact frontend revision at `/api/health` and new `/v1/me/avatar` and duel `/ready` paths in the backend OpenAPI after deployment. The backend must restart after schema application because reflection is cached per process.
