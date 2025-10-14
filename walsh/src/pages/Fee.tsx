import { Box, Stack, Text, Table } from "@mantine/core";
import useStudentList from "../components/queries/useStudentList";
import { useEffect, useMemo, useState } from "react";
import useStudentProfileColor from "../components/hooks/useStudentProfileColor";
import useClassDetails from "../components/queries/useClassDetails";
import { useSearchParams } from "react-router-dom";

interface PaymentSchedule {
  data: any;
}
interface PaymentDetails {
  status: string;
  payment_term: string;
  data: any;
  payment_url: string;
  grand_total: number;
}

export const Fee = () => {
  const { data: studentsList } = useStudentList();
  const [selectedStudent, setSelectedStudent] = useState<string>("");
  const studentProfileColor = useStudentProfileColor(selectedStudent);
  const { data: classDetails } = useClassDetails(selectedStudent);

  const [searchParams] = useSearchParams();
  const [paymentRequests, setPaymentRequests] = useState<string[]>([]);
  const [studentFee, setStudentFee] = useState("");
  const [paymentSchedule, setPaymentSchedule] = useState<PaymentSchedule[]>([]);
  const [payDeatils, setPayDetails] = useState<PaymentDetails | undefined>(
    undefined
  );
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  useEffect(() => {
    const fetchFeesData = async () => {
      try {
        setLoading(true);
        if (!selectedStudent) {
          setError("No student selected");
          setPaymentSchedule([]);
          setLoading(false);
          return;
        }
        const response = await fetch(
          `/api/resource/Fees?filters=[["student", "=", "${selectedStudent}"]]`
        );
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        const data = await response.json();
        setStudentFee(data?.data?.[0]?.name);
        setError(null);
      } catch (error: any) {
        console.log("error", error);
        setError(error.message || "Error fetching fee data");
        setPaymentSchedule([]);
      } finally {
        setLoading(false);
      }
    };

    fetchFeesData();
  }, [selectedStudent]);
  useEffect(() => {
    const paymentRequest = async (select_student: string) => {
      try {
        setLoading(true);
        if (!select_student) {
          setError("No student selected");
          setPaymentRequests([]);
          setLoading(false);
          return;
        }
        const response = await fetch(
          `/api/resource/Payment%20Request?filters=[["party","=", "${select_student}"],["reference_name","like","%252024-2025%25"],["docstatus","=","1"]]`
        );
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        const data = await response.json();
        const paymentNames = data?.data?.map?.((i: any) => i?.name) || [];

        setPaymentRequests(paymentNames);
        setError(null);
      } catch (error: any) {
        console.log("error", error);
        setError(error.message || "Error fetching payment requests");
        setPaymentRequests([]);
      } finally {
        setLoading(false);
      }
    };

    paymentRequest(selectedStudent);
  }, [selectedStudent]);

  useEffect(() => {
    const paymentRequestDetails = async () => {
      try {
        setLoading(true);
        if (paymentRequests.length === 0) {
          setError("No payment schedule available");
          setPayDetails(undefined);
          setLoading(false);
          return;
        }
        for (let name of paymentRequests) {
          const response = await fetch(
            `/api/resource/Payment%20Request/${name}`
          );
          if (!response.ok) {
            throw new Error("Network response was not ok");
          }
          const data = await response.json();
          setPayDetails(data?.data);
        }
        setError(null);
      } catch (error: any) {
        setError(error.message || "Error fetching payment request details");

        console.log("error", error);
        setPayDetails(undefined);
      } finally {
        setLoading(false);
      }
    };

    paymentRequestDetails();
  }, [paymentRequests]);

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
  }, [searchedStudent, selectedStudent, students]);

  const fetchFeesDetails = async () => {
    try {
      setLoading(true);
      if (!studentFee) {
        setError("No payment schedule available");
        setPaymentSchedule([]);
        setLoading(false);
        return;
      }
      const response = await fetch(`/api/resource/Fees/${studentFee}`);
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      const data = await response.json();
      setPaymentSchedule(data?.data?.payment_schedule);
      setError(null);
    } catch (error: any) {
      console.log("error", error);
      setError(error.message || "Error fetching fee details");
      setPaymentSchedule([]);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    fetchFeesDetails();
  }, [studentFee]);
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
                  // handleChange(e);
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
            sx={
              {
                // textAlign: "center",
              }
            }
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
            ></div>
            {loading && (
              <Text align="center" color="dimmed" weight="bold" my={30}>
                Loading...
              </Text>
            )}
            {!loading && error && (
              <Text
                color="dimmed"
                weight="bold"
                my={30}
                sx={{ textAlign: "center" }}
              >
                {error}
              </Text>
            )}
            <>
              <div>
                <Table>
                  <thead>
                    <tr>
                      <th>
                        <Text>Term</Text>
                      </th>
                      <th>
                        <Text>DueDate</Text>
                      </th>
                      <th>
                        <Text>Amount</Text>
                      </th>
                      <th>
                        <Text>Status</Text>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {!loading &&
                      paymentSchedule?.map?.((i: any) => {
                        const formatDate = (dateString: string) => {
                          const date = new Date(dateString);
                          const day = String(date.getDate()).padStart(2, "0");
                          const month = String(date.getMonth() + 1).padStart(
                            2,
                            "0"
                          );
                          const year = date.getFullYear();
                          return `${day}-${month}-${year}`;
                        };
                        return (
                          <>
                            <tr>
                              <td>
                                <Text>{i?.payment_term}</Text>
                              </td>
                              <td>
                                <Text>{formatDate(i?.due_date)}</Text>
                              </td>
                              <td>
                                <Text>₹{payDeatils?.grand_total}</Text>
                              </td>
                              <td>
                                <Text>
                                  {payDeatils?.status === "Paid" &&
                                  payDeatils?.payment_term ===
                                    i?.payment_term ? (
                                    <a
                                      href={payDeatils?.payment_url}
                                      target="_blank"
                                      style={{
                                        color: "white",
                                        textDecoration: "none",
                                        padding: "5px 0.5rem",
                                        background: "rgb(126 34 206)",
                                        borderRadius: "5px",
                                        border: "1px solid green",
                                      }}
                                    >
                                      Download
                                    </a>
                                  ) : payDeatils?.status === "Initiated" &&
                                    payDeatils?.payment_term ===
                                      i?.payment_term ? (
                                    <a
                                      href={payDeatils?.payment_url}
                                      target="_blank"
                                      style={{
                                        color: "white",
                                        textDecoration: "none",
                                        padding: "5px 1rem",
                                        background: "rgb(126 34 206)",
                                        borderRadius: "5px",
                                        border: "1px solid green",
                                        minWidth: "10px",
                                      }}
                                    >
                                      Pay Now
                                    </a>
                                  ) : (
                                    <label>Not Due</label>
                                  )}
                                </Text>
                              </td>
                            </tr>
                          </>
                        );
                      })}
                  </tbody>
                </Table>
              </div>
            </>
          </Box>
        </Box>
      </Box>
    </>
  );
};
