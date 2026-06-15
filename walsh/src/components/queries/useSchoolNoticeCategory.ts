import { useQuery } from '@tanstack/react-query';

const fetchSchoolNoticeCategories = async () => {
  const url = '/api/resource/School%20Notice%20Category?limit=0';
  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json; charset=UTF-8',
      },
    });
    const jsonData = await response.json();
    return jsonData.data.map((item: { name: string }) => item.name);
  } catch (err) {
    console.error(err);
    return [];
  }
};

const useSchoolNoticeCategory = () => {
  return useQuery({
    queryKey: ['school', 'notice', 'categories'],
    queryFn: fetchSchoolNoticeCategories,
  });
};

export default useSchoolNoticeCategory;
