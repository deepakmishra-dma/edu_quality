import { useCustom } from "@refinedev/core";
import { useCustomMutation } from "@refinedev/core";
import { useCallback } from "react";

export interface Guardian {

    first_name: string
    last_name: string
    guardian_name: string
    email_address: string
    mobile_number: string
    annual_income: string
    name: string
    relation: string
    address_line_1: string
}
interface Student_ID {
    student_id: string
}

const useGuardianList = (props: Student_ID) => {
    return useCustom<{ message: Guardian[] }>({
        config: {
            query: {
                student_id: props.student_id
            }
        },
        errorNotification: undefined,
        method: "get",
        queryOptions: {
            queryKey: ["guardian", props.student_id],
        },
        successNotification: undefined,
        url: '/api/method/edu_quality.public.py.student.relationDetails'
    })
}



interface GuardianEmailvariables {
    name: string
    new_email: string
}
interface GuardianNumbervariables {
    name: string
    mobile_number: string
}
interface GuardianFatherEmailvariables {
    name: string
    new_email: string
}
interface GuardianFatherNumbervariables {
    name: string
    mobile_number: string
}
interface GuardianAddress {
    name: string
    address_line_1: string
}
interface GuardianAddress2 {
    name: string
    address_line_2: string
}
interface UpdateBloodGroupProps {
    name: string
    blood_group: string
}
interface UpdateAnnualIncomeProps {
    name: string
    annual_income: string
}

