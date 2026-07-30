import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import PanelState from "@/components/ui/DashboardStates";
import {
  useStrengthAnalysis,
  type StrengthRow,
} from "@/api/useAdmissionsDashboard";

interface StrengthGridProps {
  academicYear?: string;
}

const PercentCellRenderer: React.FC<{ value: number }> = ({
  value,
}): JSX.Element => {
  const textColor = value < 0 ? "text-red-600" : "text-green-600";
  return <span className={textColor}>{value.toFixed(1)}%</span>;
};

const CapacityCellRenderer: React.FC<{ value: number }> = ({
  value,
}): JSX.Element => (
  <span className="bg-yellow-200 px-2 py-1 rounded">
    {value.toLocaleString()}
  </span>
);

const AddedStudentsCellRenderer: React.FC<{ value: number }> = ({
  value,
}): JSX.Element => {
  const textColor = value < 0 ? "text-red-600" : "text-green-600";
  return (
    <span className={textColor}>
      {value > 0 ? "+" : ""}
      {value}
    </span>
  );
};

/** Targets are optional, so blank out the columns that depend on them. */
const OptionalCell: React.FC<{ value: number | null }> = ({ value }) =>
  value === null || value === undefined ? (
    <span className="text-gray-400">—</span>
  ) : (
    <span>{value.toLocaleString()}</span>
  );

const StrengthGrid: React.FC<StrengthGridProps> = ({ academicYear }) => {
  const { data, isLoading, error } = useStrengthAnalysis(academicYear);

  const currentYear = data?.academic_year ?? "Current";
  const previousYear = data?.previous_academic_year ?? "Previous";
  const rows: StrengthRow[] = data?.rows ?? [];

  const mainColumnGroups = [
    { title: "Base", colspan: 2 },
    { title: "Location", colspan: 1 },
    { title: "Strength", colspan: 2 },
    { title: "Admissions", colspan: 2 },
    { title: "Not Continuing", colspan: 2 },
    { title: "Changes", colspan: 3 },
    { title: "Metrics", colspan: 2 },
  ];

  const subColumnGroups = [
    "Balance",
    "Target",
    "",
    currentYear,
    previousYear,
    "New Admissions",
    "Admission %",
    "Left",
    "Left %",
    "Net",
    "Added %",
    "Convert %",
    "Capacity",
    "Full %",
  ];

  return (
    <Card className="w-[98%] mt-4">
      <CardHeader>
        <CardTitle>Strength Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <PanelState
          isLoading={isLoading}
          error={error}
          isEmpty={!rows.length}
          emptyMessage="No branches have a location set on their School record."
        />
        {rows.length > 0 && (
          <div className="w-full overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-gray-50">
                  {mainColumnGroups.map((group, index: number) => (
                    <th
                      key={index}
                      colSpan={group.colspan}
                      className="p-2 border"
                    >
                      {group.title}
                    </th>
                  ))}
                </tr>
                <tr className="bg-gray-100">
                  {subColumnGroups.map((groupItem: string, index: number) => (
                    <th key={index} className="p-2 border">
                      {groupItem}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr
                    key={row.location}
                    className={`
                    ${index % 2 === 0 ? "bg-white" : "bg-gray-50"}
                    ${row.is_total ? "font-semibold" : ""}
                  `}
                  >
                    <td className="p-2 border">
                      <OptionalCell value={row.balance} />
                    </td>
                    <td className="p-2 border">
                      <OptionalCell value={row.target} />
                    </td>
                    <td className="p-2 border">{row.location}</td>
                    <td className="p-2 border">
                      {row.strength_current.toLocaleString()}
                    </td>
                    <td className="p-2 border">
                      {row.strength_previous.toLocaleString()}
                    </td>
                    <td className="p-2 border">{row.new_admissions}</td>
                    <td className="p-2 border">
                      <PercentCellRenderer value={row.admission_percent} />
                    </td>
                    <td className="p-2 border">{row.cancelled}</td>
                    <td className="p-2 border">
                      <PercentCellRenderer value={row.cancelled_percent} />
                    </td>
                    <td className="p-2 border">
                      <AddedStudentsCellRenderer value={row.added_students} />
                    </td>
                    <td className="p-2 border">
                      <PercentCellRenderer value={row.added_percent} />
                    </td>
                    <td className="p-2 border">
                      <PercentCellRenderer value={row.convert_percent} />
                    </td>
                    <td className="p-2 border">
                      <CapacityCellRenderer value={row.capacity} />
                    </td>
                    <td className="p-2 border">
                      <PercentCellRenderer value={row.full_percent} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default StrengthGrid;
