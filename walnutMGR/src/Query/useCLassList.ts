import { useCustom } from "@refinedev/core";
import { useCustomMutation } from "@refinedev/core";
import { useCallback } from "react";

interface CMAPVariables {
    academic_year: string,
    program: string,
    subject: string,
    unit: string[],
    from_date?: string,
    end_date?: string,
}

export const useCLassList = () => {
    return useCustom({
        errorNotification: undefined,
        method: "get",
        queryOptions: {
            queryKey: ["classesList"],
        },
        successNotification: undefined,
        url: '/api/resource/Class%20Type'
    })
}
export const useCLassName = (class_name: string) => {
    return useCustom({
        errorNotification: undefined,
        method: "get",
        queryOptions: {
            queryKey: ["class_name", class_name],
        },
        successNotification: undefined,
        url: `/api/resource/Class%20Type/${class_name}`
    })
}
export const useCmapHeaders = () => {
    return useCustom({
        errorNotification: undefined,
        method: "get",
        queryOptions: {
            queryKey: ["cmap_headers"],
        },
        successNotification: undefined,
        url: `/api/method/edu_quality.edu_quality.doctype.cmap.cmap.get_cmap_creation_headers`
    })
}
export const useCmapItemGroupID = (ids: string) => {

    return useCustom({
        config: {
            query: {
                filters: JSON.stringify([["item_group", "=", ids]])

            }
        },
        errorNotification: undefined,
        method: "get",
        queryOptions: {
            queryKey: ["cmap_item_group_id", ids],
            enabled: Boolean(ids),
        },
        successNotification: undefined,
        url: `/api/resource/Item`
    })
}


export const useCMAPTableFields = () => {
    const { mutateAsync, ...mutationObjs } = useCustomMutation({
        mutationOptions: {}
    })
    const mutationAsyncFunction = useCallback((variables: CMAPVariables) => {
        return mutateAsync({
            url: '/api/method/edu_quality.edu_quality.doctype.cmap.cmap.get_cmap_list',
            method: 'post',
            values: variables
        })
    }, [mutateAsync])
    return {
        ...mutationObjs,
        mutateAsync: mutationAsyncFunction
    }
}

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