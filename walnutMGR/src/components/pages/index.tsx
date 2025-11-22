import { useEffect, useState } from "react";

import Modal from "react-modal";
import { IconCalendar } from "@tabler/icons-react";
import Select from "react-select";

import {
  useCLassName,
  useCLassList,
  useCmapHeaders,
  useCmapItemGroupID,
  useCMAPTableFields,
  useAcademicCurrentYear,
  useAcademicNextYear,
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
    overflowY: "hidden",
    overflow: "hidden",
    zIndex: "-10000",
  },
};

import * as XLSX from "xlsx";

interface SelectedRow {
  name: string;
  index: number;
}
interface RowFields {
  chapter: string;
  textbook: string;
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
interface CmapItem {
  real_dates?: string; // Adjust the type based on your actual data structure
  // Add other properties of your CmapItem here
}

export const Index = () => {
  const { data: cmap_headers } = useCmapHeaders();
  const [draggedList, setDraggedList] = useState<DraggedItem[]>([]);
  const [formDate, setFormDate] = useState("");
  const [isOverflowVisible, setIsOverflowVisible] = useState(false);
  const [selectedCodeValues, setSelectedCodeValues] = useState("");
  const [rowField, setRowField] = useState<RowFields>({
    chapter: "",
    textbook: "",
  });
  const [toDate, setToDate] = useState("");
  const [itemDetails, setItemDetails] = useState<ItemDetail[]>([]);
  const [deletedModal, setDeletedModal] = useState(false);
  const [isEditMode, setIsEditMode] = useState<boolean>(false);
  const [modalIsOpen, setIsOpen] = useState(false);
  const [selectedName, setSelectedName] = useState("");
  const [selectedCmapItem, setSelectedCmapItem] = useState<CmapItem>({});
  const [selectedItem, setSelectedItem] = useState("");
  const [insertModal, setInsertModal] = useState(false);
  const [isButtonClicked, setIsButtonClicked] = useState(true);
  const [selectProductCode, setSelectProductCode] = useState("");
  const [unitModal, setUnitModal] = useState(false);

  const [showButtons, setShowButtons] = useState(false);
  const [selectedRows, setSelectedRows] = useState<SelectedRow[]>([]);
  const [years, setYears] = useState<string[]>([]);
  const [selectedOption, setSelectedOption] =
    useState<SingleValue<OptionType>>(null);
  const [cmapNames, setCmapNames] = useState({
    cmap_name_one: "",
    cmap_name_two: "",
    cmap_first_period: "",
    cmap_second_period: "",
  });

  const dynamicStyles = {
    ...customStyles,
    content: {
      ...customStyles.content,
      overflow: isOverflowVisible ? "visible" : "hidden",
    },
  };
  // Data for the MultiSelect component
  const unit_data = [1, 2, 3, 4].map((unit) => ({
    value: unit.toString(),
    label: unit.toString(),
  }));
  const yearOptions = years.map((year) => ({
    value: year,
    label: year,
  }));

  const [selectedClass, setSelectedClass] = useState("");
  const [selectedIDS, setSelectedIDS] = useState("");
  const { data: current_year } = useAcademicCurrentYear();
  const { data: next_year } = useAcademicNextYear();
  const { data: cmap_item_group_ids } = useCmapItemGroupID(selectedIDS);
  const [selectedYear, setSelectedYear] = useState("");
  const { data: cmap_table, mutateAsync, isLoading } = useCMAPTableFields();
  const [selectedUnits, setSelectedUnits] = useState<{ [key: string]: string }>(
    {}
  );

  const [selectedvalues, setSelectedValues] = useState({
    subjects: "",
    unit: [],
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
    setShowButtons(false);
    try {
      await mutateAsync({
        academic_year: selectedYear,
        program: selectedClass,
        subject: selectedvalues.subjects,
        unit: selectedvalues.unit?.map((i: any) => i?.value),
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
  useEffect(() => {
    if (current_year?.data?.data || next_year?.data?.data) {
      const currentYears =
        current_year?.data?.data?.map?.((i: any) => i?.name) || [];
      const nextYears = next_year?.data?.data?.map?.((i: any) => i?.name) || [];
      const combinedYears = Array.from(
        new Set([...currentYears, ...nextYears])
      );
      setYears((prevYears) => {
        const updatedYears = Array.from(
          new Set([...prevYears, ...combinedYears])
        );
        return updatedYears?.sort();
      });
    }
  }, [current_year, next_year]);
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
        handleShowTable();
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
      const response = await fetch(
        `/api/resource/Item%20Detail/${itemCodeValue}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );
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
        handleShowTable();
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

  useEffect(() => {
    if (cmap_table?.data?.message) {
      setDraggedList(cmap_table?.data?.message);
    }
  }, [setDraggedList, draggedList, cmap_table]);
  const unitValues = selectedvalues?.unit?.map?.((i: any) => i?.value);
  let printBtn = `https://uat.walnutedu.in/app/query-report/CMAP%20Print?academic_year=${selectedYear}&class=${selectedClass}&subject=%5B"${selectedvalues.subjects}"%5D&unit=%5B%22${unitValues}%22%5D`;

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
    setRowField({ chapter: "", textbook: "" });
  }

  const handleYearChange = (selectedOption: any) => {
    setSelectedYear(selectedOption ? selectedOption.value : "");
  };

  const itemCodeValue = itemDetails?.find(
    (val: any) => val?.item === selectedCodeValues
  )?.name;

  const insertFunc = async () => {
    const chapters =
      typeof rowField?.chapter === "string" ? rowField.chapter.split(",") : [];

    const uniqueChapters = [...new Set(chapters.map((item) => item.trim()))];

    const payload = {
      data: {
        item: selectedOption?.value,
        item_group: selectedIDS,
        doctype: "Item Detail",
        parenttype: "CMAP",
        parent: selectedName,
        parentfield: "products",
        chapter: `${uniqueChapters}`,
        textbook: rowField?.textbook?.split(",")[0],
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
        handleShowTable();
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
        } else {
          // Handle API error
          alert(`Error: Periods not updated`);
          handleShowTable();
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
        } else {
          // Handle API error

          alert(`Error: Periods not updated`);
          handleShowTable();
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
    setSelectedCmapItem({ real_dates: "" });
    setSelectedRows([]);
  };

  const handleEditSave = async () => {
    if (selectedCmapItem?.real_dates) {
      alert("This Cmap Cannot Be Delete");
      setSelectedCmapItem({ real_dates: "" });
    }
    if (!selectedCmapItem?.real_dates) {
      try {
        const selectedRowNames = selectedRows?.map((i: any) => i?.name);
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
        setIsEditMode(false);
        setSelectedCmapItem({ real_dates: "" });
        handleShowTable();
      } catch (error) {
        console.error("Error:", error);
      }
    }
  };
  const handleUnitSelectChange = (selectedOptions: any) => {
    setSelectedValues((prevState) => ({
      ...prevState,
      unit: selectedOptions || [],
    }));
  };

  const handleSubjectChange = (selectedOption: any) => {
    setSelectedValues((prevState) => ({
      ...prevState,
      subjects: selectedOption.value,
    }));
  };
  const subjectOptions =
    class_name?.data?.data?.subject?.map((sub: any) => ({
      value: sub?.subject,
      label: sub?.subject,
    })) || [];

  const sortedClasses = classes?.data?.data
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
    .map((cls: any) => ({
      value: cls.name,
      label: cls.name,
    }));
  const handleClassChange = (selectedOption: any) => {
    setSelectedClass(selectedOption ? selectedOption.value : "");
  };

  return (
    <section className="mt-10 p-5">
      <div className="p-3 mx-auto pt-[2rem]  bg-[#fff] rounded-[5px] shadow-lg shadow-gray-900">
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
          <Select
            styles={{
              control: (provided) => ({
                ...provided,
                backgroundColor: "#f3f3f3",
                borderColor: "none",
                borderRadius: "8px",
                boxShadow: "none",
              }),
            }}
            options={yearOptions}
            value={yearOptions.find((option) => option.value === selectedYear)}
            onChange={handleYearChange}
            placeholder="Academic Year"
          />
        </div>

        <span className="ml-5 font-bold">Show CMAP Filter -</span>
        <div className="lg:flex lg:flex-row lg:items-center lg:justify-center lg:gap-[5rem] sm:flex sm:flex-col sm:items-center sm:gap-6 mx-auto mt-6">
          <div className=" flex space-x-5 items-center justify-center z-* visible">
            <span className="text-gray-500">Class:</span>
            <Select
              styles={{
                control: (provided) => ({
                  ...provided,
                  backgroundColor: "#f3f3f3",
                  borderColor: "none",
                  borderRadius: "8px",
                  boxShadow: "none",
                }),
              }}
              options={sortedClasses}
              value={sortedClasses?.find(
                (option: any) => option.value === selectedClass
              )}
              onChange={handleClassChange}
              placeholder="Class"
            />
          </div>
          <div className="flex space-x-5 items-center justify-center">
            <span className="text-gray-500">Subject:</span>
            <div className="w-[200px] p-2 bg-[#fff]">
              <Select
                styles={{
                  control: (provided) => ({
                    ...provided,
                    backgroundColor: "#f3f3f3",
                    borderColor: "none",
                    borderRadius: "8px",
                    boxShadow: "none",
                  }),
                }}
                options={subjectOptions}
                value={
                  subjectOptions.find(
                    (option: any) => option.value === selectedvalues.subjects
                  ) || null
                }
                onChange={handleSubjectChange}
                placeholder="Subject"
              />
            </div>
          </div>
          <div className="flex space-x-5 items-center justify-center">
            <span className="text-gray-500">Unit:</span>
            <div className="w-[200px] p-2  bg-[#fff]  ">
              <Select
                styles={{
                  control: (provided) => ({
                    ...provided,
                    backgroundColor: "#f3f3f3",
                    borderRadius: "8px",
                    borderColor: "none",
                    boxShadow: "none",
                  }),
                }}
                options={unit_data}
                isMulti
                onChange={handleUnitSelectChange}
                placeholder="Unit"
              />
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

        <div className="  mt-5  mx-auto ">
          {isButtonClicked && isLoading && (
            <div>
              <div className="flex justify-center mt-5">
                <output
                  className={"flex justify-center items-center h-12 w-12"}
                >
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
          <Table
            isButtonClicked={isButtonClicked}
            isLoading={isLoading}
            setUnitModal={setUnitModal}
            cmap_table={cmap_table}
            setRowField={setRowField}
            setSelectedIDS={setSelectedIDS}
            setSelectedName={setSelectedName}
            setSelectedItem={setSelectedItem}
            setSelectedCmapItem={setSelectedCmapItem}
            setSelectedCodeValues={setSelectedCodeValues}
            selectedUnits={selectedUnits}
            setSelectedUnits={setSelectedUnits}
            openModal={openModal}
            cmap_headers={cmap_headers}
            setInsertModal={setInsertModal}
            setItemDetails={setItemDetails}
            deleteModalOpen={deleteModalOpen}
            setCmapNames={setCmapNames}
            setIsEditMode={setIsEditMode}
            setShowButtons={setShowButtons}
            draggedList={draggedList}
            setDraggedList={setDraggedList}
            selectedRows={selectedRows}
            setSelectedRows={setSelectedRows}
          />
        </div>
        <Modal
          isOpen={modalIsOpen}
          onRequestClose={closeModal}
          style={dynamicStyles}
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
                }),
                menu: (provided) => ({
                  ...provided,
                }),
              }}
              onMenuOpen={() => setIsOverflowVisible(true)}
              onMenuClose={() => setIsOverflowVisible(false)}
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
          style={dynamicStyles}
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
                insertModalClose();
              }}
            >
              X
            </button>
          </div>
          <div className="border-[1px] w-full mt-2"></div>
          <div
            className=""
            // onClick={() => setIsOverflowVisible(!isOverflowVisible)}
          >
            <Select
              id="productCode"
              value={selectedOption}
              onChange={handleChange}
              options={options}
              placeholder="Select Product Code"
              className="w-full p-1 border-[1px] "
              styles={{
                control: (provided) => ({
                  ...provided,
                }),
                menu: (provided) => ({
                  ...provided,
                }),
              }}
              onMenuOpen={() => setIsOverflowVisible(true)}
              onMenuClose={() => setIsOverflowVisible(false)}
            />
          </div>
          <input
            type="button"
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
