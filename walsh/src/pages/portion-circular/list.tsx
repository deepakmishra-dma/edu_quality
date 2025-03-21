import { Box, Table, Text, Stack } from "@mantine/core";
import usePortionCircularList, {
  PortionCircular,
} from "../../components/queries/usePortionCircular";
import { useSearchParams } from "react-router-dom";
import useClassDetails from "../../components/queries/useClassDetails.ts";
import useStudentProfileColor from "../../components/hooks/useStudentProfileColor.ts";

const PortionCircularList = () => {
  const [searchParams] = useSearchParams();
  const unit = searchParams.get("unit") || "";
  const student = searchParams.get("student") || "";

  const { data: classDetails } = useClassDetails(student);
  const { data: circularList } = usePortionCircularList(
    unit,
    classDetails?.data?.message?.division?.name || ""
  );
  const studentProfileColor = useStudentProfileColor(student);

  if (circularList?.data?.message == undefined) {
    return null;
  }
  const circulars = circularList?.data?.message;

  return (
    <Box>
      <Stack
        sx={{
          whiteSpace: "nowrap",
          overflow: "auto",
          flexDirection: "row",
          // borderBottom: '1px solid  #0005',
          gap: 0,
        }}
      >
        <Box
          sx={{
            display: "inline-block",
            marginTop: 10,
            marginBottom: 5,
            flexShrink: 0,
            flexGrow: 1,
            textAlign: "center",
          }}
        >
          <Text
            sx={{
              paddingLeft: 20,
              paddingRight: 20,
              color: "#000",
              fontWeight: "bold",
            }}
          >
            {student}
          </Text>
        </Box>
      </Stack>
      {Object.keys(circulars).map((subject) => (
        <Subject
          key={subject}
          subject={subject}
          circulars={circulars}
          studentProfileColor={studentProfileColor}
          unit={unit}
        />
      ))}
    </Box>
  );
};

const Subject = ({
  subject,
  circulars,
  studentProfileColor,
  unit,
}: {
  subject: string;
  circulars: PortionCircular;
  studentProfileColor: string;
  unit?: string;
}) => {
  return (
    <>
      <Box
        sx={{
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          gap: 10,
          backgroundColor: studentProfileColor,
          color: "white",
          padding: "5px 10px",
          justifyContent: "center",
          fontSize: 15,
          fontWeight: "bold",
        }}
      >
        <Text>
          Subject: {subject}: Unit {unit || ""}
        </Text>
      </Box>
      <Box p={16}>
        {Object.keys(circulars[subject]).map((textbook) => (
          <Textbook
            key={textbook}
            textbook={textbook}
            chapters={circulars[subject][textbook]}
            studentProfileColor={studentProfileColor}
          />
        ))}
      </Box>
    </>
  );
};

// Textbook component
const Textbook = ({
  textbook,
  chapters,
  studentProfileColor,
}: {
  textbook: string;
  chapters: PortionCircular["string"]["string"];
  studentProfileColor: string;
}) => {
  return (
    <Box py={8}>
      <Table
        withColumnBorders
        border={1}
        sx={(theme) => ({
          "&": {
            borderCollapse: "separate",
            borderSpacing: 0,
            border: `1px solid ${studentProfileColor}`,
            borderRadius: theme.radius.md,
          },
          "& thead": {
            backgroundColor: studentProfileColor + "22",
          },
          "& thead tr th": {
            color: studentProfileColor,
          },
          "& th, & td": {
            borderTop: "none",
            borderBottom: "none",
          },
        })}
      >
        <thead>
          <td>
            <Text px={8} py={4} size={"xs"}>
              Textbook: {textbook}
            </Text>
          </td>
        </thead>
        <tbody>
          {Object.keys(chapters).map((chapter) => (
            <tr>
              <td>
                <Chapter
                  key={chapter}
                  chapter={chapter}
                  studentProfileColor={studentProfileColor}
                  chapterItems={chapters[chapter]}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Box>
  );
};

// Chapter component
const Chapter = ({
  chapter,
  chapterItems,
  studentProfileColor,
}: {
  chapter: string;
  chapterItems: PortionCircular["string"]["string"]["string"];
  studentProfileColor: string;
}) => {
  return (
    <Box pb={8}>
      <Text size={"xs"} py={4}>
        Chapter: {chapter}
      </Text>
      <Table
        withColumnBorders
        sx={(theme) => ({
          "&": {
            tableLayout: "fixed",
            borderCollapse: "separate",
            borderSpacing: 0,
            // border: `1px solid ${studentProfileColor}`,
            borderRadius: theme.radius.md,
          },
          "& thead": {
            backgroundColor: studentProfileColor + "22",
          },
          "& thead tr th": {
            color: studentProfileColor,
            // fontSize: 13,
            paddingLeft: 6,
            paddingRight: 6,
          },
          "& th, & td": {
            borderTop: "none",
            borderBottom: "none",
          },
        })}
      >
        <thead>
          <tr>
            <th colSpan={3}>Item Group</th>
            <th colSpan={2}>Count</th>
            <th colSpan={3}>Link</th>
          </tr>
        </thead>
        <tbody>
          {chapterItems.map((item, index) => (
            <tr key={index} style={{ fontSize: 12 }}>
              <td colSpan={3} style={{ fontSize: 12 }}>
                {item.item_group}
              </td>
              <td colSpan={2} style={{ fontSize: 12 }}>
                {item.count}
              </td>
              <td colSpan={3}>
                {item.products?.map((product) => (
                  <>
                    <a
                      href={product.url}
                      style={{ fontSize: 12 }}
                      target="__blank"
                    >
                      {product.name}
                    </a>{" "}
                  </>
                ))}
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Box>
  );
};

export default PortionCircularList;
