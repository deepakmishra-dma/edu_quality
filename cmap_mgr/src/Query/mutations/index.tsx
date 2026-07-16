import { useCustomMutation, useUpdate } from "@refinedev/core";
import { useCallback } from "react";
import type { CMAPVariables } from "../../types";

export const useCMAPTableFields = () => {
  const { mutateAsync, ...mutationObjs } = useCustomMutation({
    mutationOptions: {},
  });
  const mutationAsyncFunction = useCallback(
    (variables: CMAPVariables) => {
      return mutateAsync({
        url: "/api/method/edu_quality.edu_quality.doctype.cmap.cmap.get_cmap_list",
        method: "post",
        values: variables,
      });
    },
    [mutateAsync]
  );
  return {
    ...mutationObjs,
    mutateAsync: mutationAsyncFunction,
  };
};

export const useMutateCMAPPeriods = () => {
  const { mutateAsync, ...mutationObjs } = useCustomMutation({
    mutationOptions: {},
  });
  const mutationAsyncFunction = useCallback(
    (data: Array<{ name: string; new_period: number | string }>) => {
      return mutateAsync({
        url: "/api/method/edu_quality.edu_quality.doctype.cmap.cmap.reorder_cmap_period",
        method: "post",
        values: { changed_cmaps: data },
      });
    },
    [mutateAsync]
  );
  return {
    ...mutationObjs,
    mutateAsync: mutationAsyncFunction,
  };
};
