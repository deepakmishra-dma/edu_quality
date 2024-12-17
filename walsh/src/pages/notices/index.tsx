import {IResourceComponentsProps} from "@refinedev/core";
import React, {useMemo, useState} from "react";
import {Box, Input, Stack, Text} from "@mantine/core";
import {useNavigate} from "react-router-dom";
// @ts-expect-error no types
import {IconArchive, IconCalendar, IconSearch, IconStar} from "@tabler/icons";
import useStudentList from "../../components/queries/useStudentList.ts";
import {getStudentProfileColor} from "../../components/hooks/useStudentProfileColor.ts";
import useMarkAsStared from "../../components/queries/useMarkStarMutation.ts";
import useMarkAsArchived from "../../components/queries/useMarkArchivedMutation.ts";
import useNoticeList from "../../components/queries/useNoticeList.ts";

interface StaredNoticeListProps extends IResourceComponentsProps {
  staredOnly?: boolean
  archivedOnly?: boolean
}

export const NoticeList: React.FC<StaredNoticeListProps> = ({staredOnly, archivedOnly}) => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const {data} = useStudentList()
  const {mutateAsync: markAsStared} = useMarkAsStared()
  const {mutateAsync: markAsArchived} = useMarkAsArchived()
  const {data: list, isLoading, remove, refetch} = useNoticeList({
    staredOnly,
    archivedOnly
  });

  const filteredList = useMemo(() => {
    if (!list)
      return [];
    if (!searchQuery)
      return list?.data?.message || [];
    return list?.data?.message?.filter(item => item?.subject?.toLowerCase?.()?.includes(searchQuery.toLowerCase())) || []
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
      {filteredList?.map?.((item) => item?.subject?.toLowerCase?.()?.includes(searchQuery.toLowerCase()) && (
        <Stack
          key={item.name + String(item.student || "")}
          sx={{
            backgroundColor: item.is_read ? '#F6FAFF' : 'white',
            marginBottom: 10,
            border: '1px solid rgba(0,0,0,0.05)',
            padding: 5,
            flexDirection: 'row',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 5
          }}>
          <Box
            p={5}
            sx={{
              cursor: 'pointer',
              width: 'calc(100% - 50px)',
              ":hover": {
                backgroundColor: 'rgba(0,0,0,0.02)'
              }
            }}
            onClick={() => {
              if (!item.is_read) {
                remove()
                refetch().then(undefined)
              }
              navigate(`/notice/${item.name}?student=${encodeURIComponent(item.student)}`)
            }}
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
            <Box my={5} sx={{
              overflow: 'hidden',
              textOverflow: 'none',
              whiteSpace: 'nowrap',
              width: '100%',
              fontSize: 14,
              height: "5em",
              pointerEvents: 'none',
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
              <Stack align="center" justify="center" mt={4} px={10} sx={{
                display: 'inline-block',
                whiteSpace: 'nowrap',
                fontSize: 13,
                backgroundColor: getStudentProfileColor(item.student, data?.data?.message || []),
                color: 'white',
                fontWeight: 'bold',
                borderRadius: 3,
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
          <Box sx={{
            padding: 5,
            paddingRight: 10,
          }}>
            <IconStar
              style={{
                marginBottom: 10
              }}
              size={35}
              fill={item.is_stared ? getStudentProfileColor(item.student, data?.data?.message || []) : 'white'}
              color={item.is_stared ? "white" : getStudentProfileColor(item.student, data?.data?.message || [])}
              stroke={1}
              onClick={() => {
                markAsStared({notice: item.name, student: item.student, stared: !item.is_stared})
                  .then(() => refetch())
              }}
            />
            <IconArchive
              size={30}
              color={item.is_archived ? "white" : getStudentProfileColor(item.student, data?.data?.message || [])}
              stroke={1}
              fill={item.is_archived ? getStudentProfileColor(item.student, data?.data?.message || []) : 'white'}
              onClick={() => {
                markAsArchived({notice: item.name, student: item.student, archived: !item.is_archived})
                  .then(() => refetch())
              }}
            />
          </Box>
        </Stack>
      ))}
    </Box>
  </Box>
};
