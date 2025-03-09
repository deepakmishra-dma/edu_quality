import { useCustom } from "@refinedev/core";

export interface PortionCircular {
  [x: string]: {
    [x: string]: {
      [x: string]: {
        cmap_name: string;
        subject: string;
        reserved_for_portion_circular: number;
        chapter: string;
        textbook: string;
        item_group: string;
        count: number;
        item_names: string;
        products: { url: string; name: string }[];
      }[];
    };
  };
}
const usePortionCircularList = (unit: string, division: string) => {
  return useCustom<{ message: PortionCircular }>({
    config: {
      query: {
        unit,
        division,
      },
    },
    errorNotification: undefined,
    method: "get",
    queryOptions: {
      queryKey: ["cmap", "list", unit, division],
    },
    successNotification: undefined,
    url: "/api/method/edu_quality.public.py.walsh.cmap.get_portion_circulars",
  });
};

export default usePortionCircularList;
