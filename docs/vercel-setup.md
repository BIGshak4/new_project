# Vercel setup status

Working project name: `jobruner` (not a final product name).

## Resources created
- Dashboard: https://vercel.com/job-runer/jobruner
- First preview inspector: https://vercel.com/job-runer/jobruner/ALbkTYkTLV3ed6pW1zwNdCTGoooL
- Preview: https://jobruner-ot9qsyy57-job-runer.vercel.app
- Deployment ID: `dpl_ALbkTYkTLV3ed6pW1zwNdCTGoooL`
- Creation was confirmed by the connected Vercel deployment tool.
- Deployment creation response: `INITIALIZING`; cloud build completion has not been verified.
- Deployment access redirects unauthenticated visitors to Vercel login. Protection was not disabled.

## Source
The source is in `apps/web`. This initial preview was uploaded through the Vercel connector;
it is not yet linked to GitHub. The deployment upload contains the web app only,
with pinned dependencies and a package lock. It excludes Supabase migrations, content banks,
product planning documents, credentials, dependencies, and local build output.

Framework: Next.js 16.3.5; React 19.3.0; TypeScript 5.9.3; Node.js 24.x.
Function region: Frankfurt (`fra1`), near the existing Supabase project in `eu-central-1`.

## Verified locally
- `npm install`: completed; audit reported zero vulnerabilities at install time.
- `npm run typecheck`: passed.
- `npm run build`: passed.
- Build produced routes `/` and `/api/health`.
- Runtime response in the cloud remains unverified because deployment access requires authentication.
- The health endpoint checks application runtime only; it performs no database or AI API call.

## Remaining setup
1. Sign into the business Vercel account and verify this project is accessible.
2. Check the first preview deployment status in the dashboard.
3. Connect the existing project to GitHub repository `BIGshak4/new_project`.
4. Set the Git-backed project's Root Directory to `apps/web` and production branch to `master`.
   The initial direct upload used the web directory as its root; do not set a nested root for that upload.
5. Keep Next.js default install/build/output settings.
6. Set environment variables for the existing Supabase project when implementing database-backed flows:
   `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.
   Keep secrets server-only; no database secret or service-role key is needed for this bootstrap.
7. Verify RLS policies and Auth redirect URLs when login is implemented.
8. Confirm the plan is suitable for the business. Vercel Hobby is restricted to personal, non-commercial use.
   No paid upgrade, subscription, domain purchase, or team invitation was performed.

## Connection issue
The connector created the deployment, but project reads returned `403 Forbidden`.
Team enumeration returned an empty array. Treat this as an access/scoping issue requiring
account confirmation or reconnection, not proof that the deployment is broken or absent.
No Vercel project ID or team ID was fabricated, and no local `.vercel/project.json` linkage is claimed.

## Official documentation
- https://vercel.com/docs/git
- https://vercel.com/docs/deployment-protection
- https://vercel.com/docs/plans/hobby
- https://nextjs.org/docs/app/getting-started/installation
# Historical bootstrap note

The active pilot is now hosted on Netlify. See [current setup](netlify-and-supabase.md). The Vercel details below are retained as earlier setup history.