export const guardin_email_update = () => {
    const { mutate, mutateAsync, ...mutationObjs } = useCustomMutation({
        mutationOptions: {}
    })
    const mutationFunction = useCallback((variables: GuardianEmailvariables) => {
        return mutate({
            url: '/api/method/edu_quality.public.py.student.update_guardian_email',
            method: 'post',
            values: variables
        })
    }, [mutate])
    const mutationAsyncFunction = useCallback((variables: GuardianEmailvariables) => {
        return mutateAsync({
            url: '/api/method/edu_quality.public.py.student.update_guardian_email',
            method: 'post',
            values: variables
        })
    }, [mutateAsync])
    return {
        ...mutationObjs,
        mutate: mutationFunction,
        mutateAsync: mutationAsyncFunction
    }
}
export const guardin_number_update = () => {
    const { mutate, mutateAsync, ...mutationObjs } = useCustomMutation({
        mutationOptions: {}
    })
    const mutationFunction = useCallback((variables: GuardianNumbervariables) => {
        return mutate({
            url: '/api/method/edu_quality.public.py.student.update_guardian_number',
            method: 'post',
            values: variables
        })
    }, [mutate])
    const mutationAsyncFunction = useCallback((variables: GuardianNumbervariables) => {
        return mutateAsync({
            url: '/api/method/edu_quality.public.py.student.update_guardian_number',
            method: 'post',
            values: variables
        })
    }, [mutateAsync])
    return {
        ...mutationObjs,
        mutate: mutationFunction,
        mutateAsync: mutationAsyncFunction
    }
}
export const guardin_father_email_update = () => {
    const { mutate, mutateAsync, ...mutationObjs } = useCustomMutation({
        mutationOptions: {}
    })
    const mutationFunction = useCallback((variables: GuardianFatherEmailvariables) => {
        return mutate({
            url: '/api/method/edu_quality.public.py.student.update_guardian_father_email',
            method: 'post',
            values: variables
        })
    }, [mutate])
    const mutationAsyncFunction = useCallback((variables: GuardianFatherEmailvariables) => {
        return mutateAsync({
            url: '/api/method/edu_quality.public.py.student.update_guardian_father_email',
            method: 'post',
            values: variables
        })
    }, [mutateAsync])
    return {
        ...mutationObjs,
        mutate: mutationFunction,
        mutateAsync: mutationAsyncFunction
    }
}
export const guardin_father_number_update = () => {
    const { mutate, mutateAsync, ...mutationObjs } = useCustomMutation({
        mutationOptions: {}
    })
    const mutationFunction = useCallback((variables: GuardianFatherNumbervariables) => {
        return mutate({
            url: '/api/method/edu_quality.public.py.student.update_guardian__father_number',
            method: 'post',
            values: variables
        })
    }, [mutate])
    const mutationAsyncFunction = useCallback((variables: GuardianFatherNumbervariables) => {
        return mutateAsync({
            url: '/api/method/edu_quality.public.py.student.update_guardian__father_number',
            method: 'post',
            values: variables
        })
    }, [mutateAsync])
    return {
        ...mutationObjs,
        mutate: mutationFunction,
        mutateAsync: mutationAsyncFunction
    }
}
export const guardin_address = () => {
    const { mutate, mutateAsync, ...mutationObjs } = useCustomMutation({
        mutationOptions: {}
    })
    const mutationFunction = useCallback((variables: GuardianAddress) => {
        return mutate({
            url: '/api/method/edu_quality.public.py.student.update_guardian__address1',
            method: 'post',
            values: variables
        })
    }, [mutate])
    const mutationAsyncFunction = useCallback((variables: GuardianAddress) => {
        return mutateAsync({
            url: '/api/method/edu_quality.public.py.student.update_guardian__address1',
            method: 'post',
            values: variables
        })
    }, [mutateAsync])
    return {
        ...mutationObjs,
        mutate: mutationFunction,
        mutateAsync: mutationAsyncFunction
    }
}
export const guardin_address2 = () => {
    const { mutate, mutateAsync, ...mutationObjs } = useCustomMutation({
        mutationOptions: {}
    })
    const mutationFunction = useCallback((variables: GuardianAddress2) => {
        return mutate({
            url: '/api/method/edu_quality.public.py.student.update_guardian__address2',
            method: 'post',
            values: variables
        })
    }, [mutate])
    const mutationAsyncFunction = useCallback((variables: GuardianAddress2) => {
        return mutateAsync({
            url: '/api/method/edu_quality.public.py.student.update_guardian__address2',
            method: 'post',
            values: variables
        })
    }, [mutateAsync])
    return {
        ...mutationObjs,
        mutate: mutationFunction,
        mutateAsync: mutationAsyncFunction
    }
}
export const updateBloodGroup = () => {
    const { mutate, mutateAsync, ...mutationObjs } = useCustomMutation({
        mutationOptions: {}
    })
    const mutationFunction = useCallback((variables: UpdateBloodGroupProps) => {
        return mutate({
            url: '/api/method/edu_quality.public.py.student.update_blood_group',
            method: 'post',
            values: variables
        })
    }, [mutate])
    const mutationAsyncFunction = useCallback((variables: UpdateBloodGroupProps) => {
        return mutateAsync({
            url: '/api/method/edu_quality.public.py.student.update_blood_group',
            method: 'post',
            values: variables
        })
    }, [mutateAsync])
    return {
        ...mutationObjs,
        mutate: mutationFunction,
        mutateAsync: mutationAsyncFunction
    }
}


export const updateAnnualIncome = () => {
    const { mutate, mutateAsync, ...mutationObjs } = useCustomMutation({
        mutationOptions: {}
    })
    const mutationFunction = useCallback((variables: UpdateAnnualIncomeProps) => {
        return mutate({
            url: '/api/method/edu_quality.public.py.student.update_annual_income',
            method: 'post',
            values: variables
        })
    }, [mutate])
    const mutationAsyncFunction = useCallback((variables: UpdateAnnualIncomeProps) => {
        return mutateAsync({
            url: '/api/method/edu_quality.public.py.student.update_annual_income',
            method: 'post',
            values: variables
        })
    }, [mutateAsync])
    return {
        ...mutationObjs,
        mutate: mutationFunction,
        mutateAsync: mutationAsyncFunction
    }
}





export default useGuardianList