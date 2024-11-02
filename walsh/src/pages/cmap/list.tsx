import {useState} from "react";
import {useSearchParams} from "react-router-dom";
import {Box, Stack, Text} from "@mantine/core";
// @ts-expect-error no types
import {IconCalendar, IconFile, IconFileChart, IconFileSpreadsheet, IconFileText} from "@tabler/icons";
import useStudentList from "../../components/queries/useStudentList.ts";
import useCmapList from "../../components/queries/useCmapList.ts";
import useClassDetails from "../../components/queries/useClassDetails.ts";
import useStudentProfileColor from "../../components/hooks/useStudentProfileColor.ts";

const fileTypes = {
  "PowerPoint Presentation": {
    color: '#fe7f00',
    icon: IconFileChart
  },
  "Answer Sheet": {
    color: '#00a8ff',
    icon: IconFileText
  },
  "Worksheet": {
    color: '#019837',
    icon: IconFileSpreadsheet
  },
  default: {
    color: '#d21eff',
    icon: IconFile
  }
}

const CmapList = () => {
  const [openedCmap, setOpenedCmap] = useState<string>('')
  // const [selectedStudent, setSelectedStudent] = useState<string | null>('Student Name 1')

  const [searchParams] = useSearchParams()
  const unit = searchParams.get('unit') || ''
  const student = searchParams.get('student') || ''
  const subject = searchParams.get('subject') || ''

  const {data: studentsList} = useStudentList()
  const {data: classDetails} = useClassDetails(student)
  const {data: cmapList, isLoading} = useCmapList(subject, unit, classDetails?.data?.message?.division?.name || '')

  const studentProfileColor = useStudentProfileColor(student)

  const studentName = studentsList?.data?.message?.find(s => s.name === searchParams.get('student'))?.first_name
  const subjectTitle = classDetails?.data?.message?.class?.subject?.find(c => c.subject === searchParams.get('subject'))?.subject

  return (
    <Box>
      <Stack sx={{
        whiteSpace: 'nowrap',
        overflow: 'auto',
        flexDirection: 'row',
        // borderBottom: '1px solid  #0005',
        gap: 0,
      }}>
        <Box
          sx={{
            display: 'inline-block',
            marginTop: 10,
            marginBottom: 5,
            flexShrink: 0,
            flexGrow: 1,
            textAlign: 'center',
          }}
        >
          <Text sx={{
            paddingLeft: 20,
            paddingRight: 20,
            color: '#000',
            fontWeight: 'bold'
          }}>{studentName}</Text>
        </Box>
      </Stack>
      <Box sx={{
        marginBottom: 10,
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: 10,
        backgroundColor: studentProfileColor,
        color: 'white',
        padding: "5px 10px",
        justifyContent: 'center',
        fontSize: 15,
        fontWeight: 'bold'
      }}>
        <Text>{subjectTitle}: Unit {searchParams.get('unit')}</Text>
      </Box>
      <Box sx={{
        padding: 2
      }}>

        {!cmapList?.data?.message?.length && <Text align="center" color="dimmed" weight="bold" my={30}>
          {isLoading ? "Loading..." : "No Curriculum Found"}
        </Text>}
        {cmapList?.data?.message?.map((cmap, i) => {
          const isOpen = openedCmap === i.toString()
          const openOrClose = () => isOpen ? setOpenedCmap("") : setOpenedCmap(i.toString())
          const broadCasts = Array.from(new Set(cmap?.products?.map(product => product?.broadcast_description))).filter(Boolean)
          const homeWorks = Array.from(new Set(cmap?.products?.map(product => product?.homework_description))).filter(Boolean)
          const products = cmap?.products?.filter(product => product?.item_data?.custom_product_url)
          return <Stack
            key={i}
            onClick={openOrClose}
            sx={{
              backgroundColor: 'white',
              marginBottom: 10,
              border: '1px solid rgba(0,0,0,0.05)',
              padding: 10,
              flexDirection: 'row',
              display: 'flex',
              // alignItems: 'center',
              gap: 10,
            }}>
            <Box sx={{
              height: 40,
              width: 40,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '100%',
              backgroundColor: studentProfileColor,
              color: 'white',
              flexGrow: 0,
              flexShrink: 0,
              fontSize: 25,
              fontWeight: 'bold',
              marginTop: 5
            }}>
              {studentName?.[0]?.toUpperCase()}
            </Box>
            <Box
              sx={{
                width: 'calc(100% - 50px)',
              }}
            >
              <Box sx={{
                cursor: 'pointer',
              }}>
                <Text sx={{
                  borderRadius: 50,
                  backgroundColor: studentProfileColor,
                  padding: "1px 7px",
                  fontSize: 10,
                  display: 'inline-block',
                  height: '1.4em',
                  lineHeight: 1.4,
                  color: 'white',
                  fontWeight: 'bold'
                }}>Period {cmap?.period}</Text>
                <Text mih={20} weight="bold" size="lg" sx={{
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  width: '100%',
                  // fontSize: 15,
                }}>
                  {subjectTitle}
                </Text>
                <Box h={isOpen ? undefined : '4em'} sx={{
                  overflow: 'hidden',
                  textAlign: 'justify',
                }}>
                  {broadCasts.filter(broadcast => broadcast).map((broadcast, j) => {
                    return <Box key={j} py={isOpen ? 3 : 0} sx={{
                      overflow: 'hidden',
                      textOverflow: 'none',
                      width: '100%',
                      fontSize: 14,
                      // borderRadius: '5px',
                      color: '#777',
                      textAlign: 'justify',
                      borderBottom: isOpen ? '1px solid rgba(0,0,0,0.03)' : undefined,
                    }}>
                      {broadcast}
                    </Box>
                  })}
                  {isOpen && homeWorks.length > 0 && (
                    <>
                      <Text sx={{
                        fontSize: 15,
                        fontWeight: 'bold',
                        marginTop: 10
                      }}> Home Work</Text>
                      {homeWorks?.map((homeWork, i) => {
                        return <Box key={i} py={3} sx={{
                          overflow: 'hidden',
                          textOverflow: 'none',
                          width: '100%',
                          fontSize: 14,
                          // borderRadius: '5px',
                          color: '#777',
                          textAlign: 'justify',
                          borderBottom: '1px solid rgba(0,0,0,0.03)',
                        }}>
                          {homeWork}
                        </Box>
                      })}
                    </>)
                  }
                </Box>
                <Stack align="center" justify="center" py={4} sx={{
                  display: 'inline-flex',
                  // justifyContent: 'center',
                  flexDirection: 'row',
                  // alignItems: 'center',
                  // borderRadius: 5,
                  whiteSpace: 'nowrap',
                  fontSize: 12,
                  gap: 5,
                  color: '#333',
                }}>
                  <IconCalendar size={13}/>
                  <span style={{paddingTop: 1}}>
                  {new Date().toLocaleDateString()?.replace(/\//g, '-') || '-'}
                </span>
                </Stack>
              </Box>
              <Box sx={{
                whiteSpace: 'nowrap',
                overflow: 'auto',
                paddingBottom: 2,
                paddingTop: 5,
                marginTop: 5,
                borderTop: '1px solid #ccc',
              }}>
                {products.map((product, i) => {
                  const fileType = fileTypes[product?.item_group as keyof typeof fileTypes] || fileTypes.default
                  return <Box
                    key={i}
                    sx={{
                      backgroundColor: fileType.color + '22',
                      // width: 10,
                      // height: 10,
                      borderRadius: 5,
                      display: 'inline-block',
                      marginRight: 5,
                      fontSize: 12,
                      padding: '0 5px',
                      marginTop: 7,
                      color: fileType.color,
                      textTransform: 'uppercase',
                      paddingTop: isOpen ? 5 : undefined
                    }}>
                    {isOpen && <Box
                        onClick={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          if (product?.item_data?.custom_product_url)
                            window.open(product?.item_data?.custom_product_url)
                        }}
                        sx={{
                          display: 'flex',
                          justifyContent: 'center',
                          alignItems: 'center',
                          height: 50,
                          cursor: isOpen ? 'pointer' : undefined,
                        }}
                    >
                        <fileType.icon stroke={1} color={fileType.color} size={30}/>
                    </Box>}
                    <Text>{product?.item}</Text>
                  </Box>
                })}
              </Box>
            </Box>
          </Stack>
        })}
      </Box>
    </Box>
  );
};

export default CmapList;
