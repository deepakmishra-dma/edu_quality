import { Box, Stack, Text, Table } from "@mantine/core";
import useStudentList from "../../components/queries/useStudentList";
import { useEffect, useMemo, useState } from "react";
import useStudentProfileColor from "../../components/hooks/useStudentProfileColor";
// import useClassDetails from "../../components/queries/useClassDetails";
import { useSearchParams } from "react-router-dom";
import useFeesList, { Fees } from "../../components/queries/useFeesList";
import useFeesSchedule, {
  FeesSchedule,
} from "../../components/queries/useFeesSchedule";

const paidStatuses: { [x: string]: string } = {
  paid: "Download",
  "partially paid": "Pay Remaining",
};
export const FeesList = () => {
  const { data: studentsList } = useStudentList();
  const [selectedStudent, setSelectedStudent] = useState<string>("");

  const studentProfileColor = useStudentProfileColor(selectedStudent);
  // const { data: classDetails } = useClassDetails(selectedStudent);

  const [searchParams] = useSearchParams();
  const academic_year = searchParams.get("academic_year");
  const {
    data: feesData,
    isLoading: feesLoading,
    isFetching: feesFetching,
    error,
  } = useFeesList(selectedStudent, academic_year);

  const {
    data: scheduleData,
    isLoading: scheduleLoading,
    isFetching: scheduleFetching,
    error: errorInSchedule,
  } = useFeesSchedule(selectedStudent, academic_year);
  const isLoading =
    scheduleLoading || scheduleFetching || feesLoading || feesFetching;

  const scheduleWiseFees = useMemo(() => {
    if (isLoading) {
      return {};
    }
    const copiedFees = feesData?.data?.message.map((el) => ({ ...el }));

    const termMap: { [x: string]: Fees[] } = {};
    copiedFees?.forEach((fee) => {
      if (!termMap[fee.payment_term]) {
        termMap[fee.payment_term] = [fee];
      } else {
        termMap[fee.payment_term].push(fee);
      }
    });

    return termMap;
  }, [feesData, isLoading]);

  const isFeesEmpty = Object.keys(scheduleWiseFees).length == 0;

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
              {academic_year}
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
            {isLoading && (
              <Text align="center" color="dimmed" weight="bold" my={30}>
                Loading...
              </Text>
            )}
            {!isLoading && (error || errorInSchedule || isFeesEmpty) ? (
              <Text
                color="dimmed"
                weight="bold"
                my={30}
                sx={{ textAlign: "center" }}
              >
                {error ? error.message : "No payment schedule available"}
              </Text>
            ) : null}
            <>
              <div>
                {!isFeesEmpty && !isLoading && !error && (
                  <Table sx={{ textAlign: "center" }}>
                    <thead style={{ background: studentProfileColor + "22" }}>
                      <tr>
                        <th>
                          <Text
                            sx={{
                              color: studentProfileColor,
                              textAlign: "center",
                            }}
                          >
                            Term
                          </Text>
                        </th>
                        <th>
                          <Text
                            sx={{
                              color: studentProfileColor,
                              textAlign: "center",
                            }}
                          >
                            DueDate
                          </Text>
                        </th>
                        <th>
                          <Text
                            sx={{
                              color: studentProfileColor,
                              textAlign: "center",
                            }}
                          >
                            Amount
                          </Text>
                        </th>
                        <th>
                          <Text
                            sx={{
                              color: studentProfileColor,
                              textAlign: "center",
                            }}
                          >
                            Status
                          </Text>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {scheduleData?.data?.message.map?.((schedule) => {
                        if (scheduleWiseFees[schedule.payment_term]) {
                          return scheduleWiseFees[schedule.payment_term]?.map(
                            (fee) => {
                              return (
                                <FeeRow
                                  paymentLinkGenerated
                                  studentProfileColor={studentProfileColor}
                                  data={fee}
                                />
                              );
                            }
                          );
                        } else {
                          return (
                            <FeeRow
                              paymentLinkGenerated={false}
                              studentProfileColor={studentProfileColor}
                              data={schedule}
                            />
                          );
                        }
                      })}
                    </tbody>
                  </Table>
                )}
              </div>
            </>
          </Box>
        </Box>
      </Box>
    </>
  );
};

const formatDate = (dateString: string | null) => {
  if (!dateString) {
    return "-";
  }
  const date = new Date(dateString);
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  return `${day}-${month}-${year}`;
};
type FeeRowProps =
  | {
      data: Fees;
      studentProfileColor: string;
      paymentLinkGenerated: true;
    }
  | {
      data: FeesSchedule;
      studentProfileColor: string;
      paymentLinkGenerated: false;
    };
function FeeRow({
  data,

  studentProfileColor,
  paymentLinkGenerated,
}: FeeRowProps) {
  if (paymentLinkGenerated) {
    return (
      <tr>
        <td>
          <Text>{data?.payment_term || "Deposit"}</Text>
        </td>
        <td>
          <Text>{formatDate(data?.due_date)}</Text>
        </td>
        <td>
          <Text>₹{data?.payment_amount}</Text>
        </td>
        <td>
          <Text>
            {paidStatuses[data?.status?.toLowerCase()] ? (
              <a
                href={data?.payment_url}
                target="_blank"
                style={{
                  width: 100,
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  margin: "0 auto",
                  height: 28,

                  textDecoration: "none",
                  fontSize: 14,

                  color: studentProfileColor,

                  padding: "4px 0.5rem",
                  background: studentProfileColor + "22",
                  borderRadius: "5px",
                  border: `1px solid ${studentProfileColor}`,
                }}
              >
                {paidStatuses[data?.status?.toLowerCase()]}
              </a>
            ) : (
              <a
                href={data?.payment_url}
                target="_blank"
                style={{
                  width: 100,
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  margin: "0 auto",
                  flexShrink: 0,
                  height: 28,
                  textDecoration: "none",
                  fontSize: 14,
                  color: studentProfileColor,
                  padding: "4px 0.5rem",
                  background: studentProfileColor + "22",
                  borderRadius: "5px",
                  border: `1px solid ${studentProfileColor}`,
                  minWidth: "10px",
                }}
              >
                Pay Now
              </a>
            )}
          </Text>
        </td>
      </tr>
    );
  }

  return (
    <>
      <tr>
        <td>
          <Text>{data?.payment_term || "Deposit"}</Text>
        </td>
        <td>
          <Text>{formatDate(data?.due_date)}</Text>
        </td>
        <td>
          <Text>₹{data?.payment_amount}</Text>
        </td>
        <td>
          <Text>
            <label>Not Due</label>
          </Text>
        </td>
      </tr>
    </>
  );
}
