interface Props {
  amount?: number | null;
  className?: string;
}

export function formatINR(amount: number): string {
  if (amount >= 10_000_000) return `₹${(amount / 10_000_000).toFixed(2)}Cr`;
  if (amount >= 100_000) return `₹${(amount / 100_000).toFixed(2)}L`;
  if (amount >= 1000) return `₹${(amount / 1000).toFixed(1)}K`;
  return `₹${amount.toLocaleString('en-IN')}`;
}

export default function AmountDisplay({ amount, className = '' }: Props) {
  if (amount == null) return <span className="text-gray-500">—</span>;
  return (
    <span className={`font-mono ${className}`} title={`₹${amount.toLocaleString('en-IN')}`}>
      {formatINR(amount)}
    </span>
  );
}
