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

interface MotherId {
    name: string
}
interface FatherId {
    name: string
}


export const useStudentDataList = (props: Student_ID) => {
    return useCustom({
        config: {
            query: {
                student_id: props.student_id
            }
        },
        errorNotification: undefined,
        method: "get",
        queryOptions: {
            queryKey: ["studentDataList", props.student_id],
        },
        successNotification: undefined,
        url: `/api/resource/Student/${props.student_id}`,
    })
}
export const useDetailsList = (student_id: string) => {
    return useCustom({
        config: {
            query: {
                student: student_id
            }
        },
        errorNotification: undefined,
        method: "get",
        queryOptions: {
            queryKey: ["DetailsDataList", student_id],
        },
        successNotification: undefined,
        url: `/api/method/edu_quality.api.student.get_student_data`,
    })
}




export const useMotherGuardianList = (props: MotherId) => {
    return useCustom({
        config: {
            query: {
                name: props.name
            }
        },
        errorNotification: undefined,
        method: "get",
        queryOptions: {
            queryKey: ["guardianMotherData", props.name],
        },
        successNotification: undefined,
        url: `/api/resource/Guardian/${props.name}`
    })
}
export const useFatherGuardianList = (props: FatherId) => {
    return useCustom({
        config: {
            query: {
                name: props.name
            }
        },
        errorNotification: undefined,
        method: "get",
        queryOptions: {
            queryKey: ["guardianFatherData", props.name],
        },
        successNotification: undefined,
        url: `/api/resource/Guardian/${props.name}`
    })
}


interface FatherDetailsProps {
    FatherGuardian: string
}

interface GuardianEmailvariables {
    name: string
    email_address: string
}
interface GuardianNumbervariables {
    name: string
    mobile_number: string
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
            url: `/api/resource/Guardian/${variables.name}`,
            method: 'put',
            values: variables
        })
    }, [mutate])
    const mutationAsyncFunction = useCallback((variables: GuardianEmailvariables) => {
        return mutateAsync({
            url: `/api/resource/Guardian/${variables.name}`,
            method: 'put',
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
            url: `/api/resource/Guardian/${variables.name}`,
            method: 'put',
            values: variables
        })
    }, [mutate])
    const mutationAsyncFunction = useCallback((variables: GuardianNumbervariables) => {
        return mutateAsync({
            url: `/api/resource/Guardian/${variables.name}`,
            method: 'put',
            values: variables
        })
    }, [mutateAsync])
    return {
        ...mutationObjs,
        mutate: mutationFunction,
        mutateAsync: mutationAsyncFunction
    }
}

export const guardin_father_number_update = ({ FatherGuardian }: FatherDetailsProps) => {
    const urls = `/api/resource/Guardian/${FatherGuardian}`;
    console.log("check url", urls)
    const { mutate, mutateAsync, ...mutationObjs } = useCustomMutation({
        mutationOptions: {}
    })
    const mutationFunction = useCallback((variables: GuardianFatherNumbervariables) => {
        return mutate({
            url: `/api/resource/Guardian/${variables.name}`,
            method: 'put',
            values: variables
        })
    }, [mutate])
    const mutationAsyncFunction = useCallback((variables: GuardianFatherNumbervariables) => {
        return mutateAsync({
            url: `/api/resource/Guardian/${variables.name}`,
            method: 'put',
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
            url: `/api/resource/Student/${variables.name}`,
            method: 'put',
            values: variables
        })
    }, [mutate])
    const mutationAsyncFunction = useCallback((variables: GuardianAddress) => {
        return mutateAsync({
            url: `/api/resource/Student/${variables.name}`,
            method: 'put',
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
            url: `/api/resource/Student/${variables.name}`,
            method: 'put',
            values: variables
        })
    }, [mutate])
    const mutationAsyncFunction = useCallback((variables: GuardianAddress2) => {
        return mutateAsync({
            url: `/api/resource/Student/${variables.name}`,
            method: 'put',
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
            url: `/api/resource/Student/${variables.name}`,
            method: 'put',
            values: variables
        })
    }, [mutate])
    const mutationAsyncFunction = useCallback((variables: UpdateBloodGroupProps) => {
        return mutateAsync({
            url: `/api/resource/Student/${variables.name}`,
            method: 'put',
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
            url: `/api/resource/Guardian/${variables.name}`,
            method: 'put',
            values: variables
        })
    }, [mutate])
    const mutationAsyncFunction = useCallback((variables: UpdateAnnualIncomeProps) => {
        return mutateAsync({
            url: `/api/resource/Guardian/${variables.name}`,
            method: 'put',
            values: variables
        })
    }, [mutateAsync])
    return {
        ...mutationObjs,
        mutate: mutationFunction,
        mutateAsync: mutationAsyncFunction
    }
}





