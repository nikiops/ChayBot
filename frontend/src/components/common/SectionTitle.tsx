type SectionTitleProps = {
  eyebrow?: string;
  title: string;
  subtitle?: string;
};

export function SectionTitle({ eyebrow, title, subtitle }: SectionTitleProps) {
  return (
    <div className="mb-4">
      {eyebrow ? <p className="mb-1 text-xs font-semibold uppercase tracking-[0.28em] text-tea-700/60">{eyebrow}</p> : null}
      <h2 className="font-display text-[2rem] font-semibold leading-tight text-tea-900">{title}</h2>
      {subtitle ? <p className="mt-2 max-w-[36ch] text-sm leading-6 text-fog">{subtitle}</p> : null}
    </div>
  );
}

