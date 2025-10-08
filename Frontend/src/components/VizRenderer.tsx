import { VizSpec } from '../types/ocean';

interface VizRendererProps {
  vizSpec?: VizSpec;
  rows?: any[];
  settings?: {
    reverseDepthAxis: boolean;
    units: string;
  };
}

function hasFields(rows: any[], fields: string[] = []): boolean {
  if (!rows?.length) return false;
  const cols = Object.keys(rows[0] || {});
  return fields.every(f => cols.includes(f));
}

export function VizRenderer({ vizSpec, rows }: VizRendererProps) {
  if (!vizSpec || !rows?.length) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <p className="text-gray-500 text-center">No visualization data available</p>
      </div>
    );
  }

  const { viz_type, title, fields_required } = vizSpec;

  if (fields_required && !hasFields(rows, fields_required)) {
    return <TableView rows={rows} />;
  }

  // For now, show a simple visualization placeholder
  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">
        {title || 'Ocean Data Visualization'}
      </h3>
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4">
        <div className="flex">
          <div className="ml-3">
            <p className="text-sm text-blue-700">
              {viz_type === 'profile_plot' && 'Temperature/Salinity profile visualization'}
              {viz_type === 'ts_diagram' && 'Temperature-Salinity diagram'}
              {viz_type === 'time_series_point' && 'Time series data visualization'}
              {viz_type === 'trajectory_map' && 'Float trajectory map'}
              {!viz_type && 'Ocean data visualization'}
            </p>
          </div>
        </div>
      </div>
      <TableView rows={rows} />
    </div>
  );
}

function TableView({ rows }: { rows: any[] }) {
  if (!rows?.length) return null;
  
  const cols = Object.keys(rows[0]);
  const displayRows = rows.slice(0, 10); // Limit display for performance
  
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {cols.map(col => (
                <th key={col} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {col.replace(/_/g, ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {displayRows.map((row, i) => (
              <tr key={i} className="hover:bg-gray-50">
                {cols.map((col, j) => (
                  <td key={j} className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                    {typeof row[col] === 'number' ? row[col].toFixed(3) : String(row[col])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > 10 && (
        <div className="px-4 py-3 bg-gray-50 text-sm text-gray-500">
          Showing 10 of {rows.length} rows
        </div>
      )}
    </div>
  );
}