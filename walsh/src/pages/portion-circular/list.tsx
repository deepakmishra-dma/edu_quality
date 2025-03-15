import { Box, Table, Text } from "@mantine/core";
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
      {Object.keys(circulars).map((subject) => (
        <Subject
          key={subject}
          subject={subject}
          circulars={circulars}
          studentProfileColor={studentProfileColor}
        />
      ))}
    </Box>
  );
};

const Subject = ({
  subject,
  circulars,
  studentProfileColor,
}: {
  subject: string;
  circulars: PortionCircular;
  studentProfileColor: string;
}) => {
  return (
    <Box p={16}>
      <Text size={"sm"}>{subject}</Text>
      {Object.keys(circulars[subject]).map((textbook) => (
        <Textbook
          key={textbook}
          textbook={textbook}
          chapters={circulars[subject][textbook]}
          studentProfileColor={studentProfileColor}
        />
      ))}
    </Box>
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
    <Box>
      <Text size={"xs"}>Textbook: {textbook}</Text>
      {Object.keys(chapters).map((chapter) => (
        <Chapter
          key={chapter}
          chapter={chapter}
          studentProfileColor={studentProfileColor}
          chapterItems={chapters[chapter]}
        />
      ))}
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
    <Box>
      <Text size={"xs"}>Chapter: {chapter}</Text>
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
          <tr>
            <th>Item Group</th>
            <th>Count</th>
            <th>Link</th>
          </tr>
        </thead>
        <tbody>
          {chapterItems.map((item, index) => (
            <tr key={index}>
              <td>{item.item_group}</td>
              <td>{item.count}</td>
              <td>
                {item.products?.map((product) => (
                  <>
                    <a href={product.url} target="__blank">
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
