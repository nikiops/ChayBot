export function ProductSkeleton() {
  return (
    <div className="glass-card overflow-hidden">
      <div className="h-44 animate-pulse-soft bg-tea-100" />
      <div className="space-y-3 p-4">
        <div className="h-5 w-3/4 animate-pulse-soft rounded-full bg-tea-100" />
        <div className="h-4 w-full animate-pulse-soft rounded-full bg-tea-100" />
        <div className="h-4 w-2/3 animate-pulse-soft rounded-full bg-tea-100" />
        <div className="mt-3 h-10 animate-pulse-soft rounded-full bg-bark-100" />
      </div>
    </div>
  );
}

