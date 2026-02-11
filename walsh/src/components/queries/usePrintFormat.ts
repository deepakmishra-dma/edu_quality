import { BaseRecord, useCustom } from "@refinedev/core";

export interface AsessmentGroupData extends BaseRecord {
  result_print_format: string | null;
  custom_print_configuration: string | null;
}

const usePrintFormat = (assessment_group: string) => {
  return useCustom<AsessmentGroupData>({
    config: {
      query: {
        name: assessment_group,
      },
    },

    errorNotification: {
      message: "Failed to get list {{ resourceName }}",
      type: "error",
    },
    method: "get",
    queryOptions: {
      queryKey: ["assessment_group", "data", assessment_group],
      enabled: !!assessment_group,
    },
    successNotification: undefined,
    url: `/api/resource/Assessment Group/${assessment_group}`,
  });
};

export default usePrintFormat;
