import type {ReactNode} from "react";
import {SubHeader} from "../organisms/sub-header";
import {Container, Stack} from "@mantine/core";

interface BaseLayoutProps {
  children: ReactNode;
  name: string;
  goBack?: () => void;
}

export const BaseLayout = ({children, name, goBack}: BaseLayoutProps) => {
  return (
    <Container px={0} size={"xs"} w={"100%"} mih={"100vh"}>
      <Stack>
        <SubHeader name={name} goBack={goBack}/>
        <Container size={"xs"} w={"100%"}>
          {children}
        </Container>
      </Stack>
    </Container>
  );
};
