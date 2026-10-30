interface Props {
  amount?: number | null;
  className?: string;
  exact?: boolean;
}

export function formatINR(amount: number): string {
  if (amount >= 10_000_000) return `₹${(amount / 10_000_000).toFixed(2)}Cr`;
  if (amount >= 100_000) return `₹${(amount / 100_000).toFixed(2)}L`;
  if (amount >= 1000) return `₹${(amount / 1000).toFixed(1)}K`;
  return `₹${amount.toLocaleString('en-IN')}`;
}

// ₹1,23,456.78 — for statutory figures, where an abbreviated ₹1.23L hides the paise
export function formatINRExact(amount: number): string {
  return `₹${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function AmountDisplay({ amount, className = '', exact = false }: Props) {
  if (amount == null) return <span className="text-gray-500">—</span>;
  return (
    <span className={`font-mono ${className}`} title={formatINRExact(amount)}>
      {exact ? formatINRExact(amount) : formatINR(amount)}
    </span>
  );
}
