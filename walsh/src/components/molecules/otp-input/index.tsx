import ReactOtpInput from "react-otp-input";
import {Input, useMantineTheme} from "@mantine/core";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const OtpInput = (props: any) => {
  const theme = useMantineTheme();
  return (
    <ReactOtpInput
      numInputs={4}
      {...props}
      renderInput={(props) => {
        return (
          <Input
            {...props}
            style={{
              flexShrink: 0,
              borderBottom: `2px solid ${theme.colors.gray[6]}`,
              color: theme.colors.gray[6],
              width: 40,
              border: 'none',
              margin: '0 5px',
              // textAlign: 'center',
              fontSize: '1em'
            }}
            sx={{
              '.mantine-Input-input': {
                letterSpacing: 2,
                fontSize: 20,
                textAlign: "center",
                "::placeholder": {
                  letterSpacing: 0,
                  textAlign: "center",
                }
              }
            }}
            type="number"
          />
        );
      }}
    />
  );
};

export default OtpInput;
