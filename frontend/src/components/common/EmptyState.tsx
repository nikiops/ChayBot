import type { ReactNode } from "react";

type EmptyStateProps = {
  title: string;
  description: string;
  action?: ReactNode;
};

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="glass-card p-6 text-center">
      <div className="mx-auto mb-4 h-14 w-14 rounded-full bg-tea-100" />
      <h3 className="text-lg font-bold text-tea-900">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-fog">{description}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

