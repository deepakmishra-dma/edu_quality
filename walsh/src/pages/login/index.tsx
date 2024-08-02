import { AuthPage } from "@refinedev/mantine";
import { Create, useForm } from "@refinedev/mantine";
import { LOGIN_FORM } from "../../components/forms";
import {
  NumberInput,
  Button,
  Box,
  Container,
  Image,
  Paper,
  Stack,
  Text,
  Flex,
  Modal,
} from "@mantine/core";
import { useCallback, useMemo, useState } from "react";
import { OtpInput } from "../../components";
import { IconArrowLeft } from "@tabler/icons";

export const Login = () => {
  const [mode, setMode] = useState<"main" | "otp">("main");
  const [admissionsOpened, setAdmissionsOpened] = useState<boolean>(false);
  const { saveButtonProps, getInputProps, errors, onSubmit, values } =
    useForm(LOGIN_FORM);

  // Doesn't really do anything
  const handleSubmit = useMemo(
    () =>
      onSubmit((values) => {
        setMode("otp");
        console.log(values, "subm");
        setTimeout(() => {
          console.log("get-otp");
        }, 6000);
      }),
    [onSubmit]
  );

  return (
    <>
      <Modal
        opened={admissionsOpened}
        onClose={() => {
          setAdmissionsOpened(false);
        }}
        title="New Admission"
      >
        For new admissions, enter the mobile number which was entered when you
        first registered with Walnut School
      </Modal>
      <Container px={0} h="100vh" size="xs" pos={"relative"} bg={"gray.0"}>
        <Container size="xs" px={0} bg={"gray.0"}>
          <Box pos={"relative"}>
            <Image
              src="/images/Banner.jpg"
              height={"40vh"}
              fit="cover"
              w={"100%"}
            />
            <Box
              pos={"absolute"}
              bg={
                "linear-gradient(to top, rgba(248,249,250, 1), rgba(248,249,250, 0))"
              }
              opacity={1}
              h={50}
              w={"100%"}
              bottom={0}
            ></Box>
          </Box>
        </Container>
        <Stack align="center" justify="center" h={"60vh"} bg={"gray.0"}>
          <Container size="xs" maw={387} w="100%" bg={"gray.0"}>
            <form onSubmit={handleSubmit}>
              {/* <OtpInput /> */}
              {mode === "otp" ? (
                <Text size={"lg"} weight={700} c="primary.5">
                  <IconArrowLeft onClick={() => setMode("main")} />
                </Text>
              ) : null}
              <Flex justify={"center"}>
                <Image
                  radius={"lg"}
                  width={72}
                  height={72}
                  src="/images/walnutschool.png"
                />
              </Flex>
              <Stack spacing={2} mt={12} mb={8} align="center">
                <Text size={"lg"} weight={700} c="primary.5">
                  {mode !== "otp" ? "Welcome" : "Enter OTP"}
                </Text>

                {mode !== "otp" ? (
                  <Text size={"sm"}>
                    If you are already a parent of Walnut School, log in below
                  </Text>
                ) : (
                  <Text size={"sm"}>Otp Sent to {values.mobile_number}</Text>
                )}
              </Stack>
              <Stack spacing={12}>
                {mode !== "otp" ? (
                  <NumberInput
                    variant="filled"
                    {...getInputProps("mobile_number")}
                    hideControls
                    placeholder="Registered Mobile Number"
                  />
                ) : (
                  <Flex justify="center">
                    <OtpInput style={{ width: "100%" }} />
                  </Flex>
                )}
                <Button type="submit">
                  {mode !== "otp" ? "Get OTP" : "Submit OTP"}
                </Button>
                <Text
                  onClick={() => {
                    setAdmissionsOpened(true);
                  }}
                  size={"xs"}
                  c="blue"
                  weight={"600"}
                  underline
                  align="center"
                >
                  New Admissions?
                </Text>
              </Stack>
            </form>
          </Container>
        </Stack>
        <Box pos="absolute" bottom={0}>
          <Image src={"/images/walnut-bg-transparent.png"} w={"100%"} />
        </Box>
      </Container>
    </>
  );
};
