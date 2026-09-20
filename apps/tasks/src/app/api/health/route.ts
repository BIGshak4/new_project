export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export function GET() {
  return Response.json(
    { service: "jobrun-tasks", status: "ok", revision: process.env.NEXT_PUBLIC_BUILD_REVISION },
    { headers: { "Cache-Control": "no-store" } },
  );
}
