import React, { useMemo } from "react";
import clsx from "clsx";
import { useFrappeGetDocList } from "frappe-react-sdk";

interface SingleSelectProps {
  label?: string;
  options?: {
    value: string;
    label?: string;
  }[];
  onChange?: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  value?: string;
  hasEmptyOption?: boolean;
  isChild?: boolean;
  required?: boolean;
  docType?: string;
}

const SingleSelect = (props: SingleSelectProps) => {
  const {
    options,
    label,
    onChange,
    value,
    hasEmptyOption,
    isChild,
    required,
    docType = "",
  } = props;
  const { data, isLoading } = useFrappeGetDocList(
    docType,
    {
      limit: 0,
    },
    !docType ? null : undefined
  );
  const parsedData = useMemo(() => {
    if (data && !isLoading) {
      return data.map((el) => {
        return { label: el.name, value: el.name };
      });
    }
    return [];
  }, [data]);

  if (isLoading) {
    return;
  }

  return (
    <div className="frappe-control input-max-width" data-fieldtype="Select">
      <div
        className="form-group"
        style={{
          marginBottom: isChild ? 0 : undefined,
        }}
      >
        {label && (
          <div className="clearfix">
            <label
              className={clsx("control-label", required && "reqd")}
              style={{ paddingRight: 0 }}
            >
              {label}
            </label>
            <span className="help"></span>
          </div>
        )}
        <div className="control-input-wrapper">
          <div className="control-input flex align-center">
            <select
              autoComplete="off"
              className="input-with-feedback form-control ellipsis bold"
              onChange={onChange}
              value={value}
            >
              {hasEmptyOption && <option value=""></option>}
              {(options || parsedData)?.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {!isChild && (
              <div className="select-icon">
                <svg className="icon  icon-sm" aria-hidden="true">
                  <use className="" href="#icon-select"></use>
                </svg>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SingleSelect;
