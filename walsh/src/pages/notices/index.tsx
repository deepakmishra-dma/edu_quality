import {IResourceComponentsProps, useList} from "@refinedev/core";
import React, {Fragment, useState} from "react";
import {Notice} from "../../providers/data/notices.ts";
import {Box, Divider, Select, Stack, Text} from "@mantine/core";
import {useNavigate} from "react-router-dom";

export const NoticeList: React.FC<IResourceComponentsProps> = () => {
  const navigate = useNavigate();
  const [category, setCategory] = useState('all');
  const {data: list} = useList<Notice>({
    pagination: {
      current: 1,
      pageSize: 10000,
      mode: 'server',
    },
  });
  return <Box>
    <Box pb={10}>
      <Select
        placeholder="Select Category"
        value={category}
        onChange={(value) => setCategory(value || "all")}
        p={10}
        data={[
          {value: 'all', label: 'All Notices For Me'},
          {value: 'school', label: 'Notice For My School'},
          // {value: 'class', label: 'Notice For My Class'},
          // {value: 'division', label: 'Notice For My Division'},
          {value: 'student', label: 'Notices For Individuals'},
        ]}
      />
    </Box>
    <Box p={2}>
      <Divider/>
      {[...Array(1)].map((_, index) => (
        <Fragment key={index}>
          {list?.data.map(item => (
            <Box key={item.name}>
              <Box p={5} sx={{
                cursor: 'pointer',
                ":hover": {
                  backgroundColor: 'rgba(0,0,0,0.01)'
                }
              }} onClick={() => navigate(`/notice/${item.name}`)}>
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
                <Stack h={35} sx={{
                  flexDirection: 'row',
                  justifyContent: 'space-between',
                  paddingTop: 5,
                  paddingBottom: 5
                }}>
                  <Box>
                    {item?.students?.map((student, index) => (
                      <Text key={index} py={2} px={5} size="xs" sx={{
                        display: 'inline-block',
                        marginRight: 5,
                        backgroundColor: 'rgba(0,0,0,0.1)',
                        borderRadius: 5
                      }}>{student}</Text>
                    ))}
                  </Box>
                  <Text size="xs">{new Date(item.creation).toLocaleDateString() || '-'}</Text>
                </Stack>
              </Box>
              <Divider/>
            </Box>
          ))}
        </Fragment>
      ))}
    </Box>
  </Box>
};
