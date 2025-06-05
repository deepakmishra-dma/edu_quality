import { useCustom } from "@refinedev/core";

export interface BonafdeList {

    bonafide_pdf: string
    creation: any
    name: any
    student_name: string
}

const useBonafideList = () => {
    return useCustom<{ message: BonafdeList[] }>({
        config: undefined,
        errorNotification: undefined,
        method: "get",
        queryOptions: {
            queryKey: ["bonafide_certificate", 'list_bonafide'],
        },
        successNotification: undefined,
        url: '/api/method/edu_quality.public.py.walsh.bonafide.bonafide_list'
    })
}

export default useBonafideList
