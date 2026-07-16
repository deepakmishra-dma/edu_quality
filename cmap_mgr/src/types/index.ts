export interface TableProps {
  isButtonClicked: boolean;
  isLoading: boolean;
  setSelectedCmapItem: React.SetStateAction<any>;

  setDraggedList: any;
  setRowField: any;
  draggedList: any;
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
  selectedRows: any;
  setIsEditMode: any;
  setSelectedRows: any;
  setCmapNames: any;
  setSelectedCodeValues: any;
  setItemDetails: any;
  deleteModalOpen: any;
  setInsertModal: any;
}
export interface SelectedRow {
  name: string;
  index: number;
}
export interface RowFields {
  chapter: string;
  textbook: string;
}
export interface ItemDetail {
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
export interface DraggedItem {
  name: string;
  period: string;
}
export interface CmapItem {
  real_dates?: string; // Adjust the type based on your actual data structure
  // Add other properties of your CmapItem here
}

export interface OptionType {
  value: string;
  label: string;
}

export interface CMAPVariables {
  academic_year: string;
  program: string;
  subject: string;
  unit: string[];
  from_date?: string;
  end_date?: string;
}
