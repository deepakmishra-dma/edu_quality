import React from "react";

interface ButtonProps {
  label: string;
  onClick: (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => void;
}

const Button = (props: ButtonProps) => {
  const { label, onClick } = props;
  return (
    <div className="frappe-control input-max-width">
      <div className="form-group">
        <div className="clearfix">
          <label className="control-label hide">&nbsp;</label>
        </div>
        <div className="control-input-wrapper">
          <div className="control-input">
            <button className="btn btn-xs btn-default" onClick={onClick}>
              {label}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Button;
