// import { PHONE_REGEX } from "../../constants";

export default {
  initialValues: {
    mobile_number: "",
    otp: "",
  },
  // validateInputOnChange: true,
  validateInputOnBlur: true,
  // validate: {
  //   mobile_number: (value: string) => {
  //     console.log(
  //       value,
  //       "hi",
  //       PHONE_REGEX.test(String(value)) ? null : "Invalid Phone Number"
  //     );

  //     return (PHONE_REGEX.test(String(value)) ? null : "Invalid Phone Number");
  //   },
  // },
};
