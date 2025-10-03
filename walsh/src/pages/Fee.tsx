import { Box, Stack, Text, Select } from "@mantine/core";
import useStudentList from "../components/queries/useStudentList";
import { useEffect, useMemo, useState } from "react";
import useStudentProfileColor from "../components/hooks/useStudentProfileColor";
import useClassDetails from "../components/queries/useClassDetails";
import { useSearchParams } from "react-router-dom";
import {
  useAcademicCurrentYear,
  useAcademicNextYear,
} from "../components/queries/useFeeDetailsList";
interface PaymentData {
  id: number;
  amount: number;
  data: any;
}
export const Fee = () => {
  const { data: studentsList } = useStudentList();
  const [selectedStudent, setSelectedStudent] = useState<string>("");
  const studentProfileColor = useStudentProfileColor(selectedStudent);
  const { data: classDetails } = useClassDetails(selectedStudent);
  const [years, setYears] = useState<string[]>([]);
  const [selectedName, setSelectedName] = useState<{ name: string }[]>([]);
  const [selectedYear, setSelectedYear] = useState<string | null>(null);
  const [fetchedData, setFetchedData] = useState<PaymentData[]>([]);
  const [searchParams] = useSearchParams();
  const { data: current_year } = useAcademicCurrentYear();
  const { data: next_year } = useAcademicNextYear();
  const [loading, setLoading] = useState(false);

  const fetchAPI = async (year: string | null, student: string | null) => {
    setLoading(true);

    try {
      const response = await fetch(
        `/api/resource/Payment%20Request?filters=[["party","=","${student}"],["reference_name","like","%25${year}%25"],["docstatus","=","1"]]`
      );
      const resp = await response.json();
      setSelectedName(resp?.data);
    } catch (error) {
      console.error("Failed to fetch data", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDetails = async () => {
    setLoading(true);
    try {
      const data = [];
      for (const name of selectedName) {
        const response = await fetch(
          `/api/resource/Payment%20Request/${name?.name}`,
          {
            method: "GET",
            headers: {
              "Content-Type": "application/json",
            },
          }
        );

        if (response.ok) {
          const result = await response.json();
          data.push(result);
        } else {
          console.error(`Failed to record ${name}`);
        }
      }
      setFetchedData(data);
    } catch (err) {
      console.log("error ", err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: any) => {
    setSelectedYear(e);
    setSelectedName([]);
    setFetchedData([]);
    setLoading(true);
    fetchAPI(e, selectedStudent);
  };
  useEffect(() => {
    if (selectedName.length > 0) {
      fetchDetails();
    }
  }, [selectedName]);
  console.log("data", fetchedData);
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
  }, [current_year, next_year]);

  const searchedStudent = searchParams.get("student");

  const students = useMemo(
    () => studentsList?.data?.message || [],
    [studentsList?.data]
  );

  useEffect(() => {
    const studentNames = students?.map?.((student) => student.name) || [];
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
  }, [searchedStudent, selectedStudent, students, selectedName]);
  const extractAcademicYear = (referenceName: any) => {
    const match = referenceName.match(/\((\d{4}-\d{4})\)/);
    return match ? match[1] : "Year not found";
  };
  return (
    <>
      <Box>
        <Stack
          sx={{
            whiteSpace: "nowrap",
            overflow: "auto",
            flexDirection: "row",

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

                  flexShrink: 0,
                  flexGrow: 1,
                  textAlign: "center",
                  minWidth: "33.33%",
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedStudent(student.name);
                  handleChange(e);
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
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                margin: "auto",
                padding: "1rem",
                alignItems: "center",
                gap: "1rem",
              }}
            >
              <Select
                placeholder="Academic Year"
                data={years?.map?.((i) => i)}
                value={selectedYear}
                onChange={handleChange}
              />
            </div>
            {loading ? (
              <>
                <div>Loading....</div>
              </>
            ) : fetchedData.length > 0 ? (
              fetchedData?.map?.((i) => {
                return (
                  <>
                    <div
                      style={{
                        border: `1px solid ${studentProfileColor}`,
                        padding: "0.2rem",
                        margin: "0.5rem",
                        display: "flex",
                        borderRadius: "10px",
                        justifyContent: "start",
                        alignItems: "start",
                        gap: "5rem",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          margin: "0px auto",
                        }}
                      >
                        <span
                          style={{
                            borderRadius: "10px",

                            background: `${
                              i?.data?.status === "Paid"
                                ? "green"
                                : " rgb(254 202 202)"
                            }`,
                            padding: "5px 1rem",
                            color: `${
                              i?.data?.status === "Paid" ? "white" : " red"
                            }`,
                          }}
                        >
                          {i?.data?.status === "Paid"
                            ? "Payment Completed"
                            : "Payment Due"}
                        </span>
                        <div
                          style={{
                            marginTop: "10px",
                          }}
                        >
                          <span style={{ color: studentProfileColor }}>
                            Name:
                          </span>
                          <span>
                            {
                              studentsList?.data?.message?.find(
                                (i) => i?.name === selectedStudent
                              )?.first_name
                            }
                          </span>
                        </div>
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            gap: "1rem",

                            marginTop: "10px",
                          }}
                        >
                          <span style={{ color: studentProfileColor }}>
                            Academic year:
                          </span>
                          <span>
                            {extractAcademicYear(i?.data?.reference_name)}
                          </span>
                        </div>
                        <div
                          style={{
                            marginTop: "10px",
                          }}
                        >
                          <span style={{ color: studentProfileColor }}>
                            Class :
                          </span>
                          <span>
                            {" "}
                            {classDetails?.data?.message?.class?.name}
                          </span>
                        </div>
                        <div
                          style={{
                            marginTop: "10px",
                          }}
                        >
                          <span style={{ color: studentProfileColor }}>
                            Term :
                          </span>
                          <span> {i?.data?.payment_term}</span>
                        </div>
                        <div
                          style={{
                            marginTop: "10px",
                          }}
                        >
                          <span style={{ color: studentProfileColor }}>
                            Amount :
                          </span>
                          <span> {i?.data?.grand_total}</span>
                        </div>
                      </div>
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          position: "relative",

                          top: "150px",
                          alignItems: "end",
                          justifyContent: "end",
                          borderRadius: "10px",
                          padding: "1rem",
                        }}
                      >
                        <a
                          href={i?.data?.payment_url}
                          target="_blank"
                          style={{
                            color: "white",
                            textDecoration: "none",
                            padding: "0px 1rem",
                            background: `${
                              i?.data?.status === "Paid"
                                ? "rgb(126 34 206)"
                                : "rgb(126 34 206)"
                            }`,
                            borderRadius: "5px",
                            gap: "1rem",
                            border: "1px solid green",
                          }}
                        >
                          {i?.data?.status === "Paid" ? "Download" : "Pay Now"}
                        </a>
                      </div>
                    </div>
                  </>
                );
              })
            ) : (
              <div>Not Found</div>
            )}
          </Box>
        </Box>
      </Box>
    </>
  );
};
