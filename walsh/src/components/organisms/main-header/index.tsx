import {Header as MantineHeader, Stack,} from "@mantine/core";
import {RefineThemedLayoutV2HeaderProps} from "@refinedev/mantine";
import React from "react";
import {useLocation, useNavigate} from "react-router-dom";
// @ts-expect-error no types
import {IconArrowLeft} from "@tabler/icons";

export const Header: React.FC<RefineThemedLayoutV2HeaderProps> = () => {
  const location = useLocation()
  const navigate = useNavigate()
  // const [sidebarOpened, setSidebarOpened] = useState(false)
  return (
    <MantineHeader height={60} sx={{
      boxShadow: "0 0 5px rgba(0, 0, 0, 0.1)",
    }}>
      <Stack align="center" justify="center" sx={{height: "100%"}}>
        {location.pathname.startsWith('/notice') && <Stack
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
          <IconArrowLeft/>
        </Stack>}
        WalSH
      </Stack>
      {/*<Group h="100%" px="md">*/}
      {/*  <Burger opened={sidebarOpened} onClick={() => setSidebarOpened(!sidebarOpened)}*/}
      {/*          hidden={sidebarOpened} size="sm"/>*/}
      {/*</Group>*/}
    </MantineHeader>
  );
};
