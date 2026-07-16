import { useForm } from "@refinedev/mantine";

import {
  Box,
  Button,
  Flex,
  Image,
  Stack,
  Text,
  TextInput,
  Select,
} from "@mantine/core";
import { IconReload } from "@tabler/icons";
import { useState } from "react";
import {
  useGetSchools,
  useGetPrograms,
} from "../components/queries/useGetRegisterSelectData";

export const Register = () => {
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isRegistered, setIsRegistered] = useState(false);
  const [selectedSchool, setSelectedSchool] = useState<string>("");

  // Use both hooks separately
  const { schools, isLoading: isLoadingSchools } = useGetSchools();
  const { programs, isLoading: isLoadingPrograms } =
    useGetPrograms(selectedSchool);

  const { getInputProps, values, setValues, onSubmit } = useForm({
    initialValues: {
      fathers_name: "",
      name: "",
      fathers_phone: "",
      email: "",
      school: "",
      class: "",
    },
  });

  console.log(schools, programs);
  // Transform the data for Mantine Select
  const schoolOptions = (schools?.data ?? []).map(
    (school: { name: string }) => ({
      value: school.name,
      label: school.name,
    })
  );

  const programOptions = (programs?.data ?? []).map(
    (program: { program_name: string }) => ({
      value: program.program_name,
      label: program.program_name,
    })
  );

  const handleSubmit = onSubmit((values) => {
    const myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");

    fetch(
      "/api/method/edu_quality.api.student_application.create_student_lead",
      {
        method: "POST",
        headers: myHeaders,
        body: JSON.stringify({
          fathers_name: values.fathers_name,
          first_name: values.name,
          fathers_phone: values.fathers_phone,
          fathers_email: values.email,
          school: values.school,
          class: values.class,
          source: "Mobile App",
        }),
        redirect: "follow",
      }
    )
      .then((response) => response.json())
      .then((result) => {
        if (result.message) {
          setSuccessMessage(
            "You have requested registration successfully. Our team will contact you shortly."
          );
          setErrorMessage("");
          setIsRegistered(true);
        } else {
          setErrorMessage(result.message.error_message);
          setSuccessMessage("");
        }
      })
      .catch(() => {
        setErrorMessage("An error occurred. Please try again.");
        setSuccessMessage("");
      });
  });

  return (
    <>
      <Box sx={{ height: "10%" }} />
      <Stack
        align="center"
        pt={50}
        mih={400}
        bg={"gray.0"}
        sx={{ padding: 40 }}
      >
        <form onSubmit={handleSubmit} style={{ width: "80vw", maxWidth: 400 }}>
          <Flex justify={"center"}>
            <Image
              radius={"lg"}
              width={160}
              src="/assets/edu_quality/walsh/images/logo.png"
            />
          </Flex>

          <Stack spacing={2} mt={12} mb={8} align="center">
            <Text size={"lg"} sx={{ fontSize: 20 }} weight={700} c="primary.5">
              Register
            </Text>
          </Stack>

          <Stack spacing={12}>
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
              placeholder="Parent Name"
              {...getInputProps("fathers_name")}
            />

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
              placeholder="Child Name"
              {...getInputProps("name")}
            />

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
              placeholder="Phone Number"
              {...getInputProps("fathers_phone")}
              onChange={(event) => {
                const value = event.target.value;
                const phoneNumberRegex = /^\+?[0-9]*$/;
                if (!phoneNumberRegex.test(value)) return;
                setValues({
                  ...values,
                  fathers_phone: value,
                });
              }}
            />

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
              placeholder="Email"
              {...getInputProps("email")}
            />

            <Select
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
              placeholder={
                isLoadingSchools ? "Loading schools..." : "Select School"
              }
              data={schoolOptions}
              {...getInputProps("school")}
              onChange={(value) => {
                setSelectedSchool(value || "");
                setValues({ ...values, school: value || "" });
              }}
            />

            <Select
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
              placeholder={
                isLoadingPrograms ? "Loading programs..." : "Select Class"
              }
              data={programOptions}
              disabled={!selectedSchool}
              {...getInputProps("class")}
            />

            {successMessage && (
              <Text color="green" size="sm" align="center">
                {successMessage}
              </Text>
            )}
            {errorMessage && (
              <Text color="red" size="sm" align="center">
                {errorMessage}
              </Text>
            )}

            <Button
              type="submit"
              disabled={isRegistered}
              sx={{
                backgroundColor: "#1E6967",
                marginTop: 10,
                ":hover": {
                  backgroundColor: "#1E6967",
                  opacity: 0.8,
                },
              }}
            >
              Register
            </Button>

            <Flex direction={"column"} align={"center"}>
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
                <IconReload size={15} style={{ marginLeft: 5 }} />
              </Button>
            </Flex>
          </Stack>
        </form>
      </Stack>
    </>
  );
};
