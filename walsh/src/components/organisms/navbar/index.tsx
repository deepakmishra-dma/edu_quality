import {
  Box,
  Burger,
  Navbar as MantineNavbar,
  NavLink,
  Stack,
} from "@mantine/core";

import React, { useEffect } from "react";
import {
  IconArchive,
  IconCalendarOff,
  IconLogout,
  IconMessage,
  IconReload,
  IconStack2,
  IconStar,
  IconCalendar,
  // IconFileDescription,
  IconUser,
  IconCreditCard,
  IconLink,
  IconPrinter,
} from "@tabler/icons";
import { IconClock } from "@tabler/icons-react";
import { useLogout } from "@refinedev/core";
import { useLocation, useNavigate } from "react-router-dom";

interface NavbarProps {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

const Navbar: React.FC<NavbarProps> = ({ setIsOpen, isOpen }) => {
  const { mutate: logout } = useLogout();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    setIsOpen(false);
  }, [location?.pathname]);

  const changeLocation: typeof navigate = (...args) => {
    // @ts-expect-error it works
    navigate(...args);
    setIsOpen(false);
  };

  if (!isOpen) return null;
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
          // right: '20%',
          backgroundColor: "white",
          // paddingTop: 10,
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
                  "url(/assets/edu_quality/walsh/images/walnut-logo-blue.png)",
                height: 36,
                width: 40,
                backgroundSize: "cover",
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
        {[
          { label: "Messages", icon: IconMessage, location: "/" },
          {
            label: "Curriculum Updates",
            icon: IconStack2,
            location: "/cmap",
            subRoutes: [
              {
                label: "Daily Updates",
                icon: IconStack2,
                location: "/cmap",
              },
              {
                label: "Portion",
                icon: IconArchive,
                location: "/portion-circular",
              },

              {
                label: "Weekly Updates",
                icon: IconArchive,
                location: "/date-circular",
              },
            ],
          },
          {
            label: "Absent Note",
            icon: IconCalendarOff,
            location: "/leave-note",
          },
          {
            label: "Early Pick Up",
            icon: IconClock,
            location: "/early-pickup",
          },
          {
            label: "PTM Links",
            icon: IconLink,
            location: "/ptm-link",
          },
          {
            label: "Student Profile",
            icon: IconUser,
            location: "/student-profile",
          },
          {
            label: "Fee",
            icon: IconCreditCard,
            location: "/fee",
          },
          {
            label: "School Calendar",
            icon: IconCalendar,
            location: "/calendar",
          },
          { label: "Starred Messages", icon: IconStar, location: "/stared" },
          {
            label: "Archived Messages",
            icon: IconArchive,
            location: "/archived",
          },
          // {
          //   label: "Result",
          //   icon: IconFileDescription,
          //   location: "/result",
          // },

          {
            label: "Bonafide Certificate",
            icon: IconPrinter,
            location: "/bonafide",
          },

          {
            label: "Reload",
            icon: IconReload,
            onClick: () => {
              window.location.reload();
            },
          },
          { label: "Logout", icon: IconLogout, onClick: () => logout() },
        ].map((n) => {
          return <NavRoute n={n} changeLocation={changeLocation} />;
        })}
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
        icon={<n.icon size={35} stroke={1.5} color="#00b8ff" />}
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
          icon={<n.icon size={35} stroke={1.5} color="#00b8ff" />}
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
