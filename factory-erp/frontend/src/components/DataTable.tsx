interface Column<T> {
  header: string;
  render: (row: T) => React.ReactNode;
  align?: "left" | "right";
}

interface DataTableProps<T> {
  rows: T[];
  columns: Column<T>[];
  keyFn: (row: T) => string;
  emptyMessage?: string;
}

export function DataTable<T>({ rows, columns, keyFn, emptyMessage = "No data yet." }: DataTableProps<T>) {
  if (rows.length === 0) {
    return <div className="p-4 text-sm text-slate-400">{emptyMessage}</div>;
  }
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-slate-500">
          {columns.map((c) => (
            <th key={c.header} className={`px-4 py-2 ${c.align === "right" ? "text-right" : ""}`}>
              {c.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={keyFn(row)} className="border-t border-slate-100">
            {columns.map((c) => (
              <td key={c.header} className={`px-4 py-2 ${c.align === "right" ? "text-right" : ""}`}>
                {c.render(row)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
