interface CsvDataTableProp {
  csvData: any[];
  maxRows?: number;
}

const CsvDataTable = (props: CsvDataTableProp) => {
  const { csvData, maxRows } = props;
  const columns = csvData.length ? Object.keys(csvData[0]) : [];
  return (
    <div className="tw-max-w-[100%] tw-overflow-auto">
      <table>
        <thead>
          <tr className="tw-border-b-[1px] tw-border-t-[1px] tw-border-l-[1px]">
            {columns.map((column) => (
              <th
                key={column}
                className="tw-p-1 tw-border-r-[1px] tw-text-center tw-px-2 tw-whitespace-nowrap"
              >
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {csvData
            .filter((_a, i) => (maxRows ? i < maxRows : true))
            .map((row) => (
              <tr key={row.id} className="tw-border-b-[1px] tw-border-l-[1px]">
                {columns.map((column) => (
                  <td
                    key={column}
                    className="tw-p-1 tw-border-r-[1px] tw-px-2 tw-whitespace-nowrap"
                  >
                    {row[column]}
                  </td>
                ))}
              </tr>
            ))}
        </tbody>
      </table>
      <div>Total Rows: {csvData.length}</div>
    </div>
  );
};

export default CsvDataTable;
