import { useNotification } from "@refinedev/core";
import { useMutation } from "react-query";

interface VerifyOtpRequest {
  id: string;
  student: string;
  otp: string;
  approve: boolean;
}

interface VerifyOtpResponse {
  message: {
    success: boolean;
    text: string;
  };
}

const useNoticeOtpVerification = () => {
  const { open } = useNotification();

  return useMutation<VerifyOtpResponse, Error, VerifyOtpRequest>({
    mutationFn: async ({ id, student, otp, approve }) => {
      const response = await fetch(
        "/api/method/edu_quality.public.py.walsh.notices.verify_otp",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ id, student, otp, approve }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to verify OTP");
      }

      const data = await response.json();
      return data;
    },
    onSuccess: (data) => {
      if (data.message.success) {
        open?.({
          type: "success",
          message: "Notice approved",
          description: data.message.text,
        });
      } else {
        open?.({
          type: "error",
          message: "OTP Verification Failed",
          description: data.message.text,
        });
      }
    },
    onError: (error) => {
      open?.({
        type: "error",
        message: "OTP Verification Error",
        description: error.message,
      });
    },
  });
};

export default useNoticeOtpVerification;
