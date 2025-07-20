import React, { useState } from 'react';
import clsx from 'clsx';

interface FileSelectProps {
  label?: string;
  options: {
    value: string;
    label?: string;
  }[];
  onChange: (values: React.ChangeEvent<HTMLInputElement>) => void;
  required?: boolean;
}

const FileSelect = (props: FileSelectProps) => {
  const [value, setValue] = useState('');
  const { label, onChange, required } = props;
  return (
    <div className="frappe-control input-max-width" data-fieldname="select_csv">
      <div className="form-group">
        {label && (
          <div className="clearfix">
            <label
              className={clsx('control-label', required && 'reqd')}
              data-style-str="padding-right: 0px;"
            >
              {label}
            </label>
          </div>
        )}
        <div className="control-input-wrapper">
          <div className="control-input">
            {!value && (
              <label
                className="btn btn-default btn-sm btn-attach bold"
                htmlFor="walsh-admin-csv-input"
              >
                Attach
              </label>
            )}
            <input
              style={{
                display: 'none',
              }}
              value={value ? undefined : ''}
              accept=".csv"
              onChange={(e) => {
                onChange(e);
                setValue(e.target.value);
              }}
              type="file"
              id="walsh-admin-csv-input"
            />
          </div>
          {value && (
            <button
              className="btn btn-default btn-sm btn-attach bold"
              onClick={() => {
                setValue('');
              }}
            >
              Clear
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileSelect;
