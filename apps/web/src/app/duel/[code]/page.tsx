import { DuelPage } from "../../../components/duels/duel-page";

export default async function InvitePage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  return <DuelPage invite={code} />;
}
