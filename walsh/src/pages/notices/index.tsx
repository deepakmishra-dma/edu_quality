import {IResourceComponentsProps, useList} from "@refinedev/core";
import React, {useMemo, useState} from "react";
import {Notice} from "../../providers/data/notices.ts";
import {Box, Input, Stack, Text} from "@mantine/core";
import {useNavigate} from "react-router-dom";
// @ts-expect-error no types
import {IconCalendar, IconSearch} from "@tabler/icons";
import {getStudentProfileColor} from "../../components/hooks/useStudentProfileColor.ts";
import useStudentList from "../../components/queries/useStudentList.ts";

export const NoticeList: React.FC<IResourceComponentsProps> = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const {data} = useStudentList()
  const {data: list, isLoading} = useList<Notice>({
    queryOptions: {
      queryKey: ["list", "notices"],
    },
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
    <Box pb={10} pt={15} px={5}>
      <Input
        mx={5}
        onChange={(e) => setSearchQuery(e.target.value)}
        value={searchQuery} placeholder="Search..." icon={<IconSearch/>}
      />
    </Box>
    <Box p={2} sx={{
      // backgroundColor: 'rgba(0,0,0,0.04)',
    }}>
      {/*<Divider/>*/}
      {!filteredList?.length && <Text align="center" color="dimmed" weight="bold" my={30}>
        {isLoading ? "Loading..." : "No Notice Found"}
      </Text>}
      {filteredList?.map((item) => item?.subject?.toLowerCase?.()?.includes(searchQuery.toLowerCase()) && (
        <Stack
          key={item.name + String(item.student || "")}
          sx={{
            backgroundColor: 'white',
            marginBottom: 10,
            border: '1px solid rgba(0,0,0,0.05)',
            padding: 5,
            flexDirection: 'row',
            display: 'flex',
            alignItems: 'center',
            gap: 5
          }}>
          <Box sx={{
            height: 40,
            width: 40,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '100%',
            backgroundColor: getStudentProfileColor(item.student, data?.data?.message || []),
            color: 'white',
            flexGrow: 0,
            flexShrink: 0,
            fontSize: 25,
            fontWeight: 'bold',
          }}>
            {item?.student_first_name?.[0]?.toUpperCase()}
          </Box>
          <Box
            p={5}
            sx={{
              cursor: 'pointer',
              width: 'calc(100% - 50px)',
              ":hover": {
                backgroundColor: 'rgba(0,0,0,0.02)'
              }
            }}
            onClick={() => navigate(`/notice/${item.name}?student=${encodeURIComponent(item.student)}`)}
          >
            <Text mih={20} weight="bold" size="lg" sx={{
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              width: '100%',
              // fontSize: 15,
            }}>
              {item.subject || '-'}
            </Text>
            <Box h={55} my={5} sx={{
              overflow: 'hidden',
              textOverflow: 'none',
              whiteSpace: 'nowrap',
              width: '100%',
              fontSize: 12,
              // borderRadius: '5px',
              // color: '#888',
            }}>
              <div dangerouslySetInnerHTML={{__html: item.notice || ""}}></div>
            </Box>

            <Stack h={35} sx={{
              flexDirection: 'row',
              // justifyContent: 'space-between',
              paddingTop: 5,
              paddingBottom: 5,
              borderTop: '1px solid #eee',
              gap: 10,
              color: '#666',
            }}>
              <Stack align="center" justify="center" pt={4} pr={10} sx={{
                display: 'inline-block',
                whiteSpace: 'nowrap',
                fontSize: 13,
                borderRight: '1px solid #eee'
              }}>{item?.student_first_name}</Stack>
              <Stack align="center" justify="center" py={4} sx={{
                display: 'inline-flex',
                // justifyContent: 'center',
                flexDirection: 'row',
                // alignItems: 'center',
                // borderRadius: 5,
                whiteSpace: 'nowrap',
                fontSize: 13,
                gap: 5
              }}>
                <IconCalendar size={15}/>
                <span style={{paddingTop: 5}}>
                  {new Date(item.creation).toLocaleDateString()?.replace(/\//g, '-') || '-'}
                </span>
              </Stack>
            </Stack>
          </Box>
          {/*<Divider/>*/}
        </Stack>
      ))}
    </Box>
  </Box>
};
