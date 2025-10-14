import { useCustom } from "@refinedev/core";




export const useAcademicCurrentYear = () => {

    const { data, error, ...rest } = useCustom({
        config: {
            query: {
                filters: JSON.stringify([["Academic Year", "custom_current_academic_year", "=", "1"]]),
            }
        },
        errorNotification: undefined,
        method: "get",
        queryOptions: {
            queryKey: ["currentYear"],

        },
        successNotification: undefined,
        url: `/api/resource/Academic%20Year`,
    })
    return {
        data,
        error: error?.response?.data?.exception, // Extract the error message
        ...rest,
    };
}
export const useAcademicNextYear = () => {
    const { data, error, ...rest } = useCustom({
        config: {
            query: {
                filters: JSON.stringify([["Academic Year", "custom_next_academic_year", "=", "1"]]),
            }
        },
        errorNotification: undefined,
        method: "get",
        queryOptions: {
            queryKey: ["nextYear"],
        },
        successNotification: undefined,
        url: `/api/resource/Academic%20Year`,
    })
    return {
        data,
        error: error?.response?.data?.exception, // Extract the error message
        ...rest,
    };
}







