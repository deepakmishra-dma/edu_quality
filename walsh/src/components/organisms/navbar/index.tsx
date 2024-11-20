import {Box, Burger, Navbar as MantineNavbar, NavLink, Stack} from '@mantine/core';
import React, {useEffect} from "react";
// @ts-expect-error no types
import {IconLogout, IconMessage, IconReload, IconStack2} from "@tabler/icons";
import {useLogout} from "@refinedev/core";
import {useLocation, useNavigate} from "react-router-dom";

interface NavbarProps {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>
}

const Navbar: React.FC<NavbarProps> = ({setIsOpen, isOpen}) => {
  const {mutate: logout} = useLogout()
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    setIsOpen(false)
  }, [location?.pathname])

  const changeLocation: typeof navigate = (...args) => {
    // @ts-expect-error it works
    navigate(...args)
    setIsOpen(false)
  }

  if (!isOpen) return null;
  return (
    <MantineNavbar
      hidden={!isOpen}
      style={{
        backgroundColor: 'transparent',
        position: 'fixed',
        inset: 0,
        height: '100dvh',
      }}>
      <Box
        sx={{
          backgroundColor: '#0005',
          position: 'absolute',
          inset: 0,
        }}
        onClick={() => setIsOpen(false)}
      />
      <Box sx={{
        position: 'absolute',
        inset: 0,
        // right: '20%',
        backgroundColor: 'white',
        // paddingTop: 10,
        overflowX: 'hidden',
        overflowY: 'auto',
      }}>
        <Stack sx={{
          height: 60,
          borderBottom: '1px solid rgba(0,0,0,0.1)',
          flexDirection: 'row',
        }}>
          <Box sx={{
            height: 59,
            width: 60,
            padding: '10px 10px',
          }}>
            <Box sx={{
              backgroundImage: 'url(/assets/edu_quality/walsh/images/walnut-logo-blue.png)',
              height: 36,
              width: 40,
              backgroundSize: 'cover',
            }}/>
          </Box>
          <Stack
            onClick={() => setIsOpen(o => !o)}
            justify="center"
            align="center"
            p={10}
            w={50}
            sx={{
              right: 0,
              top: 0,
              bottom: 0,
              cursor: "pointer",
              marginLeft: 'auto'
            }}>
            <Burger opened={isOpen}/>
          </Stack>
        </Stack>
        <NavLink
          onClick={() => changeLocation('/')}
          sx={{margin: 5, boxSizing: 'border-box', maxWidth: '100%', borderBottom: '1px solid rgba(0,0,0,0.1)'}}
          label="Messages"
          icon={<IconMessage size={35} stroke={1.5} color='#00b8ff'/>}
        />
        <NavLink
          onClick={() => changeLocation('/cmap')}
          sx={{margin: 5, boxSizing: 'border-box', maxWidth: '100%', borderBottom: '1px solid rgba(0,0,0,0.1)'}}
          label="Curriculum Updates"
          icon={<IconStack2 size={35} stroke={1.5} color='#00b8ff'/>}
        />
        {/*<NavLink*/}
        {/*  onClick={() => changeLocation('/absent-note')}*/}
        {/*  sx={{margin: 5, boxSizing: 'border-box', maxWidth: '100%', borderBottom: '1px solid rgba(0,0,0,0.1)'}}*/}
        {/*  label="Absent/Sick Note"*/}
        {/*  icon={<IconMoodSad size={35} stroke={1.5} color='#00b8ff'/>}*/}
        {/*/>*/}
        {/*<NavLink*/}
        {/*  onClick={() => changeLocation('/student-profile')}*/}
        {/*  sx={{margin: 5, boxSizing: 'border-box', maxWidth: '100%', borderBottom: '1px solid rgba(0,0,0,0.1)'}}*/}
        {/*  label="Student Profile"*/}
        {/*  icon={<IconUser size={35} stroke={1.5} color='#00b8ff'/>}*/}
        {/*/>*/}
        <NavLink
          onClick={() => window.location.reload()}
          sx={{margin: 5, boxSizing: 'border-box', maxWidth: '100%', borderBottom: '1px solid rgba(0,0,0,0.1)'}}
          label="Reload"
          icon={<IconReload size={35} stroke={1.5} color='#00b8ff'/>}
        />
        <NavLink
          label="Logout"
          icon={<IconLogout size={35} stroke={1.5} color='#00b8ff'/>}
          onClick={() => logout()}
          sx={{
            position: 'sticky', borderBottom: '1px solid rgba(0,0,0,0.1)',
            margin: 5, boxSizing: 'border-box', maxWidth: '100%', bottom: 0,
          }}
        />
      </Box>
    </MantineNavbar>
  );
};

export default Navbar;
