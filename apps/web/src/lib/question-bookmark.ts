import type { Entry } from "./practice-ui";
import { supabase } from "./supabase";

const entryFields = "id,user_id,question_id,answer,self_rating,bookmarked,completed,hidden,version";

/** Patch only the bookmark so concurrent notes and personal-status saves stay intact. */
export async function saveQuestionBookmark(userId: string, questionId: string, bookmarked: boolean): Promise<Entry> {
  if (!userId || !questionId || typeof bookmarked !== "boolean") throw new Error("Invalid question bookmark");
  const update = () => supabase.from("jr_practice_entries")
    .update({ bookmarked })
    .eq("user_id", userId)
    .eq("question_id", questionId)
    .select(entryFields)
    .maybeSingle();

  let result = await update();
  if (result.error) throw result.error;
  if (!result.data) {
    result = await supabase.from("jr_practice_entries")
      .insert({ user_id: userId, question_id: questionId, bookmarked })
      .select(entryFields)
      .single();
    // A completion, note or another tab may have created the entry after our UPDATE.
    if (result.error?.code === "23505") result = await update();
  }
  const saved = result.data as Entry | null;
  if (result.error || !saved || saved.user_id !== userId || saved.question_id !== questionId || saved.bookmarked !== bookmarked) {
    throw new Error("Could not save question bookmark");
  }
  return saved;
}
