import { Box, Button, Stack, Text } from "@mantine/core";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import useStudentList from "../../components/queries/useStudentList.ts";
import useClassDetails from "../../components/queries/useClassDetails.ts";
import useStudentProfileColor from "../../components/hooks/useStudentProfileColor.ts";
import { IconCalendar } from "@tabler/icons";
import { DateRangePicker } from "@mantine/dates";
import type { DateRangePickerValue } from "@mantine/dates";
import { format } from "date-fns";

const DateCmap = () => {
  const [selectedStudent, setSelectedStudent] = useState<string>("");
  const [selectedDateRange, setselectedDateRange] =
    useState<DateRangePickerValue>(getLastAndTodaysDate);

  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const searchedStudent = searchParams.get("student");

  const { data: studentsList } = useStudentList();
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

  // useEffect(() => {
  //   const subjectNames = subjectOptions.map((subject) => subject.value);
  //   if (!subjectNames.includes(selectedSubject)) {
  //     setSelectedSubject(subjectNames[0]);
  //   }
  // }, [selectedSubject, subjectOptions]);

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
            <DateRangePicker
              value={selectedDateRange}
              color={studentProfileColor}
              onChange={(value) => setselectedDateRange(value)}
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
              icon={<IconCalendar color={studentProfileColor} stroke={1} />}
            />

            <Button
              sx={{
                marginBottom: 10,
                marginTop: 10,
                borderRadius: 10,
                backgroundColor: studentProfileColor,
              }}
              onClick={() => {
                if (selectedDateRange?.every(Boolean))
                  navigate(
                    `/date-circular/list?date=${encodeURIComponent(
                      selectedDateRange
                        ?.map((value) => {
                          if (value) {
                            return format(value, "yyyy-MM-dd");
                          }
                          return "";
                        })
                        .join(",") || ""
                    )}
                  &student=${encodeURIComponent(selectedStudent || "")}`
                  );
              }}
            >
              Show Curriculum
            </Button>
          </Box>
        </Box>
      )}
    </Box>
  );
};

function getLastAndTodaysDate(): [Date, Date] {
  const today = new Date();

  // Get the day of the week (0 = Sunday, 1 = Monday, ..., 6 = Saturday)
  const dayOfWeek = today.getDay();

  // Calculate the difference between today and the last Monday
  const diffToLastMonday = (dayOfWeek + 6) % 7; // Adding 6 to handle Sunday as the first day of the week

  // Calculate the date of the last Monday
  const lastMonday = new Date(today);
  lastMonday.setDate(today.getDate() - diffToLastMonday);

  // Format the dates as desired (e.g., MM/DD/YYYY)

  return [lastMonday, today];
}
export default DateCmap;
