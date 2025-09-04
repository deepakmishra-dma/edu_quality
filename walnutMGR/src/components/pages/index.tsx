import { useEffect, useState } from "react";
import Select from "react-select";
import Modal from "react-modal";
import { IconCalendar } from "@tabler/icons-react";

import {
  useCLassName,
  useCLassList,
  useCmapHeaders,
  useCmapItemGroupID,
  useCMAPTableFields,
} from "../../Query/useCLassList";
import { SingleValue } from "react-select";

interface OptionType {
  value: string;
  label: string;
}
import { Table } from "./Table";
const customStyles = {
  content: {
    top: "50%",
    left: "50%",
    right: "auto",
    bottom: "auto",
    marginRight: "-50%",
    transform: "translate(-50%, -50%)",
  },
};

import * as XLSX from "xlsx";

interface SelectedRow {
  name: string;
  index: number;
}
interface ItemDetail {
  name: string;
  owner: string;
  creation: string;
  modified: string;
  modified_by: string;
  docstatus: number;
  idx: number;
  item_group: string;
  textbook: string;
  chapter: string;
  item: string;
  parent: string;
  parentfield: string;
  parenttype: string;
  doctype: string;
}
interface DraggedItem {
  name: string;
  period: string;
}

export const Index = () => {
  const { data: cmap_headers } = useCmapHeaders();
  const [draggedList, setDraggedList] = useState<DraggedItem[]>([]);
  const [formDate, setFormDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [itemDetails, setItemDetails] = useState<ItemDetail[]>([]);
  const [deletedModal, setDeletedModal] = useState(false);
  const [isEditMode, setIsEditMode] = useState<boolean>(false);
  const [modalIsOpen, setIsOpen] = useState(false);
  const [selectedName, setSelectedName] = useState("");
  const [selectedItem, setSelectedItem] = useState("");
  const [insertModal, setInsertModal] = useState(false);
  const [isButtonClicked, setIsButtonClicked] = useState(true);
  const [selectProductCode, setSelectProductCode] = useState("");
  const [unitModal, setUnitModal] = useState(false);
  const [showButtons, setShowButtons] = useState(false);
  const [selectedRows, setSelectedRows] = useState<SelectedRow[]>([]);
  const [selectedOption, setSelectedOption] =
    useState<SingleValue<OptionType>>(null);
  const [cmapNames, setCmapNames] = useState({
    cmap_name_one: "",
    cmap_name_two: "",
    cmap_first_period: "",
    cmap_second_period: "",
  });

  const [selectedClass, setSelectedClass] = useState("");
  const [selectedIDS, setSelectedIDS] = useState("");

  const { data: cmap_item_group_ids } = useCmapItemGroupID(selectedIDS);
  const [selectedYear, setSelectedYear] = useState("");
  const { data: cmap_table, mutateAsync, isLoading } = useCMAPTableFields();
  const [selectedUnits, setSelectedUnits] = useState<{ [key: string]: string }>(
    {}
  );
  const [selectedvalues, setSelectedValues] = useState({
    subjects: "",
    unit: "",
  });

  const { data: classes } = useCLassList();
  const { data: class_name } = useCLassName(selectedClass);
  const exportToExcel = () => {
    const ws = XLSX.utils.json_to_sheet(cmap_table?.data?.message);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Table Data");
    XLSX.writeFile(wb, "table_data.xlsx");
  };
  const formatDate = (dateString: any) => {
    const [year, month, day] = dateString.split("-");
    return `${day}-${month}-${year}`;
  };

  const handleShowTable = async () => {
    if (!selectedYear) {
      alert("Please select a year.");
      return;
    }
    if (!selectedvalues.subjects) {
      alert("Please select a subject.");
      return;
    }
    if (!selectedvalues.unit) {
      alert("Please select a unit.");
      return;
    }
    if (!selectedClass) {
      alert("Please select a class.");
      return;
    }

    setIsButtonClicked(true);
    try {
      await mutateAsync({
        academic_year: selectedYear,
        program: selectedClass,
        subject: selectedvalues.subjects,
        unit: `${selectedvalues.unit}`,
        from_date: formatDate(formDate),
        end_date: formatDate(toDate),
      });
    } catch (error) {
      console.error("Error marking as archived:", error);
    }
  };

  const id =
    itemDetails?.find(
      (i: any) => i?.parent === selectedName && i?.item_group === selectedItem
    )?.name ?? "";

  const selectedDeleteCode =
    itemDetails?.find(
      (i: any) => i?.parent === selectedName && i?.item_group === selectedItem
    )?.item ?? "";

  const deleteCode = async () => {
    try {
      const payload = {
        item:
          itemDetails?.find(
            (i: any) =>
              i?.parent === selectedName && i?.item_group === selectedItem
          )?.item ?? "",
      };

      const response = await fetch(`/api/resource/Item%20Detail/${id}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      if (response.ok) {
        const result = await response.json();
        console.log("Update response:", result);
        alert("Product Code Deleteded Successfully");
        deleteModalClose();
        handleShowTable();
      } else {
        alert(` Product Code Not Deleted ${selectedOption?.value}`);
      }
    } catch (error) {
      console.error("Error updating the product:", error);
    }
  };

  const updateProduct = async () => {
    const payload = {
      item: selectedOption?.value,
    };
    try {
      const response = await fetch(`/api/resource/Item%20Detail/${id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      if (response.ok) {
        const result = await response.json();
        console.log("Update response:", result);
        alert("Product Code Updated Successfully");
        setSelectedOption((prevState) => ({
          ...prevState,
          label: "",
          value: "",
        }));
        closeModal();
        handleShowTable();
      } else {
        alert(`selected Product Code Not Available ${selectedOption?.value}`);
        setSelectedOption((prevState) => ({
          ...prevState,
          label: "",
          value: "",
        }));
      }
    } catch (error) {
      console.error("Error updating the product:", error);
    }
  };

  function openModal(ids: string) {
    if (
      cmap_headers?.data?.message?.filter((items: any) => items?.label === ids)
    ) {
      setIsOpen(true);
    }
  }
  function deleteModalOpen() {
    setDeletedModal(true);
  }
  function deleteModalClose() {
    setDeletedModal(false);
  }

  function closeModal() {
    setSelectedIDS("");
    setIsOpen(false);
  }
  const handleEdit = () => {
    setIsEditMode(true);
  };
  useEffect(() => {
    if (cmap_table?.data?.message) {
      setDraggedList(cmap_table?.data?.message);
    }
  }, [setDraggedList, draggedList, cmap_table]);

  let printBtn = `https://uat.walnutedu.in/app/query-report/CMAP%20Print?academic_year=${selectedYear}&class=${selectedClass}&subject=%5B"${selectedvalues.subjects}"%5D&unit=%5B%22${selectedvalues.unit}%22%5D`;
  const handleChange = (selectedOption: any) => {
    setSelectedOption(selectedOption);
  };
  const options = cmap_item_group_ids?.data?.data?.map((item: any) => ({
    value: item.name,
    label: item.name,
  }));

  function insertModalClose() {
    setSelectedIDS("");
    setInsertModal(false);
  }
  const insertFunc = async () => {
    const payload = {
      data: {
        item: selectedOption?.value,
        item_group: selectedIDS,
        doctype: "Item Detail",
        parenttype: "CMAP",
        parent: selectedName,
        parentfield: "products",
        // chapter: rowField?.chapter,
        // textbook: rowField?.textbook,
        // subject: rowField?.subject,
      },
    };
    try {
      const response = await fetch(`/api/resource/Item%20Detail`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      if (response.ok) {
        const result = await response.json();
        console.log("Update response:", result);
        alert(`Added Product Code ${selectedOption?.value} Successfully`);
        setSelectProductCode("");
        setSelectedOption((prevState: any) => ({
          ...prevState,
          label: "",
          value: "",
        }));
        insertModalClose();
        handleShowTable();
      } else {
        alert(`selected Unit Not Available ${selectedOption?.value}`);
        setSelectProductCode("");
      }
    } catch (error) {
      console.error("Error updating the product:", error);
    }
  };
  const unitModalClose = () => {
    setUnitModal(false);
  };
  const handleUnitChanges = async () => {
    const payload = {
      unit: selectedUnits[0],
    };
    try {
      const response = await fetch(`/api/resource/CMAP/${selectedName}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      if (response.ok) {
        const result = await response.json();
        console.log("Update response:", result);
        alert("Unit Updated Successfully");
        setSelectProductCode("");
        setSelectedUnits({});
        unitModalClose();
        handleShowTable();
      } else {
        alert(`selected Unit Not Available ${selectedUnits}`);
        setSelectProductCode("");
        setSelectedUnits({});
      }
    } catch (error) {
      console.error("Error updating the product:", error);
    }
  };
  async function handleSave() {
    try {
      if (cmapNames.cmap_name_one) {
        const response = await fetch(
          `/api/resource/CMAP/${cmapNames.cmap_name_one}`,
          {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ period: cmapNames.cmap_second_period }),
          }
        );
        if (response.ok) {
          const result = await response.json();
          console.log("Update response:", result);
          alert("Period Reordered Successfully");
          handleShowTable();
          setCmapNames((prevState) => ({
            ...prevState,
            cmap_first_period: "",
            cmap_second_period: "",
            cmap_name_one: "",
            cmap_name_two: "",
          }));
          setShowButtons(false);
        }
      }

      if (cmapNames.cmap_name_two) {
        const response = await fetch(
          `/api/resource/CMAP/${cmapNames.cmap_name_two}`,
          {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ period: cmapNames.cmap_first_period }),
          }
        );
        if (response.ok) {
          const result = await response.json();
          console.log("Update response:", result);

          handleShowTable();
          setCmapNames((prevState) => ({
            ...prevState,
            cmap_first_period: "",
            cmap_second_period: "",
            cmap_name_one: "",
            cmap_name_two: "",
          }));
        }
        setShowButtons(false);
      }
    } catch (error) {
      console.error("Error:", error);
    }
  }
  function handleCancel() {
    setDraggedList(cmap_table?.data?.message);
    setShowButtons(false);
    handleShowTable();
  }

  const handleEditCancel = () => {
    setIsEditMode(false);

    setSelectedRows([]);
  };
  const handleEditSave = async () => {
    const selectedRowNames = selectedRows?.map((i: any) => i?.name);

    try {
      for (const name of selectedRowNames) {
        const response = await fetch(`/api/resource/CMAP/${name}`, {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (response.ok) {
          const result = await response.json();
          console.log(`Record ${name} deleted successfully:`, result);
        } else {
          console.error(`Failed to delete record ${name}`);
        }
      }
      alert("Selected records deleted successfully");
      setSelectedRows([]);

      handleShowTable();
    } catch (error) {
      console.error("Error:", error);
    }
  };
  return (
    <section className="mt-10 p-5">
      <div className="p-3 mx-auto pt-[2rem]  bg-[#fff] overflow-hidden rounded-[5px] shadow-lg shadow-gray-900">
        <div className="flex items-center justify-between ml-5">
          <span className="font-bold text-[20px]  ">C-Map Creation</span>
          {/* <div className='border-[1px] mt-[1rem]'></div> */}
          {/* <i className="fa fa-calendar"></i> */}
          <div className="flex gap-2 items-center">
            <IconCalendar stroke={2} />
            <span className="font-bold text-[20px] ">13 May 2024</span>
          </div>
        </div>
        <hr className="bg-[#eee] w-[63%] text-center mx-auto" />
        <div className="flex items-center space-x-5 justify-center mt-6">
          <span className="text-gray-500">Academic Year:</span>
          <select
            className="w-[140px] p-1 border-[1px]"
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
          >
            <option value="">Select Year</option>
            <option value="2023-2024">2023-2024</option>
            <option value="2024-2025">2024-2025</option>
          </select>
        </div>

        <span className="ml-5 font-bold">Show CMAP Filter -</span>
        <div className="lg:flex lg:flex-row lg:items-center lg:justify-center lg:gap-[5rem] sm:flex sm:flex-col sm:items-center sm:gap-6 mx-auto mt-6">
          <div className=" space-x-5">
            <span className="text-gray-500">class:</span>
            <select
              className="w-[140px] p-1 border-[1px]"
              value={selectedClass}
              onChange={(e) => setSelectedClass(e.target.value)}
            >
              <option value="">select class</option>

              {classes?.data?.data
                ?.sort((a: any, b: any) => {
                  const isANumeric = !isNaN(a.name);
                  const isBNumeric = !isNaN(b.name);

                  if (!isANumeric && isBNumeric) {
                    return -1;
                  } else if (isANumeric && !isBNumeric) {
                    return 1;
                  } else if (!isANumeric && !isBNumeric) {
                    return a.name.localeCompare(b.name);
                  } else {
                    return parseInt(a.name, 10) - parseInt(b.name, 10);
                  }
                })
                .map((cls: any) => {
                  return (
                    <option key={cls?.name} value={cls?.name}>
                      {cls?.name}
                    </option>
                  );
                })}
            </select>
          </div>
          <div className="flex space-x-5">
            <span className="text-gray-500">Subject:</span>
            <div className="w-[200px] p-2 h-[150px] bg-[#fff] overflow-x-auto border-[1px] overflow-y-scroll">
              <span>Select Subject</span>
              <ul>
                {class_name?.data?.data?.subject?.map?.((sub: any) => (
                  <li
                    key={sub?.subject}
                    className={
                      selectedvalues.subjects === sub?.subject
                        ? "bg-[#428bca] text-white cursor-pointer"
                        : "cursor-pointer"
                    }
                    style={{ listStyle: "none" }}
                    onClick={() => {
                      setSelectedValues((prevState) => ({
                        ...prevState,
                        subjects: sub?.subject,
                      }));
                    }}
                  >
                    {sub?.subject}
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div className="flex space-x-5">
            <span className="text-gray-500">Unit:</span>
            <div className="w-[200px] p-2 h-[150px] bg-[#fff] border-[1px] overflow-y-scroll">
              <span>Select Unit</span>
              <ul>
                {[1, 2, 3, 4].map?.((sub: any) => {
                  return (
                    <>
                      <li
                        className={
                          selectedvalues.unit === sub
                            ? "bg-[#428bca] text-white cursor-pointer"
                            : "cursor-pointer"
                        }
                        style={{ listStyle: "none" }}
                        onClick={() => {
                          setSelectedValues((prevState) => ({
                            ...prevState,
                            unit: sub,
                          }));
                        }}
                      >
                        {sub}
                      </li>
                    </>
                  );
                })}
              </ul>
            </div>
          </div>
        </div>

        <div className="lg:flex lg:justify-center lg:gap-[22rem] mx-auto sm:flex sm:justify-center  mt-5 lg:items-center">
          <div className="space-x-2 mt-3">
            <span className="text-gray-500">From Date:</span>
            <input
              type="date"
              name="formDate"
              id="formDate"
              value={formDate}
              onChange={(e) => setFormDate(e.target.value)}
              className="h-[40px] p-1 border-[1px]"
            />
          </div>
          <div className="space-x-2 mt-3">
            <span className="text-gray-500"> To Date:</span>
            <input
              type="date"
              name=""
              id=""
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="h-[40px] p-1 border-[1px]"
            />
          </div>
        </div>
        <div className="flex items-center justify-center mt-4 space-x-[50px]">
          <button
            className="bg-[#428bca] p-3   py-2 text-white rounded-[5px]"
            onClick={handleShowTable}
          >
            Show
          </button>
          <button
            className="bg-[#428bca] p-3  py-2 text-white rounded-[5px]"
            onClick={exportToExcel}
          >
            Export
          </button>
          <div className="flex">
            <a
              href="https://uat.walnutedu.in/app/data-import?reference_doctype=CMAP"
              target="_blank"
              className="bg-[#428bca] p-3   py-2 text-white rounded-[5px]"
            >
              Import
            </a>
            <a href="#" className="flex items-end text-[#88bbc8] underline">
              Create CMAP Sample CSV
            </a>
          </div>
        </div>

        <Table
          isButtonClicked={isButtonClicked}
          isLoading={isLoading}
          setUnitModal={setUnitModal}
          cmap_table={cmap_table}
          setSelectedIDS={setSelectedIDS}
          setSelectedName={setSelectedName}
          setSelectedItem={setSelectedItem}
          selectedUnits={selectedUnits}
          setSelectedUnits={setSelectedUnits}
          openModal={openModal}
          cmap_headers={cmap_headers}
          setInsertModal={setInsertModal}
          setItemDetails={setItemDetails}
          deleteModalOpen={deleteModalOpen}
          setCmapNames={setCmapNames}
          isEditMode={isEditMode}
          setShowButtons={setShowButtons}
        />

        <Modal
          isOpen={modalIsOpen}
          onRequestClose={closeModal}
          style={customStyles}
          contentLabel="Example Modal"
        >
          <div className="flex justify-between w-[500px] p-0 m-0 ">
            <h1 className="text-[#666] font-bold text-[20px] mx-auto">
              Product Details
            </h1>
            <button
              className="text-red-700 right-0"
              onClick={() => {
                setSelectedOption(null);
                closeModal();
              }}
            >
              X
            </button>
          </div>
          <div className="border-[1px] w-full mt-2"></div>

          <div className="relative">
            <Select
              id="productCode"
              value={selectedOption}
              onChange={handleChange}
              options={options}
              placeholder="Select Product Code"
              className="w-full p-1 border-[1px]"
              styles={{
                control: (provided) => ({
                  ...provided,
                  minHeight: "40px",
                }),
                menu: (provided) => ({
                  ...provided,
                  maxHeight: "100px",
                  overflowY: "auto",
                }),
              }}
            />
          </div>
          <input
            type="hidden"
            name="selectedProductCode"
            value={selectProductCode}
          />
          <button
            className="bg-[#428bca] p-3 text-center py-2 text-white rounded-[5px] relative mt-5 left-[13rem]"
            onClick={updateProduct}
          >
            Update
          </button>
        </Modal>
        <Modal
          isOpen={deletedModal}
          onRequestClose={deleteModalClose}
          style={customStyles}
          contentLabel="Example Modal"
        >
          <div className="flex justify-end w-[500px] p-0 m-0">
            <button className="text-red-700 right-0" onClick={deleteModalClose}>
              X
            </button>
          </div>
          <div className="border-[1px] w-full mt-2"></div>

          <h1>
            Are you sure you want to delete the Product Code{" "}
            {selectedDeleteCode}
          </h1>
          <button
            className="bg-[#428bca] p-3 text-center py-2 text-white rounded-[5px] relative mt-5 left-[13rem]"
            onClick={deleteCode}
          >
            Delete
          </button>
        </Modal>
        <Modal
          isOpen={insertModal}
          onRequestClose={insertModalClose}
          style={customStyles}
          contentLabel="Example Modal"
        >
          <div className="flex justify-between w-[500px] p-0 m-0">
            <h1 className="text-[#666] font-bold text-[20px] mx-auto">
              Product Details
            </h1>
            <button
              className="text-red-700 right-0"
              onClick={() => {
                setSelectedOption(null);
                insertModalClose();
              }}
            >
              X
            </button>
          </div>
          <div className="border-[1px] w-full mt-2"></div>
          <div className="relative">
            <Select
              id="productCode"
              value={selectedOption}
              onChange={handleChange}
              options={options}
              placeholder="Select Product Code"
              className="w-full p-1 border-[1px]"
              styles={{
                control: (provided) => ({
                  ...provided,
                  minHeight: "40px",
                }),
                menu: (provided) => ({
                  ...provided,
                  maxHeight: "100px",
                  overflowY: "auto",
                }),
              }}
            />
          </div>
          <input
            type="hidden"
            name="selectedProductCode"
            value={selectProductCode}
          />
          <button
            className="bg-[#428bca] p-3 text-center py-2 text-white rounded-[5px] relative mt-5 left-[13rem]"
            onClick={insertFunc}
          >
            Insert
          </button>
        </Modal>
        <Modal
          isOpen={unitModal}
          onRequestClose={unitModalClose}
          style={customStyles}
          contentLabel="Example Modal"
        >
          <div className="flex justify-between w-[500px] p-0 m-0">
            <p className="text-[#666] font-bold text-[20px] mx-auto">
              Unit Move
            </p>
            <button onClick={unitModalClose} className="text-red-700 right-0">
              X
            </button>
          </div>
          <div className="border-[1px] w-full mt-2"></div>
          <div className="flex flex-col items-center justify-center gap-5">
            <h2>Are you sure to Move the Unit {selectedUnits[0]}</h2>
            <button
              className="bg-[#428bca] p-2 text-white rounded-[5px] mt-2"
              onClick={handleUnitChanges}
            >
              Move
            </button>
          </div>
        </Modal>

        {showButtons && (
          <div className="flex justify-between mt-4">
            <button
              className="bg-[#428bca] p-3 text-white rounded-[5px]"
              onClick={handleSave}
            >
              Save
            </button>
            <button
              className="bg-red-500 p-3 text-white rounded-[5px]"
              onClick={handleCancel}
            >
              Cancel
            </button>
          </div>
        )}
        {isButtonClicked &&
          !isLoading &&
          !showButtons &&
          cmap_table?.data?.message?.length > 0 && (
            <div className="flex mt-2 flex-row items-end justify-end">
              {!isEditMode ? (
                <>
                  <a
                    href={printBtn}
                    target="_blank"
                    className="bg-[#428bca] p-3 text-white rounded-[5px] mr-5"
                  >
                    Print
                  </a>
                  <button
                    onClick={handleEdit}
                    className="bg-[#428bca] p-3 text-white rounded-[5px] "
                  >
                    Edit
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={handleEditCancel}
                    className="bg-[#d9534f] p-3 text-white rounded-[5px]"
                  >
                    Cancel
                  </button>
                  <button
                    className="bg-[#428bca] p-3 text-white rounded-[5px] ml-5"
                    onClick={handleEditSave}
                  >
                    Delete
                  </button>
                </>
              )}
            </div>
          )}
      </div>
    </section>
  );
};
