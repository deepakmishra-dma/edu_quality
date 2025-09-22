import { Box, Stack, Text } from "@mantine/core";
import { Table } from "@mantine/core";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import useStudentList from "../components/queries/useStudentList.ts";
import useClassDetails from "../components/queries/useClassDetails.ts";
import useStudentProfileColor from "../components/hooks/useStudentProfileColor.ts";
import {
  usePTMLinksQuery,
  useofflinePTMLinksQuery,
} from "../components/queries/usePTMLinksQuery.tsx";

function timeToMinutes(timeStr: any) {
  const [time, period] = timeStr.split(" ");
  let [hours, minutes] = time.split(":").map(Number);

  if (period === "PM" && hours !== 12) {
    hours += 12;
  } else if (period === "AM" && hours === 12) {
    hours = 0;
  }

  return hours * 60 + minutes;
}

function isTimeBeforeCurrent(
  meetTime: string,
  currentTime: Date,
  date: string
) {
  if (typeof date === "string" && !isToday(date)) {
    return false;
  }

  const fiveMinutes = 5;
  const [startTime, endTime] = meetTime.split(" - ");
  const meetTimeInMinutes = timeToMinutes(startTime);
  const endTimeInMinutes = timeToMinutes(endTime);
  const currentMinutes = currentTime.getHours() * 60 + currentTime.getMinutes();

  return (
    meetTimeInMinutes - fiveMinutes <= currentMinutes &&
    currentMinutes <= endTimeInMinutes
  );
}

