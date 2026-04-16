import { useCustom } from "@refinedev/core";
import { useCustomMutation } from "@refinedev/core";
import { useCallback } from "react";
import type { CMAPVariables } from "../../types";

export const useCLassList = () => {
  return useCustom({
    errorNotification: undefined,
    method: "get",
    queryOptions: {
      queryKey: ["classesList"],
    },
    successNotification: undefined,
    url: "/api/resource/Class%20Type",
  });
};
export const useCLassName = (class_name: string) => {
  return useCustom({
    errorNotification: undefined,
    method: "get",
    queryOptions: {
      queryKey: ["class_name", class_name],
    },
    successNotification: undefined,
    url: `/api/resource/Class%20Type/${class_name}`,
  });
};
export const useCmapHeaders = () => {
  return useCustom({
    errorNotification: undefined,
    method: "get",
    queryOptions: {
      queryKey: ["cmap_headers"],
    },
    successNotification: undefined,
    url: `/api/method/edu_quality.edu_quality.doctype.cmap.cmap.get_cmap_creation_headers`,
  });
};
export const useCmapItemGroupID = (ids: string) => {
  return useCustom({
    config: {
      query: {
        filters: JSON.stringify([["item_group", "=", ids]]),
      },
    },
    errorNotification: undefined,
    method: "get",
    queryOptions: {
      queryKey: ["cmap_item_group_id", ids],
      enabled: Boolean(ids),
    },
    successNotification: undefined,
    url: `/api/resource/Item`,
  });
};

export const useAcademicCurrentYear = () => {
  const { data, error, ...rest } = useCustom({
    config: {
      query: {
        filters: JSON.stringify([
          ["Academic Year", "custom_current_academic_year", "=", "1"],
        ]),
      },
    },
    errorNotification: undefined,
    method: "get",
    queryOptions: {
      queryKey: ["currentYear"],
    },
    successNotification: undefined,
    url: `/api/resource/Academic%20Year`,
  });
  return {
    data,
    error: error?.response?.data?.exception, // Extract the error message
    ...rest,
  };
};

export const useAcademicNextYear = () => {
  const { data, error, ...rest } = useCustom({
    config: {
      query: {
        filters: JSON.stringify([
          ["Academic Year", "custom_next_academic_year", "=", "1"],
        ]),
      },
    },
    errorNotification: undefined,
    method: "get",
    queryOptions: {
      queryKey: ["nextYear"],
    },
    successNotification: undefined,
    url: `/api/resource/Academic%20Year`,
  });
  return {
    data,
    error: error?.response?.data?.exception, // Extract the error message
    ...rest,
  };
};

export const useAcademicYears = () => {
  const { data, error, ...rest } = useCustom({
    config: {
      query: {
        as_dict: true,
        doctype: "Academic Year",
        txt: "2",
        searchfield: "name",
        start: 0,
        page_len: 10,
      },
    },
    errorNotification: undefined,
    method: "get",
    queryOptions: {
      queryKey: ["academic-years"],
    },
    successNotification: undefined,
    url: `/api/method/edu_quality.public.py.utils.academic_year_query`,
  });
  return {
    data,
    error: error?.response?.data?.exception, // Extract the error message
    ...rest,
  };
};
