import {BaseRecord} from "@refinedev/core";
import {IDataContextProvider} from "@refinedev/core/dist/contexts/data/IDataContext";

export interface Cmap extends BaseRecord {
  name: string;
  subject: string;
  cmap: string;
  students?: string[]
}

const cmapsDataProvider: Partial<IDataContextProvider> = {
  getList: async () => {
    const url = "/api/method/edu_quality.public.py.walsh.cmaps.get_all_cmaps"
    const response = await fetch(url);
    const data = await response.json();
    if (!data?.message?.success) {
      throw Error("Failed to get list: " + (data?.message?.error_message || data.exception));
    }
    return data.message;
  }
}

export default cmapsDataProvider
