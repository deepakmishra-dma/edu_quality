import {Box, Navbar as MantineNavbar, NavLink} from '@mantine/core';
import React from "react";
// @ts-expect-error no types
import {IconLogout, IconMoodSad, IconReload, IconStack2, IconUser} from "@tabler/icons";
import {useLogout} from "@refinedev/core";
import {useNavigate} from "react-router-dom";

interface NavbarProps {
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>
}


const Navbar: React.FC<NavbarProps> = ({setIsOpen, isOpen}) => {
  const {mutate: logout} = useLogout()
  const navigate = useNavigate()
  if (!isOpen) return null;
  return (
    <MantineNavbar
      hidden={!isOpen}
      style={{
        backgroundColor: 'transparent',
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
        right: '20%',
        backgroundColor: 'white',
        paddingTop: 10,
        overflow: 'auto',
      }}>
        <NavLink
          onClick={() => navigate('/curriculum-updates')}
          sx={{margin: 5, boxSizing: 'border-box', maxWidth: '100%'}}
          label="Curriculum Updates"
          icon={<IconStack2 size={25} stroke={1.5}/>}
        />
        <NavLink
          onClick={() => navigate('/absent-note')}
          sx={{margin: 5, boxSizing: 'border-box', maxWidth: '100%'}}
          label="Absent/Sick Note"
          icon={<IconMoodSad size={25} stroke={1.5}/>}
        />
        <NavLink
          onClick={() => navigate('/student-profile')}
          sx={{margin: 5, boxSizing: 'border-box', maxWidth: '100%'}}
          label="Student Profile"
          icon={<IconUser size={25} stroke={1.5}/>}
        />
        <NavLink
          onClick={() => window.location.reload()}
          sx={{margin: 5, boxSizing: 'border-box', maxWidth: '100%'}}
          label="Reload"
          icon={<IconReload size={25} stroke={1.5}/>}
        />
        <NavLink
          label="Logout"
          icon={<IconLogout size={25} stroke={1.5}/>}
          onClick={() => logout()}
          sx={{
            position: 'sticky',
            bottom: 0,
            margin: 5, boxSizing: 'border-box', maxWidth: '100%'
          }}
        />
      </Box>
    </MantineNavbar>
  );
};

export default Navbar;
