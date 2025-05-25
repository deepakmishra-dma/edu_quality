import { Box, Stack, Text } from "@mantine/core";
import { Table } from "@mantine/core";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import useStudentList from "../components/queries/useStudentList.ts";
import useClassDetails from "../components/queries/useClassDetails.ts";
import useStudentProfileColor from "../components/hooks/useStudentProfileColor.ts";
import { usePTMLinksQuery } from "../components/queries/usePTMListQuery.tsx";

// import useLeaveNote from "../components/queries/useLeaveNoteMutation.ts";


export const PtmLinks = () => {
    const [selectedStudent, setSelectedStudent] = useState<string>('')
    const [selectedSubject, setSelectedSubject] = useState<string>('')
    const [selectedUnit, setSelectedUnit] = useState<string>('unit 1')
    // const [fromDate, setFromDate] = useState<Date | null>(null)
    const data = [
        {
            subject: "English",
            date: "21-Apr-2024",
            links: "https://meet.google.com/xyz-xyz",
            time: "2:00PM"
        },
        {
            subject: "Math",
            date: "5-March-2024",
            links: "https://meet.google.com/xyz-xyz",
            time: "12:00PM"
        },
        {
            subject: "Marathi",
            date: "2-June-2024",
            links: "https://meet.google.com/xyz-xyz",
            time: "1:00PM"
        },
    ]
    // const { data: calendar } = useStudentList();
    // const schoolName = calendar?.data?.message[0].school;




    // const [, setNote] = useState<string>('')
    // const [, setSickLeave] = useState<'sick' | 'leave'>('sick')
    const [success, setSuccess] = useState(false)

    const [searchParams, setSearchParams] = useSearchParams()
    const searchedStudent = searchParams.get('student')

    const { data: studentsList } = useStudentList()
    const { data: classDetails } = useClassDetails(selectedStudent)
    // console.log("selected student ", classDetails)
    const students = useMemo(() => studentsList?.data?.message || [], [studentsList?.data])

    useEffect(() => {
        if (selectedStudent) {
            searchParams.set('student', selectedStudent || '')
            setSearchParams(searchParams, { replace: true })
        }

    }, [selectedStudent])


    // useEffect(() => {
    //   if (!selectedStudent && searchedStudent && selectedStudent != searchedStudent) {
    //     setSelectedStudent(searchedStudent)
    //   }
    // }, [searchedStudent, selectedStudent]);


    const subjectOptions = useMemo(() => {
        return classDetails?.data?.message?.class?.subject?.map?.(subject => ({
            label: subject.subject,
            value: subject.subject
        })) || []
    }, [classDetails?.data?.message?.class?.subject])

    const unitOptions = useMemo(() => [{
        label: `Absent`,
        value: `absent`
    }, {
        label: `Sick`,
        value: `sick`
    }], [])

    useEffect(() => {
        const studentNames = students?.map(student => student.name) || []
        if (!selectedStudent && searchedStudent && (selectedStudent != searchedStudent) && studentNames.includes(searchedStudent)) {
            setSelectedStudent(searchedStudent)
        } else if (!studentNames.includes(selectedStudent)) {
            setSelectedStudent(studentNames[0])
        }
    }, [searchedStudent, selectedStudent, students]);

    useEffect(() => {
        const subjectNames = subjectOptions.map(subject => subject.value)
        if (!subjectNames.includes(selectedSubject)) {
            setSelectedSubject(subjectNames[0])
        }
    }, [selectedSubject, subjectOptions]);

    useEffect(() => {
        const unitNames = unitOptions.map(unit => unit.value)
        if (!unitNames.includes(selectedUnit)) {
            setSelectedUnit(unitNames[0])
        }
    }, [selectedUnit, unitOptions]);

    const studentProfileColor = useStudentProfileColor(selectedStudent)

    useEffect(() => {
        if (success)
            setSuccess(false)
    }, [selectedStudent]);

    const { data: onlinePTM, refetch } = usePTMLinksQuery(selectedStudent)

    const rows = data.map((element) => (
        <tr >
            <td style={{ width: "312px" }}><Text sx={{

            }}>{element.subject}</Text></td>
            <td style={{ width: "312px" }}><Text sx={{

            }}>{element.date}</Text></td>
            <td style={{ width: "312px" }}><Text sx={{

            }}>{element.time}</Text></td>
            <td style={{ width: "312px" }}>
                <a href={element.links} target="__blank">
                    <Text sx={{

                    }}>Link</Text>
                </a>
            </td>
        </tr>
    ));
    console.log("data ", onlinePTM)
    const ptm_dates = [
        {
            "start": "2024-04-06",
            "end": "2024-04-07",
            "event": "Shivane-Electric Saturdays"
        },
        {
            "start": "2024-04-09",
            "end": "2024-04-10",
            "event": "Shivane-GUDI PADWA"
        },
        {
            "start": "2024-04-13",
            "end": "2024-04-14",
            "event": "Shivane-Summer Break"
        },
        {
            "start": "2024-06-03",
            "end": "2024-06-04",
            "event": "Shivane-School Begins!"
        },
        {
            "start": "2024-06-04",
            "end": "2024-06-05",
            "event": "Shivane-School Begins!"
        },
        {
            "start": "2024-06-15",
            "end": "2024-06-16",
            "event": "Shivane-Electric Saturdays"
        },
        {
            "start": "2024-06-22",
            "end": "2024-06-23",
            "event": "Shivane-Electric Saturdays"
        },
        {
            "start": "2024-06-29",
            "end": "2024-06-30",
            "event": "Shivane-Offline PTM"
        },
        {
            "start": "2024-07-01",
            "end": "2024-07-07",
            "event": "Shivane-Practice Test"
        },
        {
            "start": "2024-07-01",
            "end": "2024-07-06",
            "event": "Shivane-Practice Test"
        },
        {
            "start": "2024-07-01",
            "end": "2024-07-02",
            "event": "Shivane-Test"
        },
        {
            "start": "2024-07-02",
            "end": "2024-07-03",
            "event": "Shivane-Study Leave"
        },
        {
            "start": "2024-07-03",
            "end": "2024-07-04",
            "event": "Shivane-Test"
        },
        {
            "start": "2024-07-04",
            "end": "2024-07-05",
            "event": "Shivane-Study Leave"
        },
        {
            "start": "2024-07-05",
            "end": "2024-07-06",
            "event": "Shivane-Test"
        },
        {
            "start": "2024-07-08",
            "end": "2024-07-09",
            "event": "Shivane-Assimilate"
        },
        {
            "start": "2024-07-09",
            "end": "2024-07-13",
            "event": "Shivane-Unit Test"
        },
        {
            "start": "2024-07-09",
            "end": "2024-07-10",
            "event": "Shivane-Test"
        },
        {
            "start": "2024-07-09",
            "end": "2024-07-14",
            "event": "Shivane-Unit Test"
        },
        {
            "start": "2024-07-09",
            "end": "2024-07-12",
            "event": "Shivane-Unit Test"
        },
        {
            "start": "2024-07-10",
            "end": "2024-07-11",
            "event": "Shivane-Study Leave"
        },
        {
            "start": "2024-07-11",
            "end": "2024-07-12",
            "event": "Shivane-Test"
        },
        {
            "start": "2024-07-12",
            "end": "2024-07-13",
            "event": "Shivane-Study Leave"
        },
        {
            "start": "2024-07-15",
            "end": "2024-07-16",
            "event": "Shivane-Holiday"
        },
        {
            "start": "2024-07-15",
            "end": "2024-07-16",
            "event": "Shivane-Test"
        },
        {
            "start": "2024-07-15",
            "end": "2024-07-16",
            "event": "Shivane-Unit Test"
        },
        {
            "start": "2024-07-20",
            "end": "2024-07-21",
            "event": "Shivane-Electric Saturdays"
        },
        {
            "start": "2024-07-27",
            "end": "2024-07-28",
            "event": "Shivane-Electric Saturdays"
        },
        {
            "start": "2024-08-03",
            "end": "2024-08-04",
            "event": "Shivane-Electric Saturdays"
        },
        {
            "start": "2024-08-10",
            "end": "2024-08-11",
            "event": "Shivane-Electric Saturdays"
        },
        {
            "start": "2024-08-15",
            "end": "2024-08-16",
            "event": "Shivane-Independence Day"
        },
        {
            "start": "2024-08-17",
            "end": "2024-08-18",
            "event": "Shivane-Offline PTM"
        },
        {
            "start": "2024-08-19",
            "end": "2024-08-20",
            "event": "Shivane-NARALI PURNIMA"
        },
        {
            "start": "2024-08-20",
            "end": "2024-08-21",
            "event": "Shivane-P2 & P4"
        },
        {
            "start": "2024-08-24",
            "end": "2024-08-25",
            "event": "Shivane-Electric Saturdays"
        },
        {
            "start": "2024-08-26",
            "end": "2024-08-27",
            "event": "Shivane-DAHI HANDI"
        },
        {
            "start": "2024-08-27",
            "end": "2024-08-28",
            "event": "Shivane-DAHI HANDI"
        },
        {
            "start": "2024-08-31",
            "end": "2024-09-01",
            "event": "Shivane-Electric Saturdays"
        }
    ]
    const rows2 = ptm_dates?.map((element) => {
        if (element.event?.includes("PTM")) {
            const startDate = new Date(element.start);
            const endDate = new Date(element.end);

            const formattedStartDate = startDate.toLocaleDateString('en-GB').replace(/\//g, '-');; // Format: dd-mm-yyyy
            const formattedEndDate = endDate.toLocaleDateString('en-GB').replace(/\//g, '-');; // Format: dd-mm-yyyy
            return (
                <>
                    <tr >
                        <td style={{ width: "312px" }}><Text sx={{

                        }}>{element.event}</Text></td>
                        <td style={{ width: "312px" }}><Text sx={{

                        }}>{formattedStartDate}</Text></td>
                        <td style={{ width: "312px" }}><Text sx={{

                        }}>{formattedEndDate}</Text></td>

                    </tr>
                </>
            )
        }
    })


    return (
        <Box>
            <Stack sx={{
                whiteSpace: 'nowrap',
                overflow: 'auto',
                flexDirection: 'row',
                // borderBottom: '1px solid  #0005',
                gap: 0
            }}>
                {students.map((student, index) => {
                    const isSelected = selectedStudent === student.name
                    return <Box
                        key={index}
                        sx={{
                            display: 'inline-block',
                            marginTop: 10,
                            // marginBottom: 10,
                            flexShrink: 0,
                            flexGrow: 1,
                            textAlign: 'center',
                            minWidth: '33.33%'
                        }}
                        onClick={() => setSelectedStudent(student.name)}
                    >
                        <Text sx={{
                            paddingLeft: 20,
                            paddingRight: 20,
                            borderLeft: index && '1px solid black',
                            color: isSelected ? 'black' : '#0007'
                        }}>{student.first_name}</Text>
                        <Box sx={{
                            marginTop: isSelected ? 4 : 5,
                            borderBottom: isSelected ? '2px solid ' + studentProfileColor : '1px solid #0005'
                        }} />
                    </Box>
                })}
            </Stack>
            <Box sx={{
                border: '1px solid ' + studentProfileColor + "77",
                margin: 20,
                borderRadius: 10
            }}>
                <Stack sx={{
                    borderBottom: '1px solid ' + studentProfileColor + "77",
                    padding: "5px 10px",
                    backgroundColor: studentProfileColor + '22',
                    flexDirection: 'row',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                }}>
                    <Text sx={{
                        color: studentProfileColor,
                        fontWeight: 'bold'
                    }}>{classDetails?.data?.message?.program.program_name} - {classDetails?.data?.message?.division.student_group_name}</Text>
                    {students.find(student => student.name === selectedStudent)?.reference_number && <Text sx={{
                        borderRadius: 50,
                        backgroundColor: studentProfileColor + '22',
                        padding: "1px 5px",
                        fontSize: 10,
                        display: 'inline-block',
                        height: '1.4em',
                        lineHeight: 1.4,
                        color: studentProfileColor,
                        fontWeight: 'bold',
                        letterSpacing: 0.5,
                        textTransform: 'uppercase'
                    }}>{students.find(student => student.name === selectedStudent)?.reference_number}</Text>}
                </Stack>
                <Box sx={{
                    textAlign: 'center',
                }}>
                    {
                        success ? <>
                            <Text sx={{
                                margin: "20px 0",
                                color: studentProfileColor
                            }}>Note is saved successfully</Text>
                        </> : <>
                            {
                                data?.length > 0 ? (
                                    <>

                                        <Text sx={{
                                            margin: "20px 0",
                                            color: studentProfileColor
                                        }}>Upcoming Online PTMs</Text>
                                        <Box sx={{ overflowX: "auto", textAlign: "center", }}>

                                            <Table horizontalSpacing="xl">
                                                <thead style={{ backgroundColor: studentProfileColor + "22" }}>
                                                    <tr>
                                                        <td> <Text sx={{
                                                            borderBottom: `1px solid #dee2e6`,
                                                            color: studentProfileColor,
                                                            fontWeight: "bold"
                                                        }}>Subject</Text></td>
                                                        <td> <Text sx={{
                                                            borderBottom: `1px solid #dee2e6`,
                                                            color: studentProfileColor,
                                                            fontWeight: "bold"
                                                        }}>Date</Text></td>
                                                        <td> <Text sx={{
                                                            borderBottom: `1px solid #dee2e6`,
                                                            color: studentProfileColor,
                                                            fontWeight: "bold"
                                                        }}>Time</Text></td>
                                                        <td> <Text sx={{
                                                            borderBottom: `1px solid #dee2e6`,
                                                            color: studentProfileColor,
                                                            fontWeight: "bold"
                                                        }}>Link</Text></td>
                                                    </tr>
                                                </thead>
                                                <tbody>{rows}</tbody>
                                            </Table>
                                        </Box>
                                    </>
                                )
                                    :
                                    <>
                                        <Text sx={{
                                            margin: "10px 0",
                                            color: studentProfileColor
                                        }}>There is no Online PTM Scheduled</Text>
                                    </>
                            }

                        </>
                    }
                </Box>
            </Box>
            <Box sx={{
                border: '1px solid ' + studentProfileColor + "77",
                margin: 20,
                borderRadius: 10,
                textAlign: "center"
            }}>
                <Stack sx={{
                    borderBottom: '1px solid ' + studentProfileColor + "77",
                    padding: "5px 10px",
                    backgroundColor: studentProfileColor + '22',
                    flexDirection: 'row',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                }}>
                    <Text sx={{
                        color: studentProfileColor,
                        fontWeight: 'bold'
                    }}>{classDetails?.data?.message?.program.program_name} - {classDetails?.data?.message?.division.student_group_name}</Text>
                    {students.find(student => student.name === selectedStudent)?.reference_number && <Text sx={{
                        borderRadius: 50,
                        backgroundColor: studentProfileColor + '22',
                        padding: "1px 5px",
                        fontSize: 10,
                        display: 'inline-block',
                        height: '1.4em',
                        lineHeight: 1.4,
                        color: studentProfileColor,
                        fontWeight: 'bold',
                        letterSpacing: 0.5,
                        textTransform: 'uppercase'
                    }}>{students.find(student => student.name === selectedStudent)?.reference_number}</Text>}
                </Stack>
                <div style={{ marginTop: "1rem" }}>
                    <Text sx={{
                        margin: "30px 0px",
                        color: studentProfileColor,

                    }}>Offline PTMs Scheduled</Text>
                    <Box sx={{ display: "flex", alignItems: "start", flexDirection: "column", justifyContent: "start" }}>
                        <Table horizontalSpacing="md">
                            <thead style={{ backgroundColor: studentProfileColor + "22" }}>
                                <tr>
                                    <td> <Text sx={{
                                        borderBottom: `1px solid #dee2e6`,
                                        color: studentProfileColor,
                                        fontWeight: "bold"
                                    }}>PTM Event</Text></td>
                                    <td> <Text sx={{
                                        borderBottom: `1px solid #dee2e6`,
                                        color: studentProfileColor,
                                        fontWeight: "bold"
                                    }}>Start</Text></td>
                                    <td> <Text sx={{
                                        borderBottom: `1px solid #dee2e6`,
                                        color: studentProfileColor,
                                        fontWeight: "bold"
                                    }}>End</Text></td>

                                </tr>
                            </thead>
                            <tbody>{rows2}</tbody>
                        </Table>

                    </Box>
                </div>
            </Box>
        </Box >
    );
};