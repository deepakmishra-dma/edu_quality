import {
  Box,
  Container,
  Divider,
  Paper,
  Stack,
  Text,
  Image,
  useMantineTheme,
  Flex,
} from "@mantine/core";
import {
  IconUserCircle,
  IconLanguage,
  IconLogout,
  IconSwitchHorizontal,
} from "@tabler/icons";

export const SelectStudent = () => {
  const theme = useMantineTheme();
  return (
    <>
      <Stack mx={"auto"} mb={12} align="center" justify="center" spacing={0}>
        <Box w={96}>
          <Image
            src={"/images/walnutschool.png"}
            w={96}
            h={96}
            radius={"50%"}
            mb={8}
          />
        </Box>
        <Text fw={600} c="gray.7" size={"sm"}>
          aguyran@gmail.com
        </Text>
      </Stack>
      <Paper
        w={"100%"}
        radius={"md"}
        style={{
          boxShadow:
            "0 0 #0000, 0 0 #0000,0 0 #0000, 0 0 #0000,0 1px 3px 0 rgb(0 0 0 / .1), 0 1px 2px -1px rgb(0 0 0 / .1)",
        }}
        py={0}
        px={0}
      >
        <Box px={8} py={12}>
          <Text fw={600} c="gray.9" size={"md"}>
            Settings
          </Text>
        </Box>
        <Flex align={"center"} gap={6} px={8} py={12}>
          <IconUserCircle />
          <Text fw={600} c="gray.9" size={"sm"}>
            View Profile
          </Text>
        </Flex>

        <Divider />
        <Flex align={"center"} gap={6} px={8} py={12}>
          <IconLanguage />
          <Text fw={600} c="gray.9" size={"sm"}>
            Change Language
          </Text>
        </Flex>
        <Divider />
        <Text fw={600} c="red.9" size={"sm"}>
          <Flex align={"center"} gap={6} px={8} py={12}>
            <IconLogout />

            <Text fw={600} c="red.9" size={"sm"}>
              Logout
            </Text>
          </Flex>
        </Text>
      </Paper>

      <Paper w={"100%"} shadow="xs" py={0} mt={20} px={0}>
        <Box px={8} py={12}>
          <Text fw={600} c="gray.9" size={"md"}>
            Other Accounts
          </Text>
        </Box>

        <Box px={8} py={12}>
          <Flex justify={"space-between"}>
            <Flex gap={8} align={"center"}>
              <Image
                width={32}
                height={32}
                radius={"lg"}
                styles={{
                  image: {
                    border: `2px solid ${theme.colors.gray[7]}`,
                  },
                }}
                src={"/images/walnutschool.png"}
              />
              <Text fw={600} c="gray.9" size={"sm"}>
                aguyran@gmail.com
              </Text>
            </Flex>
            <Text c="gray.9" size={"sm"}>
              <IconSwitchHorizontal />
            </Text>
          </Flex>
        </Box>
        <Divider />
        <Box px={8} py={12}>
          <Flex justify={"space-between"}>
            <Flex gap={8} align={"center"}>
              <Image
                width={32}
                height={32}
                radius={"lg"}
                styles={{
                  image: {
                    border: `2px solid ${theme.colors.gray[7]}`,
                  },
                }}
                src={"/images/walnutschool.png"}
              />
              <Text fw={600} c="gray.9" size={"sm"}>
                aguyran@gmail.com
              </Text>
            </Flex>
            <Text c="gray.9" size={"sm"}>
              <Box>
                <IconSwitchHorizontal />
              </Box>
            </Text>
          </Flex>
        </Box>
      </Paper>
    </>
  );
};
