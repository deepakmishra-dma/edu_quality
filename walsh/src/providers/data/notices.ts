import {IDataContextProvider} from "@refinedev/core/dist/contexts/data/IDataContext";

const noticesDataProvider: Partial<IDataContextProvider> = {
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
