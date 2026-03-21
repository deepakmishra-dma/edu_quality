import { useCustomMutation } from "@refinedev/core";
import { useCallback } from "react";

interface LeaveNoteVariables {
  note: string;
  status: "sick" | "leave";
  student: string;
  end_date: string;
  start_date: string;
  dates: string[];
  program: string;
}

const useLeaveNote = () => {
  const { mutate, mutateAsync, ...mutationObjs } = useCustomMutation({
    mutationOptions: {},
  });
  const mutationFunction = useCallback(
    (variables: LeaveNoteVariables) => {
      return mutate({
        url: "/api/method/edu_quality.public.py.walsh.leave.add_leave_note",
        method: "post",
        values: variables,
      });
    },
    [mutate]
  );
  const mutationAsyncFunction = useCallback(
    (variables: LeaveNoteVariables) => {
      return mutateAsync({
        url: "/api/method/edu_quality.public.py.walsh.leave.add_leave_note",
        method: "post",
        values: variables,
      });
    },
    [mutateAsync]
  );
  return {
    ...mutationObjs,
    mutate: mutationFunction,
    mutateAsync: mutationAsyncFunction,
  };
};

export default useLeaveNote;
