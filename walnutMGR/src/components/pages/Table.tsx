import { IconPencil, IconTrash } from "@tabler/icons-react";

import { DragDropContext, Draggable } from "react-beautiful-dnd";
import { StrictModeDroppable } from "../../StrictModeDroppable";
import { useEffect, useMemo } from "react";
const formatDate = (dateString: any) => {
  if (dateString) {
    const [year, month, day] = dateString.split("-");
    return `${day}-${month}-${year}`;
  } else {
    return "-";
  }
};
export const Table = ({
  isButtonClicked,
  draggedList,
  isLoading,
  setSelectedCodeValues,
  setSelectedCmapItem,
  setSelectedUnits,
  setRowField,
  setSelectedRows,
  setDraggedList,
  selectedUnits,
  cmap_table,
  selectedRows,
  handlePlanDate,
  setIsEditMode,
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
  const handleSelectNames = (value: string) => {
    setSelectedCodeValues(value);
  };
  const groupHash = useMemo(() => {
    if (cmap_headers?.data && cmap_headers?.data?.message) {
      const resultHash = {};
      const itemGroups = cmap_headers?.data?.message?.filter(
        (header) => header?.type == "item_group"
      );
      for (let group of itemGroups) {
        resultHash[group?.fieldname] = group?.label;
      }
      return resultHash;
    }
    return {};
  }, [cmap_headers]);
  const handleSelectAll = (e: any) => {
    const isChecked = e.target.checked;
    setIsEditMode(isChecked);
    setSelectedRows(
      e.target.checked
        ? draggedList.map((item: any, index: any) => ({
            name: item?.name,
            index,
          }))
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
    const updatedSelectedRows = selectedRows.some(
      (row: any) => row.index === index
    )
      ? selectedRows.filter((row: any) => row.index !== index)
      : [...selectedRows, { index, name }];

    setSelectedRows(updatedSelectedRows);
    setIsEditMode(updatedSelectedRows.length > 0);
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
    // setReOrderList([]);
  }, [setDraggedList, draggedList, cmap_table]);

  function handleOnDragEnd(result: any) {
    if (!result.destination) return;

    const items = draggedList;
    const [reorderedItem] = items?.splice(result.source.index, 1);
    items?.splice(result.destination.index, 0, reorderedItem);

    draggedList.forEach((el, index) => {
      el.newPeriod = index + 1;
    });
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
      {isButtonClicked && !isLoading && cmap_table?.data?.message?.length > 0 && (
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
                      {/* {isEditMode && ( */}
                      <th className="w-[50px] text-[#fff] border-r-[1px] h-[50px] text-center">
                        <input
                          type="checkbox"
                          checked={selectedRows.length === draggedList.length}
                          onChange={handleSelectAll}
                        />
                      </th>
                      {/* <th className="text-[#fff] border-r-[1px] w-[100px] h-[50px] text-[12px]">
                          Real Date
                        </th> */}
                      {/* )} */}
                      {cmap_table?.data?.message?.length > 0 &&
                        cmap_headers?.data?.message
                          ?.filter?.(
                            (val: any) =>
                              !["Academic Year", "Subject", "Class"].includes(
                                val?.label
                              )
                          )
                          ?.map?.((val: any) => {
                            return (
                              <>
                                <th
                                  className={` ${
                                    val?.label === "Period" ||
                                    val?.label === "Class" ||
                                    val?.label === "Subject" ||
                                    val?.label === "Academic Year" ||
                                    val?.label === "Last Period of the Unit" ||
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
                                {/* {isEditMode && ( */}
                                <td className="w-[50px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px]">
                                  <input
                                    type="checkbox"
                                    checked={selectedRows.some(
                                      (row: any) => row.index === index
                                    )}
                                    onChange={() => {
                                      setSelectedCmapItem(val);
                                      handleSelectRow({
                                        index,
                                        name: val.name,
                                      });
                                    }}
                                  />
                                </td>
                                {/* <td className="w-[100px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px]">
                                    {formatDate(
                                      val?.real_dates?.split?.(",")[0]
                                    )}
                                  </td> */}
                                <td className="min-w-[200px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                  {cmap_headers?.data?.message?.find(
                                    (items: any) =>
                                      items?.fieldname === "plan_date"
                                  ) ? (
                                    <input
                                      type="date"
                                      value={val?.plan_date}
                                      onChange={async (e) => {
                                        setSelectedName(val?.name);
                                        console.log(
                                          e.target.value,
                                          val?.plan_date
                                        );
                                        await handlePlanDate(
                                          e.target.value,
                                          val?.name
                                        );
                                      }}
                                    ></input>
                                  ) : (
                                    "NOT ASSIGNED"
                                  )}
                                </td>
                                <td className="w-[100px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                  {cmap_headers?.data?.message?.find(
                                    (items: any) =>
                                      items?.fieldname === "period"
                                  ) ? (
                                    <>
                                      <span
                                        className={
                                          val?.newPeriod
                                            ? "line-through text-red-500 font-bold"
                                            : ""
                                        }
                                      >
                                        {val?.period}
                                      </span>
                                      &nbsp;&nbsp;&nbsp;
                                      {val?.newPeriod ? (
                                        <span className="text-green-500 font-bold">
                                          {val?.newPeriod}{" "}
                                        </span>
                                      ) : null}
                                    </>
                                  ) : (
                                    "NOT ASSIGNED"
                                  )}
                                </td>
                                {/* <td className="w-[200px] border-[1px] flex items-center justify-center border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
                                    {cmap_headers?.data?.message?.find(
                                      (items: any) =>
                                        items?.fieldname ===
                                        "reserved_for_portion_circular"
                                    )
                                      ? val?.reserved_for_portion_circular
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
                                      items?.fieldname === "material_required"
                                  )
                                    ? val?.material_required
                                    : "NOT ASSIGNED"}
                                </td>
                                {Object.keys(groupHash).map((group) => {
                                  return (
                                    <AddItemGroupCell
                                      groupName={groupHash[group]}
                                      groupFieldName={group}
                                      row={val}
                                      insertModalOpen={insertModalOpen}
                                      handleSelectNames={handleSelectNames}
                                      setSelectedIDS={setSelectedIDS}
                                      setSelectedName={setSelectedName}
                                      setRowField={setRowField}
                                      setSelectedItem={setSelectedItem}
                                      fetchData={fetchData}
                                      openModal={openModal}
                                      deleteModalOpen={deleteModalOpen}
                                    />
                                  );
                                })}
                                {/* <td
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
                                        ? answer_sheet?.map?.((i: any) => {
                                            return (
                                              <>
                                                <div className="flex items-center justify-center gap-2">
                                                  <span className="text-[13px]">
                                                    {i}
                                                  </span>
                                                  <IconPencil
                                                    width={20}
                                                    onClick={() => {
                                                      handleSelectNames(i);

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
                                                      if (val?.real_dates) {
                                                        alert(
                                                          "This Product Code Cannot be Delete"
                                                        );
                                                      }
                                                      if (!val?.real_dates) {
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
                                                      }
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
                                        items?.fieldname === "competitive_exams"
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
                                                      handleSelectNames(i);
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
                                                      if (val?.real_dates) {
                                                        alert(
                                                          "This Product Code Cannot be Delete"
                                                        );
                                                      }
                                                      if (!val?.real_dates) {
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
                                                      }
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
                                                      handleSelectNames(i);
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
                                                      if (val?.real_dates) {
                                                        alert(
                                                          "This Product Code Cannot be Delete"
                                                        );
                                                      }
                                                      if (!val?.real_dates) {
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
                                                      }
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
                                    <div className="flex flex-col gap-2">
                                      <span
                                        className="text-[#8b91a0] font-semibold text-[35px] p-0 cursor-pointer"
                                        onClick={() => {
                                          const ids =
                                            cmap_headers?.data?.message?.find(
                                              (items: any) =>
                                                items?.fieldname === "worksheet"
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
                                                    handleSelectNames(i);
                                                    const ids =
                                                      cmap_headers?.data?.message?.find(
                                                        (items: any) =>
                                                          items?.fieldname ===
                                                          "worksheet"
                                                      )?.label;
                                                    setSelectedItem(ids);
                                                    setSelectedIDS(ids);
                                                    setSelectedName(val?.name);
                                                    fetchData(val?.name);
                                                    setTimeout(() => {
                                                      openModal(ids);
                                                    }, 2000);
                                                  }}
                                                />
                                                <IconTrash
                                                  width={20}
                                                  onClick={() => {
                                                    if (val?.real_dates) {
                                                      alert(
                                                        "This Product Code Cannot be Delete"
                                                      );
                                                    }
                                                    if (!val?.real_dates) {
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
                                                    }
                                                  }}
                                                />
                                              </div>
                                            </>
                                          );
                                        })}
                                    </div>
                                  </td> */}
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
    </>
  );
};

function AddItemGroupCell({
  row,

  handleSelectNames,
  setSelectedIDS,
  setSelectedName,
  insertModalOpen,
  setRowField,
  setSelectedItem,
  fetchData,
  openModal,
  groupFieldName,
  groupName,
  deleteModalOpen,
}) {
  console.log(row, groupFieldName, groupName);
  const values = row?.[groupFieldName]?.split(",");

  return (
    <td className="w-[200px] border-[1px] border-[#aaa] text-center text-[#8b91a0] text-[12px] p-2   ">
      <div className="flex flex-col gap-2">
        <span
          className="text-[#8b91a0] font-semibold text-[35px] p-0 cursor-pointer"
          onClick={() => {
            setSelectedIDS(groupName);
            setRowField(row);
            setSelectedName(row?.name);
            insertModalOpen();
          }}
        >
          +
        </span>
        {values?.map((item: any) => {
          return (
            <>
              <div className="flex items-center justify-center gap-2">
                <span className="text-[13px]">{item}</span>
                <IconPencil
                  width={20}
                  onClick={async () => {
                    handleSelectNames(item);

                    setSelectedItem(groupName);
                    setSelectedIDS(groupName);
                    setSelectedName(row?.name);
                    await fetchData(row?.name);

                    openModal(groupName);
                  }}
                />
                <IconTrash
                  width={20}
                  onClick={async () => {
                    if (row?.real_dates) {
                      alert("This Product Code Cannot be Delete");
                    }
                    if (!row?.real_dates) {
                      setSelectedName(row?.name);
                      setSelectedItem(groupName);
                      await fetchData(row?.name);

                      deleteModalOpen();
                    }
                  }}
                />
              </div>
            </>
          );
        })}
      </div>
    </td>
  );
}
