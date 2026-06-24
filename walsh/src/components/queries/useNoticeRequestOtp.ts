import { useNotification } from "@refinedev/core";
import { useMutation } from "react-query";

interface RequestOtp {
  id: string;
  student: string;
}

const useRequestOtp = () => {
  const { open } = useNotification();

  return useMutation<{ message: string }, Error, RequestOtp>({
    mutationFn: async ({ id, student }) => {
      const response = await fetch(
        "/api/method/edu_quality.public.py.walsh.notices.request_otp",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ id, student }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to request OTP");
      }

      const data = await response.json();
      return data;
    },
    onSuccess: () => {
      console.log("OTP requested successfully");
    },
    onError: (error) => {
      open?.({
        type: "error",
        message: "OTP Request Failed",
        description: error.message,
      });
    },
  });
};

export default useRequestOtp;