/** Shared locks prevent an expanded circuit from restoring a tour's stale scroll lock on exit. */
const locks = new WeakMap<Document, { count: number; original: string }>();
export function lockBodyScroll(owner: Document = document): () => void {
  let state = locks.get(owner);
  if (!state) { state = { count: 0, original: owner.body.style.overflow }; locks.set(owner, state); }
  state.count++;
  owner.body.style.overflow = "hidden";
  let released = false;
  return () => {
    if (released) return;
    released = true;
    const current = locks.get(owner);
    if (current && --current.count === 0) { owner.body.style.overflow = current.original; locks.delete(owner); }
  };
}
