import { BaseRecord, useCustom } from "@refinedev/core";

export interface SchoolLetterHead extends BaseRecord {
  letter_head: string | null;
}

const useSchoolLetterHead = (school: string) => {
  return useCustom<SchoolLetterHead>({
    config: {
      query: {
        name: school,
      },
    },

    errorNotification: {
      message: "Failed to get list {{ resourceName }}",
      type: "error",
    },
    method: "get",
    queryOptions: {
      queryKey: ["school", "letter_head", school],
      enabled: !!school,
    },
    successNotification: undefined,
    url: `/api/resource/School/${school}?fields=["letter_head"]`,
  });
};

export default useSchoolLetterHead;
