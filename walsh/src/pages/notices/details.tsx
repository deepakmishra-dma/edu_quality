import { IResourceComponentsProps, useOne } from "@refinedev/core";
import React, { } from "react";
import { Box, Stack, Text } from "@mantine/core";
import { useParams, useSearchParams } from "react-router-dom";
// import {   } from "@mantine/core";
import { useNavigate } from "react-router-dom";
import { IconCalendar } from "@tabler/icons";
import useNoticeList, { Notice } from "../../components/queries/useNoticeList.ts";
import { IconArchive, IconStar } from "@tabler/icons";
import { getStudentProfileColor } from "../../components/hooks/useStudentProfileColor.ts";
import useMarkAsArchived from "../../components/queries/useMarkArchivedMutation.ts";
import useMarkAsStared from "../../components/queries/useMarkStarMutation.ts";

interface StaredNoticeListProps extends IResourceComponentsProps {
  staredOnly?: boolean
  archivedOnly?: boolean
}
export const NoticeDetails: React.FC<StaredNoticeListProps> = ({ }) => {
  const params = useParams()
  const [queries] = useSearchParams()
  const navigate = useNavigate();

  // const [searchQuery,] = useState('');
  const { mutateAsync: markAsStared } = useMarkAsStared()
  const { mutateAsync: markAsArchived } = useMarkAsArchived()
  const { refetch } = useNoticeList({});
  const { data, isLoading } = useOne<Notice>({
    id: params?.id || "", queryOptions: {
      queryKey: ["details", "notices", params?.id, queries?.get("student")],
    }
  });
  console.log("list ", data)



  if (isLoading)
    return <Text align="center" color="dimmed" weight="bold" my={30}>Loading...</Text>



  return <Box>
    <Box sx={{
      backgroundColor: '#422e1a',
      color: 'white',
      padding: 10
    }}>
      <Text weight="bold" size="lg" sx={{
        width: '100%',
        padding: '5px 0',
        fontWeight: 'bold',
        textAlign: 'center'
      }}>
        {data?.data?.subject || '-'}
      </Text>
      <Stack h={35} sx={{
        flexDirection: 'row',
        // justifyContent: 'space-between',
        paddingTop: 5,
        paddingBottom: 5,
        borderTop: '1px solid #eee',
        gap: 10,
        color: '#fdc426',
        justifyContent: 'center'
      }}>
        <Stack align="center" justify="center" pt={4} pr={10} sx={{
          display: 'inline-block',
          whiteSpace: 'nowrap',
          fontSize: 13,
          borderRight: '1px solid #eee'
        }}>{data?.data?.student_first_name}</Stack>

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
          <IconCalendar size={15} />
          <span style={{ paddingTop: 5 }}>
            {new Date(data?.data.creation).toLocaleDateString()?.replace(/\//g, '-') || '-'}
          </span>

          <IconStar
            style={{
              marginTop: 5,
              position: "absolute",
              right: 45,
              borderRight: '1px solid #eee',
              paddingRight: "5px"
            }}
            size={35}

            fill={data?.data?.is_stared ? getStudentProfileColor(data?.data?.student, data?.data?.message || []) : '#fdc426'}
            color={getStudentProfileColor(data?.data?.student, data?.data?.message || [])}
            stroke={1}
            onClick={() => {
              const noticeName = data?.data?.name ?? '';
              markAsStared({ notice: noticeName, student: data?.data?.student, stared: !data?.data?.is_stared })
                .then(() => refetch())
              navigate("/")
            }}

          />
          <IconArchive
            style={{
              marginTop: 5,
              position: "absolute",
              right: 8
            }}
            size={30}
            color={data?.data?.is_archived ? "white" : getStudentProfileColor(data?.data?.student, data?.data?.message || [])}
            stroke={1}
            fill={data?.data?.is_archived ? getStudentProfileColor(data?.data?.student, data?.data?.message || []) : '#fdc426'}
            onClick={() => {
              const noticeName = data?.data?.name ?? '';
              markAsArchived({ notice: noticeName, student: data?.data?.student, archived: !data?.data?.is_archived })
                .then(() => refetch())
              navigate("/")

            }}
          />

        </Stack>
      </Stack>
    </Box>
    <Box sx={{
      overflow: 'auto',
      width: '100%',
      padding: 10
    }}>
      {
        data?.data?.is_raw_html ? <>
          <div dangerouslySetInnerHTML={{ __html: data?.data?.notice || "" }}></div>
        </> : <>
          <link href="https://cdn.jsdelivr.net/npm/quill@2.0.0-beta.0/dist/quill.snow.css" rel="stylesheet" />
          <link href="https://cdn.jsdelivr.net/npm/quill@2.0.0-beta.0/dist/quill.bubble.css" rel="stylesheet" />
          <div className="ql-editor" dangerouslySetInnerHTML={{ __html: data?.data?.notice || "" }}></div>
        </>
      }
    </Box>
  </Box>


};