export const PtmLinks = () => {
  const [selectedStudent, setSelectedStudent] = useState<string>("");
  const [selectedSubject, setSelectedSubject] = useState<string>("");
  const [selectedUnit, setSelectedUnit] = useState<string>("unit 1");

  const [success, setSuccess] = useState(false);

  const [searchParams, setSearchParams] = useSearchParams();
  const searchedStudent = searchParams.get("student");

  const { data: studentsList } = useStudentList();
  const { data: classDetails } = useClassDetails(selectedStudent);

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

  const subjectOptions = useMemo(() => {
    return (
      classDetails?.data?.message?.class?.subject?.map?.((subject) => ({
        label: subject.subject,
        value: subject.subject,
      })) || []
    );
  }, [classDetails?.data?.message?.class?.subject]);

  const unitOptions = useMemo(
    () => [
      {
        label: `Absent`,
        value: `absent`,
      },
      {
        label: `Sick`,
        value: `sick`,
      },
    ],
    []
  );

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

  useEffect(() => {
    const subjectNames = subjectOptions.map((subject) => subject.value);
    if (!subjectNames.includes(selectedSubject)) {
      setSelectedSubject(subjectNames[0]);
    }
  }, [selectedSubject, subjectOptions]);

  useEffect(() => {
    const unitNames = unitOptions.map((unit) => unit.value);
    if (!unitNames.includes(selectedUnit)) {
      setSelectedUnit(unitNames[0]);
    }
  }, [selectedUnit, unitOptions]);

  const studentProfileColor = useStudentProfileColor(selectedStudent);

  useEffect(() => {
    if (success) setSuccess(false);
  }, [selectedStudent]);
  const custom_school = classDetails?.data?.message?.division?.custom_school;
  const {
    data: onlinePTM,
    refetch: onlinePTMRefetch,
    isLoading,
  } = usePTMLinksQuery(selectedStudent);
  const {
    data: offlinePTM,
    refetch: offlineRefetch,
    isLoading: offlinePtmLoading,
  } = useofflinePTMLinksQuery(custom_school);

  useEffect(() => {
    onlinePTMRefetch();
    offlineRefetch();
  }, [onlinePTMRefetch, offlineRefetch]);

  const rows2 = offlinePTM?.data?.message?.map?.((element: any) => {
    if (element?.event?.includes("PTM")) {
      const startDate = new Date(element?.start);
      const formattedStartDate = startDate
        .toLocaleDateString("en-GB")
        .replace(/\//g, "-");
      return (
        <>
          <tr>
            <td>
              <Text sx={{ color: studentProfileColor }}>{element?.event}</Text>
            </td>
            <td>
              <Text sx={{ color: studentProfileColor }}>
                {formattedStartDate}
              </Text>
            </td>
          </tr>
        </>
      );
    }
  });

  const renderedElements = useMemo(() => {
    const colors = [
      "#fe7f00",
      "#00a8ff",
      "#019837",
      "#d21eff",
      "#ff0000",
      "#00ff00",
      "#0000ff",
    ];

    return onlinePTM?.data?.message?.map((element: any, index: number) => {
      const endDate = new Date(element?.date);
      const formattedEndDate = endDate
        .toLocaleDateString("en-GB")
        .replace(/\//g, "-");
      const colorIndex = index % colors.length;
      const color = colors[colorIndex];

      return (
        <div
          key={index}
          style={{
            borderTop: `1px solid ${color}`,
            marginTop: "1rem",
            padding: "1rem 0px",
            position: "relative",
            marginBottom: "1rem",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "0px 1rem",
              gap: "1rem",
            }}
          >
            <Text sx={{ color: color }}>
              Date: {formattedEndDate} ({element?.day})
            </Text>
            <span
              style={{
                border: `1px solid ${color}`,
                width: "1px",
                height: "30px",
              }}
            ></span>
            <Text sx={{ color: color }}>Time: {element?.slot}</Text>
          </div>
          <Text
            sx={{ color: color }}
            style={{
              display: "flex",
              alignItems: "center",
              padding: "0px 1rem",
              margin: "1rem auto",
              justifyContent: "center",
              gap: "0.5rem",
            }}
          >
            Subject:{" "}
            <span style={{ fontWeight: "bold", padding: "0 5px" }}>
              {" "}
              {element?.subject}
            </span>
          </Text>
          <div
            style={{
              margin: "5px auto",
              width: "250px",
              position: "absolute",
              left: "0px",
              right: "0px",
              bottom: "0px",
              height: "10px",
              marginBottom: "1rem",
            }}
          >
            <Rows element={element} studentProfileColor={studentProfileColor} />
          </div>
        </div>
      );
    });
  }, [onlinePTM?.data?.message]);
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
      <Box
        sx={{
          border: "1px solid " + studentProfileColor + "77",
          margin: 20,
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
          <Text
            sx={{
              color: "black",
              fontWeight: "bold",
            }}
          >
            Upcoming Online PTMs
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
        {isLoading ? (
          <Text align="center" color="dimmed" weight="bold" my={30}>
            Loading...
          </Text>
        ) : (
          <Box
            sx={{
              textAlign: "center",
            }}
          >
            <>
              {onlinePTM?.data?.message?.length > 0 ? (
                <>
                  <Box sx={{ textAlign: "center" }}>{renderedElements}</Box>
                </>
              ) : (
                <>
                  <Text
                    sx={{
                      margin: "10px 0",
                      color: "black",
                      fontWeight: "bold",
                    }}
                  >
                    There is no Online PTM Scheduled
                  </Text>
                </>
              )}
            </>
          </Box>
        )}
      </Box>

      <Box
        sx={{
          border: "1px solid " + studentProfileColor + "77",
          margin: 20,
          borderRadius: 10,
          textAlign: "center",
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
          <Text
            sx={{
              color: "black",
              fontWeight: "bold",
            }}
          >
            Offline PTMs Scheduled
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
        {offlinePtmLoading ? (
          <Text align="center" color="dimmed" weight="bold" my={30}>
            Loading...
          </Text>
        ) : (
          <Box
            sx={{
              textAlign: "center",
            }}
          >
            <>
              {offlinePTM?.data?.message?.length > 0 ? (
                <div style={{ marginTop: "1rem" }}>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "start",
                      flexDirection: "column",
                      justifyContent: "start",
                    }}
                  >
                    <Table horizontalSpacing="md">
                      <thead
                        style={{ backgroundColor: studentProfileColor + "22" }}
                      >
                        <tr>
                          <td>
                            {" "}
                            <Text
                              sx={{
                                borderBottom: `1px solid #dee2e6`,
                                color: studentProfileColor,
                                fontWeight: "bold",
                              }}
                            >
                              PTM Event
                            </Text>
                          </td>
                          <td>
                            {" "}
                            <Text
                              sx={{
                                borderBottom: `1px solid #dee2e6`,
                                color: studentProfileColor,
                                fontWeight: "bold",
                              }}
                            >
                              Date
                            </Text>
                          </td>
                        </tr>
                      </thead>
                      <tbody>{rows2}</tbody>
                    </Table>
                  </Box>
                </div>
              ) : (
                <>
                  <Text
                    sx={{
                      margin: "10px 0",
                      color: "black",
                      fontWeight: "bold",
                    }}
                  >
                    There is no Offline PTM Scheduled
                  </Text>
                </>
              )}
            </>
          </Box>
        )}
      </Box>
    </Box>
  );
};

const Rows = ({
  element,
  studentProfileColor,
}: {
  element: any;
  studentProfileColor: string;
}) => {
  const isLinkedEnable = isTimeBeforeCurrent(
    element?.slot,
    new Date(),
    element?.date
  );
  const [reRender, setRerender] = useState(0);

  useEffect(() => {
    const timeoutRef = setTimeout(() => {
      setRerender((reRender) => reRender + 1);
    }, 30000);
    return () => {
      clearTimeout(timeoutRef);
    };
  }, [reRender]);

  return (
    <>
      {
        <a
          aria-disabled={!isLinkedEnable}
          href={element.gmeet_link}
          target="__blank"
          style={{
            textDecoration: "none",
            opacity: isLinkedEnable ? 1 : 0.5,
            cursor: isLinkedEnable ? "pointer" : "not-allowed",
          }}
          onClick={(e) => {
            if (!isLinkedEnable) {
              e.preventDefault();
            }
          }}
        >
          <Text
            sx={{
              backgroundColor: studentProfileColor,
              borderRadius: "25px",
            }}
            style={{ color: "white", padding: "1px" }}
          >
            JOIN PTM VIA LINK
          </Text>
        </a>
      }
    </>
  );
};

function isToday(dateString: string) {
  const today = new Date();

  const parsedDate = new Date(dateString);

  // Check if the parsed date is equal to today's date
  return (
    parsedDate.getDate() === today.getDate() &&
    parsedDate.getMonth() === today.getMonth() &&
    parsedDate.getFullYear() === today.getFullYear()
  );
}
