type SectionTitleProps = {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  tone?: "light" | "dark";
};

export function SectionTitle({ eyebrow, title, subtitle, tone = "light" }: SectionTitleProps) {
  const eyebrowClass = tone === "light" ? "text-[#cdb689]/72" : "text-tea-700/60";
  const titleClass = tone === "light" ? "text-parchment" : "text-tea-900";
  const subtitleClass = tone === "light" ? "text-[#dac7a7]/74" : "text-fog";

  return (
    <div className="mb-4">
      {eyebrow ? <p className={`mb-1 text-xs font-semibold uppercase tracking-[0.28em] ${eyebrowClass}`}>{eyebrow}</p> : null}
      <h2 className={`font-display text-[2rem] font-semibold leading-tight ${titleClass}`}>{title}</h2>
      {subtitle ? <p className={`mt-2 max-w-[36ch] text-sm leading-6 ${subtitleClass}`}>{subtitle}</p> : null}
    </div>
  );
}
