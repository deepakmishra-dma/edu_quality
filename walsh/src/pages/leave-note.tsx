import {
  Box,
  Button,
  Stack,
  Sx,
  Text,
  Textarea,
  Tabs,
  Grid,
} from "@mantine/core";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import useStudentList from "../components/queries/useStudentList.ts";
import useClassDetails from "../components/queries/useClassDetails.ts";
import useStudentProfileColor from "../components/hooks/useStudentProfileColor.ts";
import { IconList } from "@tabler/icons";

import { DatePicker } from "@mantine/dates";
import useLeaveNote from "../components/queries/useLeaveNoteMutation.ts";
import usePastLeaveNotes from "../components/queries/usePastLeaveNotes.ts";

const styling: { [key: string]: (color: string) => Sx } = {
  dateSelect: (color: string) => ({
    margin: 10,
    textAlign: "left",
    ".mantine-DatePicker-label": {
      color: color,
      ".mantine-Input-input": {
        color: color,
      },
    },
    ".mantine-DatePicker-dropdown": {
      '.mantine-Select-item[data-hovered="true"]': {
        backgroundColor: color,
      },
    },
    ".mantine-Input-input": {
      color: color,
      ":active": {
        borderColor: color,
      },
      ":focus": {
        borderColor: color,
      },
    },
  }),
};

