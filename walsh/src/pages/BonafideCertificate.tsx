

import { useEffect, useCallback } from "react"
import { useNavigate } from "react-router-dom";
import useStudentList from "../components/queries/useStudentList";

export const BonafideCertificate = () => {
    const { data: studentsList } = useStudentList()
    const student_id = studentsList?.data?.message[0].name;
    const navigate = useNavigate()
    const requestBonafide = useCallback(async () => {
        const myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");
        fetch("/api/method/edu_quality.public.py.walsh.bonafide.send_bonafide", {
            method: 'POST',
            headers: myHeaders,
            body: JSON.stringify({
                "student_id": student_id
            }),
            redirect: 'follow'
        })
            .then(response => response.json())
            .then(result => result.message)
            .then((message) => {
                if (message && message.success) {
                    console.log("success ", message.message);
                    // Other actions on success
                } else if (message && message.error_message) {
                    console.log("error-message ", message.error_message);
                    // Handle error message
                } else {
                    console.log("Unexpected response format:", message);
                }

            })
            .catch(error => console.log('error', error))
            .finally(() => {
                // setSendingOtp(false)
            })
    }, [studentsList, navigate]);
    useEffect(() => {

        requestBonafide();
        navigate("/")
    }, [requestBonafide, navigate]);

    return (
        <>
            <h1>Hii</h1>
        </>
    )
}