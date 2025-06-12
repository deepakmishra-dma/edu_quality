import { Box, Stack, Text } from "@mantine/core";
import { Table } from "@mantine/core";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import useStudentList from "../components/queries/useStudentList.ts";
import useClassDetails from "../components/queries/useClassDetails.ts";
import useStudentProfileColor from "../components/hooks/useStudentProfileColor.ts";
import { usePTMLinksQuery, useofflinePTMLinksQuery } from "../components/queries/usePTMLinksQuery.tsx";

export const PtmLinks = () => {
    const [selectedStudent, setSelectedStudent] = useState<string>('')
    const [selectedSubject, setSelectedSubject] = useState<string>('')
    const [selectedUnit, setSelectedUnit] = useState<string>('unit 1')

    const [success, setSuccess] = useState(false)
    const [IsErrorOnlineCheck, setIsErrorOnlineCheck] = useState(false)
    const [IsErrorofflineCheck, setIsErrorOfflineCheck] = useState(false)
    const [searchParams, setSearchParams] = useSearchParams()
    const searchedStudent = searchParams.get('student')

    const { data: studentsList } = useStudentList()
    const { data: classDetails } = useClassDetails(selectedStudent)

    const students = useMemo(() => studentsList?.data?.message || [], [studentsList?.data])

    useEffect(() => {
        if (selectedStudent) {
            searchParams.set('student', selectedStudent || '')
            setSearchParams(searchParams, { replace: true })
        }

    }, [selectedStudent])

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
    const custom_school = classDetails?.data?.message?.division?.custom_school

    const { data: onlinePTM, refetch: onlineRefetch, isLoading, isError: IsErrorOnline } = usePTMLinksQuery(selectedStudent)
    const { data: offlinePTM, refetch: offlineRefetch, isLoading: offlinePtmLoading, isError: IsErrorOffline } = useofflinePTMLinksQuery(custom_school)
    useEffect(() => {

        onlineRefetch().catch(() => setIsErrorOnlineCheck(true))
        offlineRefetch().catch(() => setIsErrorOfflineCheck(true))
    }, [onlineRefetch, offlineRefetch]);

    const rows = onlinePTM?.message?.map?.((element: any) => {
        const [linkEnabled, setLinkEnabled] = useState(false);
        const endDate = new Date(element.date);
        const formattedEndDate = endDate.toLocaleDateString('en-GB').replace(/\//g, '-');
        useEffect(() => {

            const slotStartTimeParts = element.slot.split(' - ')[0].split(' ');
            const slotStartHours = parseInt(slotStartTimeParts[0].split(':')[0]);
            const slotStartMinutes = parseInt(slotStartTimeParts[0].split(':')[1]);
            const slotStartPeriod = slotStartTimeParts[1];

            let slotStartHours24 = slotStartHours;
            if (slotStartPeriod === 'PM' && slotStartHours !== 12) {
                slotStartHours24 += 12;
            }

            const slotStartTime = new Date();
            slotStartTime.setHours(slotStartHours24, slotStartMinutes, 0, 0);

            const currentDateTime = new Date();
            const currentHours = currentDateTime.getHours() % 12 || 12;
            const currentMinutes = currentDateTime.getMinutes();
            const currentPeriod = currentDateTime.getHours() < 12 ? 'AM' : 'PM';

            let currentHours24 = currentHours;
            if (currentPeriod === 'PM' && currentHours !== 12) {
                currentHours24 += 12;
            }

            currentDateTime.setHours(currentHours24, currentMinutes, 0, 0);


            const timeDifference = Math.floor((slotStartTime.getTime() - currentDateTime.getTime()) / (60 * 1000));

            const timeoutId = setTimeout(() => {
                setLinkEnabled(true);
            }, timeDifference * 60 * 1000 - 5 * 60 * 1000);

            return () => clearTimeout(timeoutId);
        }, [element.slot, element.date]);

        return (
            <tr key={element.id}>
                <td><Text>{element.subject}</Text></td>
                <td><Text>{formattedEndDate}</Text></td>
                <td><Text>{element.slot}</Text></td>
                <td>
                    {
                        linkEnabled ?
                            <a href={element.gmeet_link} target="__blank" style={{ textDecoration: 'none', }}>
                                <Text sx={{ backgroundColor: studentProfileColor, borderRadius: '25px' }} style={{ color: 'white', padding: '1px' }}>Meet Link</Text>
                            </a>
                            :
                            <span>Not Available</span>
                    }

                </td>
            </tr>
        );
    });


    const rows2 = offlinePTM?.message?.map?.((element: any) => {
        if (element?.event?.includes("PTM")) {
            const startDate = new Date(element.start);
            const formattedStartDate = startDate.toLocaleDateString('en-GB').replace(/\//g, '-');
            return (
                <>
                    <tr >
                        <td ><Text >{element.event}</Text></td>
                        <td ><Text >{formattedStartDate}</Text></td>
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
                {IsErrorOnline && <Text color="red">Error fetching online PTM data</Text>}
                {IsErrorOffline && <Text color="red">Error fetching offline PTM data</Text>}
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
                {
                    !IsErrorOnline && !isLoading &&
                    // isLoading ?
                    // <Text align="center" color="dimmed" weight="bold" my={30}>Loading...</Text>
                    // :
                    <Box sx={{
                        textAlign: 'center',
                    }}>

                        <>
                            {
                                onlinePTM?.message && onlinePTM?.message?.length > 0 ? (
                                    <>
                                        <Text sx={{
                                            margin: "20px 0",
                                            color: "black",
                                            fontWeight: "bold"
                                        }}>Upcoming Online PTMs</Text>
                                        <Box sx={{ textAlign: "center", overflowX: "scroll" }}>



                                            <Table horizontalSpacing="sm">
                                                <thead style={{ backgroundColor: studentProfileColor + "22" }}>
                                                    <tr>
                                                        <td> <Text sx={{
                                                            borderBottom: `1px solid #dee2e6`,
                                                            color: studentProfileColor,
                                                            fontWeight: "bold",
                                                        }}>Subject</Text></td>
                                                        <td> <Text sx={{
                                                            borderBottom: `1px solid #dee2e6`,
                                                            color: studentProfileColor,
                                                            fontWeight: "bold",
                                                        }}>Date</Text></td>

                                                        <td> <Text sx={{
                                                            borderBottom: `1px solid #dee2e6`,
                                                            color: studentProfileColor,
                                                            fontWeight: "bold",
                                                        }}>Time</Text></td>
                                                        <td> <Text sx={{
                                                            borderBottom: `1px solid #dee2e6`,
                                                            color: studentProfileColor,
                                                            fontWeight: "bold",
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
                                            color: "black",
                                            fontWeight: "bold"
                                        }}>There is no Online PTM Scheduled</Text>
                                    </>
                            }

                        </>

                    </Box>
                }
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
                {
                    !IsErrorOffline && !offlinePtmLoading &&
                    //  offlinePtmLoading ?
                    //     <Text align="center" color="dimmed" weight="bold" my={30}>Loading...</Text>
                    //     :
                    <Box sx={{
                        textAlign: 'center',
                    }}>
                        <>


                            {
                                offlinePTM?.message?.length > 0 ?
                                    <div style={{ marginTop: "1rem" }}>
                                        <Text sx={{
                                            margin: "30px 0px",
                                            color: "black",
                                            fontWeight: "bold",

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
                                                        }}>Date</Text></td>


                                                    </tr>
                                                </thead>
                                                <tbody>{rows2}</tbody>
                                            </Table>

                                        </Box>
                                    </div>
                                    :
                                    <>
                                        <Text sx={{
                                            margin: "10px 0",
                                            color: "black",
                                            fontWeight: "bold"
                                        }}>There is no Offline PTM Scheduled</Text>
                                    </>
                            }
                        </>

                    </Box>
                }
            </Box>



        </Box >
    );
};