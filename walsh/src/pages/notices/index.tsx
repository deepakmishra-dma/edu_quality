import {IResourceComponentsProps, useList} from "@refinedev/core";
import React, {useMemo, useState} from "react";
import {Notice} from "../../providers/data/notices.ts";
import {Box, Divider, Input, Stack, Text} from "@mantine/core";
import {useNavigate} from "react-router-dom";
// @ts-expect-error no types
import {IconSearch} from "@tabler/icons";

export const NoticeList: React.FC<IResourceComponentsProps> = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const {data: list} = useList<Notice>({
    pagination: {
      current: 1,
      pageSize: 10000,
      mode: 'server',
    },
  });

  const filteredList = useMemo(() => {
    if (!list)
      return [];
    if (!searchQuery)
      return list?.data;
    return list?.data.filter(item => item?.subject?.toLowerCase?.()?.includes(searchQuery.toLowerCase())) || []
  }, [list, searchQuery]);

  return <Box>
    <Box pb={10}>
      <Input
        mx={5}
        onChange={(e) => setSearchQuery(e.target.value)}
        value={searchQuery} placeholder="Search..." icon={<IconSearch/>}
      />
    </Box>
    <Box p={2}>
      <Divider/>
      {!filteredList?.length &&
        <Text align="center" color="dimmed" weight="bold" my={30}>No Notice Found</Text>}
      {filteredList?.map(item => item?.subject?.toLowerCase?.()?.includes(searchQuery.toLowerCase()) && (
        <Box key={item.name + String(item.student || "")}>
          <Box p={5} sx={{
            cursor: 'pointer',
            ":hover": {
              backgroundColor: 'rgba(0,0,0,0.01)'
            }
          }}
               onClick={() => navigate(`/notice/${item.name}?student=${encodeURIComponent(item.student)}`)}>
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
              }}>{item?.student_first_name}</Stack>
              <Stack align="center" justify="center" py={4} px={10} sx={{
                display: 'inline-block',
                marginLeft: "auto",
                borderRadius: 5,
                whiteSpace: 'nowrap',
                fontSize: 12
              }}>{new Date(item.creation).toLocaleDateString() || '-'}</Stack>
              {/*<Stack sx={{*/}
              {/*  flexDirection: 'row',*/}
              {/*  gap: 5*/}
              {/*}}>*/}
              {/*  <IconStar fill="white" stroke="black"/>*/}
              {/*  <IconArchive fill="white" stroke="black"/>*/}
              {/*</Stack>*/}
            </Stack>
            <Text h={25} weight="bold" size="lg" sx={{
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              width: '100%',
            }}>
              {item.subject || '-'}
            </Text>
            <Box h={50} my={5} sx={{
              overflow: 'hidden',
              textOverflow: 'none',
              whiteSpace: 'nowrap',
              width: '100%',
              backgroundColor: 'rgba(0,0,0,0.03)',
              borderRadius: '5px',
            }}>
              <div dangerouslySetInnerHTML={{__html: item.notice || ""}}></div>
            </Box>
          </Box>
          <Divider/>
        </Box>
      ))}
    </Box>
  </Box>
};
