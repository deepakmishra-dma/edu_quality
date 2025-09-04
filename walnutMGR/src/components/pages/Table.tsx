import { IconPencil, IconTrash } from "@tabler/icons-react";

import { DragDropContext, Draggable } from "react-beautiful-dnd";
import { StrictModeDroppable } from "../../StrictModeDroppable";
import { useEffect, useState } from "react";

interface TableProps {
  isButtonClicked: boolean;
  isLoading: any;
  cmap_table: any;
  cmap_headers: any;
  setSelectedIDS: any;
  setSelectedName: any;
  setSelectedItem: any;
  setSelectedUnits: any;
  selectedUnits: any;
  setShowButtons: any;
  setUnitModal: any;
  openModal: any;
  isEditMode: any;
  setCmapNames: any;
  setItemDetails: any;
  deleteModalOpen: any;
  setInsertModal: any;
}
interface SelectedRow {
  name: string;
  index: number;
}
interface DraggedItem {
  name: string;
  period: string;
}
interface RowFieldsProps {
  chapter: string;
  textbook: string;
  subject: string;
}

export const Table = ({
  isButtonClicked,
  isLoading,
  setSelectedUnits,
  selectedUnits,
  cmap_table,
  isEditMode,
  cmap_headers,
  setShowButtons,
  setCmapNames,
  setSelectedIDS,
  setSelectedName,
  setSelectedItem,
  openModal,
  setItemDetails,
  setUnitModal,
  deleteModalOpen,
  setInsertModal,
}: TableProps) => {
  const [draggedList, setDraggedList] = useState<DraggedItem[]>([]);

  const [, setRowField] = useState<RowFieldsProps>();

  const [selectedRows, setSelectedRows] = useState<SelectedRow[]>([]);
  const handleSelectAll = (e: any) => {
    setSelectedRows(
      e.target.checked
        ? draggedList.map((item, index) => ({ name: item?.name, index }))
        : []
    );
  };

  const handleSelectRow = ({
    index,
    name,
  }: {
    index: number;
    name: string;
  }) => {
    setSelectedRows((prevSelectedRows) =>
      prevSelectedRows.some((row) => row.index === index)
        ? prevSelectedRows.filter((row) => row.index !== index)
        : [...prevSelectedRows, { index, name }]
    );
  };

  const unitModalOpen = () => {
    setUnitModal(true);
  };

  const fetchData = async (id: string) => {
    await fetch(`/api/resource/CMAP/${id}`)
      .then((response) => response.json())

      .then((data) => setItemDetails(data.data.products))

      .catch((error) => console.error("Error fetching the data:", error));
  };

  useEffect(() => {
    if (cmap_table?.data?.message) {
      setDraggedList(cmap_table?.data?.message);
    }
  }, [setDraggedList, draggedList, cmap_table]);

  function handleOnDragEnd(result: any) {
    if (!result.destination) return;

    const items = draggedList;
    const [reorderedItem] = items?.splice(result.source.index, 1);
    items?.splice(result.destination.index, 0, reorderedItem);

    setDraggedList(items);
    setShowButtons(true);

    const draggedItem = draggedList[result.source.index];
    const droppedOnItem = draggedList[result.destination.index];

    setCmapNames((prevState: any) => ({
      ...prevState,
      cmap_name_one: draggedItem?.name,
      cmap_name_two: droppedOnItem?.name,
      cmap_first_period: draggedItem?.period,
      cmap_second_period: droppedOnItem?.period,
    }));
  }

  const handleUnitChange = (
    e: React.ChangeEvent<HTMLSelectElement>,
    rowId: number
  ) => {
    setSelectedUnits({
      ...selectedUnits,
      [rowId]: e.target.value,
    });
  };

  function insertModalOpen() {
    setInsertModal(true);
  }
  return (
    <>
      <div className="  mt-5  mx-auto ">
        {isButtonClicked && isLoading && (
          <div>
            <div className="flex justify-center mt-5">
              <output className={"flex justify-center items-center h-12 w-12"}>
                <svg
                  aria-hidden="true"
                  className="inline w-8 h-8 text-gray-200 animate-spin fill-blue-600"
                  viewBox="0 0 100 101"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
                    fill="currentColor"
                  />
                  <path
                    d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
                    fill="currentFill"
                  />
                </svg>
              </output>
            </div>
          </div>
        )}
        {isButtonClicked &&
          !isLoading &&
          cmap_table?.data?.message?.length > 0 && (
            <section style={{ height: "500px", overflowX: "scroll" }}>
              <DragDropContext onDragEnd={handleOnDragEnd}>
                <StrictModeDroppable droppableId="characters">
                  {(provided: any) => (
                    <table
                      className=" "
                      ref={provided.innerRef}
                      {...provided.droppableProps}
                    >
                      <thead className="flex mt-5 h-[50px] mx-auto  w-full  bg-[#428bca] items-center">
                        <tr>
                          {isEditMode && (
                            <th className="w-[50px] text-[#fff] border-r-[1px] h-[50px] text-center">
                              <input
                                type="checkbox"
                                checked={
                                  selectedRows.length === draggedList.length
                                }
                                onChange={handleSelectAll}
                              />
                            </th>
                          )}
                          {cmap_table?.data?.message?.length > 0 &&
                            cmap_headers?.data?.message
                              ?.filter(
                                (val: any) =>
                                  ![
                                    "Academic Year",
                                    "Subject",
                                    "Class",
                                  ].includes(val?.label)
                              )
                              ?.map((val: any) => {
                                return (
                                  <>
                                    <th
                                      className={` ${
                                        val?.label === "Period" ||
                                        val?.label === "Class" ||
                                        val?.label === "Subject" ||
                                        val?.label === "Academic Year" ||
                                        val?.label === "Plan Date" ||
                                        val?.label ===
                                          "Last Period of the Unit" ||
                                        val?.label === "Parent Note" ||
                                        val?.label === "Home Work" ||
                                        val?.label === "Class Work"
                                          ? "w-[100px]"
                                          : "min-w-[200px]"
                                      } text-[#fff] border-r-[1px] h-[50px] text-[12px]`}
                                    >
                                      {val?.label}
                                    </th>
                                  </>
                                );
                              })}
                        </tr>
                      </thead>

                      <tbody
                        ref={provided.innerRef}
                        style={{ overflowX: "scroll" }}
                        {...provided.droppableProps}
                      >
                        {draggedList?.map?.((val: any, index: number) => {
                          const powerpoint_presentation =
                            val?.powerpoint_presentation
                              ?.split(",")
                              .map((item: any) => item.trim());
                          const answer_sheet = val?.answer_sheet
                            ?.split(",")
                            .map((item: any) => item.trim());
                          const worksheet = val?.worksheet
                            ?.split(",")
                            .map((item: any) => item.trim());
                          const lesson_plan = val?.lesson_plan
                            ?.split(",")
                            .map((item: any) => item.trim());

                          return (
                            <>
                              <Draggable
                                key={index}
                                draggableId={index.toString()}
                                index={index}
                              >
                                {(provided: any) => (
                                  <tr
                                    className="flex    w-full    "
                                    ref={provided.innerRef}
                                    {...provided.draggableProps}
                                    {...provided.dragHandleProps}
                                  >
                                    {isEditMode && (
                                      <td className="w-[50px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px]">
                                        <input
                                          type="checkbox"
                                          checked={selectedRows.some(
                                            (row) => row.index === index
                                          )}
                                          onChange={() =>
                                            handleSelectRow({
                                              index,
                                              name: val.name,
                                            })
                                          }
                                        />
                                      </td>
                                    )}
                                    {/* <td className="w-[100px] border-[1px] flex items-center justify-center flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "academic_year"
                                      )
                                        ? val?.academic_year
                                        : "NOT ASSIGNED"}
                                    </td> */}
                                    {/* <td className="w-[100px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "subject"
                                      )
                                        ? val?.subject
                                        : "NOT ASSIGNED"}
                                    </td> */}
                                    <td className="w-[100px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "period"
                                      )
                                        ? val?.period
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[200px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname ===
                                          "reserved_for_portion_circular"
                                      )
                                        ? val?.reserved_for_portion_circular
                                        : "NOT ASSIGNED"}
                                    </td>
                                    {/* <td className="w-[100px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "class"
                                      )
                                        ? val?.class
                                        : "NOT ASSIGNED"}
                                    </td> */}
                                    <td className="w-[200px] border-[1px] flex flex-col items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      <div className="flex justify-center flex-col items-center my-auto gap-2">
                                        <div className="flex items-center justify-center gap-2">
                                          <span>Unit:</span>
                                          <select
                                            name=""
                                            id=""
                                            className="border-[1px] h-[30px]"
                                            value={selectedUnits[index] || ""}
                                            onChange={(e) =>
                                              handleUnitChange(e, index)
                                            }
                                          >
                                            <option>1</option>
                                            <option>2</option>
                                            <option>3</option>
                                            <option>4</option>
                                          </select>
                                        </div>
                                        <button
                                          className="bg-[#428bca] p-2 text-white rounded-[5px] mt-2"
                                          onClick={() => {
                                            setSelectedName(val?.name);
                                            setTimeout(() => {
                                              unitModalOpen();
                                            }, 2000);
                                          }}
                                        >
                                          Move
                                        </button>
                                      </div>
                                    </td>
                                    <td className="w-[100px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "plan_date"
                                      )
                                        ? val?.plan_date
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[100px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname ===
                                          "last_period_of_the_unit"
                                      )
                                        ? val?.last_period_of_the_unit
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[200px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "textbook"
                                      )
                                        ? val?.textbook
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[200px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "chapter"
                                      )
                                        ? val?.chapter
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[200px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "broadcast"
                                      )
                                        ? val?.broadcast
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[100px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "parent_note"
                                      )
                                        ? val?.parent_note
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[100px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "home_work"
                                      )
                                        ? val?.home_work
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[100px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "class_work"
                                      )
                                        ? val?.class_work
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[200px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname ===
                                          "material_required"
                                      )
                                        ? val?.material_required
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td
                                      className={`w-[200px] border-[1px] flex flex-col border-[#aaa] text-center text-[#8b91a0] text-[12px]  `}
                                    >
                                      <span
                                        className="text-[#8b91a0] p-0 font-semibold text-[35px]   cursor-pointer"
                                        onClick={() => {
                                          const ids =
                                            cmap_headers?.data?.message?.find(
                                              (items: any) =>
                                                items?.fieldname ===
                                                "answer_sheet"
                                            )?.label;
                                          setSelectedIDS(ids);
                                      
                                          setRowField(val);
                                          setSelectedName(val?.name);
                                          setTimeout(() => {
                                            insertModalOpen();
                                          }, 2000);
                                        }}
                                      >
                                        +
                                      </span>
                                      <div className="flex flex-col  items-center justify-start overflow-hidden 	">
                                        {cmap_headers?.data?.message?.find(
                                          (items: any) =>
                                            items?.fieldname === "answer_sheet"
                                        )
                                          ? answer_sheet?.map((i: any) => {
                                              return (
                                                <>
                                                  <div className="flex items-center justify-center gap-2">
                                                    <span className="text-[13px]">
                                                      {i}
                                                    </span>
                                                    <IconPencil
                                                      width={20}
                                                      onClick={() => {
                                                        const ids =
                                                          cmap_headers?.data?.message?.find(
                                                            (items: any) =>
                                                              items?.fieldname ===
                                                              "answer_sheet"
                                                          )?.label;
                                                        setSelectedItem(ids);
                                                        setSelectedIDS(ids);
                                                        setSelectedName(
                                                          val?.name
                                                        );
                                                        fetchData(val?.name);
                                                        setTimeout(() => {
                                                          openModal(ids);
                                                        }, 2000);
                                                      }}
                                                    />
                                                    <IconTrash
                                                      width={20}
                                                      onClick={() => {
                                                        const ids =
                                                          cmap_headers?.data?.message?.find(
                                                            (items: any) =>
                                                              items?.fieldname ===
                                                              "answer_sheet"
                                                          )?.label;
                                                        setSelectedItem(ids);
                                                        setSelectedName(
                                                          val?.name
                                                        );
                                                        fetchData(val?.name);
                                                        setTimeout(() => {
                                                          deleteModalOpen();
                                                        }, 2000);
                                                      }}
                                                    />
                                                  </div>
                                                </>
                                              );
                                            })
                                          : "NOT ASSIGNED"}
                                      </div>
                                    </td>
                                    <td className="w-[200px] border-[1px] border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname ===
                                          "answer_sheet_for_practice_tests"
                                      )
                                        ? val?.answer_sheet_for_practice_tests
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[200px] border-[1px] border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname ===
                                          "competitive_exams"
                                      )
                                        ? val?.competitive_exams
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[200px] border-[1px] border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "laminated_sheet"
                                      )
                                        ? val?.laminated_sheet
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[200px] border-[1px] border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      <div className="flex flex-col gap-2">
                                        <span
                                          className="text-[#8b91a0] font-semibold text-[35px] p-0 cursor-pointer"
                                          onClick={() => {
                                            const ids =
                                              cmap_headers?.data?.message?.find(
                                                (items: any) =>
                                                  items?.fieldname ===
                                                  "lesson_plan"
                                              )?.label;
                                            setSelectedIDS(ids);
                                           
                                            setRowField(val);
                                            setSelectedName(val?.name);
                                            setTimeout(() => {
                                              insertModalOpen();
                                            }, 2000);
                                          }}
                                        >
                                          +
                                        </span>
                                        {cmap_headers?.data?.message?.find(
                                          (items: any) =>
                                            items?.fieldname === "lesson_plan"
                                        )
                                          ? lesson_plan?.map((i: any) => {
                                              return (
                                                <>
                                                  <div className="flex items-center justify-center gap-2">
                                                    <span className="text-[13px]">
                                                      {i}
                                                    </span>
                                                    <IconPencil
                                                      width={20}
                                                      onClick={() => {
                                                        const ids =
                                                          cmap_headers?.data?.message?.find(
                                                            (items: any) =>
                                                              items?.fieldname ===
                                                              "lesson_plan"
                                                          )?.label;
                                                        setSelectedItem(ids);
                                                        setSelectedIDS(ids);
                                                        setSelectedName(
                                                          val?.name
                                                        );
                                                        fetchData(val?.name);
                                                        setTimeout(() => {
                                                          openModal(ids);
                                                        }, 2000);
                                                      }}
                                                    />
                                                    <IconTrash
                                                      width={20}
                                                      onClick={() => {
                                                        const ids =
                                                          cmap_headers?.data?.message?.find(
                                                            (items: any) =>
                                                              items?.fieldname ===
                                                              "lesson_plan"
                                                          )?.label;
                                                        setSelectedItem(ids);
                                                        setSelectedName(
                                                          val?.name
                                                        );
                                                        fetchData(val?.name);
                                                        setTimeout(() => {
                                                          deleteModalOpen();
                                                        }, 2000);
                                                      }}
                                                    />
                                                  </div>
                                                </>
                                              );
                                            })
                                          : "NOT ASSIGNED"}
                                      </div>
                                    </td>
                                    <td
                                      className={`w-[200px] border-[1px] border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2    `}
                                    >
                                      <span
                                        className="text-[#8b91a0] font-semibold text-[35px] p-0 cursor-pointer"
                                        onClick={() => {
                                          const ids =
                                            cmap_headers?.data?.message?.find(
                                              (items: any) =>
                                                items?.fieldname ===
                                                "powerpoint_presentation"
                                            )?.label;
                                          setSelectedIDS(ids);
                              
                                          setRowField(val);
                                          setSelectedName(val?.name);
                                          setTimeout(() => {
                                            insertModalOpen();
                                          }, 2000);
                                        }}
                                      >
                                        +
                                      </span>
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname ===
                                          "powerpoint_presentation"
                                      )
                                        ? powerpoint_presentation?.map(
                                            (i: any) => {
                                              return (
                                                <>
                                                  <div className="flex items-center justify-center gap-2">
                                                    <span className="text-[13px]">
                                                      {i}
                                                    </span>
                                                    <IconPencil
                                                      width={20}
                                                      onClick={() => {
                                                        const ids =
                                                          cmap_headers?.data?.message?.find(
                                                            (items: any) =>
                                                              items?.fieldname ===
                                                              "powerpoint_presentation"
                                                          )?.label;
                                                        setSelectedItem(ids);
                                                        setSelectedIDS(ids);
                                                        setSelectedName(
                                                          val?.name
                                                        );
                                                        fetchData(val?.name);
                                                        setTimeout(() => {
                                                          openModal(ids);
                                                        }, 2000);
                                                      }}
                                                    />
                                                    <IconTrash
                                                      width={20}
                                                      onClick={() => {
                                                        const ids =
                                                          cmap_headers?.data?.message?.find(
                                                            (items: any) =>
                                                              items?.fieldname ===
                                                              "powerpoint_presentation"
                                                          )?.label;
                                                        setSelectedName(
                                                          val?.name
                                                        );
                                                        setSelectedItem(ids);
                                                        fetchData(val?.name);
                                                        setTimeout(() => {
                                                          deleteModalOpen();
                                                        }, 2000);
                                                      }}
                                                    />
                                                  </div>
                                                </>
                                              );
                                            }
                                          )
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[200px] border-[1px] border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "practice_test"
                                      )
                                        ? val?.practice_test
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[200px] border-[1px] border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "revision_sheet"
                                      )
                                        ? val?.revision_sheet
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[200px] border-[1px] border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "unit_test"
                                      )
                                        ? val?.unit_test
                                        : "NOT ASSIGNED"}
                                    </td>
                                    <td className="w-[200px] border-[1px] border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      {cmap_headers?.data?.message?.find(
                                        (items: any) =>
                                          items?.fieldname === "walmiki_quiz"
                                      )
                                        ? val?.unit_test
                                        : "NOT ASSIGNED"}
                                    </td>

                                    <td className="w-[200px] border-[1px] border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                      <div className="flex flex-col gap-2">
                                        <span
                                          className="text-[#8b91a0] font-semibold text-[35px] p-0 cursor-pointer"
                                          onClick={() => {
                                            const ids =
                                              cmap_headers?.data?.message?.find(
                                                (items: any) =>
                                                  items?.fieldname ===
                                                  "worksheet"
                                              )?.label;
                                            setSelectedIDS(ids);
                                
                                            setRowField(val);
                                            setSelectedName(val?.name);
                                            setTimeout(() => {
                                              insertModalOpen();
                                            }, 2000);
                                          }}
                                        >
                                          +
                                        </span>
                                        {cmap_headers?.data?.message?.find(
                                          (items: any) =>
                                            items?.fieldname === "worksheet"
                                        ) &&
                                          worksheet?.map((i: any) => {
                                            return (
                                              <>
                                                <div className="flex items-center justify-center gap-2">
                                                  <span className="text-[13px]">
                                                    {i}
                                                  </span>
                                                  <IconPencil
                                                    width={20}
                                                    onClick={() => {
                                                      const ids =
                                                        cmap_headers?.data?.message?.find(
                                                          (items: any) =>
                                                            items?.fieldname ===
                                                            "worksheet"
                                                        )?.label;
                                                      setSelectedItem(ids);
                                                      setSelectedIDS(ids);
                                                      setSelectedName(
                                                        val?.name
                                                      );
                                                      fetchData(val?.name);
                                                      setTimeout(() => {
                                                        openModal(ids);
                                                      }, 2000);
                                                    }}
                                                  />
                                                  <IconTrash
                                                    width={20}
                                                    onClick={() => {
                                                      const ids =
                                                        cmap_headers?.data?.message?.find(
                                                          (items: any) =>
                                                            items?.fieldname ===
                                                            "worksheet"
                                                        )?.label;
                                                      setSelectedName(
                                                        val?.name
                                                      );
                                                      setSelectedItem(ids);
                                                      fetchData(val?.name);
                                                      setTimeout(() => {
                                                        deleteModalOpen();
                                                      }, 2000);
                                                    }}
                                                  />
                                                </div>
                                              </>
                                            );
                                          })}
                                      </div>
                                    </td>
                                  </tr>
                                )}
                              </Draggable>
                            </>
                          );
                        })}
                        {provided.placeholder}
                      </tbody>
                    </table>
                  )}
                </StrictModeDroppable>
              </DragDropContext>
            </section>
          )}

        {isButtonClicked &&
          !isLoading &&
          cmap_table?.data?.message?.length === 0 && (
            <div className="text-red-500 text-center">
              CMAP not created or uploaded for selected filter
            </div>
          )}
      </div>
    </>
  );
};
