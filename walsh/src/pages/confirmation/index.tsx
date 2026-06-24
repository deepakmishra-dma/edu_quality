import React, { useState } from "react";
import { Button, Flex, Stack, Text, Title } from "@mantine/core";
import useNoticeOtpVerification from "../../components/queries/useNoticeOtpVerification";

interface OtpComponentProps {
  onClose: () => void;
  setHideButtons: (hide: boolean) => void;
  approve: boolean;
  studentId: string;
  noticeId: string;
}

const OtpComponent: React.FC<OtpComponentProps> = ({
  onClose,
  setHideButtons,
  approve,
  studentId,
  noticeId,
}) => {
  const [otp, setOtp] = useState<string[]>(["", "", "", ""]);
  const [error, setError] = useState<string | null>(null);

  const { mutate: verifyOtp, isLoading } = useNoticeOtpVerification();

  const handleChange = (value: string, index: number) => {
    if (/^[0-9]*$/.test(value) && value.length <= 1) {
      const newOtp = [...otp];
      newOtp[index] = value;
      setOtp(newOtp);
      setError(null);
      if (value && index < 3) {
        const nextInput = document.getElementById(`otp-${index + 1}`);
        if (nextInput) nextInput.focus();
      }
    }
  };

  const handleKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement>,
    index: number
  ) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      const prevInput = document.getElementById(`otp-${index - 1}`);
      if (prevInput) {
        prevInput.focus();
        const newOtp = [...otp];
        newOtp[index - 1] = "";
        setOtp(newOtp);
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const otpString = otp.join("");
    if (otpString.length === 4) {
      verifyOtp(
        {
          id: noticeId,
          student: studentId,
          otp: otpString,
          approve,
        },
        {
          onSuccess: (data) => {
            if (data.message.success) {
              onClose();
              setHideButtons(true);
            } else {
              setError(data.message.text || "OTP verification failed.");
            }
          },
          onError: (error) => {
            setError(error.message || "An error occurred while verifying OTP.");
          },
        }
      );
    } else {
      setError("Please complete all OTP fields.");
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        maxWidth: "400px",
        margin: "auto",
        padding: "30px",
        border: "1px solid #e9ecef",
        borderRadius: "12px",
        boxShadow: "0 4px 16px rgba(0, 0, 0, 0.1)",
        backgroundColor: "white",
      }}
    >
      <Stack spacing="lg">
        <Flex direction="column" align="center">
          <Title order={4} align="center" color="gray.7" mb={8}>
            Verify Your Account
          </Title>
          <Text size="sm" color="gray.6" align="center" px="md">
            Enter the 4-digit OTP sent to your email to confirm your identity.
          </Text>
        </Flex>

        <Flex justify="center" gap="md">
          {otp.map((digit, index) => (
            <input
              key={index}
              id={`otp-${index}`}
              type="text"
              value={digit}
              maxLength={1}
              onChange={(e) => handleChange(e.target.value, index)}
              onKeyDown={(e) => handleKeyDown(e, index)}
              disabled={isLoading}
              style={{
                width: "40px",
                height: "40px",
                textAlign: "center",
                fontSize: "1.5rem",
                border: "1px solid #ced4da",
                borderRadius: "4px",
              }}
            />
          ))}
        </Flex>

        {error && (
          <Text size="sm" color="red" align="center">
            {error}
          </Text>
        )}

        <Flex justify="space-between" mt="md">
          <Button
            variant="outline"
            color="gray"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button type="submit" color="blue" loading={isLoading}>
            Verify
          </Button>
        </Flex>
      </Stack>
    </form>
  );
};

export default OtpComponent;
