import { useQuery } from "@tanstack/react-query";

const fetchSchoolNoticeCategories = async () => {
  const url =
    "/api/method/edu_quality.public.py.walsh.notices.get_school_notice_category";
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json; charset=UTF-8",
      },
    });
    const jsonData = await response.json();
    return jsonData.message.map((item: { name: string }) => item.name);
  } catch (err) {
    console.error(err);
    return [];
  }
};

const useSchoolNoticeCategory = ({ identity }: { identity: any }) => {
  return useQuery({
    queryKey: ["school", "notice", "categories", identity],
    queryFn: fetchSchoolNoticeCategories,
  });
};

export default useSchoolNoticeCategory;
