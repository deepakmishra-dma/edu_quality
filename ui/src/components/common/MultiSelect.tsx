import SingleSelect from '@/walsh-admin/components/SingleSelect';
import { useEffect, useState } from 'react';
import clsx from 'clsx';

interface MultiSelectProps {
  label?: string;
  options: {
    value: string;
    label?: string;
  }[];
  onChange: (values: string[]) => void;
  values: string[];
  maxSelection?: number;
  required?: boolean;
}

const MultiSelect = (props: MultiSelectProps) => {
  const { options, label, onChange, values, maxSelection, required } = props;
  const [selectedOptions, setSelectedOptions] = useState<typeof options>([]);
  const [remainingOptions, setRemainingOptions] = useState<typeof options>([]);

  useEffect(() => {
    setSelectedOptions(
      options.filter((option) => values.includes(option.value))
    );
  }, [options]);

  useEffect(() => {
    setRemainingOptions(
      options.filter(
        (option) =>
          !selectedOptions.find((s_option) => s_option.value === option.value)
      )
    );
  }, [options, selectedOptions]);

  useEffect(() => {
    onChange(selectedOptions.map((s) => s.value));
  }, [selectedOptions]);

  return (
    <div className="frappe-control input-max-width">
      <div className="form-group">
        {label && (
          <div className="clearfix">
            <label
              className={clsx('control-label', required && 'reqd')}
              style={{ paddingRight: 0 }}
            >
              {label}
            </label>
            <span className="help"></span>
          </div>
        )}
        <div className="control-input-wrapper">
          <div className="control-input form-control table-multiselect tw-pb-2">
            {selectedOptions?.map((option) => {
              return (
                <button
                  key={option.value}
                  className="data-pill btn tb-selected-value"
                >
                  <span className="btn-link-to-form">
                    {option.label || option.value}
                  </span>
                  <span className="btn-remove">
                    <svg
                      className="icon  icon-sm"
                      aria-hidden="true"
                      onClick={() => {
                        setSelectedOptions(
                          selectedOptions.filter(
                            (s) => s.value !== option.value
                          )
                        );
                      }}
                    >
                      <use className="" href="#icon-close"></use>
                    </svg>
                  </span>
                </button>
              );
            })}
            {(maxSelection ? selectedOptions.length < maxSelection : true) &&
              remainingOptions?.length > 0 && (
                <div className="link-field ui-front tw-relative">
                  <SingleSelect
                    options={remainingOptions}
                    onChange={(e) => {
                      const value = e.target.value;
                      const option = remainingOptions.find(
                        (val) => val.value === value
                      );
                      if (option)
                        setSelectedOptions([...selectedOptions, option]);
                    }}
                    value=""
                    hasEmptyOption
                    isChild
                  />
                </div>
              )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MultiSelect;
