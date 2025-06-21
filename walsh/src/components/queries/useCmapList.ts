import {useCustom} from "@refinedev/core";

export interface Cmap {
  class: string
  unit: string
  period: string
  real_date: string
  products: [{
    chapter: string
    item_group: string
    broadcast_description: string
    homework_description: string
    parentnote_description: string
    home_work: string
    item: string
    hide_in_walsh:boolean;
    item_data: {
      custom_product_url: string
    }
  }]
}

const useCmapList = (subject: string, unit: string, division: string) => {
  return useCustom<{ message: Cmap[] }>({
    config: {
      query: {
        subject,
        unit,
        division
      }
    },
    errorNotification: undefined,
    method: "get",
    queryOptions: {
      queryKey: ["cmap", 'list', subject, unit, division],
    },
    successNotification: undefined,
    url: '/api/method/edu_quality.public.py.walsh.cmap.get_all_cmaps'
  })
}

export default useCmapList
