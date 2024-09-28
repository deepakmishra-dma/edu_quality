import {IResourceComponentsProps, useOne} from "@refinedev/core";
import React from "react";
import {Notice} from "../../providers/data/notices.ts";
import {Box, Divider, Stack, Text} from "@mantine/core";
import {useParams, useSearchParams} from "react-router-dom";
// import {IconArchive, IconStar} from "@tabler/icons";

export const NoticeDetails: React.FC<IResourceComponentsProps> = () => {
  const params = useParams()
  const [queries] = useSearchParams()
  const {data, isLoading} = useOne<Notice>({
    id: params?.id || "", queryOptions: {
      queryKey: ["details", "notices", params?.id, queries?.get("student")],
    }
  });

  if (isLoading)
    return <Text align="center" color="dimmed" weight="bold" my={30}>Loading...</Text>

  return <Box p={10}>
    <Stack h={35} sx={{
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingTop: 5,
      paddingBottom: 5,
      gap: 5
    }}>
      <Stack align="center" justify="center" py={4} px={10} sx={{
        display: 'inline-block',
        backgroundColor: 'rgba(0,0,0,0.1)',
        borderRadius: 5,
        whiteSpace: 'nowrap',
        fontSize: 12
      }}>{data?.data?.student_first_name}</Stack>
      <Stack align="center" justify="center" py={4} px={10} sx={{
        display: 'inline-block',
        marginLeft: "auto",
        borderRadius: 5,
        whiteSpace: 'nowrap',
        fontSize: 12
      }}>{new Date(data?.data?.creation).toLocaleDateString() || '-'}</Stack>
      {/*<Stack sx={{*/}
      {/*  flexDirection: 'row',*/}
      {/*  gap: 5*/}
      {/*}}>*/}
      {/*  <IconStar fill="white" stroke="black"/>*/}
      {/*  <IconArchive fill="white" stroke="black"/>*/}
      {/*</Stack>*/}
    </Stack>
    <Text weight="bold" size="lg" sx={{
      width: '100%',
      padding: '5px 0',
      textAlign: 'justify',
    }}>
      {data?.data?.subject || '-'}
    </Text>
    <Divider my={10}/>
    <Box sx={{
      overflow: 'auto',
      width: '100%',
      backgroundColor: 'rgba(0,0,0,0.02)',
      borderRadius: '5px'
    }}>
      <div dangerouslySetInnerHTML={{__html: data?.data?.notice || ""}}></div>
    </Box>
  </Box>
};
