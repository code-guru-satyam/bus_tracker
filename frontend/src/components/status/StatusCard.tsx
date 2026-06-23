type StatusCardProps = {
  label: string;
  value: string;
  tone: 'ok' | 'neutral' | 'danger';
};

export function StatusCard({ label, value, tone }: StatusCardProps) {
  return (
    <article className={`status-card status-card-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

