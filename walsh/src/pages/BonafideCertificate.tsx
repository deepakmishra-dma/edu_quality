import { Box, Button, Stack, Text } from "@mantine/core";
import { useEffect, useMemo, useState } from "react";
import useStudentList from "../components/queries/useStudentList";
import useClassDetails from "../components/queries/useClassDetails";
import useStudentProfileColor from "../components/hooks/useStudentProfileColor";
import { useSearchParams } from "react-router-dom";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import useBonafideList from "../components/queries/useBonafideList";

export const BonafideCertificate = () => {
    const [selectedStudent, setSelectedStudent] = useState<string>('')
    const [selectedSubject, setSelectedSubject] = useState<string>('')
    const [selectedUnit, setSelectedUnit] = useState<string>('unit 1')
    const [, setDownloadFile] = useState(false)
    const [searchParams] = useSearchParams()

    const searchedStudent = searchParams.get('student')


    const { data: studentsList } = useStudentList()
    const { data: bonafideList, refetch } = useBonafideList()
    const { data: classDetails } = useClassDetails(selectedStudent)
    const students = useMemo(() => studentsList?.data?.message || [], [studentsList?.data])
    const studentProfileColor = useStudentProfileColor(selectedStudent)
    console.log("Student --", selectedStudent)
    const subjectOptions = useMemo(() => {
        return classDetails?.data?.message?.class?.subject?.map?.(subject => ({
            label: subject.subject,
            value: subject.subject
        })) || []
    }, [classDetails?.data?.message?.class?.subject])
    const reGenerateBonafide = () => {
        const myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");
        fetch("/api/method/edu_quality.public.py.walsh.bonafide.send_bonafide", {
            method: 'POST',
            headers: myHeaders,
            body: JSON.stringify({
                "student_id": selectedStudent
            }),
        })
            .then(response => response.json())
            .then(result => result.message)
            .then((message) => {
                if (message) {
                    console.log("success ", message);

                    refetch()

                } else if (message) {
                    console.log("error-message ", message);
                    // Handle error message
                } else {
                    console.log("Unexpected response format:", message);
                }

            })
            .catch(error => console.log('error', error))
            .finally(() => {
                // setSendingOtp(false)
            })
    };
    const requestBonafide = () => {
        const myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");
        fetch("/api/method/edu_quality.public.py.walsh.bonafide.send_bonafide", {
            method: 'POST',
            headers: myHeaders,
            body: JSON.stringify({
                "student_id": selectedStudent
            }),
        })
            .then(response => response.json())
            .then(result => result.message)
            .then((message) => {
                if (message) {
                    console.log("success ", message);
                    setDownloadFile(true)
                    refetch()

                } else if (message) {
                    console.log("error-message ", message);
                    // Handle error message
                } else {
                    console.log("Unexpected response format:", message);
                }

            })
            .catch(error => console.log('error', error))
            .finally(() => {
                // setSendingOtp(false)
            })
    };
    const unitOptions = useMemo(() => {
        return [...Array(4)].map((_, i) => ({
            label: `Unit ${i + 1}`,
            value: `${i + 1}`
        }))
    }, [])
    const bonafide_name_id = bonafideList?.data?.message?.find((i) => i.reference_number === selectedStudent)?.reference_number
    const bonafide_download = bonafideList?.data?.message?.find((i) => i.reference_number === selectedStudent)?.bonafide_pdf



    console.log("chec k ", bonafideList)
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
    const showToastMessage = () => {
        toast.success("Please Check Your Email!", {
            position: "top-right"
        });
    };
    const dates = bonafideList?.data?.message?.find((i) => i.reference_number === selectedStudent)?.creation;
    const formatDate = new Date(dates);
    const formattedStartDate = formatDate.toLocaleDateString('en-GB').replace(/\//g, '-');


    return (
        <>
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
                    margin: 30,
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
                            bonafide_name_id === selectedStudent ?
                                (
                                    <>
                                        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "1rem" }}>
                                            <a href={bonafide_download} download={bonafide_download}>

                                                <Button
                                                    sx={{
                                                        marginBottom: 10,
                                                        marginTop: 10,
                                                        marginLeft: 5,
                                                        borderRadius: 10,
                                                        backgroundColor: studentProfileColor,
                                                    }}
                                                    onClick={() => {

                                                    }}
                                                > Download Bonafide</Button>

                                            </a>
                                            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>



                                                <Button
                                                    sx={{
                                                        marginBottom: 10,
                                                        marginTop: 10,
                                                        marginLeft: 5,
                                                        borderRadius: 10,
                                                        backgroundColor: studentProfileColor,
                                                    }}
                                                    onClick={() => {
                                                        reGenerateBonafide();
                                                        showToastMessage();
                                                    }}
                                                > ReGenerate Bonafide</Button>


                                            </div>
                                        </div>
                                        <Box sx={{ display: "flex", alignItems: "center", flexDirection: "column", justifyContent: "start" }}>

                                            <Text sx={{
                                                color: studentProfileColor,
                                                fontWeight: 'bold'
                                            }}>ReGenerate On : {formattedStartDate}</Text>
                                        </Box>
                                    </>
                                )
                                :
                                <Button
                                    sx={{
                                        marginBottom: 10,
                                        marginTop: 10,
                                        marginLeft: 5,
                                        borderRadius: 10,
                                        backgroundColor: studentProfileColor,
                                    }}
                                    onClick={() => {
                                        requestBonafide();
                                        showToastMessage();

                                    }}
                                > Request Bonafide</Button>

                        }

                        <ToastContainer />
                    </Box>
                </Box>
            </Box>
        </>
    )
}