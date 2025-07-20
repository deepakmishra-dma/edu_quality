import React from 'react';
import clsx from 'clsx';

interface CheckBoxProps {
  label?: string;
  onChange: (values: React.ChangeEvent<HTMLInputElement>) => void;
  checked: boolean;
  required?: boolean;
}

const CheckBox = (props: CheckBoxProps) => {
  const { label, onChange, checked, required } = props;
  return (
    <div
      className="form-group frappe-control input-max-width"
      data-fieldname="also_send_emails"
    >
      <div className="checkbox">
        <label>
          <span className="input-area">
            <input
              type="checkbox"
              className="input-with-feedback"
              data-fieldname="also_send_emails"
              onChange={onChange}
              checked={checked}
            />
          </span>
          {label && (
            <span className={clsx('label-area', required && 'reqd')}>
              {label}
            </span>
          )}
        </label>
        <p className="help-box small text-muted"></p>
      </div>
    </div>
  );
};

export default CheckBox;
