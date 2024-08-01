import ReactOtpInput from "react-otp-input";
import { NumberInput, TextInput, useMantineTheme } from "@mantine/core";

const OtpInput = (props) => {
  const theme = useMantineTheme();
  return (
    <ReactOtpInput
      numInputs={6}
      value="123457"
      onChange={() => {
        console.log("s");
      }}
      {...props}
      renderInput={(props) => {
        return (
          <TextInput
            {...props}
            variant="unstyled"
            size="md"
            styles={{
              input: {
                textAlign: "center",
              },
            }}
            style={{
              flexShrink: 0,
              borderBottom: `2px solid ${theme.colors.gray[6]}`,
              color: theme.colors.gray[6],
              // textAlign: "center",
            }}
            w={36}
            h={36}
            mx={8}
          />
        );
      }}
    />
  );
};

export default OtpInput;
