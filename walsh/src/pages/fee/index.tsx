import { Box, Button, Select, Stack, Text } from "@mantine/core";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import useStudentList from "../../components/queries/useStudentList.ts";
import useClassDetails from "../../components/queries/useClassDetails.ts";
import useStudentProfileColor from "../../components/hooks/useStudentProfileColor.ts";
import { IconCalendarEvent } from "@tabler/icons";
import useFeesAcademicYear from "../../components/queries/useFeesAcademicYear.ts";

const Fees = () => {
  const [selectedStudent, setSelectedStudent] = useState<string>("");

  const [selectedAcademicYear, setSelectedAcademicYear] = useState<string>("");

  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const searchedStudent = searchParams.get("student");

  const { data: studentsList } = useStudentList();
  const { data: academicYearData } = useFeesAcademicYear(selectedStudent);

  const {
    data: classDetails,
    error: classError,
    isFetching: classLoading,
  } = useClassDetails(selectedStudent);

  const students = useMemo(
    () => studentsList?.data?.message || [],
    [studentsList?.data]
  );

  useEffect(() => {
    if (selectedStudent) {
      searchParams.set("student", selectedStudent || "");
      setSearchParams(searchParams, { replace: true });
    }
  }, [selectedStudent]);

  useEffect(() => {
    const studentNames = students?.map((student) => student.name) || [];
    if (
      !selectedStudent &&
      searchedStudent &&
      selectedStudent != searchedStudent &&
      studentNames.includes(searchedStudent)
    ) {
      setSelectedStudent(searchedStudent);
    } else if (!studentNames.includes(selectedStudent)) {
      setSelectedStudent(studentNames[0]);
    }
  }, [searchedStudent, selectedStudent, students]);

  const studentProfileColor = useStudentProfileColor(selectedStudent);
  const notEnrolledInProgram =
    classLoading ||
    classError ||
    !classDetails?.data?.message ||
    Object.keys(classDetails?.data?.message).length == 0;

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
        {students.map((student, index) => {
          const isSelected = selectedStudent === student.name;
          return (
            <Box
              key={index}
              sx={{
                display: "inline-block",
                marginTop: 10,
                // marginBottom: 10,
                flexShrink: 0,
                flexGrow: 1,
                textAlign: "center",
                minWidth: "33.33%",
              }}
              onClick={() => setSelectedStudent(student.name)}
            >
              <Text
                sx={{
                  paddingLeft: 20,
                  paddingRight: 20,
                  borderLeft: index && "1px solid black",
                  color: isSelected ? "black" : "#0007",
                }}
              >
                {student.first_name}
              </Text>
              <Box
                sx={{
                  marginTop: isSelected ? 4 : 5,
                  borderBottom: isSelected
                    ? "2px solid " + studentProfileColor
                    : "1px solid #0005",
                }}
              />
            </Box>
          );
        })}
      </Stack>
      {notEnrolledInProgram ? (
        <Text align="center" color="dimmed" weight="bold" my={30}>
          {classLoading ? "Loading..." : "Not Enrolled in program"}
        </Text>
      ) : (
        <Box
          sx={{
            border: "1px solid " + studentProfileColor + "77",
            margin: 30,
            borderRadius: 10,
          }}
        >
          <Stack
            sx={{
              borderBottom: "1px solid " + studentProfileColor + "77",
              padding: "5px 10px",
              backgroundColor: studentProfileColor + "22",
              flexDirection: "row",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <Text
              sx={{
                color: studentProfileColor,
                fontWeight: "bold",
              }}
            >
              {classDetails?.data?.message?.program?.program_name} -{" "}
              {classDetails?.data?.message?.division?.student_group_name}
            </Text>

            {students.find((student) => student.name === selectedStudent)
              ?.reference_number && (
              <Text
                sx={{
                  borderRadius: 50,
                  backgroundColor: studentProfileColor + "22",
                  padding: "1px 5px",
                  fontSize: 10,
                  display: "inline-block",
                  height: "1.4em",
                  lineHeight: 1.4,
                  color: studentProfileColor,
                  fontWeight: "bold",
                  letterSpacing: 0.5,
                  textTransform: "uppercase",
                }}
              >
                {
                  students.find((student) => student.name === selectedStudent)
                    ?.reference_number
                }
              </Text>
            )}
          </Stack>
          <Box
            sx={{
              textAlign: "center",
            }}
          >
            <Select
              color={studentProfileColor}
              sx={{
                margin: 10,
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
              data={academicYearData?.data?.message || []}
              value={selectedAcademicYear}
              onChange={(value) => setSelectedAcademicYear(value || "")}
              icon={
                <IconCalendarEvent color={studentProfileColor} stroke={1} />
              }
            />
            <Button
              sx={{
                marginBottom: 10,
                marginTop: 10,
                borderRadius: 10,
                backgroundColor: studentProfileColor,
              }}
              onClick={() => {
                if (selectedStudent && selectedAcademicYear)
                  navigate(
                    `/fee/list?academic_year=${encodeURIComponent(
                      selectedAcademicYear || ""
                    )}&student=${encodeURIComponent(selectedStudent || "")}`
                  );
              }}
            >
              Show Fees
            </Button>
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default Fees;
