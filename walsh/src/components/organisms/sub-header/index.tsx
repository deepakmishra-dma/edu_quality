import {
  ActionIcon,
  Avatar,
  Flex,
  Group,
  Header as MantineHeader,
  Menu,
  Sx,
  Text,
  Title,
  Box,
  useMantineColorScheme,
  useMantineTheme,
} from "@mantine/core";
import { useGetIdentity, useGetLocale, useSetLocale } from "@refinedev/core";
import {
  HamburgerMenu,
  RefineThemedLayoutV2HeaderProps,
} from "@refinedev/mantine";
import {
  IconLanguage,
  IconMoonStars,
  IconSun,
  IconArrowLeft,
} from "@tabler/icons";
import i18n from "i18next";
import React from "react";

type IUser = {
  id: number;
  name: string;
  avatar: string;
};
export function SubHeader({ name, goBack }) {
  const { data: user } = useGetIdentity<IUser>();
  const sticky = true;
  const changeLanguage = useSetLocale();

  const theme = useMantineTheme();
  const locale = useGetLocale();
  const currentLocale = locale();
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
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
        <IconArrowLeft style={{ weight: 400 }} />
        <Box>
          <Text size={"xl"} weight={"600"}>
            {name}
          </Text>
        </Box>
      </Flex>
    </MantineHeader>
  );
}
