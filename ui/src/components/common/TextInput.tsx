import clsx from 'clsx';
import React from 'react';

interface TextInputProps {
  label: string;
  value: string;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  required?: boolean;
}

const TextInput = (props: TextInputProps) => {
  const { label, value, onChange, required } = props;
  return (
    <div className="frappe-control input-max-width">
      <div className="form-group">
        <div className="clearfix">
          <label className={clsx('control-label', required && 'reqd')}>
            {label}
          </label>
        </div>
        <div className="control-input-wrapper">
          <div className="control-input">
            <input
              type="text"
              className="input-with-feedback form-control bold"
              onChange={onChange}
              value={value}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default TextInput;
