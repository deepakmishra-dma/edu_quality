import useStudentList, { Student } from "../queries/useStudentList.ts";

const profileColors = ["#00a8ff", "#019837", "#d21eff", "#fe7f00", "#fdc426"];
const iconsColors = ["#fdc426"];

export const getStudentProfileColor = (
  student_id: string | null,
  students: Student[]
) => {
  const idx = Math.max(
    students?.findIndex((student) => student.name === student_id) || -1,
    0
  );
  return profileColors[idx % profileColors.length];
};
export const getStudentIconColor = (
  student_id: string,
  students: Student[]
) => {
  const idx = Math.max(
    students?.findIndex((student) => student.name === student_id) || -1,
    0
  );
  return iconsColors[idx % iconsColors.length];
};

const useStudentProfileColor = (student_id: string | null) => {
  const { data } = useStudentList();
  return getStudentProfileColor(student_id, data?.data?.message || []);
};

export default useStudentProfileColor;
