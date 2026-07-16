import { useForm } from "@refinedev/mantine";
import { LOGIN_FORM } from "../components/forms";
import {
  Box,
  Button,
  Flex,
  Image,
  Stack,
  Text,
  TextInput,
  SegmentedControl,
} from "@mantine/core";
import { useEffect, useMemo, useState } from "react";
import { OtpInput } from "../components";
import { useLogin } from "@refinedev/core";
import { IconReload } from "@tabler/icons";
import { Link } from "react-router-dom";

export const Login = () => {
  const { mutateAsync, isLoading } = useLogin();
  const [mode, setMode] = useState<"main" | "otp">("main");
  const [loginType, setLoginType] = useState<"phone" | "email">("phone");
  const [errorMessage, setErrorMessage] = useState("");
  const [otpMessage, setOtpMessage] = useState("");
  const [sendingOtp, setSendingOtp] = useState(false);
  const { getInputProps, values, setValues, onSubmit } = useForm({
    ...LOGIN_FORM,
    initialValues: {
      ...LOGIN_FORM.initialValues,
      email: "",
    },
  });

  const handleSubmit = useMemo(
    () =>
      onSubmit((values) => {
        if (isLoading || sendingOtp) return;

        if (mode == "otp") {
          mutateAsync({
            [loginType === "email" ? "email" : "phone"]:
              loginType === "email" ? values.email : values.mobile_number,
            otp: values.otp,
          })
            .then((r) => r.json())
            .then((data) => {
              if (data.message.success) {
                setMode("main");
                setErrorMessage("");
              } else setErrorMessage(data.message.error_message);
            });
          return;
        }
        setSendingOtp(true);
        const myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");
        fetch("/api/method/edu_quality.public.py.walsh.login.send_otp", {
          method: "POST",
          headers: myHeaders,
          body: JSON.stringify({
            [loginType === "email" ? "email" : "phone_no"]:
              loginType === "email" ? values.email : values.mobile_number,
          }),
          redirect: "follow",
        })
          .then((response) => response.json())
          .then((result) => result.message)
          .then((message) => {
            if (message.success) {
              setMode("otp");
              setErrorMessage("");
              setOtpMessage(message.message);
            } else setErrorMessage(message.error_message);
          })
          .catch((error) => console.log("error", error))
          .finally(() => {
            setSendingOtp(false);
          });
      }),
    [isLoading, mode, mutateAsync, onSubmit, sendingOtp, loginType]
  );

  useEffect(() => {
    setErrorMessage("");
    setOtpMessage("");
  }, [values.mobile_number, values.email]);

  return (
    <>
      <Box
        sx={{
          height: "10%",
        }}
      />
      <Stack
        align="center"
        pt={50}
        mih={400}
        bg={"gray.0"}
        sx={{
          padding: 40,
        }}
      >
        <form
          onSubmit={handleSubmit}
          style={{
            width: "80vw",
            maxWidth: 400,
          }}
        >
          <Flex justify={"center"}>
            <Image
              radius={"lg"}
              width={160}
              src="/assets/edu_quality/walsh/images/logo.png"
            />
          </Flex>
          <Stack spacing={2} mt={12} mb={8} align="center">
            <Text
              size={"lg"}
              sx={{
                fontSize: 20,
              }}
              weight={700}
              c="primary.5"
            >
              {mode !== "otp" ? "Welcome" : "Enter OTP"}
            </Text>
            {mode !== "otp" ? (
              <>
                <Text
                  size={"sm"}
                  sx={{
                    fontSize: 14,
                    color: "#565766",
                    marginTop: 10,
                    marginBottom: 10,
                  }}
                  align="center"
                >
                  If you are already a parent <br /> Log in below
                </Text>
                <SegmentedControl
                  value={loginType}
                  onChange={(value: "phone" | "email") => setLoginType(value)}
                  data={[
                    { label: "Phone", value: "phone" },
                    { label: "Email", value: "email" },
                  ]}
                />
              </>
            ) : (
              <Text size={"sm"}>
                {loginType === "email" ? "Email" : "Phone No"}:{" "}
                {loginType === "email" ? values.email : values.mobile_number}
              </Text>
            )}
          </Stack>
          <Stack spacing={12}>
            {mode !== "otp" ? (
              loginType === "phone" ? (
                <TextInput
                  variant="filled"
                  sx={{
                    ".mantine-Input-input": {
                      letterSpacing: 2,
                      borderRadius: 8,
                      border: "1px solid rgba(0,0,0,0.1)",
                      fontSize: 20,
                      "::placeholder": {
                        letterSpacing: 0,
                        textAlign: "center",
                      },
                    },
                  }}
                  placeholder="Enter Mobile Number"
                  {...getInputProps("mobile_number")}
                  onChange={(event) => {
                    const value = event.target.value;
                    const phoneNumberIncompleteRegix = /^\+?[0-9]*$/;
                    if (!phoneNumberIncompleteRegix.test(value)) return;
                    setValues({
                      ...values,
                      mobile_number: event.target.value,
                    });
                  }}
                />
              ) : (
                <TextInput
                  variant="filled"
                  sx={{
                    ".mantine-Input-input": {
                      letterSpacing: 2,
                      borderRadius: 8,
                      border: "1px solid rgba(0,0,0,0.1)",
                      fontSize: 20,
                      "::placeholder": {
                        letterSpacing: 0,
                        textAlign: "center",
                      },
                    },
                  }}
                  placeholder="Enter Email"
                  {...getInputProps("email")}
                />
              )
            ) : (
              <Flex
                justify="center"
                sx={{
                  marginTop: 20,
                }}
              >
                <OtpInput style={{ width: "100%" }} {...getInputProps("otp")} />
              </Flex>
            )}
            {errorMessage && (
              <Text color={"red"} size={"sm"} align={"center"}>
                {errorMessage}
              </Text>
            )}
            {otpMessage && (
              <Text color={"green"} size={"sm"} align={"center"}>
                {otpMessage}
              </Text>
            )}
            <Button
              type="submit"
              sx={{
                backgroundColor: "#1E6967",
                marginTop: 10,
                ":hover": {
                  backgroundColor: "#1E6967",
                  opacity: 0.8,
                },
              }}
            >
              {mode !== "otp" ? "Get OTP" : "Submit OTP"}
            </Button>

            <Flex
              direction={"column"}
              align={"center"}
              sx={{
                textAlign: "center",
              }}
            >
              <Button
                sx={{
                  backgroundColor: "transparent",
                  color: "#1E6967",
                  width: "fit-content",
                  ":hover": {
                    backgroundColor: "transparent",
                  },
                  ":active": {
                    backgroundColor: "transparent",
                  },
                }}
                onClick={() => window.location.reload()}
              >
                Reload
                <IconReload
                  size={15}
                  style={{
                    marginLeft: 5,
                  }}
                />
              </Button>
              {mode !== "otp" && (
                <Button
                  component={Link}
                  to="/register"
                  sx={{
                    backgroundColor: "transparent",
                    color: "#1E6967",
                    width: "fit-content",
                    ":hover": {
                      backgroundColor: "transparent",
                    },
                    ":active": {
                      backgroundColor: "transparent",
                    },
                  }}
                >
                  Don't Have an Account ? Register Now
                </Button>
              )}
            </Flex>

            {mode === "otp" ? (
              <Text
                align="center"
                sx={{
                  fontSize: 14,
                  color: "#000",
                  textDecoration: "underline",
                }}
                onClick={() => {
                  setMode("main");
                  setOtpMessage("");
                  setErrorMessage("");
                }}
              >
                Resend OTP
              </Text>
            ) : null}
          </Stack>
        </form>
      </Stack>
    </>
  );
};
