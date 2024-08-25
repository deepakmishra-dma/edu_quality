import {
  Box,
  Flex,
  Header as MantineHeader,
  Sx,
  Text,
  useMantineColorScheme,
  useMantineTheme,
} from "@mantine/core";
// @ts-expect-error types error
import {IconArrowLeft,} from "@tabler/icons";

// type IUser = {
//   id: number;
//   name: string;
//   avatar: string;
// };

export function SubHeader({name}: any) {
  // const {data: user} = useGetIdentity<IUser>();
  const sticky = true;

  const theme = useMantineTheme();
  const {colorScheme} = useMantineColorScheme();
  const dark = colorScheme === "dark";

  const borderColor = dark ? theme.colors.dark[6] : theme.colors.gray[2];

  let stickyStyles: Sx = {};
  if (sticky) {
    stickyStyles = {
      position: `sticky`,
      top: 0,
      zIndex: 1,
    };
  }

  return (
    <MantineHeader
      zIndex={199}
      height={64}
      py={6}
      px="sm"
      sx={{
        borderBottom: `1px solid ${borderColor}`,

        ...stickyStyles,
      }}
    >
      <Flex
        align="center"
        sx={{
          height: "100%",
        }}
        gap={12}
      >
        <IconArrowLeft style={{weight: 400}}/>
        <Box>
          <Text size={"xl"} weight={"600"}>
            {name}
          </Text>
        </Box>
      </Flex>
    </MantineHeader>
  );
}
