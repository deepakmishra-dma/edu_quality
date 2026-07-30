import { useQuery } from "@tanstack/react-query";
import axiosInstance from "@/utility/axiosInstance";

const BASE = "/api/method/edu_quality.api.admissions_dashboard";
const STALE_TIME = 5 * 60 * 1000;

async function callDashboard<T>(
  method: string,
  params?: Record<string, string | undefined>
): Promise<T> {
  const response = await axiosInstance.get(`${BASE}.${method}`, { params });
  return response.data.message as T;
}

export interface ClassColumn {
  key: string;
  label: string;
  short: string;
}

export interface DashboardMeta {
  academic_years: string[];
  /** The year in progress today, when one of them is. */
  default_academic_year: string | null;
  locations: string[];
  classes: ClassColumn[];
}

export interface StrengthRow {
  location: string;
  is_total?: boolean;
  target: number | null;
  balance: number | null;
  strength_current: number;
  strength_previous: number;
  new_admissions: number;
  admission_percent: number;
  cancelled: number;
  cancelled_percent: number;
  added_students: number;
  added_percent: number;
  enquiries: number;
  convert_percent: number;
  capacity: number;
  full_percent: number;
}

export interface StrengthAnalysis {
  academic_year: string;
  previous_academic_year: string | null;
  rows: StrengthRow[];
}

export interface ClassDistributionRow {
  location: string;
  target: Record<string, number>;
  admissions: Record<string, number>;
}

export interface ClassDistribution {
  academic_year: string;
  classes: ClassColumn[];
  rows: ClassDistributionRow[];
}

export interface BranchMonth {
  month: string;
  label: string;
  enquiries: number;
  admissions: number;
}

export interface Branch {
  location: string;
  months: BranchMonth[];
  stats: {
    total_enquiries: number;
    total_admissions: number;
    conversion_rate: number;
    peak_month: string;
  };
}

export interface BranchReport {
  academic_year: string;
  branches: Branch[];
}

export interface MatrixRow {
  name: string;
  data: number[];
}

export interface AdmissionDetail {
  academic_year: string;
  previous_academic_year: string | null;
  location: string;
  locations: string[];
  columns: string[];
  stats: MatrixRow[];
  admissions: MatrixRow[];
  waiting_list: MatrixRow[];
}

export const useDashboardMeta = () =>
  useQuery<DashboardMeta, Error>({
    queryKey: ["admissions-dashboard", "meta"],
    queryFn: () => callDashboard<DashboardMeta>("get_dashboard_meta"),
    staleTime: STALE_TIME,
  });

export const useStrengthAnalysis = (academicYear?: string) =>
  useQuery<StrengthAnalysis, Error>({
    queryKey: ["admissions-dashboard", "strength", academicYear],
    queryFn: () =>
      callDashboard<StrengthAnalysis>("get_strength_analysis", {
        academic_year: academicYear,
      }),
    enabled: Boolean(academicYear),
    staleTime: STALE_TIME,
  });

export const useClassDistribution = (academicYear?: string) =>
  useQuery<ClassDistribution, Error>({
    queryKey: ["admissions-dashboard", "class-distribution", academicYear],
    queryFn: () =>
      callDashboard<ClassDistribution>("get_class_distribution", {
        academic_year: academicYear,
      }),
    enabled: Boolean(academicYear),
    staleTime: STALE_TIME,
  });

export const useBranchReport = (academicYear?: string) =>
  useQuery<BranchReport, Error>({
    queryKey: ["admissions-dashboard", "branch-report", academicYear],
    queryFn: () =>
      callDashboard<BranchReport>("get_branch_report", {
        academic_year: academicYear,
      }),
    enabled: Boolean(academicYear),
    staleTime: STALE_TIME,
  });

export const useAdmissionDetail = (academicYear?: string, location?: string) =>
  useQuery<AdmissionDetail, Error>({
    queryKey: ["admissions-dashboard", "detail", academicYear, location],
    queryFn: () =>
      callDashboard<AdmissionDetail>("get_admission_detail", {
        academic_year: academicYear,
        location,
      }),
    enabled: Boolean(academicYear),
    staleTime: STALE_TIME,
  });
