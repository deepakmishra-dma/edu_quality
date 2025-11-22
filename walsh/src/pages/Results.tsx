import { Box, Stack, Text, Button } from "@mantine/core";
import useStudentList from "../components/queries/useStudentList";
import { useEffect, useMemo, useState } from "react";
import useStudentProfileColor from "../components/hooks/useStudentProfileColor";
import { useSearchParams } from "react-router-dom";
import useClassDetails from "../components/queries/useClassDetails";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";

import {
  useAcademicCurrentYear,
  useAcademicNextYear,
} from "../components/queries/useFeeDetailsList";

interface PrintFormat {
  html: string;
  style: string;
}
const handleDownloadPdf = () => {
  const input = document.getElementById("print-format-container");
  if (input) {
    html2canvas(input).then((canvas) => {
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF();
      const imgWidth = 210; // A4 width in mm
      const pageHeight = 297; // A4 height in mm
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      let heightLeft = imgHeight;
      let position = 0;

      pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;

      while (heightLeft >= 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }

      pdf.save("download.pdf");
    });
  }
};
export const Results = () => {
  const [selectedStudent, setSelectedStudent] = useState<string>("");

  const { data: studentsList } = useStudentList();
  const [errorTrue, setErrorTrue] = useState(true);
  const [loading, setLoading] = useState(false); // Loading state
  const [error, setError] = useState<string>("null");
  const { data: classDetails } = useClassDetails(selectedStudent);
  const [selectedUnit, setSelectedUnit] = useState<string>("unit 1");
  const [years, setYears] = useState<string[]>([]);
  const [examResult, setExamResult] = useState<string[]>([]);
  const [examOptions, setExamOptions] = useState<
    { value: string; label: string }[]
  >([]);
  const [selectedYear, setSelectedYear] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [selectedExam, setSelectedExam] = useState("");
  const [printFormat, setPrintFormat] = useState<PrintFormat>({
    html: "",
    style: "",
  });
  const { data: current_year } = useAcademicCurrentYear();
  const { data: next_year } = useAcademicNextYear();
  const studentProfileColor = useStudentProfileColor(selectedStudent);

  const [searchParams] = useSearchParams();
  const searchedStudent = searchParams.get("student");
  const [selectedSubject, setSelectedSubject] = useState<string>("");
  const examName = examResult?.map?.((i: any) => i?.name);
  const assessmentGroupFilter = async (
    selected_year: string,
    class_name: any
  ) => {
    try {
      const resp = await fetch(
        `/api/resource/Assessment%20Group?filters=[["custom_academic_year",%20"=",%20"${selected_year}"],["custom_program",%20"=",%20"${class_name}"]]`
      );
      if (!resp.ok) {
        throw new Error("No Result Found");
      }
      const data = await resp.json();
      if (data?.data?.length < 1) {
        setErrorMessage("Result Not Found");
        // setExamOptions({});
      }
      if (data?.data?.length > 0) {
        const groupNames = data?.data?.map?.((i: any) => i.name);

        const examOpts = groupNames?.map?.((name: string) => ({
          value: name,
          label: name,
        }));
        setExamOptions(examOpts);
      }
    } catch (error) {
      console.log("error", error);
    }
  };

  const assessmentResuktFilter = async (
    selected_year: string,
    selected_exam: string
  ) => {
    try {
      const resp = await fetch(
        `/api/resource/Assessment%20Result?filters=[["academic_year", "=", "${selected_year}"], ["assessment_group", "=", "${selected_exam}"], ["program", "=", "${classDetails?.data?.message?.division?.program}"], ["student", "=", "${selectedStudent}"], ["docstatus", "=", "1"]]`
      );
      if (!resp.ok) {
        throw new Error("No Result Found");
      }
      const data = await resp.json();

      if (data?.data?.length < 1) {
        setErrorMessage("Result Not Found");
        setExamResult([]); // Clear previous results
      } else {
        setExamResult(data?.data);
        setErrorMessage(""); // Clear any previous error messages
      }
    } catch (error) {
      console.log("error", error);
    }
  };

  const printFormatView = async (exam_name: any, class_name: any) => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(
        `/api/method/frappe.www.printview.get_html_and_style?`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            doc: "Assessment Result",
            name: `${exam_name}`,
            program: class_name,
            print_format: "Report_Print_Configuration_Unit_test_format",
            no_letterhead: 0,
            letterhead: "Default letter head",
            _lang: "en",
          }),
        }
      );
      if (!response.ok) {
        setError("No Result Found");
      }

      const responseData = await response.text();
      if (responseData.trim() === "") {
        throw new Error("Empty response data");
      }
      const data = JSON.parse(responseData); // Parse JSON
      const printResp = data?.message || {};

      const style = document.createElement("style");
      style.innerHTML = printResp?.style || "";
      document.head.appendChild(style);

      setPrintFormat(printResp);
    } catch (error: any) {
      setError(error.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (examName[0] && classDetails?.data?.message?.division?.program) {
      setErrorTrue(false);
      printFormatView(
        examName[0],
        classDetails?.data?.message?.division?.program
      );
    }
    if (selectedExam === "") {
      setPrintFormat({ html: "", style: "" });
      printFormatView(undefined, undefined);
      setError("");
      setErrorTrue(true);
    }
  }, [
    examName[0],
    classDetails?.data?.message?.division?.program,
    selectedStudent,
    setError,
    selectedExam,
  ]);

  const handleExamChange = (e: any) => {
    setSelectedExam(e.target.value);

    assessmentResuktFilter(selectedYear, e.target.value);
  };

  const subjectOptions = useMemo(() => {
    return (
      classDetails?.data?.message?.class?.subject?.map?.((subject) => ({
        label: subject.subject,
        value: subject.subject,
      })) || []
    );
  }, [classDetails?.data?.message?.class?.subject]);

  const unitOptions = useMemo(() => {
    return [...Array(4)].map((_, i) => ({
      label: `Unit ${i + 1}`,
      value: `${i + 1}`,
    }));
  }, []);

  const students = useMemo(
    () => studentsList?.data?.message || [],
    [studentsList?.data]
  );

  useEffect(() => {
    if (current_year?.data?.data || next_year?.data?.data) {
      const currentYears =
        current_year?.data?.data?.map?.((i: any) => i?.name) || [];
      const nextYears = next_year?.data?.data?.map?.((i: any) => i?.name) || [];
      const combinedYears = Array.from(
        new Set([...currentYears, ...nextYears])
      );
      setYears((prevYears) => {
        const updatedYears = Array.from(
          new Set([...prevYears, ...combinedYears])
        );
        return updatedYears?.sort();
      });
    }
  }, [current_year, next_year, selectedStudent]);

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

  const handleYearChange = (e: any) => {
    setSelectedYear(e.target.value);
    assessmentGroupFilter(
      e.target.value,
      classDetails?.data?.message?.division?.program
    );
  };

  let html = printFormat?.html;

  let style = printFormat.style;

  let combinedHtml = `
    <style>${style}</style>
    ${html}
  `;

  const clearFilters = () => {
    setSelectedYear("");
    setSelectedExam("");
    setExamOptions([]);
    setErrorMessage("");
  };
  console.log("errorMessage", errorMessage);

  return (
    <>
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
          {students?.map?.((student, index) => {
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
                onClick={() => {
                  clearFilters();
                  setSelectedStudent(student.name);
                }}
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
            margin: 30,
            borderRadius: 10,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              flexDirection: "column",
              justifyContent: "center",

              gap: "1rem",
              marginTop: "1rem",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "1rem",
              }}
            >
              <span style={{ color: studentProfileColor }}>Academic Year:</span>

              <select
                style={{
                  backgroundColor: "#f3f3f3",
                  border: "none",
                  borderRadius: "8px",
                  boxShadow: "none",
                  width: "25vh",
                  padding: "8px",
                }}
                value={selectedYear}
                onChange={handleYearChange}
              >
                <option value="">Select Year</option>
                {years.map?.((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "1.8rem",
              }}
            >
              <span style={{ color: studentProfileColor }}>Select Exam:</span>
              <select
                style={{
                  backgroundColor: "#f3f3f3",
                  border: "none",
                  borderRadius: "8px",
                  boxShadow: "none",
                  width: "25vh",
                  padding: "8px",
                }}
                value={selectedExam}
                onChange={handleExamChange}
              >
                <option value="">Select Exam</option>
                {examOptions.map?.((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {errorMessage && (
            <div
              className="error-message"
              style={{
                textAlign: "center",
                fontWeight: "bold",
                color: "red",
                marginTop: "1rem",
              }}
            >
              {errorMessage}
            </div>
          )}
          {errorTrue ||
            (loading && (
              <p
                style={{
                  textAlign: "center",
                  fontWeight: "bold",
                  color: "gray",
                  marginTop: "1rem",
                }}
              >
                Loading...
              </p>
            ))}

          {errorTrue ||
            (error && (
              <p
                className="error"
                style={{
                  textAlign: "center",
                  fontWeight: "bold",
                  color: "red",
                  marginTop: "1rem",
                }}
              >
                {error}
              </p>
            ))}
          {!loading && !error && (
            <>
              <div>
                <Button
                  onClick={handleDownloadPdf}
                  sx={{
                    margin: "0px auto",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    borderRadius: 10,
                    backgroundColor: studentProfileColor,
                    textAlign: "center",
                    marginTop: "1rem",
                  }}
                >
                  Download
                </Button>
                <div
                  id="print-format-container"
                  style={{ marginTop: "2rem" }}
                  dangerouslySetInnerHTML={{ __html: combinedHtml }}
                  className="print-format-gutter print-format"
                />
              </div>
            </>
          )}
        </Box>
      </Box>
    </>
  );
};
