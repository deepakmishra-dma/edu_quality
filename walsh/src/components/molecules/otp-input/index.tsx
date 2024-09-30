import ReactOtpInput from "react-otp-input";
import {TextInput, useMantineTheme} from "@mantine/core";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const OtpInput = (props: any) => {
  const theme = useMantineTheme();
  return (
    <ReactOtpInput
      numInputs={4}
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
