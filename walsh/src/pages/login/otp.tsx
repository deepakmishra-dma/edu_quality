import { Flex, Stack, Text } from "@mantine/core";
import { OtpInput } from "../../components";

export function OtpPage() {
  return (
    <Flex justify="center">
      <Stack>
        <OtpInput style={{ width: "100%" }} />
        <Text size={"xs"} c={"gray.6"} weight={500}>
          Resend Now
        </Text>
      </Stack>
    </Flex>
  );
}
