import { useCustom } from "@refinedev/core";




export const usePTMLinksQuery = (selectedStudent: string) => {
    return useCustom({
        config: {
            query: {
                student_id: selectedStudent
            }
        },
        errorNotification: undefined,
        method: "get",
        queryOptions: {
            queryKey: ["onlinePTMList", selectedStudent],
        },
        successNotification: undefined,
        url: `/api/method/edu_quality.cmap_jobs.get_upcoming_online_ptm_links`,
    })
}

export const useofflinePTMLinksQuery = (custom_school: string | undefined) => {
    return useCustom({
        config: {
            query: {
                school: custom_school
            }
        },
        errorNotification: undefined,
        method: "get",
        queryOptions: {
            queryKey: ["offlinePTMList", custom_school],
        },
        successNotification: undefined,
        url: `/api/method/edu_quality.api.calendar.get_calender_events`,
    })
}