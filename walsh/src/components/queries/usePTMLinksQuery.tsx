
// import { useCustom } from "@refinedev/core";
import { useQuery } from '@tanstack/react-query';




export const usePTMLinksQuery = (selectedStudent: string) => {
    return useQuery({
        queryKey: ['onlinePTMList', selectedStudent],
        queryFn: () =>
            fetch(`/api/method/edu_quality.cmap_jobs.get_upcoming_online_ptm_links?student_id=${selectedStudent}`).then((res) => {
                if (res.status === 200) return res.json();
                throw new Error('Error fetching PTM links');
            }),
    });
};



export const useofflinePTMLinksQuery = (custom_school: string | undefined) => {
    return useQuery({
        queryKey: ['offlinePTMList', custom_school],
        queryFn: () =>
            fetch(`/api/method/edu_quality.api.calendar.get_calender_events?school=${custom_school}`).then((res) => {
                if (res.status === 200) return res.json();
                throw new Error('Failed to fetch offline PTM links');
            }),
    });
};
