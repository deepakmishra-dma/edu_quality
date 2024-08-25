import {ColorScheme, MantineThemeOverride} from "@mantine/core";

const theme = (colorScheme: ColorScheme): MantineThemeOverride => ({
  ...{
    globalStyles: (theme) => ({
      body: {
        backgroundColor:
          theme.colorScheme === "dark"
            ? theme.colors.dark[8]
            : theme.colors.gray[0],
      },
    }),
    colors: {
      brand: [
        "#fafafa", // 50
        "#f5f5f5", // 100
        "#e5e5e5", // 200
        "#d4d4d4", // 300
        "#a3a3a3", // 400
        "#262626", // 800
        "#171717", // 900
        "#0a0a0a", // 950
      ],
    },
    primaryColor: "brand",
  },
  colorScheme: colorScheme,
  fontFamily: "Inter, sans-serif",
})

export default theme
