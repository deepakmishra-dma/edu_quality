import {
  Select,
  Box,
  Flex,
  Stack,
  Accordion,
  Table,
  Text,
  Button,
} from "@mantine/core";
import { useState, useMemo } from "react";
import useStudentList from "../components/queries/useStudentList";
import useStudentProfileColor from "../components/hooks/useStudentProfileColor";
import useMockResult from "../components/queries/useMockResult";
import { IconDownload, IconShare2 } from "@tabler/icons-react";
const Result = () => {
  const [selectedStudent, setSelectedStudent] = useState<string | null>("");
  const { data: studentsList } = useStudentList();
  const resultData = useMockResult();

  const students = useMemo(
    () => studentsList?.data?.message || [],
    [studentsList?.data]
  );

  const studentNames =
    students?.map((student) => ({
      label: student.first_name,
      value: student.name,
    })) || [];

  const studentProfileColor = useStudentProfileColor(selectedStudent);

  return (
    <Box p={12}>
      <Stack spacing={14}>
        <Flex gap={10}>
          <Select
            value={selectedStudent}
            data={studentNames}
            onChange={(value) => setSelectedStudent(value)}
            placeholder="Student"
            sx={{
              ".mantine-Select-dropdown": {
                '.mantine-Select-item[data-hovered="true"]': {
                  backgroundColor: studentProfileColor,
                },
              },
              ".mantine-Select-input": {
                color: studentProfileColor,
                ":active": {
                  borderColor: studentProfileColor,
                },
                ":focus": {
                  borderColor: studentProfileColor,
                },
              },
              borderRadius: 10,
              borderColor: studentProfileColor,
            }}
          />
          <Select
            sx={{
              ".mantine-Select-dropdown": {
                '.mantine-Select-item[data-hovered="true"]': {
                  backgroundColor: studentProfileColor,
                },
              },
              ".mantine-Select-input": {
                color: studentProfileColor,
                ":active": {
                  borderColor: studentProfileColor,
                },
                ":focus": {
                  borderColor: studentProfileColor,
                },
              },
              borderRadius: 10,
              borderColor: studentProfileColor,
            }}
            placeholder="Class"
            data={["1", "2", "3", "4", "5", "6", "7", "8", "9"]}
          />
        </Flex>
        <Accordion
          defaultValue={resultData?.subjects[0]?.name}
          sx={{
            "&": {
              border: `1px solid gray`,
              borderRadius: 4,
            },
            "& .mantine-Accordion-content": {
              fontSize: 12,
            },
            "& .mantine-Accordion-label": {
              fontSize: 14,
              fontWeight: "bold",
            },
          }}
        >
          {resultData["subjects"]?.map((subject) => (
            <Accordion.Item value={subject?.name}>
              <Accordion.Control>{subject.name}</Accordion.Control>
              <Accordion.Panel>
                <Table
                  withColumnBorders
                  withBorder
                  sx={{
                    "&": {
                      borderCollapse: "separate",
                      borderSpacing: 0,
                      borderColor: "black",
                      borderRadius: "4px",
                      tableLayout: "fixed",
                    },
                    "& tbody tr td, & thead .second-row th": {
                      fontSize: 12,
                    },
                    "& thead tr th, & tbody tr td": {
                      borderColor: "black",
                    },
                  }}
                >
                  <thead>
                    <tr>
                      <th>
                        Term1 <Text size={10}>(100 Marks)</Text>
                      </th>
                      <th>
                        Term2 <Text size={10}>(100 Marks)</Text>
                      </th>
                      <th></th>
                      <th></th>
                    </tr>
                    <tr className="second-row">
                      <th>Grade</th>
                      <th>Grade</th>
                      <th>Grade</th>
                      <th>Grade Points</th>
                    </tr>
                  </thead>
                  <tbody>
                    {subject.result.map((result) => (
                      <tr>
                        <td>{result.term1}</td>
                        <td>{result.term2}</td>
                        <td>{result.grade}</td>
                        <td>{result.gradePoints}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </Accordion.Panel>
            </Accordion.Item>
          ))}
        </Accordion>
        <Box>
          <Text size={14} fw={"bold"} c="gray.9">
            Remarks
          </Text>
          <Box
            py={10}
            px={10}
            bg="white"
            sx={{
              "&": {
                border: `1px solid black`,
                borderRadius: "4px",
              },
            }}
          >
            <Text size={12}>{resultData.remarks}</Text>
          </Box>{" "}
        </Box>

        <Box>
          <Text size={14} fw={"bold"} c="gray.9">
            Attendance
          </Text>
          <Table
            withColumnBorders
            withBorder
            sx={{
              "&": {
                borderCollapse: "separate",
                borderSpacing: 0,
                borderColor: "black",
                borderRadius: "4px",
                tableLayout: "fixed",
              },
              "& tbody tr td, & thead .second-row th": {
                fontSize: 12,
              },
              "& thead tr th, & tbody tr td": {
                borderColor: "black",
              },
            }}
          >
            <thead>
              <tr>
                <th>Attendance</th>
                <th>Attended</th>
                <th>Total</th>
                <th>Percentage</th>
              </tr>
            </thead>

            <tbody>
              {resultData?.attendance?.map((row) => (
                <tr>
                  <td>{row.attendance}</td>
                  <td>{row.attended}</td>
                  <td>{row.total}</td>
                  <td>{row.percentage}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Box>
        <Flex justify={"space-between"} my={12}>
          <Text size={18} fw={"bold"}>
            Remark:{" "}
          </Text>
          <Text size={18} fw={"500"}>
            {resultData.result}
          </Text>
        </Flex>
        <Stack>
          <Button w={"100%"} rightIcon={<IconDownload size={16} />}>
            Download
          </Button>
          <Button w={"100%"} rightIcon={<IconShare2 size={16} />}>
            Share
          </Button>
        </Stack>
      </Stack>
    </Box>
  );
};

export default Result;
