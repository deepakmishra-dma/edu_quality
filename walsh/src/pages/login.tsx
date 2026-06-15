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
} from "@mantine/core";
import { useState } from "react";
import { useLogin } from "@refinedev/core";

export const Login = () => {
  const { mutateAsync: loginMutateAsync, isLoading } = useLogin();
  const [errorMessage, setErrorMessage] = useState("");
  const { getInputProps, values, setValues, onSubmit } = useForm(LOGIN_FORM);
  const [forgotPassword, setForgotPassword] = useState(false);
  const [sendingResetMail, setSendingResetMail] = useState(false);

  const handleLogin = (values: { username: string; password: string }) => {
    if (isLoading) return;
    loginMutateAsync({
      username: values.username,
      password: values.password,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.message.success) {
          setErrorMessage("");
        } else {
          setErrorMessage(data.message.error_message);
        }
      })
      .catch((error) => {
        console.error("Login error:", error);
        setErrorMessage("An error occurred. Please try again.");
      });
  };

  const handleForgotPassword = (email: string) => {
    if (sendingResetMail) return;

    setSendingResetMail(true);
    fetch("/api/method/frappe.core.doctype.user.user.reset_password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        cmd: "frappe.core.doctype.user.user.reset_password",
        user: email,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log(data);
        if (data._server_messages) {
          setErrorMessage("Password reset email sent successfully!");
        } else {
          setErrorMessage("Error resetting password.");
        }
      })
      .catch((error) => {
        console.error("Forgot password error:", error);
        setErrorMessage("An error occurred. Please try again.");
      })
      .finally(() => {
        setSendingResetMail(false);
      });
  };

  const handleSubmit = onSubmit((values) => {
    if (forgotPassword) {
      handleForgotPassword(values.username);
    } else {
      handleLogin(values);
    }
  });

  const handleToggleForgotPassword = () => {
    setForgotPassword((prev) => !prev);
    setErrorMessage("");
  };

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
              src="/assets/edu_quality/walsh/images/tgaa_logo.jpg"
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
              {!forgotPassword ? "Welcome" : "Forgot Password"}
            </Text>
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
              {!forgotPassword
                ? "Please log in to continue."
                : "Please enter your email to reset the password"}
            </Text>
          </Stack>
          <Stack spacing={12}>
            <TextInput
              type="text"
              variant="filled"
              sx={{
                ".mantine-Input-input": {
                  letterSpacing: 2,
                  borderRadius: 8,
                  border: "1px solid rgba(0,0,0,0.1)",
                  fontSize: 16,
                  "::placeholder": {
                    letterSpacing: 0,
                  },
                },
              }}
              placeholder={
                !forgotPassword ? "Enter username/email" : "Enter email"
              }
              {...getInputProps("username")}
              onChange={(event) => {
                setValues({
                  ...values,
                  username: event.target.value,
                });
              }}
            />
            {!forgotPassword && (
              <TextInput
                type="password"
                variant="filled"
                sx={{
                  ".mantine-Input-input": {
                    letterSpacing: 2,
                    borderRadius: 8,
                    border: "1px solid rgba(0,0,0,0.1)",
                    fontSize: 16,
                    "::placeholder": {
                      letterSpacing: 0,
                    },
                  },
                }}
                placeholder="Enter password"
                {...getInputProps("password")}
                onChange={(event) => {
                  setValues({
                    ...values,
                    password: event.target.value,
                  });
                }}
              />
            )}
            {errorMessage && (
              <Text
                color={errorMessage.includes("successfully") ? "green" : "red"}
                size={"sm"}
                align={"center"}
              >
                {errorMessage}
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
              {!forgotPassword ? "Log In" : "Reset"}
            </Button>
            <Button
              variant="subtle"
              sx={{
                color: "#03aaf1",
                width: "fit-content",
                margin: "auto",
                ":hover": {
                  backgroundColor: "transparent",
                  textDecoration: "underline",
                },
              }}
              onClick={handleToggleForgotPassword}
            >
              {!forgotPassword ? "Forgot Password?" : "Back to login"}
            </Button>
          </Stack>
        </form>
      </Stack>
      {/* <Box
        pos="fixed"
        bottom={0}
        left={0}
        right={0}
        style={{
          pointerEvents: "none",
        }}
      >
        <Image
          src={"/assets/edu_quality/walsh/images/walnut-bg-transparent.png"}
          w={"100%"}
        />
      </Box> */}
    </>
  );
};