const LeaveNote = () => {
  const [selectedStudent, setSelectedStudent] = useState<string>("");
  const [selectedSubject, setSelectedSubject] = useState<string>("");
  const [selectedUnit, setSelectedUnit] = useState<string>("unit 1");
  const [fromDate, setFromDate] = useState<Date | null>(null);
  const [toDate, setToDate] = useState<Date | null>(null);
  const [note, setNote] = useState<string>("");
  const [sickLeave, setSickLeave] = useState<"sick" | "leave">("sick");
  const [success, setSuccess] = useState(false);

  const [searchParams, setSearchParams] = useSearchParams();
  const searchedStudent = searchParams.get("student");

  const { data: studentsList } = useStudentList();
  const {
    data: classDetails,
    error: classError,
    isFetching: classLoading,
  } = useClassDetails(selectedStudent);

  const {
    data: pastNotes,
    error: noteError,
    isFetching: noteLoading,
  } = usePastLeaveNotes(selectedStudent);

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

  // useEffect(() => {
  //   if (!selectedStudent && searchedStudent && selectedStudent != searchedStudent) {
  //     setSelectedStudent(searchedStudent)
  //   }
  // }, [searchedStudent, selectedStudent]);

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
  const notEnrolledInProgram =
    classLoading ||
    classError ||
    !classDetails?.data?.message ||
    Object.keys(classDetails?.data?.message).length == 0;
  useEffect(() => {
    if (fromDate && toDate && fromDate > toDate) {
      setToDate(fromDate);
    }
  }, [fromDate, toDate]);

  useEffect(() => {
    if (success) setSuccess(false);
  }, [selectedStudent]);

  const { mutateAsync, isLoading } = useLeaveNote();

  const clearForm = () => {
    setSelectedSubject("");
    setSelectedUnit("");
    setFromDate(null);
    setToDate(null);
    setNote("");
    setSickLeave("sick");
  };

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
        <>
          <Tabs
            defaultValue="create"
            styles={{
              tabsList: {
                borderBottom: "1px solid " + studentProfileColor + "77",
                margin: "10px 20px",
                marginTop: 20,
                // borderTopLeftRadius: "10px",
                // borderTopRightRadius: "10px",
                backgroundColor: studentProfileColor + "22",
                color: studentProfileColor,
              },
              tab: {
                "&[data-active]": {
                  borderColor: studentProfileColor,
                  color: studentProfileColor,
                },
              },
            }}
          >
            <Tabs.List>
              <Tabs.Tab value="create">Create</Tabs.Tab>
              <Tabs.Tab value="past">Past Notes</Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="create">
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
                        students.find(
                          (student) => student.name === selectedStudent
                        )?.reference_number
                      }
                    </Text>
                  )}
                </Stack>
                <Box
                  sx={{
                    textAlign: "center",
                  }}
                >
                  {success ? (
                    <>
                      <Text
                        sx={{
                          margin: "20px 0",
                          color: studentProfileColor,
                        }}
                      >
                        Note is saved successfully
                      </Text>
                    </>
                  ) : (
                    <>
                      <DatePicker
                        placeholder="Pick date"
                        label="From"
                        value={fromDate}
                        onChange={(date) => {
                          setFromDate(date);
                        }}
                        sx={styling.dateSelect(studentProfileColor)}
                        icon={
                          <IconList color={studentProfileColor} stroke={1} />
                        }
                      />
                      <DatePicker
                        placeholder="Pick date"
                        label="To"
                        value={toDate}
                        minDate={fromDate || undefined}
                        onChange={(date) => {
                          setToDate(date);
                        }}
                        sx={styling.dateSelect(studentProfileColor)}
                        icon={
                          <IconList color={studentProfileColor} stroke={1} />
                        }
                      />
                      <Textarea
                        placeholder="Your Note (max 140 characters)"
                        label="Your Note"
                        maxLength={140}
                        value={note}
                        onChange={(event) => setNote(event.currentTarget.value)}
                        withAsterisk
                        sx={{
                          margin: 10,
                          textAlign: "left",
                          ".mantine-Textarea-label": {
                            color: studentProfileColor,
                          },
                          ".mantine-Input-input": {
                            minHeight: 150,
                            color: studentProfileColor,
                            padding: 5,
                            ":focus": {
                              border: `1px solid ${studentProfileColor}`,
                            },
                          },
                        }}
                      />
                      <Button
                        loading={isLoading}
                        sx={{
                          marginBottom: 10,
                          marginTop: 10,
                          borderRadius: 10,
                          backgroundColor: studentProfileColor,
                        }}
                        onClick={() => {
                          if (!fromDate || !toDate || !note || !sickLeave)
                            return;
                          const dates = [];
                          const from = new Date(fromDate);
                          const to = new Date(toDate);
                          const delay = new Date().getTimezoneOffset();
                          // to get local formatted string from iso string
                          from.setMinutes(from.getMinutes() - delay);
                          to.setMinutes(to.getMinutes() - delay);
                          console.log();
                          for (
                            let i = from;
                            i <= to;
                            i.setDate(i.getDate() + 1)
                          ) {
                            dates.push(i.toISOString().split("T")[0]);
                          }
                          mutateAsync({
                            student: selectedStudent,
                            dates: dates,
                            note: note,
                            start_date: dates.at(0) as string,
                            end_date: dates.at(-1) as string,
                            program: classDetails?.data?.message?.program?.name,
                            status: sickLeave,
                          }).then(() => {
                            clearForm();
                            setSuccess(true);
                          });
                        }}
                      >
                        Save
                      </Button>
                    </>
                  )}
                </Box>
              </Box>
            </Tabs.Panel>

            <Tabs.Panel value="past">
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
                        students.find(
                          (student) => student.name === selectedStudent
                        )?.reference_number
                      }
                    </Text>
                  )}
                </Stack>
                <Box
                  sx={{
                    textAlign: "center",
                  }}
                >
                  {!noteError &&
                    !noteLoading &&
                    pastNotes &&
                    pastNotes.data.message &&
                    pastNotes.data.message.map((pastNote) => (
                      <Grid>
                        <Grid.Col span={6} py={12}>
                          <Text size={"sm"}> {pastNote.date}</Text>
                        </Grid.Col>
                        <Grid.Col span={6} py={12}>
                          <Text size={"sm"}>{pastNote.reason}</Text>
                        </Grid.Col>
                      </Grid>
                    ))}
                </Box>
              </Box>
            </Tabs.Panel>
          </Tabs>
        </>
      )}
    </Box>
  );
};

export default LeaveNote;
