import {useForm} from "@refinedev/mantine";
import {LOGIN_FORM} from "../../components/forms";
import {Box, Button, Flex, Image, Stack, Text, TextInput,} from "@mantine/core";
import {useEffect, useMemo, useState} from "react";
import {OtpInput} from "../../components";
// @ts-expect-error types error
import {IconArrowLeft} from "@tabler/icons";
import {useLogin} from "@refinedev/core";

export const Login = () => {
  const {mutateAsync, isLoading} = useLogin();
  const [mode, setMode] = useState<"main" | "otp">("main");
  const [errorMessage, setErrorMessage] = useState("");
  const [otpMessage, setOtpMessage] = useState("");
  const [sendingOtp, setSendingOtp] = useState(false);
  const {getInputProps, values, setValues, onSubmit} =
    useForm(LOGIN_FORM);

  const handleSubmit = useMemo(
    () => onSubmit((values) => {
      if (isLoading || sendingOtp)
        return
      if (mode == 'otp') {
        mutateAsync({
          phone: values.mobile_number,
          otp: values.otp
        })
          .then(r => r.json())
          .then(data => {
            if (data.message.success) {
              setMode("main")
              setErrorMessage("")
            } else
              setErrorMessage(data.message.error_message)
          })
        return;
      }
      setSendingOtp(true)
      const myHeaders = new Headers();
      myHeaders.append("Content-Type", "application/json");
      fetch("/api/method/edu_quality.public.py.walsh.login.send_otp", {
        method: 'POST',
        headers: myHeaders,
        body: JSON.stringify({
          "phone_no": values.mobile_number
        }),
        redirect: 'follow'
      })
        .then(response => response.json())
        .then(result => result.message)
        .then((message) => {
          if (message.success) {
            setMode("otp");
            setErrorMessage("")
            setOtpMessage(message.message)
          } else
            setErrorMessage(message.error_message)
        })
        .catch(error => console.log('error', error))
        .finally(() => {
          setSendingOtp(false)
        })
    }),
    [isLoading, mode, mutateAsync, onSubmit, sendingOtp]
  );

  useEffect(() => {
    setErrorMessage("")
    setOtpMessage("")
  }, [values.mobile_number]);

  return (
    <>
      <Box pos={"relative"}>
        <Image
          src="/assets/edu_quality/walsh/images/Banner.jpg"
          height={"40vh"}
          fit="cover"
          w={"100%"}
        />
        <Box
          pos={"absolute"}
          bg={"linear-gradient(to top, rgba(248,249,250, 1), rgba(248,249,250, 0))"}
          opacity={1}
          h={50}
          w={"100%"}
          bottom={0}
        ></Box>
      </Box>
      <Stack align="center" justify="center" h={"60vh"} bg={"gray.0"} sx={{
        padding: 10
      }}>
        <form onSubmit={handleSubmit}>
          {mode === "otp" ? (
            <Text size={"lg"} weight={700} c="primary.5">
              <IconArrowLeft onClick={() => setMode("main")}/>
            </Text>
          ) : null}
          <Flex justify={"center"}>
            <Image
              radius={"lg"}
              width={72}
              height={72}
              src="/assets/edu_quality/walsh/images/walnutschool.png"
            />
          </Flex>
          <Stack spacing={2} mt={12} mb={8} align="center">
            <Text size={"lg"} weight={700} c="primary.5">
              {mode !== "otp" ? "Welcome" : "Enter OTP"}
            </Text>
            {mode !== "otp" ? (
              <Text size={"sm"} align="center">
                If you are already a parent of Walnut School, log in below
              </Text>
            ) : (
              <Text size={"sm"}>Phone No: {values.mobile_number}</Text>
            )}
          </Stack>
          <Stack spacing={12}>
            {mode !== "otp" ? (
              <TextInput
                variant="filled"
                placeholder="Registered Mobile Number"
                {...getInputProps("mobile_number")}
                onChange={(event) => {
                  const value = event.target.value;
                  const phoneNumberIncompleteRegix = /^\+?[0-9]*$/;
                  if (!phoneNumberIncompleteRegix.test(value))
                    return;
                  setValues({
                    ...values,
                    mobile_number: event.target.value,
                  });
                }}
              />
            ) : (
              <Flex justify="center">
                <OtpInput style={{width: "100%"}} {...getInputProps("otp")} />
              </Flex>
            )}
            <Text color={"red"} size={"sm"}>{errorMessage}</Text>
            <Text color={"green"} size={"sm"}>{otpMessage}</Text>
            <Button type="submit">
              {mode !== "otp" ? "Get OTP" : "Submit OTP"}
            </Button>
          </Stack>
        </form>
      </Stack>
      <Box pos="absolute" bottom={0} left={0} right={0} style={{
        pointerEvents: "none"
      }}>
        <Image src={"/assets/edu_quality/walsh/images/walnut-bg-transparent.png"} w={"100%"}/>
      </Box>
    </>
  );
};
