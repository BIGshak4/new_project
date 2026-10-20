"use client";
import { ArrowRight, ArrowLeft, RefreshCw } from "lucide-react";

export function Pagination({ page, total, size = 25, busy, onChange }: {
  page: number; total: number; size?: number; busy: boolean; onChange: (page: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / size));
  return <div className="admin-pagination" aria-label="עמודי התוצאות">
    <span className="small muted">{total ? `${(page - 1) * size + 1}–${Math.min(page * size, total)} מתוך ${total}` : "אין תוצאות"}</span>
    <div className="row">
      <button type="button" disabled={busy || page <= 1} onClick={() => onChange(page - 1)}><ArrowRight size={15} />הקודם</button>
      <span className="small">עמוד {page} מתוך {pages}</span>
      <button type="button" disabled={busy || page >= pages} onClick={() => onChange(page + 1)}>הבא<ArrowLeft size={15} /></button>
    </div>
  </div>;
}

export function AdminLoading({ label }: { label: string }) {
  return <div role="status" aria-live="polite" className="admin-loading">
    <p>{label}</p>
    <div className="admin-loading-line" /><div className="admin-loading-line" /><div className="admin-loading-line" />
  </div>;
}

export function AdminError({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="notice error admin-message" role="alert"><span>{message}</span>{retry && <button type="button" onClick={retry}><RefreshCw size={15} />ניסיון נוסף</button>}</div>;
}
