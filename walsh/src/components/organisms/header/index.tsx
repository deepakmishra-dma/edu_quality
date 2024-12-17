import {Box, Burger, Header as MantineHeader, Stack} from "@mantine/core";
import React from "react";
import {useLocation, useNavigate} from "react-router-dom";
// @ts-expect-error no types
import {IconArrowLeft} from "@tabler/icons";

interface HeaderProps {
  setNavbarOpen: React.Dispatch<React.SetStateAction<boolean>>;
  navbarOpen: boolean
}

export const Header: React.FC<HeaderProps> = ({setNavbarOpen}) => {
  const location = useLocation()
  const navigate = useNavigate()

  // const [sidebarOpened, setSidebarOpened] = useState(false)
  return (
    <MantineHeader height={60} sx={{
      boxShadow: "0 0 5px rgba(0, 0, 0, 0.1)",
    }}>
      <Stack justify="center" pl={50} sx={{height: "100%"}}>
        {location.pathname !== '/' && <Stack
            onClick={() => navigate(-1)}
            justify="center"
            align="center"
            p={10}
            w={50}
            sx={{
              position: "absolute",
              left: 0,
              top: 0,
              bottom: 0,
              cursor: "pointer",
            }}>
            <IconArrowLeft size={30} stroke={1.5}/>
        </Stack>}
        <Stack
          onClick={() => setNavbarOpen(o => !o)}
          // justify="center"
          // align="center"
          p={10}
          w={50}
          mr={10}
          sx={{
            position: "absolute",
            right: 0,
            top: 0,
            bottom: 0,
            cursor: "pointer",
          }}>
          <Burger opened={false}/>
        </Stack>
        <Box sx={{
          fontSize: 20,
          fontWeight: "bold",
        }}>
          {location.pathname === '/' ? "Notices" :
           location.pathname === '/archived' ? "Archived Messages" :
           location.pathname === '/stared' ? "Stared Messages" :
           /^\/notice\/([0-9a-f]+)$/.test(location.pathname) ? "" :
           /^\/cmap$/.test(location.pathname) ? "Curriculum Updates" :
           /^\/cmap\/list$/.test(location.pathname) ? "Curriculum Updates" :
           ""}
        </Box>
      </Stack>
    </MantineHeader>
  );
};
