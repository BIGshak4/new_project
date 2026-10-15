import { Children, type ReactNode } from "react";

/** Keep technical expressions intact inside surrounding Hebrew prose. */
export function BidiText({ children }: { children?: ReactNode }) {
  return <>{Children.map(children, child => typeof child !== "string" ? child
    : child.split(/([A-Za-z0-9][\x20-\x7E\u2190-\u2194\u2212]*[A-Za-z0-9)]|[A-Za-z0-9])/g)
      .map((part, i) => i % 2 ? <bdi key={i} dir="ltr">{part}</bdi> : part))}</>;
}
