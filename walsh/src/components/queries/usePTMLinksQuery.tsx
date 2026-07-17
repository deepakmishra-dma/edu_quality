import { useCustom } from "@refinedev/core";

export const usePTMLinksQuery = (selectedStudent: string) => {
  const { data, error, ...rest } = useCustom({
    config: {
      query: {
        student_id: selectedStudent,
      },
    },
    errorNotification: undefined,
    method: "get",
    queryOptions: {
      queryKey: ["onlinePTMList", selectedStudent],
    },
    successNotification: undefined,
    url: `/api/method/edu_quality.cmap_jobs.get_upcoming_online_ptm_links`,
  });
  return {
    data,
    error: error?.response?.data?.exception, // Extract the error message
    ...rest,
  };
};

export const useOfflinePTMLinksQuery = (custom_school: string | undefined) => {
  const { data, error, ...rest } = useCustom({
    config: {
      query: {
        school: custom_school,
      },
    },
    errorNotification: undefined,
    method: "get",
    queryOptions: {
      enabled: !!custom_school,
      queryKey: ["offlinePTMList", custom_school],
    },
    successNotification: undefined,
    url: `/api/method/edu_quality.api.calendar.get_calender_events`,
  });
  return {
    data,
    error: error?.response?.data?.exception, // Extract the error message
    ...rest,
  };
};
