import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import PanelState from "@/components/ui/DashboardStates";
import { useBranchReport, type Branch } from "@/api/useAdmissionsDashboard";

interface BranchReportProps {
  academicYear?: string;
}

// Branches come from the database, so colours are assigned by position.
const BRANCH_COLORS = ["#4F46E5", "#059669", "#DC2626", "#D97706", "#0891B2"];

const StatTile = ({
  label,
  value,
  color,
}: {
  label: string;
  value: string | number;
  color: string;
}) => (
  <div className="px-4 py-2 bg-white rounded-lg shadow">
    <div className="text-gray-600">{label}</div>
    <div className="text-xl font-bold" style={{ color }}>
      {value}
    </div>
  </div>
);

const BranchSection = ({
  branch,
  color,
}: {
  branch: Branch;
  color: string;
}) => (
  <Card className="w-full mb-8 shadow-lg">
    <CardHeader className="border-b" style={{ backgroundColor: `${color}15` }}>
      <CardTitle className="flex items-center justify-between">
        <span className="text-2xl font-bold" style={{ color }}>
          {branch.location}
        </span>
        <div className="flex gap-4 text-sm">
          <StatTile
            label="Total Enquiries"
            value={branch.stats.total_enquiries}
            color={color}
          />
          <StatTile
            label="Total Admissions"
            value={branch.stats.total_admissions}
            color={color}
          />
          <StatTile
            label="Conversion Rate"
            value={`${branch.stats.conversion_rate.toFixed(1)}%`}
            color={color}
          />
          <StatTile
            label="Peak Month"
            value={branch.stats.peak_month}
            color={color}
          />
        </div>
      </CardTitle>
    </CardHeader>
    <CardContent className="p-6">
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="p-3 text-left font-semibold">Month</th>
              <th className="p-3 text-left font-semibold">Enquiries</th>
              <th className="p-3 text-left font-semibold">Admissions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {branch.months.map((row) => (
              <tr key={row.month} className="hover:bg-gray-50">
                <td className="p-3">{row.label}</td>
                <td className="p-3">{row.enquiries}</td>
                <td className="p-3">{row.admissions}</td>
              </tr>
            ))}
            {!branch.months.length && (
              <tr>
                <td className="p-3 text-gray-500" colSpan={3}>
                  No enquiries or admissions recorded for this year.
                </td>
              </tr>
            )}
            <tr className="font-bold bg-gray-50">
              <td className="p-3">Total</td>
              <td className="p-3">{branch.stats.total_enquiries}</td>
              <td className="p-3">{branch.stats.total_admissions}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </CardContent>
  </Card>
);

const BranchReport = ({ academicYear }: BranchReportProps) => {
  const { data, isLoading, error } = useBranchReport(academicYear);
  const branches = data?.branches ?? [];

  return (
    <Card className="w-[98%]">
      <CardHeader>
        <CardTitle>Branch-wise Report</CardTitle>
      </CardHeader>
      <CardContent>
        <PanelState
          isLoading={isLoading}
          error={error}
          isEmpty={!branches.length}
          emptyMessage="No branches have a location set on their School record."
        />
        <div className="space-y-8">
          {branches.map((branch, index) => (
            <BranchSection
              key={branch.location}
              branch={branch}
              color={BRANCH_COLORS[index % BRANCH_COLORS.length]}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default BranchReport;
