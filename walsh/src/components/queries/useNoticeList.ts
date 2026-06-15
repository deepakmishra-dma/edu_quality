import { useInfiniteQuery } from "@tanstack/react-query";
import { BaseRecord } from "@refinedev/core";

export interface Notice extends BaseRecord {
  name: string;
  subject: string;
  notice: string;
  students?: string[];
  is_read?: boolean;
  is_archived?: boolean;
  is_stared?: boolean;
}

interface NoticeListProps {
  archivedOnly?: boolean;
  staredOnly?: boolean;
  limit?: number;
  category?: string;
}

const useNoticeList = (props: NoticeListProps) => {
  return useInfiniteQuery<{ message: { notices: Notice[]; total: number } }>(
    ["student", "list", props.staredOnly, props.archivedOnly, props.category],
    async ({ pageParam = 1 }) => {
      const response = await fetch(
        `/api/method/edu_quality.public.py.walsh.notices.get_all_notices?${new URLSearchParams(
          {
            stared_only: props.staredOnly?.toString() || "",
            archived_only: props.archivedOnly?.toString() || "",
            page: pageParam.toString(),
            limit: String(props.limit || 10),
            category: props.category || "",
          }
        )}`
      );

      if (!response.ok) {
        throw new Error("Failed to get list");
      }

      return response.json();
    },
    {
      getNextPageParam: (lastPage, pages) => {
        const totalPages = Math.ceil(
          lastPage.message.total / (props?.limit || 10)
        );
        const nextPage = pages.length + 1;
        return nextPage <= totalPages ? nextPage : undefined;
      },
    }
  );
};

export default useNoticeList;
