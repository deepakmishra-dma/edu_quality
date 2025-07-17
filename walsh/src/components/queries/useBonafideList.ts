import { useCustom } from "@refinedev/core";

export interface BonafdeList {

    bonafide_pdf: string
    creation: any
    name: any
    student_name: string
}

const useBonafideList = (student_id: string) => {
    return useCustom<{ message: BonafdeList[] }>({
        config: {
            query: {
                student_id: student_id
            }
        },
        errorNotification: undefined,
        method: "get",
        queryOptions: {
            queryKey: ["bonafide_certificate", 'list_bonafide', student_id], 
        },
        successNotification: undefined,
        url: '/api/method/edu_quality.public.py.walsh.bonafide.bonafide_list'
    })
}

export default useBonafideList
