import {BaseRecord} from "@refinedev/core";
import {IDataContextProvider} from "@refinedev/core/dist/contexts/data/IDataContext";

export interface Notice extends BaseRecord {
  name: string;
  subject: string;
  notice: string;
  students?: string[]
}

const noticesDataProvider: Partial<IDataContextProvider> = {
  getList: async (params) => {
    let url = "/api/method/edu_quality.public.py.walsh.notices.get_all_notices"
    if (params.pagination?.mode === 'server')
      url += `?page=${params.pagination?.current}&limit=${params.pagination?.pageSize}`;
    const response = await fetch(url);
    const data = await response.json();
    if (!data?.message?.success) {
      throw Error("Failed to get list: " + (data?.message?.error_message || data.exception));
    }
    return data.message;
  },
  getOne: async (params) => {
    let url = `/api/method/edu_quality.public.py.walsh.notices.get_notice_by_id?id=${params.id}`
    if (params?.meta?.student)
      url += `&student=${params?.meta?.student}`
    const response = await fetch(url);
    const data = await response.json();
    return data.message;
  }
}

export default noticesDataProvider
