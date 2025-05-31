import { useCustom } from "@refinedev/core";

export interface Student {
  name: string
  first_name: string
  reference_number: string
  school: string
  middle_name: string
  date_of_birth: string
  religion: string
  caste: string
  sub_caste: string
  mother_tongue: string
  address_line_1: string
  address_line_2: string
  enquired_class: string
  blood_group: string
  annual_income: string
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
