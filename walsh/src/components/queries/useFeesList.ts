import { useCustom } from "@refinedev/core";

export interface Fees {
  status: FeesStatus;
  grand_total: number;
  payment_term: string;
  payment_hash: string;
  due_date: string;
  payment_url: string;
  payment_amount: string;
  type: "fees" | "advance";
}

type FeesStatus =
  | "Draft"
  | "Requested"
  | "Initiated"
  | "Partially Paid"
  | "Payment Ordered"
  | "Paid"
  | "Failed"
  | "Cancelled";

const useFeesList = (student: string, academic_year: string | null) => {
  return useCustom<{ message: Fees[] }>({
    config: {
      query: {
        student,
        academic_year,
      },
    },
    errorNotification: undefined,
    method: "get",
    queryOptions: {
      queryKey: ["fees", "list", student, academic_year],
      enabled: !!student,
    },
    successNotification: undefined,
    url: "/api/method/edu_quality.public.py.walsh.fee.get_student_fees",
  });
};

export default useFeesList;
