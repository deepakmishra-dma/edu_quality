import { useQuery } from "@tanstack/react-query";
import axios from "axios";

interface School {
  name: string;
}

interface Program {
  program_name: string;
}

interface SchoolResponse {
  message: { data: School[] };
  error?: {
    error_type: string;
    error_message: string;
  };
}

interface ProgramResponse {
  message: { data: Program[] };
  error?: {
    error_type: string;
    error_message: string;
  };
}

export const useGetSchools = () => {
  const schoolsQuery = useQuery<SchoolResponse>({
    queryKey: ["schools"],
    queryFn: async () => {
      const response = await axios.get(
        "/api/method/edu_quality.public.py.walsh.login.get_schools_for_guest"
      );
      return response.data;
    },
  });

  return {
    schools: schoolsQuery.data?.message ?? { data: [] },
    isLoading: schoolsQuery.isLoading,
    error: schoolsQuery.error,
  };
};

export const useGetPrograms = (selectedSchool?: string) => {
  const programsQuery = useQuery<ProgramResponse>({
    queryKey: ["programs", selectedSchool],
    queryFn: async () => {
      const response = await axios.get(
        "/api/method/edu_quality.public.py.walsh.login.get_programs_for_guest",
        {
          params: { school: selectedSchool },
        }
      );
      return response.data;
    },
    enabled: !!selectedSchool,
  });

  return {
    programs: programsQuery.data?.message ?? { data: [] },
    isLoading: programsQuery.isLoading,
    error: programsQuery.error,
  };
};
