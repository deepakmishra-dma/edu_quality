import { AuthBindings } from "@refinedev/core";

export const authProvider: AuthBindings = {
  login: async ({ phone, otp }) => {
    // @ts-expect-error undefined
    const pushToken = window.getPushNotificationToken?.();
    const myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");

    const response = await fetch(
      "/api/method/edu_quality.public.py.walsh.login.verify_otp",
      {
        method: "POST",
        headers: myHeaders,
        body: JSON.stringify({
          phone_no: phone,
          otp: otp,
          push_token: pushToken || undefined,
        }),
        redirect: "follow",
      }
    );
    const data = await response.json();
    const message = data?.message;

    if (message?.success) {
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

    // @ts-expect-error undefined
    const pushToken = window.getPushNotificationToken?.();

    const response = await fetch(
      "/api/method/edu_quality.public.py.walsh.login.logout",
      {
        method: "POST",
        headers: myHeaders,
        body: JSON.stringify({
          push_token: pushToken || undefined,
        }),
        redirect: "follow",
      }
    );
    const data = await response.json();
    const message = data?.message;
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
    const authenticated = data?.message && data?.message !== "Guest";
    if (authenticated) {
      await sendPushToken();
    }
    
    return {
      authenticated,
    };
  },
  getPermissions: async () => null,
  getIdentity: async () => {},
  onError: async (error) => {
    if (error.statusCode === 401 || error.statusCode === 403) {
      return {
        logout: true,
        redirectTo: "/walsh",
        error,
      };
    }
    return { error };
  },
};

const sendPushToken = async () => {
  // @ts-expect-error undefined
  const pushToken = window.getPushNotificationToken?.();
  if (pushToken) {
    try {
      const response = await fetch(
        "/api/method/edu_quality.public.py.walsh.login.register_push_notice",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            push_token: pushToken,
          }),
        }
      );
      const data = await response.json();
      if (data?.message?.success) {
        console.log("Push token sent successfully");
      } else {
        console.error("Failed to send push token:", data?.message?.error_message);
      }
    } catch (error) {
      console.error("Error sending push token:", error);
    }
  }
};