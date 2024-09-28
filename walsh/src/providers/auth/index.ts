import {AuthBindings} from "@refinedev/core";

export const authProvider: AuthBindings = {
  login: async ({phone, otp}) => {
    // @ts-expect-error undefined
    const pushToken = window.getPushNotificationToken?.();
    const myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");

    const response = await fetch("/api/method/edu_quality.public.py.walsh.login.verify_otp", {
      method: 'POST',
      headers: myHeaders,
      body: JSON.stringify({
        phone_no: phone,
        otp: otp,
        push_token: pushToken || undefined
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
    const myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");

    const response = await fetch("/api/method/edu_quality.public.py.walsh.login.logout", {
      method: 'POST',
      headers: myHeaders,
      body: JSON.stringify({}),
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
        name: "Logout Error",
        message: message.error_message,
      },
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
