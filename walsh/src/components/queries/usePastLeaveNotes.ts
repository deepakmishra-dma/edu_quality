import { BaseRecord, useCustom } from "@refinedev/core";

export interface LeaveNoteData extends BaseRecord {
  reason: string;
  date: string;
}

const usePastLeaveNotes = (student: string) => {
  return useCustom<{ message: LeaveNoteData[] }>({
    config: {
      query: {
        student,
      },
    },
    errorNotification: {
      message: "Failed to get list {{ resourceName }}",
      type: "error",
    },
    method: "get",
    queryOptions: {
      queryKey: ["past-leave-note", "list", student],
    },
    successNotification: undefined,
    url: "/api/method/edu_quality.public.py.walsh.leave.get_past_pick_ups",
  });
};

export default usePastLeaveNotes;
