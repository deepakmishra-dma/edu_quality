// import { Button, Collapse } from '@mantine/core';
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import useStudentList from "../components/queries/useStudentList.ts";
import useClassDetails from "../components/queries/useClassDetails.ts";
import useStudentProfileColor from "../components/hooks/useStudentProfileColor.ts";
import { Box, Stack, Image } from "@mantine/core";

import { StudentProfleFOrm } from "./StudentProfileForm.tsx";

export const StudentProfle = () => {
  const [selectedStudent, setSelectedStudent] = useState<string>("");

  const [selectedSubject, setSelectedSubject] = useState<string>("");
  const [selectedUnit, setSelectedUnit] = useState<string>("unit 1");

  const [opened, setOpened] = useState(false);

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

  return (
    <>
      <Box>
        <Stack
          sx={{
            whiteSpace: "nowrap",
            overflow: "auto",
            flexDirection: "column",

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
                  textAlign: "left",
                  minWidth: "33.33%",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "0.5rem",
                    background:
                      student.first_name === searchedStudent
                        ? studentProfileColor
                        : "",
                  }}
                  onClick={() => {
                    setSelectedStudent(student.name);
                    setOpened(!opened);
                  }}
                >
                  {`${student.first_name}  -  ${student.reference_number}`}
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className={`icon icon-tabler ${
                      student.name === selectedStudent && opened
                        ? "icon-tabler-chevron-up"
                        : "icon-tabler-chevron-up"
                    } `}
                    width="44"
                    height="44"
                    viewBox="0 0 24 24"
                    stroke-width="1.5"
                    stroke="currentColor"
                    fill="none"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path stroke="none" d="M0 0h24v24H0z" fill="none" />
                    <path
                      d={`${
                        student.name === selectedStudent && !opened
                          ? "M6 15l6 -6l6 6"
                          : "M6 9l6 6l6 -6"
                      }`}
                    />
                  </svg>
                </div>

                <Box
                  sx={{
                    marginTop: isSelected ? 4 : 5,
                    borderBottom: isSelected
                      ? "2px solid " + studentProfileColor
                      : "1px solid #0005",
                  }}
                />
                {student.name === selectedStudent && !opened && (
                  <StudentProfleFOrm
                    student={student}
                    selectedStudent={selectedStudent}
                    studentProfileColor={studentProfileColor}
                    classDetails={classDetails}
                    isSelected={isSelected}
                  />
                )}
              </Box>
            );
          })}
          <Box
            pos="fixed"
            bottom={0}
            left={0}
            right={0}
            style={{
              pointerEvents: "none",
            }}
          >
            <Image
              src={"/assets/edu_quality/walsh/images/walnut-bg-transparent.png"}
              w={"100%"}
            />
          </Box>
        </Stack>
      </Box>
    </>
  );
};
