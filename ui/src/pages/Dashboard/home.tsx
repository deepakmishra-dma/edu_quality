import { useEffect, useState } from "react";
import DataDisplay from "@/components/ui/DataDisplay1";
import CombinedDataDisplay from "@/components/ui/DataDisplay2";
import AcademicDataComponent from "@/components/ui/DataDisplay3";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useDashboardMeta } from "@/api/useAdmissionsDashboard";

function Home() {
  const { data: meta, isLoading, error } = useDashboardMeta();
  const [academicYear, setAcademicYear] = useState<string | undefined>();

  // Open on the year currently in progress, not whatever sorts newest.
  useEffect(() => {
    if (!academicYear && meta?.academic_years?.length) {
      setAcademicYear(meta.default_academic_year ?? meta.academic_years[0]);
    }
  }, [meta, academicYear]);

  return (
    <div className="max-w-[1960px] w-full flex items-center justify-center">
      <div className="w-full flex flex-col items-center justify-center gap-4">
        <div className="w-[98%] flex items-center justify-between pt-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              Admissions MIS
            </h1>
            <p className="text-sm text-gray-600">
              Live figures from enquiries, applications and enrolments.
            </p>
          </div>
          <Select
            value={academicYear}
            onValueChange={setAcademicYear}
            disabled={isLoading || !meta?.academic_years?.length}
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Academic Year" />
            </SelectTrigger>
            <SelectContent>
              {(meta?.academic_years ?? []).map((year) => (
                <SelectItem key={year} value={year}>
                  {year}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {error && (
          <div className="w-[98%] rounded-md border border-red-200 bg-red-50 p-4 text-red-700">
            Could not load the dashboard. {error.message}
          </div>
        )}

        <DataDisplay academicYear={academicYear} />
        <CombinedDataDisplay academicYear={academicYear} />
        <AcademicDataComponent academicYear={academicYear} />
      </div>
    </div>
  );
}

export default Home;
