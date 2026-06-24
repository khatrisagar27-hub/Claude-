import type { Severity } from '../../types';

interface Props {
  severity: Severity | string;
  size?: 'sm' | 'md';
}

const classes: Record<string, string> = {
  critical: 'badge-critical',
  high: 'badge-high',
  medium: 'badge-medium',
  low: 'badge-low',
};

export default function SeverityBadge({ severity, size = 'sm' }: Props) {
  const cls = classes[severity?.toLowerCase()] || 'badge-low';
  return (
    <span className={cls}>
      {severity?.toUpperCase()}
    </span>
  );
}
