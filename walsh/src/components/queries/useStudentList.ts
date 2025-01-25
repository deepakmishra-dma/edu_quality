import {useCustom} from "@refinedev/core";

export interface Student {
  name: string
  first_name: string
  reference_number: string
}

const useStudentList = () => {
  return useCustom<{ message: Student[] }>({
    config: undefined,
    errorNotification: undefined,
    method: "get",
    queryOptions: {
      queryKey: ["student", 'list'],
    },
    successNotification: undefined,
    url: '/api/method/edu_quality.public.py.walsh.cmap.get_students'
  })
}

export default useStudentList
