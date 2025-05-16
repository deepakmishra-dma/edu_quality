import { useMemo, useState } from "react";
import useGuardianList, { guardin_address, guardin_address2, guardin_email_update, guardin_father_number_update, guardin_number_update, updateAnnualIncome, updateBloodGroup } from "../components/queries/useGuardianList";
import { Box, Text } from "@mantine/core";
import { IconEdit, IconSend } from '@tabler/icons-react';
import OTPInput from "otp-input-react";
import useStudentList from "../components/queries/useStudentList";

interface StudentProfileProps {
    student: any
    selectedStudent: any
    studentProfileColor: any
    classDetails: any
    isSelected: any
}
export const StudentProfleFOrm = ({ student, selectedStudent, studentProfileColor, classDetails, isSelected }: StudentProfileProps) => {
    const { data: guardianList, refetch } = useGuardianList({
        student_id: selectedStudent
    })
    const { mutateAsync: mutateAddress } = guardin_address()

    const { mutateAsync: mutateAddress2 } = guardin_address2()
    const { mutateAsync: mutateAsyncAnnualIncome } = updateAnnualIncome()
    const findAnnualI = (id: string): string => {
        const findIncome = guardianList?.data?.message?.find((i) => i.relation === id)?.name;
        return findIncome || '';
    }

    const { mutateAsync: mutateAsyncBloodGroup } = updateBloodGroup()



    const { mutateAsync: mutateAsyncFatherNumbers } = guardin_father_number_update()

    const { mutateAsync: mutateAsyncNumber } = guardin_number_update()

    const findName = (id: string): string => {
        const findEmail = guardianList?.data?.message?.find((i) => i.relation === id)?.name;
        return findEmail || '';
    }
    const { mutateAsync } = guardin_email_update()
    const [statusColor, setStatusColor] = useState('');


    const [verificationStatus, setVerificationStatus] = useState('');
    const { data: studentsList, refetch: student_list_refetch } = useStudentList()
    const [editIcom, setEditIcon] = useState({
        mother_email: false,
        mother_number: false,
        father_email: false,
        father_number: false,
    });
    const [submitBtn, setSubmitBtn] = useState({
        mother_email: false,
        mother_number: false,
        father_email: false,
        father_number: false,
        address1: false,
        address2: false,
        bloods_group: false,
        annual__father_income: false,
        annual__mother_income: false,
    })
    const [isEditable, setIsEditable] = useState({
        mother_email: false,
        mother_number: false,
        father_email: false,
        father_number: false,
        address: false,
        address2: false,
        bloods_group: false,
        annual__father_income: false,
        annual__mother_income: false,
    });
    const [sendOtp, setSendotp] = useState({
        mother_email: false,
        mother_number: false,
        father_email: false,
        father_number: false,

    });
    const [newEmail, setNewEmail] = useState({
        mother_email_input: '',
        father_email_input: '',
    });
    const [, setEmailOtp] = useState('');
    const [newNumber, setNewNumber] = useState({
        mother_number_input: '',
        father_number_input: '',
    });
    const [newBloodG, setBloodG] = useState('');
    const [newAnnualI, setAnnualI] = useState('');
    const [newAnnualIMother, setAnnualIMother] = useState('');
    const [addressguardian1, setAddressGuardian1] = useState('')
    const [addressguardian2, setAddressGuardian2] = useState('')
    const [, setErrorMessage] = useState("");
    const [otpMessage, setOtpMessage] = useState("");
    const [otpVerify, setOtpVerify] = useState("");
    const FatherEmail = guardianList?.data?.message?.find((i) => i.relation === "Father")?.email_address || ''
    const MotherEmail = guardianList?.data?.message?.find((i) => i.relation === "Mother")?.email_address || ''
    const FatherMobile = guardianList?.data?.message?.find((i) => i.relation === "Father")?.mobile_number || ''
    const MotherMobile = guardianList?.data?.message?.find((i) => i.relation === "Mother")?.mobile_number || ''
    const MotherName = guardianList?.data?.message?.find((i) => i.relation === "Mother")?.guardian_name || "N/A"
    const FatherName = guardianList?.data?.message?.find((i) => i.relation === "Father")?.guardian_name || "N/A"
    const address_guardian = studentsList?.data?.message[0]?.address_line_1;
    const blood_group = studentsList?.data?.message?.find((i) => i.name === selectedStudent)?.blood_group || "N/A"
    const annuals_income = guardianList?.data?.message?.find((i) => i.relation === "Father")?.annual_income || "N/A"
    const annuals_income_mother = guardianList?.data?.message?.find((i) => i.relation === "Mother")?.annual_income || "N/A"
    const address_guardian2 = studentsList?.data?.message[0]?.address_line_2;
    console.log("mother ", MotherEmail)
    const verifyOTP = async (id: string) => {
        if (id === guardianList?.data?.message?.find((i) => i.relation === "Mother")?.relation) {

            try {
                const payload = { "otp": otpVerify, "email": MotherEmail };
                const response = await fetch('/api/method/edu_quality.public.py.walsh.studentProfile.verify_otp', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                });
                const data = await response.json();
                if (data.message.success) {
                    setVerificationStatus('OTP Verified!');
                    setStatusColor('green');
                    setTimeout(() => {
                        mutateAsyncNumber({
                            name: findName("Mother"),
                            mobile_number: newNumber.mother_number_input
                        }).then(() => {
                            refetch()
                            setIsEditable(prevState => ({
                                ...prevState,
                                mother_number: false
                            }))
                            setSubmitBtn(prevState => ({
                                ...prevState,
                                mother_number: false
                            }))
                        })
                        setSendotp(prevState => ({
                            ...prevState,
                            mother_number: false
                        }));
                        setEditIcon(prevState => ({
                            ...prevState,
                            mother_number: false
                        }))
                        setOtpVerify(" ")
                        setVerificationStatus('');

                    }, 2000);
                    // Proceed with further actions like updating email address, etc.
                } else {
                    setVerificationStatus('Invalid OTP. Please try again.');
                    setStatusColor('red');
                    setVerificationStatus('');

                }
            } catch (error) {
                console.error('Error verifying OTP:', error);
                setVerificationStatus('Error verifying OTP. Please try again later.');
            }
        }
        if (id === guardianList?.data?.message?.find((i) => i.relation === "Father")?.relation) {
            try {
                const payload = { "otp": otpVerify, "email": FatherEmail };
                const response = await fetch('/api/method/edu_quality.public.py.walsh.studentProfile.verify_otp', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                });
                const data = await response.json();
                if (data.message.success) {
                    setVerificationStatus('OTP Verified!');
                    setStatusColor('green');
                    setTimeout(() => {
                        mutateAsyncFatherNumbers({
                            name: findName("Father"),
                            mobile_number: newNumber.father_number_input
                        }).then(() => {
                            refetch()
                            setIsEditable(prevState => ({
                                ...prevState,
                                father_number: false
                            }))
                            setSubmitBtn(prevState => ({
                                ...prevState,
                                father_number: false
                            }))
                        })
                        setSendotp(prevState => ({
                            ...prevState,
                            father_number: false
                        }));
                        setEditIcon(prevState => ({
                            ...prevState,
                            father_number: false
                        }))
                        setOtpVerify(" ")
                        setVerificationStatus('');


                    }, 2000);
                    // Proceed with further actions like updating email address, etc.
                } else {
                    setVerificationStatus('Invalid OTP. Please try again.');
                    setStatusColor('red');
                    setVerificationStatus('');

                }
            } catch (error) {
                console.error('Error verifying OTP:', error);
                setVerificationStatus('Error verifying OTP. Please try again later.');
            }
        }
    };


    const verifyMobileOTP = async (id: string) => {
        if (id === guardianList?.data?.message?.find((i) => i.relation === "Mother")?.relation) {

            try {
                const payload = { "otp": otpVerify, "phone_no": MotherMobile };
                const response = await fetch('/api/method/edu_quality.public.py.walsh.studentProfile.verify_otp_mobile', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                });
                const data = await response.json();
                if (data.message.success) {
                    setVerificationStatus('OTP Verified!');
                    setStatusColor('green');

                    setTimeout(() => {
                        mutateAsync({
                            name: findName("Mother"),
                            new_email: newEmail.mother_email_input
                        }).then(() => {
                            refetch()
                            setIsEditable(prevState => ({
                                ...prevState,
                                mother_email: false
                            }))
                            setSubmitBtn(prevState => ({
                                ...prevState,
                                mother_email: false
                            }))
                        })
                        setSendotp(prevState => ({
                            ...prevState,
                            mother_email: false
                        }));
                        setEditIcon(prevState => ({
                            ...prevState,
                            mother_email: false
                        }))
                        setOtpVerify(" ")
                        setVerificationStatus('');

                    }, 2000);
                } else {
                    setVerificationStatus('Invalid OTP. Please try again.');
                    setStatusColor('red');
                    setVerificationStatus('');

                }
            } catch (error) {
                console.error('Error verifying OTP:', error);
                setVerificationStatus('Error verifying OTP. Please try again later.');
            }
        }
        if (id === guardianList?.data?.message?.find((i) => i.relation === "Father")?.relation) {
            try {

                const payload = { "otp": otpVerify, "phone_no": FatherMobile };
                const response = await fetch('/api/method/edu_quality.public.py.walsh.studentProfile.verify_otp_mobile', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                });
                const data = await response.json();
                if (data.message.success) {
                    setVerificationStatus('OTP Verified!');
                    setStatusColor('green');
                    setTimeout(() => {
                        mutateAsync({
                            name: findName("Father"),
                            new_email: newEmail.father_email_input
                        }).then(() => {
                            refetch()
                            setIsEditable(prevState => ({
                                ...prevState,
                                father_email: false
                            }))
                            setSubmitBtn(prevState => ({
                                ...prevState,
                                father_email: false
                            }))
                        })
                        setSendotp(prevState => ({
                            ...prevState,
                            father_email: false
                        }));
                        setEditIcon(prevState => ({
                            ...prevState,
                            father_email: false
                        }))
                        setOtpVerify(" ")
                        setVerificationStatus('');

                    }, 2000);
                    // Proceed with further actions like updating email address, etc.
                } else {
                    setVerificationStatus('Invalid OTP. Please try again.');
                    setStatusColor('red');
                    setVerificationStatus('');

                }
            } catch (error) {
                console.error('Error verifying OTP:', error);
                setVerificationStatus('Error verifying OTP. Please try again later.');
            }
        }
    };

    const handleSubmit = useMemo(
        () => (id: string) => {
            if (id === "Mother") {

                const myHeaders = new Headers();
                const payload = { "email_address": MotherEmail };
                myHeaders.append("Content-Type", "application/json");
                fetch("/api/method/edu_quality.public.py.walsh.studentProfile.send_otp_to_email_address", {
                    method: 'POST',
                    headers: myHeaders,
                    body: JSON.stringify(payload),
                    redirect: 'follow'
                })
                    .then(response => response.json())
                    .then(result => result.message)
                    .then((message) => {
                        if (message.success) {
                            setErrorMessage("");
                            setOtpMessage(message.message);
                            console.log("Message ", message.message)
                        } else {
                            setErrorMessage(message.error_message);
                            console.log("Error ", message.error)
                        }
                    })
                    .catch(error => console.log('error', error))
            }
            if (id === "Father") {

                const myHeaders = new Headers();
                const payload = { "email_address": FatherEmail };
                myHeaders.append("Content-Type", "application/json");
                fetch("/api/method/edu_quality.public.py.walsh.studentProfile.send_otp_to_email_address", {
                    method: 'POST',
                    headers: myHeaders,
                    body: JSON.stringify(payload),
                    redirect: 'follow'
                })
                    .then(response => response.json())
                    .then(result => result.message)
                    .then((message) => {
                        if (message.success) {
                            setErrorMessage("");
                            setOtpMessage(message.message);
                            console.log("Message ", message.message)
                        } else {
                            setErrorMessage(message.error_message);
                            console.log("Error ", message.error)
                        }
                    })
                    .catch(error => console.log('error', error))
            }



        }, [MotherEmail, FatherEmail])
    const handleMobileNumber = useMemo(
        () => (id: string) => {
            if (id === "Mother") {

                const myHeaders = new Headers();
                const payload = { "mobile_number": MotherMobile };
                myHeaders.append("Content-Type", "application/json");
                fetch("/api/method/edu_quality.public.py.walsh.studentProfile.send_otp_to_mobile_number", {
                    method: 'POST',
                    headers: myHeaders,
                    body: JSON.stringify(payload),
                    redirect: 'follow'
                })
                    .then(response => response.json())
                    .then(result => result.message)
                    .then((message) => {
                        if (message.success) {
                            setErrorMessage("");
                            setOtpMessage(message.message);
                            console.log("Message ", message.message)
                        } else {
                            setErrorMessage(message.error_message);
                            console.log("Error ", message.error)
                        }
                    })
                    .catch(error => console.log('error', error))
            }
            if (id === "Father") {

                const myHeaders = new Headers();
                const payload = { "mobile_number": FatherMobile };
                myHeaders.append("Content-Type", "application/json");
                fetch("/api/method/edu_quality.public.py.walsh.studentProfile.send_otp_to_mobile_number", {
                    method: 'POST',
                    headers: myHeaders,
                    body: JSON.stringify(payload),
                    redirect: 'follow'
                })
                    .then(response => response.json())
                    .then(result => result.message)
                    .then((message) => {
                        if (message.success) {
                            setErrorMessage("");
                            setOtpMessage(message.message);
                            console.log("Message ", message.message)
                        } else {
                            setErrorMessage(message.error_message);
                            console.log("Error ", message.error)
                        }
                    })
                    .catch(error => console.log('error', error))
            }



        }, [MotherMobile, FatherMobile])
    return (
        <>
            <div style={{ display: "flex", alignItems: "start", flexDirection: "column", justifyContent: "space-between", width: "100%", overflowX: "hidden" }}>
                <div >
                    <div style={{ display: "flex", alignItems: "center", borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>
                        <Text sx={{
                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Class:</Text>
                        <span style={{ color: "black" }}>{classDetails?.data?.message?.class?.name}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>

                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>School: </Text>
                        <span style={{ color: "black" }}>{classDetails?.data?.message?.division?.custom_school}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>

                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Mother Name: </Text>
                        <span style={{ color: "black" }}>{MotherName}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>

                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Father Name: </Text>
                        <span style={{ color: "black" }}>{FatherName}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>

                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Date of Birth: </Text>
                        <span style={{ color: "black" }}>{studentsList?.data?.message[0]?.date_of_birth}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>

                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Religion: </Text>
                        <span style={{ color: "black" }}>{studentsList?.data?.message[0]?.religion}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>
                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Caste:</Text>
                        <span style={{ color: "black" }}>{studentsList?.data?.message[0]?.caste}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>

                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Sub Caste: </Text>
                        <span style={{ color: "black" }}>{studentsList?.data?.message[0]?.sub_caste}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>
                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Mother Tongue: </Text>
                        <span style={{ color: "black" }}>{studentsList?.data?.message[0]?.mother_tongue}</span>
                    </div>

                    <div style={{ position: "relative", borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>
                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Mother Email:</Text>
                        <div style={{ display: "flex", flexDirection: "row", gap: "0.2rem", alignItems: "center" }}>

                            <input type="text" name="" id="" style={{ borderRadius: "8px", width: "312px", marginLeft: "1rem", padding: "0.5rem", backgroundColor: "lightgray", border: "none" }} value={isEditable.mother_email ? newEmail.mother_email_input : MotherEmail} onChange={(e) => {
                                setNewEmail((prevEmail) => ({
                                    ...prevEmail,
                                    mother_email_input: e.target.value
                                }))

                            }}
                                disabled={!isEditable.mother_email}
                            />
                            {
                                student.name === selectedStudent && (!MotherEmail && MotherEmail === '' || MotherEmail) && !submitBtn.mother_email && !editIcom.mother_email ?
                                    <IconEdit stroke={2} onClick={() => {
                                        setIsEditable(prevState => ({
                                            ...prevState,
                                            mother_email: true
                                        }))
                                        // setNewEmail(MotherEmail || '');
                                        setNewEmail((prevEmail) => ({
                                            ...prevEmail,
                                            mother_email_input: MotherEmail || ''
                                        }))
                                        setSubmitBtn(prevState => ({
                                            ...prevState,
                                            mother_email: true
                                        }))
                                    }} />
                                    :
                                    <IconSend style={{ position: "absolute", bottom: "0.5rem", left: "20.7rem", display: sendOtp.mother_email ? "none" : "inline" }} stroke={2} onClick={() => {
                                        if (MotherEmail === '') {
                                            mutateAsync({
                                                name: findName("Mother"),
                                                new_email: newEmail.mother_email_input
                                            }).then(() => {
                                                refetch()
                                                setSubmitBtn(prevState => ({
                                                    ...prevState,
                                                    mother_email: false
                                                }))
                                                setIsEditable(prevState => ({
                                                    ...prevState,
                                                    mother_email: false
                                                }))
                                            })
                                        }
                                        else {
                                            setEmailOtp(newEmail.mother_email_input)
                                            handleMobileNumber("Mother")
                                            setEditIcon(prevState => ({
                                                ...prevState,
                                                mother_email: true
                                            }))
                                            setSendotp(prevState => ({
                                                ...prevState,
                                                mother_email: true
                                            }))

                                        }


                                    }} />


                            }

                        </div>
                        {
                            student.name === selectedStudent && MotherEmail && sendOtp.mother_email &&
                            (
                                <>
                                    <p style={{ color: "green", marginLeft: "1rem" }}>OTP sent to {MotherMobile} {otpMessage}</p>
                                    <div style={{ display: "flex", flexDirection: "column", width: "100%", gap: "1rem", marginLeft: "1rem" }}>

                                        <OTPInput autoFocus OTPLength={4} value={otpVerify} onChange={setOtpVerify} otpType="number" disabled={false} secure />
                                        <button style={{ width: "25%", marginLeft: "1rem", backgroundColor: "rgb(31 197 94)", color: "white", border: "none", padding: "0.5rem", borderRadius: "10px" }} onClick={() => {
                                            verifyMobileOTP("Mother")
                                        }}>Send OTP</button>
                                        {verificationStatus && <p style={{ color: statusColor, marginLeft: "1rem" }}>{verificationStatus}</p>}
                                    </div>
                                </>
                            )
                        }

                    </div>
                    {/* avantee.joshi@yopmail.com */}
                    <div style={{ borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>
                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Mother's Mobile:</Text>

                        <div style={{ display: "flex", flexDirection: "row", gap: "0.2rem", alignItems: "center" }}>

                            <input type="text" name="" id="" style={{ borderRadius: "8px", width: "312px", marginLeft: "1rem", padding: "0.5rem", backgroundColor: "lightgray", border: "none" }} value={isEditable.mother_number ? newNumber.mother_number_input : MotherMobile} onChange={(e) => {
                                setNewNumber((prevEmail) => ({
                                    ...prevEmail,
                                    mother_number_input: e.target.value
                                }));
                            }} disabled={!isEditable.mother_number} />
                            {
                                student.name === selectedStudent && (!MotherMobile && MotherMobile === '' || MotherMobile) && !submitBtn.mother_number && !editIcom.mother_number ?
                                    <IconEdit stroke={2} onClick={() => {
                                        setIsEditable(prevState => ({
                                            ...prevState,
                                            mother_number: true
                                        }))
                                        // setNewFatherEmail(FatherEmail || '');
                                        setNewNumber((prevEmail) => ({
                                            ...prevEmail,
                                            mother_number_input: MotherMobile || ''
                                        }))
                                        setSubmitBtn(prevState => ({
                                            ...prevState,
                                            mother_number: true
                                        }))
                                    }} />
                                    :
                                    <IconSend style={{ display: sendOtp.mother_number ? "none" : "inline" }} stroke={2} onClick={() => {

                                        if (MotherMobile === '') {
                                            mutateAsyncNumber({
                                                name: findName("Mother"),
                                                mobile_number: newNumber.mother_number_input
                                            }).then(() => {
                                                refetch()
                                                setSubmitBtn(prevState => ({
                                                    ...prevState,
                                                    mother_number: false
                                                }))
                                                setIsEditable(prevState => ({
                                                    ...prevState,
                                                    mother_number: false
                                                }))
                                            })
                                        }
                                        else {
                                            setEmailOtp(newNumber.mother_number_input)
                                            handleSubmit("Mother")
                                            setEditIcon(prevState => ({
                                                ...prevState,
                                                mother_number: true
                                            }))
                                            setSendotp(prevState => ({
                                                ...prevState,
                                                mother_number: true
                                            }))

                                        }
                                    }} />

                            }
                        </div>
                        {
                            student.name === selectedStudent && MotherMobile && sendOtp.mother_number &&
                            (
                                <>
                                    <p style={{ color: "green", marginLeft: "1rem" }}>OTP sent to {MotherEmail} {otpMessage}</p>
                                    <div style={{ display: "flex", flexDirection: "column", width: "100%", gap: "1rem", marginLeft: "1rem" }}>

                                        <OTPInput autoFocus OTPLength={4} value={otpVerify} onChange={setOtpVerify} otpType="number" disabled={false} secure />
                                        <button style={{ width: "25%", marginLeft: "1rem", backgroundColor: "rgb(31 197 94)", color: "white", border: "none", padding: "0.5rem", borderRadius: "10px" }} onClick={() => {
                                            verifyOTP("Mother")
                                        }}>Send OTP</button>
                                        {verificationStatus && <p style={{ color: statusColor, marginLeft: "1rem" }}>{verificationStatus}</p>}
                                    </div>
                                </>
                            )
                        }

                    </div>
                    <div style={{ position: "relative", borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>
                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Father's Email:</Text>

                        <div style={{ display: "flex", flexDirection: "row", gap: "0.2rem", alignItems: "center" }}>
                            <input type="text" name="" id="" style={{ borderRadius: "8px", width: "312px", marginLeft: "1rem", padding: "0.5rem", backgroundColor: "lightgray", border: "none" }} value={isEditable.father_email ? newEmail.father_email_input : FatherEmail} onChange={(e) => {
                                setNewEmail((prevEmail) => ({
                                    ...prevEmail,
                                    father_email_input: e.target.value
                                }))
                            }} disabled={!isEditable.father_email} />
                            {
                                student.name === selectedStudent && (!FatherEmail && FatherEmail === '' || FatherEmail) && !submitBtn.father_email && !editIcom.father_email ?
                                    <IconEdit stroke={2} onClick={() => {
                                        setIsEditable(prevState => ({
                                            ...prevState,
                                            father_email: true
                                        }))
                                        // setNewFatherEmail(FatherEmail || '');
                                        setNewEmail((prevEmail) => ({
                                            ...prevEmail,
                                            father_email_input: FatherEmail || ''
                                        }))
                                        setSubmitBtn(prevState => ({
                                            ...prevState,
                                            father_email: true
                                        }))
                                    }} />
                                    :
                                    <IconSend style={{ display: sendOtp.father_email ? "none" : "inline" }} stroke={2} onClick={() => {

                                        if (FatherEmail === '') {
                                            mutateAsync({
                                                name: findName("Father"),
                                                new_email: newEmail.father_email_input
                                            }).then(() => {
                                                refetch()
                                                setSubmitBtn(prevState => ({
                                                    ...prevState,
                                                    father_email: false
                                                }))
                                                setIsEditable(prevState => ({
                                                    ...prevState,
                                                    father_email: false
                                                }))
                                            })
                                        }
                                        else {
                                            setEmailOtp(newEmail.father_email_input)
                                            handleMobileNumber("Father")
                                            setEditIcon(prevState => ({
                                                ...prevState,
                                                father_email: true
                                            }))
                                            setSendotp(prevState => ({
                                                ...prevState,
                                                father_email: true
                                            }))

                                        }
                                    }} />

                            }
                        </div>

                        {
                            student.name === selectedStudent && FatherEmail && sendOtp.father_email &&
                            (
                                <>
                                    <p style={{ color: "green", marginLeft: "1rem" }}>OTP sent to {FatherEmail} {otpMessage}</p>
                                    <div style={{ display: "flex", flexDirection: "column", width: "100%", gap: "1rem", marginLeft: "1rem" }}>

                                        {/* <OtpInput /> */}
                                        <OTPInput autoFocus OTPLength={4} value={otpVerify} onChange={setOtpVerify} otpType="number" disabled={false} secure />
                                        <button style={{ width: "25%", marginLeft: "1rem", backgroundColor: "rgb(31 197 94)", color: "white", border: "none", padding: "0.5rem", borderRadius: "10px" }} onClick={() => {
                                            verifyMobileOTP("Father")
                                        }}>Send OTP</button>
                                        {verificationStatus && <p style={{ color: statusColor, marginLeft: "1rem" }}>{verificationStatus}</p>}
                                    </div>
                                </>
                            )
                        }






                    </div>
                    <div style={{ borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>
                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Father's Mobile:</Text>
                        <div style={{ display: "flex", flexDirection: "row", gap: "0.2rem", alignItems: "center" }}>

                            <input type="text" name="" id="" style={{ borderRadius: "8px", width: "312px", marginLeft: "1rem", padding: "0.5rem", backgroundColor: "lightgray", border: "none" }} value={isEditable.father_number ? newNumber.father_number_input : FatherMobile} onChange={(e) => {
                                setNewNumber((prevState) => ({
                                    ...prevState,
                                    father_number_input: e.target.value
                                }))
                            }} disabled={!isEditable.father_number} />
                            {
                                student.name === selectedStudent && (!FatherMobile && FatherMobile === '' || FatherMobile) && !submitBtn.father_number && !editIcom.father_number ?
                                    <IconEdit stroke={2} onClick={() => {
                                        setIsEditable(prevState => ({
                                            ...prevState,
                                            father_number: true
                                        }))
                                        // setNewFatherEmail(FatherEmail || '');
                                        setNewNumber((prevEmail) => ({
                                            ...prevEmail,
                                            father_number_input: FatherMobile || ''
                                        }))
                                        setSubmitBtn(prevState => ({
                                            ...prevState,
                                            father_number: true
                                        }))
                                    }} />
                                    :
                                    <IconSend style={{ display: sendOtp.father_number ? "none" : "inline" }} stroke={2} onClick={() => {

                                        if (FatherMobile === '') {
                                            mutateAsyncFatherNumbers({
                                                name: findName("Father"),
                                                mobile_number: newNumber.father_number_input
                                            }).then(() => {
                                                refetch()
                                                setSubmitBtn(prevState => ({
                                                    ...prevState,
                                                    father_number: false
                                                }))
                                                setIsEditable(prevState => ({
                                                    ...prevState,
                                                    father_number: false
                                                }))
                                            })
                                        }
                                        else {
                                            setEmailOtp(newNumber.father_number_input)
                                            handleSubmit("Father")
                                            setEditIcon(prevState => ({
                                                ...prevState,
                                                father_number: true
                                            }))
                                            setSendotp(prevState => ({
                                                ...prevState,
                                                father_number: true
                                            }))

                                        }
                                    }} />

                            }
                        </div>

                        {
                            student.name === selectedStudent && FatherMobile && sendOtp.father_number &&
                            (
                                <>
                                    <p style={{ color: "green", marginLeft: "1rem" }}>OTP sent to {FatherEmail} {otpMessage}</p>
                                    <div style={{ display: "flex", flexDirection: "column", width: "100%", gap: "1rem", marginLeft: "1rem" }}>

                                        <OTPInput autoFocus OTPLength={4} value={otpVerify} onChange={setOtpVerify} otpType="number" disabled={false} secure />
                                        <button style={{ width: "25%", marginLeft: "1rem", backgroundColor: "rgb(31 197 94)", color: "white", border: "none", padding: "0.5rem", borderRadius: "10px" }} onClick={() => {
                                            verifyOTP("Father")
                                        }}>Send OTP</button>
                                        {verificationStatus && <p style={{ color: statusColor, marginLeft: "1rem" }}>{verificationStatus}</p>}
                                    </div>
                                </>
                            )
                        }


                    </div>
                    <div style={{ borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>
                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Address 1</Text>
                        <input type="text" name="" id="" style={{ borderRadius: "8px", width: "312px", marginLeft: "1rem", padding: "0.5rem", backgroundColor: "lightgray", border: "none" }} value={isEditable.address ? addressguardian1 : address_guardian} disabled={!isEditable.address} onChange={(e) => setAddressGuardian1(e.target.value)} />
                        {
                            student.name === selectedStudent && address_guardian && !submitBtn.address1 ?
                                <IconEdit stroke={2} onClick={() => {
                                    setIsEditable(prevState => ({
                                        ...prevState,
                                        address: true
                                    }))

                                    setAddressGuardian1(address_guardian || '')
                                    setSubmitBtn(prevState => ({
                                        ...prevState,
                                        address1: true
                                    }))
                                }} />
                                :
                                <IconSend stroke={2} onClick={() => {
                                    mutateAddress({
                                        name: student.name,
                                        address_line_1: addressguardian1,
                                    }).then(() => {
                                        student_list_refetch()
                                        // setAddressGuardian1(address_guardian || '')
                                        setIsEditable(prevState => ({
                                            ...prevState,
                                            address: false
                                        }))
                                        setSubmitBtn(prevState => ({
                                            ...prevState,
                                            address1: false
                                        }))
                                    })
                                }} />

                        }
                    </div>
                    <div style={{ borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>
                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Address 2</Text>
                        <input type="text" name="" id="" style={{ borderRadius: "8px", width: "312px", marginLeft: "1rem", padding: "0.5rem", backgroundColor: "lightgray", border: "none" }} value={isEditable.address2 ? addressguardian2 : address_guardian2} disabled={!isEditable.address2} onChange={(e) => setAddressGuardian2(e.target.value)} />
                        {
                            student.name === selectedStudent && address_guardian2 && !submitBtn.address2 ?
                                <IconEdit stroke={2} onClick={() => {
                                    setIsEditable(prevState => ({
                                        ...prevState,
                                        address2: true
                                    }))

                                    setAddressGuardian2(address_guardian2 || '')
                                    setSubmitBtn(prevState => ({
                                        ...prevState,
                                        address2: true
                                    }))
                                }} />
                                :
                                <IconSend stroke={2} onClick={() => {
                                    mutateAddress2({
                                        name: student.name,
                                        address_line_2: addressguardian2

                                    }).then(() => {
                                        student_list_refetch()
                                        setIsEditable(prevState => ({
                                            ...prevState,
                                            address2: false
                                        }))
                                        setSubmitBtn(prevState => ({
                                            ...prevState,
                                            address2: false
                                        }))
                                    })
                                }} />

                        }
                    </div>
                    <div style={{ borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>
                        <Text sx={{
                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Blood Group</Text>
                        <input type="text" name="" id="" style={{ borderRadius: "8px", width: "312px", marginLeft: "1rem", padding: "0.5rem", backgroundColor: "lightgray", border: "none" }} value={isEditable.bloods_group ? newBloodG : blood_group} onChange={(e) => setBloodG(e.target.value)} disabled={!isEditable.bloods_group} />
                        {
                            student.name === selectedStudent && blood_group && !submitBtn.bloods_group ?
                                <IconEdit stroke={2} onClick={() => {
                                    setIsEditable(prevState => ({
                                        ...prevState,
                                        bloods_group: true
                                    }))

                                    setBloodG(blood_group || '')
                                    setSubmitBtn(prevState => ({
                                        ...prevState,
                                        bloods_group: true
                                    }))
                                }} />
                                :
                                <IconSend stroke={2} onClick={() => {
                                    mutateAsyncBloodGroup({
                                        name: student.name,
                                        blood_group: newBloodG

                                    }).then(() => {
                                        student_list_refetch()
                                        setIsEditable(prevState => ({
                                            ...prevState,
                                            bloods_group: false
                                        }))
                                        setSubmitBtn(prevState => ({
                                            ...prevState,
                                            bloods_group: false
                                        }))
                                    })
                                }} />

                        }
                    </div>
                    <div style={{ borderBottom: `1px solid ${studentProfileColor}`, paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>
                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Approximate Yearly Income of Father</Text>
                        <input type="text" name="" id="" style={{ borderRadius: "8px", width: "312px", marginLeft: "1rem", padding: "0.5rem", backgroundColor: "lightgray", border: "none" }} value={isEditable.annual__father_income ? newAnnualI : annuals_income} onChange={(e) => setAnnualI(e.target.value)} disabled={!isEditable.annual__father_income} />
                        {
                            student.name === selectedStudent && annuals_income && !submitBtn.annual__father_income ?
                                <IconEdit stroke={2} onClick={() => {
                                    setIsEditable(prevState => ({
                                        ...prevState,
                                        annual__father_income: true
                                    }))

                                    setAnnualI(annuals_income || '')
                                    setSubmitBtn(prevState => ({
                                        ...prevState,
                                        annual__father_income: true
                                    }))
                                }} />
                                :
                                <IconSend stroke={2} onClick={() => {
                                    mutateAsyncAnnualIncome({
                                        name: findAnnualI("Father"),
                                        annual_income: newAnnualI

                                    }).then(() => {
                                        refetch()
                                        setIsEditable(prevState => ({
                                            ...prevState,
                                            annual__father_income: false
                                        }))
                                        setSubmitBtn(prevState => ({
                                            ...prevState,
                                            annual__father_income: false
                                        }))
                                    })
                                }} />

                        }
                    </div>
                    <div style={{ paddingBottom: "0.5rem", width: "700px", margin: "0px auto" }}>
                        <Text sx={{

                            color: studentProfileColor,
                            padding: "10px 1rem"
                        }}>Approximate Yearly Income of Mother</Text>
                        <input type="text" name="" id="" style={{ borderRadius: "8px", width: "312px", marginLeft: "1rem", padding: "0.5rem", backgroundColor: "lightgray", border: "none" }} value={isEditable.annual__mother_income ? newAnnualIMother : annuals_income_mother} onChange={(e) => setAnnualIMother(e.target.value)} disabled={!isEditable.annual__mother_income} />
                        {
                            student.name === selectedStudent && annuals_income_mother && !submitBtn.annual__mother_income ?
                                <IconEdit stroke={2} onClick={() => {
                                    setIsEditable(prevState => ({
                                        ...prevState,
                                        annual__mother_income: true
                                    }))

                                    setAnnualIMother(annuals_income_mother || '')
                                    setSubmitBtn(prevState => ({
                                        ...prevState,
                                        annual__mother_income: true
                                    }))
                                }} />
                                :
                                <IconSend stroke={2} onClick={() => {
                                    mutateAsyncAnnualIncome({
                                        name: findAnnualI("Mother"),
                                        annual_income: newAnnualIMother

                                    }).then(() => {
                                        refetch()
                                        setIsEditable(prevState => ({
                                            ...prevState,
                                            annual__mother_income: false
                                        }))
                                        setSubmitBtn(prevState => ({
                                            ...prevState,
                                            annual__mother_income: false
                                        }))
                                    })
                                }} />

                        }
                    </div>
                </div>
                <Box sx={{
                    marginTop: "2rem",
                    width: "100%",
                    borderBottom: isSelected ? '2px solid ' + studentProfileColor : '1px solid #0005'
                }} />
            </div >
        </>
    )
}