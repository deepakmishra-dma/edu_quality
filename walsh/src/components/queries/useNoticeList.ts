import { BaseRecord, useCustom } from "@refinedev/core";

export interface Notice extends BaseRecord {
  name: string;
  subject: string;
  notice: string;
  students?: string[]
  is_read?: boolean
  is_archived?: boolean
  is_stared?: boolean
}

interface NoticeListProps {
  archivedOnly?: boolean;
  staredOnly?: boolean;
}

const useNoticeList = (props: NoticeListProps) => {
  return useCustom<{ message: Notice[] }>({
    config: {
      query: {
        stared_only: props.staredOnly,
        archived_only: props.archivedOnly
      }
    },
    errorNotification: {
      message: "Failed to get list {{ resourceName }}",
      type: "error",
    },
    method: "get",
    queryOptions: {
      queryKey: ["student", 'list', props.staredOnly, props.archivedOnly],
    },
    successNotification: undefined,
    url: "/api/method/edu_quality.public.py.walsh.notices.get_all_notices",
  })
}

export default useNoticeList
