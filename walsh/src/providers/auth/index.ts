import {AuthBindings} from "@refinedev/core";

export const authProvider: AuthBindings = {
  login: async ({phone, otp}) => {
    console.log({
      phone,
      otp,
    })

    const myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");

    const response = await fetch("/api/method/edu_quality.public.py.walsh.verify_otp", {
      method: 'POST',
      headers: myHeaders,
      body: JSON.stringify({
        "phone_no": phone,
        "otp": otp
      }),
      redirect: 'follow'
    })
    const data = await response.json()
    const message = data?.message

    if (message.success) {
      return {
        success: true,
        redirectTo: "/",
      };
    }

    return {
      success: false,
      error: {
        name: "InvalidOtp",
        message: message.error_message,
      },
    };
  },
  logout: async () => {
    return {
      success: true,
      redirectTo: "/login",
    };
  },
  check: async () => {
    const response = await fetch("/api/method/frappe.auth.get_logged_user");
    const data = await response.json();
    return {
      authenticated: data?.message && data?.message !== "Guest",
    };
  },
  getPermissions: async () => null,
  getIdentity: async () => {
  },
  onError: async (error) => {
    console.error(error);
    return {error};
  },
};
