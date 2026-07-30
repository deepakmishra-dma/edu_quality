import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Link } from "react-router-dom";
import PanelState from "@/components/ui/DashboardStates";
import { useClassDistribution } from "@/api/useAdmissionsDashboard";

interface ClassDivisionGridProps {
  academicYear?: string;
}

interface CombinedCellProps {
  target: number;
  admission: number;
}

const CombinedCell: React.FC<CombinedCellProps> = ({
  target,
  admission,
}): JSX.Element => (
  <td className="p-2 border text-center">
    <div className="flex flex-col">
      <span className="font-medium text-gray-800">{target}</span>
      <span
        className={`text-sm ${
          admission < 0 ? "text-red-600" : "text-blue-600"
        }`}
      >
        {admission}
      </span>
    </div>
  </td>
);

const ClassDivisionGrid: React.FC<ClassDivisionGridProps> = ({
  academicYear,
}) => {
  const { data, isLoading, error } = useClassDistribution(academicYear);
  const isPending = isLoading || !academicYear;

  const columns = data?.classes ?? [];
  const rows = data?.rows ?? [];

  const columnTotal = (
    field: "target" | "admissions",
    key: string
  ): number => rows.reduce((sum, row) => sum + (row[field][key] ?? 0), 0);

  return (
    <Card className="w-[98%]">
      <div className="w-full flex justify-between items-center p-4">
        <div>
          <h2 className="text-xl font-bold text-gray-800">
            Class-wise Distribution
          </h2>
          <h3 className="text-sm text-gray-600">(Target/Admissions)</h3>
        </div>
        <Link
          to="/dashboard/detailed"
          className="px-4 py-2 bg-blue-500 text-white font-medium rounded-lg hover:bg-blue-600 transition duration-200"
        >
          Detailed View
        </Link>
      </div>

      <CardContent>
        <PanelState
          isLoading={isPending}
          error={error}
          isEmpty={!rows.length}
          emptyMessage="No branches have a location set on their School record."
        />
        {rows.length > 0 && (
          <div className="w-full overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-gray-50">
                  <th className="p-2 border">Location</th>
                  {columns.map((col) => (
                    <th key={col.key} className="p-2 border">
                      {col.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.location} className="hover:bg-gray-50">
                    <td className="p-2 border font-medium bg-pink-100">
                      {row.location}
                    </td>
                    {columns.map((col) => (
                      <CombinedCell
                        key={col.key}
                        target={row.target[col.key] ?? 0}
                        admission={row.admissions[col.key] ?? 0}
                      />
                    ))}
                  </tr>
                ))}
                <tr className="bg-gray-100 font-medium">
                  <td className="p-2 border">Total</td>
                  {columns.map((col) => (
                    <CombinedCell
                      key={col.key}
                      target={columnTotal("target", col.key)}
                      admission={columnTotal("admissions", col.key)}
                    />
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ClassDivisionGrid;
