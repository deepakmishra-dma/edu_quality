import { Text } from "@mantine/core";

const HelpLink = ({ studentProfileColor }: { studentProfileColor: string }) => {
  return (
    <Text
      sx={{
        margin: 10,
        padding: 10,
        borderRadius: 10,
        backgroundColor: studentProfileColor + "22",
        color: studentProfileColor,
        fontWeight: "normal",
        textAlign: "center",
      }}
    >
      If you are unable to open PPT files, please follow{" "}
      <a
        href="https://www.youtube.com/shorts/dx2VL1hZPqc"
        target="_blank"
        rel="noopener noreferrer"
        style={{ color: studentProfileColor, fontWeight: "bold" }}
      >
        this link
      </a>
    </Text>
  );
};

export default HelpLink;
