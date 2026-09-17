export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export function GET() {
  return Response.json(
    { service: "jobruner-web", status: "ok", checks: { application: "ok" } },
    { headers: { "Cache-Control": "no-store" } },
  );
}
