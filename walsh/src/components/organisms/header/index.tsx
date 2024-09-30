import {Burger, Header as MantineHeader, Stack} from "@mantine/core";
import React from "react";
import {useLocation, useNavigate} from "react-router-dom";
// @ts-expect-error no types
import {IconArrowLeft} from "@tabler/icons";

interface HeaderProps {
  setNavbarOpen: React.Dispatch<React.SetStateAction<boolean>>;
  navbarOpen: boolean
}

export const Header: React.FC<HeaderProps> = ({setNavbarOpen, navbarOpen}) => {
  const location = useLocation()
  const navigate = useNavigate()

  // const [sidebarOpened, setSidebarOpened] = useState(false)
  return (
    <MantineHeader height={60} sx={{
      boxShadow: "0 0 5px rgba(0, 0, 0, 0.1)",
    }}>
      <Stack align="center" justify="center" sx={{height: "100%"}}>
        <Stack
          onClick={() => location.pathname !== '/' ? navigate(-1) : setNavbarOpen(o => !o)}
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

          {location.pathname === '/' ? <Burger opened={navbarOpen}/> : <IconArrowLeft size={30} stroke={1.5}/>}
        </Stack>
        WalSH
      </Stack>
      {/*<Group h="100%" px="md">*/}
      {/*  <Burger opened={sidebarOpened} onClick={() => setSidebarOpened(!sidebarOpened)}*/}
      {/*          hidden={sidebarOpened} size="sm"/>*/}
      {/*</Group>*/}
    </MantineHeader>
  );
};
