import {
  Avatar,
  Flex,
  Group,
  Header as MantineHeader,
  Sx,
  Title,
  useMantineColorScheme,
  useMantineTheme,
} from "@mantine/core";
import {useGetIdentity} from "@refinedev/core";
import {HamburgerMenu, RefineThemedLayoutV2HeaderProps,} from "@refinedev/mantine";
import React from "react";

type IUser = {
  id: number;
  name: string;
  avatar: string;
};

export const Header: React.FC<RefineThemedLayoutV2HeaderProps> = (
  {sticky = true,}
) => {
  const {data: user} = useGetIdentity<IUser>();


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
        justify="space-between"
        sx={{
          height: "100%",
        }}
      >
        <HamburgerMenu/>
        <Group>
          {(user?.name || user?.avatar) && (
            <Group spacing="xs">
              {user?.name && <Title order={6}>{user?.name}</Title>}
              <Avatar src={user?.avatar} alt={user?.name} radius="xl"/>
            </Group>
          )}
        </Group>
      </Flex>
    </MantineHeader>
  );
};
