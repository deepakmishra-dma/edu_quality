import {
  Box,
  Burger,
  Navbar as MantineNavbar,
  NavLink,
  Stack,
  Text,
} from "@mantine/core";

import React, { useEffect } from "react";
import {
  IconArchive,
  IconCalendarOff,
  IconLogout,
  IconMessage,
  IconReload,
  // IconStack2,
  IconStar,
  // IconCalendar,
  // IconFileDescription,
  // IconReport,
  IconUser,
  IconCreditCard,
  // IconLink,
  // IconPrinter,
} from "@tabler/icons";
import { IconClock } from "@tabler/icons-react";
// import { IconReport } from "@tabler/icons-react";
import { useLogout, useGetIdentity } from "@refinedev/core";
import { useLocation, useNavigate } from "react-router-dom";

interface NavbarProps {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

const Navbar: React.FC<NavbarProps> = ({ setIsOpen, isOpen }) => {
  const { mutate: logout } = useLogout();
  const navigate = useNavigate();
  const location = useLocation();
  const { data: identity } = useGetIdentity();

  useEffect(() => {
    setIsOpen(false);
  }, [location?.pathname]);

  const changeLocation: typeof navigate = (...args) => {
    // @ts-expect-error it works
    navigate(...args);
    setIsOpen(false);
  };

  if (!isOpen) return null;

  const navItems = identity
    ? [
        { label: "Messages", icon: IconMessage, location: "/" },
        {
          label: "Absent Note",
          icon: IconCalendarOff,
          location: "/leave-note",
        },
        { label: "Early Pick Up", icon: IconClock, location: "/early-pickup" },
        { label: "Starred Messages", icon: IconStar, location: "/stared" },
        {
          label: "Archived Messages",
          icon: IconArchive,
          location: "/archived",
        },
        {
          label: "Student Profile",
          icon: IconUser,
          location: "/student-profile",
        },
        { label: "Fee", icon: IconCreditCard, location: "/fee" },
        {
          label: "Reload",
          icon: IconReload,
          onClick: () => {
            window.location.reload();
          },
        },
        {
          label: "Logout",
          icon: IconLogout,
          onClick: async () => {
            logout();
            setIsOpen(false);
          },
        },
      ]
    : [
        { label: "Messages", icon: IconMessage, location: "/" },
        { label: "Login", icon: IconUser, location: "/login" },
        {
          label: "Reload",
          icon: IconReload,
          onClick: () => {
            window.location.reload();
          },
        },
        { label: "Register", icon: IconUser, location: "/register" },
      ];

  return (
    <MantineNavbar
      hidden={!isOpen}
      style={{
        backgroundColor: "transparent",
        position: "fixed",
        inset: 0,
        height: "100dvh",
      }}
    >
      <Box
        sx={{
          backgroundColor: "#0005",
          position: "absolute",
          inset: 0,
        }}
        onClick={() => setIsOpen(false)}
      />
      <Box
        sx={{
          position: "absolute",
          inset: 0,
          backgroundColor: "white",
          overflowX: "hidden",
          overflowY: "auto",
        }}
      >
        <Stack
          sx={{
            height: 60,
            borderBottom: "1px solid rgba(0,0,0,0.1)",
            flexDirection: "row",
          }}
        >
          <Box
            sx={{
              height: 59,
              width: 60,
              padding: "10px 10px",
            }}
          >
            <Box
              sx={{
                backgroundImage:
                  "url(/assets/edu_quality/walsh/images/tgaa1024.jpg)",
                height: 40,
                width: 40,
                borderRadius: 4,
                backgroundSize: "contain",
              }}  
            />
          </Box>
          <Stack
            onClick={() => setIsOpen((o) => !o)}
            justify="center"
            align="center"
            p={10}
            w={50}
            sx={{
              right: 0,
              top: 0,
              bottom: 0,
              cursor: "pointer",
              marginLeft: "auto",
              marginRight: 10,
            }}
          >
            <Burger opened={isOpen} />
          </Stack>
        </Stack>
        {navItems.map((n, index) => {
          return <NavRoute key={index} n={n} changeLocation={changeLocation} />;
        })}
        {!identity && (
          <Box p="md">
            <Text size="sm" color="gray">
              Login to see more features
            </Text>
          </Box>
        )}
      </Box>
    </MantineNavbar>
  );
};

interface NavRouteData {
  label: string;
  icon: typeof IconReload;
  location?: string;
  subRoutes?: NavRouteData[];
  onClick?: () => void;
}
function NavRoute({
  n,
  changeLocation,
}: {
  n: NavRouteData;
  changeLocation: ReturnType<typeof useNavigate>;
}) {
  if (!n.subRoutes)
    return (
      <NavLink
        key={n.label}
        onClick={() =>
          n.location ? changeLocation(n.location) : n?.onClick?.()
        }
        sx={{
          margin: 5,
          boxSizing: "border-box",
          maxWidth: "100%",
          borderBottom: "1px solid rgba(0,0,0,0.1)",
        }}
        label={n.label}
        icon={<n.icon size={35} stroke={1.5} color="#1E6967" />}
      />
    );

  if (n.subRoutes) {
    return (
      <Box
        pb={8}
        sx={{
          borderBottom: "1px solid rgba(0,0,0,0.1)",
        }}
      >
        <NavLink
          pb={0}
          mb={0}
          key={n.label}
          sx={{
            margin: 5,
            boxSizing: "border-box",
            maxWidth: "100%",
          }}
          childrenOffset={55}
          label={n.label}
          icon={<n.icon size={35} stroke={1.5} color="#1E6967" />}
        >
          {n.subRoutes.map((n) => (
            <NavLink
              key={n.label}
              onClick={() =>
                n.location ? changeLocation(n.location) : n?.onClick?.()
              }
              styles={{
                label: {
                  fontSize: "12px !important",
                },
              }}
              py={6}
              sx={{
                boxSizing: "border-box",
                maxWidth: "100%",
              }}
              label={n.label}
            />
          ))}
        </NavLink>
      </Box>
    );
  }
}
export default Navbar;
