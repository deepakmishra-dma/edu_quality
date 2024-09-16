import {IResourceComponentsProps, useOne} from "@refinedev/core";
import React from "react";
import {Notice} from "../../providers/data/notices.ts";
import {Box, Divider, Stack, Text} from "@mantine/core";
import {useParams} from "react-router-dom";

export const NoticeDetails: React.FC<IResourceComponentsProps> = () => {
  const params = useParams()
  const {data} = useOne<Notice>({id: params?.id || ""});
  return <Box p={10}>
    <Stack h={25} px={5} sx={{
      flexDirection: 'row',
      justifyContent: 'space-between',
    }}>
      <Box>
        {data?.data?.students?.map((student, index) => (
          <Text key={index} py={2} px={5} size="xs" sx={{
            display: 'inline-block',
            marginRight: 5,
            backgroundColor: 'rgba(0,0,0,0.1)',
            borderRadius: 5
          }}>{student}</Text>
        ))}
      </Box>
      <Text size="xs">{new Date(data?.data?.creation).toLocaleDateString() || '-'}</Text>
    </Stack>
    <Text weight="bold" size="lg" sx={{
      width: '100%',
      padding: '5px',
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
