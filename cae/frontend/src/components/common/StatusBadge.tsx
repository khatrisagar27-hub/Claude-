const classes: Record<string, string> = {
  open: 'bg-blue-900/40 text-blue-400 border border-blue-800/50',
  acknowledged: 'bg-purple-900/40 text-purple-400 border border-purple-800/50',
  query_raised: 'bg-yellow-900/40 text-yellow-400 border border-yellow-800/50',
  escalated: 'bg-red-900/40 text-red-400 border border-red-800/50',
  resolved: 'bg-green-900/40 text-green-400 border border-green-800/50',
  closed: 'bg-gray-800 text-gray-500 border border-gray-700',
  pending: 'bg-yellow-900/40 text-yellow-400 border border-yellow-800/50',
  responded: 'bg-cyan-900/40 text-cyan-400 border border-cyan-800/50',
};

export default function StatusBadge({ status }: { status: string }) {
  const cls = classes[status?.toLowerCase()] || classes.closed;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {status?.replace('_', ' ').toUpperCase()}
    </span>
  );
}
