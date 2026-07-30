import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import PanelState from "@/components/ui/DashboardStates";
import {
  useAdmissionDetail,
  useDashboardMeta,
  type MatrixRow,
} from "@/api/useAdmissionsDashboard";

const TAB_ADMISSIONS = "Admissions";
const TAB_WAITING_LIST = "Waiting List";
const TABS = [TAB_WAITING_LIST, TAB_ADMISSIONS];

const AdmissionsDashboard = () => {
  const { data: meta } = useDashboardMeta();
  const [academicYear, setAcademicYear] = useState<string | undefined>();
  const [location, setLocation] = useState<string | undefined>();
  const [selectedTab, setSelectedTab] = useState(TAB_ADMISSIONS);

  // Open on the year currently in progress, not whatever sorts newest.
  useEffect(() => {
    if (!academicYear && meta?.academic_years?.length) {
      setAcademicYear(meta.default_academic_year ?? meta.academic_years[0]);
    }
    if (!location && meta?.locations?.length) {
      setLocation(meta.locations[0]);
    }
  }, [meta, academicYear, location]);

  const { data, isLoading, error } = useAdmissionDetail(academicYear, location);

  const columns = data?.columns ?? [];
  const currentData: MatrixRow[] =
    selectedTab === TAB_ADMISSIONS
      ? data?.admissions ?? []
      : data?.waiting_list ?? [];

  const renderTable = (
    rows: MatrixRow[],
    isStatsTable: boolean = false
  ): JSX.Element => (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow className="bg-gray-50">
            <TableHead className="w-[200px]">
              {isStatsTable ? "Metric" : "Date"}
            </TableHead>
            {columns.map((col) => (
              <TableHead key={col} className="text-center w-[60px] py-3">
                {col}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row, index) => (
            <TableRow
              key={row.name}
              className={index % 2 === 0 ? "bg-gray-50" : ""}
            >
              <TableCell className="font-medium py-3">{row.name}</TableCell>
              {row.data.map((value, i) => (
                <TableCell
                  key={i}
                  className={`${
                    typeof value === "number" && value > 0 ? "font-semibold" : ""
                  } text-center py-3`}
                >
                  {typeof value === "number"
                    ? Number.isInteger(value)
                      ? value
                      : value.toFixed(1)
                    : value}
                </TableCell>
              ))}
            </TableRow>
          ))}
          {!rows.length && (
            <TableRow>
              <TableCell
                className="py-6 text-center text-gray-500"
                colSpan={columns.length + 1}
              >
                Nothing recorded for this branch and year.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );

  return (
    <div className="w-full bg-gray-50 flex justify-center items-center">
      <Card className="max-w-[1960px] w-full">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="text-4xl">
            {location || "Select Branch"}
          </CardTitle>
          <div className="flex gap-4">
            <Select value={academicYear} onValueChange={setAcademicYear}>
              <SelectTrigger className="w-[180px]">
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
            <Select value={location} onValueChange={setLocation}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Select Branch" />
              </SelectTrigger>
              <SelectContent>
                {(meta?.locations ?? []).map((branch) => (
                  <SelectItem key={branch} value={branch}>
                    {branch}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>

        <CardContent>
          <PanelState isLoading={isLoading} error={error} />
        </CardContent>

        {!isLoading && !error && (
          <Tabs
            value={selectedTab}
            onValueChange={setSelectedTab}
            className="w-full"
          >
            <TabsList className="mb-4 mx-6">
              {TABS.map((type) => (
                <TabsTrigger key={type} value={type} className="px-8">
                  {type}
                </TabsTrigger>
              ))}
            </TabsList>

            {TABS.map((type) => (
              <TabsContent key={type} value={type} className="m-0">
                <CardContent className="space-y-6">
                  {type === TAB_ADMISSIONS && (
                    <>
                      <div className="flex flex-col gap-4">
                        {renderTable(data?.stats ?? [], true)}
                      </div>
                      <h1 className="text-3xl font-semibold text-gray-800">
                        Date-wise Admissions
                      </h1>
                    </>
                  )}
                  {type === TAB_WAITING_LIST && (
                    <h1 className="text-3xl font-semibold text-gray-800">
                      Date-wise Waiting List
                    </h1>
                  )}
                  <div className="flex flex-col gap-4">
                    {renderTable(currentData)}
                  </div>
                </CardContent>
              </TabsContent>
            ))}
          </Tabs>
        )}
      </Card>
    </div>
  );
};

export default AdmissionsDashboard;
