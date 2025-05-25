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
        url: `/api/method/edu_quality.cmap_jobs.get_upcoming_online_ptm_links?student_id=SHED21`,
    })
}