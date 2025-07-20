import SingleSelect from "../../components/common/SingleSelect";
import Table from "../../components/common/Table";

const columns = [
  {
    accessorKey: "subject",
    label: "Subject",
    cell: (info) => {
      return <SingleSelect docType="Course" value={info.getValue()} />;
    },
  },
  {
    accessorKey: "textbook",
    label: "Textbook",
    cell: (info) => {
      return <SingleSelect docType="Textbook" value={info.getValue()} />;
    },
  },
  { accessorKey: "Assesment_criteria_1", label: "Assesment Criteria 1" },
  { accessorKey: "Assesment_criteria_2", label: "Assesment Criteria 2" },
  { accessorKey: "Assesment_criteria_3", label: "Assesment Criteria 3" },
  { accessorKey: "Assesment_criteria_4", label: "Assesment Criteria 4" },
  { accessorKey: "Assesment_criteria_5", label: "Assesment Criteria 5" },
];

const CreateExamComponent = () => {
  return (
    <div>
      <Table columns={columns} data={[{ subject: "" }]}></Table>
    </div>
  );
};
export default CreateExamComponent;
