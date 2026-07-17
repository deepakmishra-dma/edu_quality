import { useMemo } from "react";

import Table from "../../components/common/Table";
import { useFrappeGetCall } from "frappe-react-sdk";
import TextInput from "../../components/common/TextInput";

const initialColumns = [
  {
    accessorKey: "refno",
    label: "Ref No",
  },
  {
    accessorKey: "name",
    label: "Name",
  },
];

const MarksEntry = () => {
  const { data: columns, isLoading } = useFrappeGetCall(
    "edu_quality.api.result_tool.get_subject_criteria_columns",
    { assessment_group: "ASas" }
  );

  const finalColumns = useMemo(() => {
    const columns = [
      {
        label: "English",
        accessorKey: "english",
        cell: () => {
          return <TextInput type="number" />;
        },
      },
      {
        label: "Social Studies",
        accessorKey: "social_studies",
        cell: () => {
          return <TextInput type="number" />;
        },
      },
      {
        label: "Computer",
        accessorKey: "computer",
        cell: () => {
          return <TextInput type="number" />;
        },
      },
    ];
    if (isLoading || !columns) {
      return [];
    }

    return [...initialColumns, ...columns];
  }, [isLoading, columns]);

  if (isLoading) {
    return "Loading";
  }

  return (
    <div>
      <Table
        columns={finalColumns}
        data={[
          {
            refno: "1234",
            name: "Aryan",
            english: 0,
            social_studies: 0,
            computer: 0,
          },
          {
            refno: "1234",
            name: "Aryan",
            english: 0,
            social_studies: 0,
            computer: 0,
          },
          {
            refno: "1234",
            name: "Aryan",
            english: 0,
            social_studies: 0,
            computer: 0,
          },
          {
            refno: "1234",
            name: "Aryan",
            english: 0,
            social_studies: 0,
            computer: 0,
          },
        ]}
      ></Table>
    </div>
  );
};
export default MarksEntry;
