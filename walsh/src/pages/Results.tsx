import { Box, Stack, Text, Select, Tabs } from "@mantine/core";
import useStudentList from "../components/queries/useStudentList";
import { useEffect, useMemo, useState } from "react";
import useStudentProfileColor from "../components/hooks/useStudentProfileColor";
import { useSearchParams } from "react-router-dom";
import useClassDetails from "../components/queries/useClassDetails";

import {
  useAcademicCurrentYear,
  useAcademicNextYear,
} from "../components/queries/useFeeDetailsList";
import usePrintFormat from "../components/queries/usePrintFormat";
import useSchoolLetterHead from "../components/queries/useSchoolLetterHead";

interface PrintFormat {
  html: string;
  style: string;
}

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
  const [printFormatMode, setPrintFormatMode] = useState<"result" | "marks">(
    "result"
  );

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
  const [, setSelectedUnitExam] = useState("");
  const [searchParams] = useSearchParams();
  const searchedStudent = searchParams.get("student");
  const [selectedSubject, setSelectedSubject] = useState<string>("");
  const { data: assessmentGroupData } = usePrintFormat(selectedExam);
  const { data: letterHeadData } = useSchoolLetterHead(
    assessmentGroupData?.data?.data?.custom_school
  );
  console.log(letterHeadData);

  const examName = examResult?.map?.((i: any) => i?.name);
  const assessmentGroupFilter = async (
    selected_year: string,
    class_name: any
  ) => {
    try {
      const resp = await fetch(
        `/api/resource/Assessment%20Group?filters=[["custom_academic_year",%20"=",%20"${selected_year}"],["custom_program",%20"=",%20"${class_name}"],["custom_show_in_app","=", "1"]]`
      );
      if (!resp.ok) {
        throw new Error("No Result Found");
      }
      const data = await resp.json();
      if (data?.data?.length < 1) {
        setErrorMessage("Result Not Found");
        setPrintFormat({ html: "", style: "" });
        setSelectedExam("");
        setExamOptions([]);
      }
      if (data?.data?.length > 0) {
        const groupNames = data?.data?.map?.((i: any) => i.name);

        const examOpts = groupNames?.map?.((name: string) => ({
          value: name,
          label: name,
        }));

        assessmentGroupName(examOpts);
      }
    } catch (error) {
      console.log("error", error);
    }
  };
  console.log(letterHeadData?.data?.data?.letter_head, "eetr");
  const params = {
    doctype: "Assessment Result",
    name: examName[0],
    program: classDetails?.data?.message?.division?.program,
    format:
      printFormatMode == "result"
        ? assessmentGroupData?.data?.data.custom_print_configuration
        : assessmentGroupData?.data?.data.result_print_format,
    no_letterhead: 0,
    letterhead:
      letterHeadData?.data?.data?.letter_head || "Default letter head",
    _lang: "en",
  };

  const generateQueryString = (params: any) => {
    return Object.keys(params)
      .map(
        (key) => encodeURIComponent(key) + "=" + encodeURIComponent(params[key])
      )
      .join("&");
  };

  const assessmentGroupName = async (exam_options: any) => {
    const examnames: any[] = [];
    try {
      for (const name of exam_options) {
        const resp = await fetch(
          `/api/resource/Assessment%20Group/${name.value}`
        );
        if (!resp.ok) {
          throw new Error("No Result Found");
        }
        const data = await resp.json();
        examnames.push(data?.data);

        const options = examnames?.map?.((i: any) => ({
          value: i.name,
          label: i.assessment_group_name,
        }));
        setExamOptions(options);
      }
    } catch (error) {
      console.log("error", error);
    }
  };

  // const handleDownloadPdf = () => {
  //   const input = document.getElementById("print-format-container");
  //   if (input) {
  //     const scale = 8;
  //     html2canvas(input, { scale }).then((canvas) => {
  //       const imgData = canvas.toDataURL("image/png", 1.0);
  //       const pdf = new jsPDF("p", "mm", "a4");
  //       const imgWidth = 210; // A4 width in mm
  //       const pageHeight = 297; // A4 height in mm
  //       const imgHeight = (canvas.height * imgWidth) / canvas.width;
  //       let heightLeft = imgHeight;
  //       let position = 0;

  //       pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
  //       heightLeft -= pageHeight;

  //       while (heightLeft >= 0) {
  //         position = heightLeft - imgHeight;
  //         pdf.addPage();
  //         pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
  //         heightLeft -= pageHeight;
  //       }
  //       const download_name = `${selectedStudent} ${selectedUnitExam}`;
  //       pdf.save(download_name);
  //     });
  //   }
  // };
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
        setPrintFormat({ html: "", style: "" });
        setSelectedExam("");

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
      const printFormat =
        printFormatMode == "result"
          ? assessmentGroupData?.data?.data.custom_print_configuration
          : assessmentGroupData?.data?.data.result_print_format;

      if (!printFormat) {
        setError("No Result Format");
        throw new Error("No Result Format");
      }

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
            format: printFormat,
            no_letterhead: 0,
            letterhead:
              letterHeadData?.data?.data?.letter_head || "Default letter head",
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

      setError("Select year and exam");
      setErrorTrue(true);
    }
  }, [
    examName[0],
    assessmentGroupData,
    printFormatMode,
    classDetails?.data?.message?.division?.program,
    selectedStudent,
    setError,
    selectedExam,
  ]);

  const handleExamChange = (e: any) => {
    setSelectedExam(e);
    const selectedLabel =
      examOptions.find((option) => option.value === e)?.label || "";
    setSelectedUnitExam(selectedLabel);
    assessmentResuktFilter(selectedYear, e);
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
    setSelectedYear(e);
    assessmentGroupFilter(e, classDetails?.data?.message?.division?.program);
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
    setSelectedUnitExam("");
  };

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

              <Select
                style={{
                  border: "none",
                  borderRadius: "8px",
                  boxShadow: "none",
                  width: "25vh",
                  padding: "8px",
                }}
                value={selectedYear}
                onChange={(value) => handleYearChange(value)}
                placeholder="Select Year"
                data={years.map((year) => ({ value: year, label: year }))}
              />
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

              <Select
                style={{
                  border: "none",
                  borderRadius: "8px",
                  boxShadow: "none",
                  width: "25vh",
                  padding: "8px",
                }}
                value={selectedExam}
                onChange={handleExamChange}
                placeholder="Select Year"
                data={examOptions}
              />
            </div>
          </div>
          {selectedExam ? (
            <Tabs
              value={printFormatMode}
              onTabChange={(value) => {
                if (value == "marks" || value == "result")
                  setPrintFormatMode(value);
              }}
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
                <Tabs.Tab
                  value="marks"
                  disabled={
                    !assessmentGroupData?.data?.data.result_print_format
                  }
                >
                  Marks
                </Tabs.Tab>
                <Tabs.Tab
                  value="result"
                  disabled={
                    !assessmentGroupData?.data?.data.custom_print_configuration
                  }
                >
                  Results
                </Tabs.Tab>
              </Tabs.List>
            </Tabs>
          ) : null}
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
                <div
                  id="print-format-container"
                  style={{ marginTop: "2rem" }}
                  dangerouslySetInnerHTML={{ __html: combinedHtml }}
                  className="print-format-gutter print-format"
                />
                <a
                  href={`/api/method/frappe.utils.print_format.download_pdf?${generateQueryString(
                    params
                  )}`}
                  style={{
                    margin: "0px auto",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    borderRadius: 10,

                    bottom: "16rem",
                    color: "white",
                    maxWidth: "75%",
                    textDecoration: "none",
                    padding: "8px 4px",
                    backgroundColor: studentProfileColor,
                    textAlign: "center",
                    marginTop: "1rem",
                  }}
                >
                  Download
                </a>
              </div>
            </>
          )}
        </Box>
      </Box>
    </>
  );
};
