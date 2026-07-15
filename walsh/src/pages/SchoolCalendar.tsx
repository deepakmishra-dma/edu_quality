import useStudentList from "../components/queries/useStudentList";
export const SchoolCalendar = () => {
  const { data } = useStudentList();
  // Calendar embed URL is provided per-school by the backend (School record),
  // so no tenant-specific calendar IDs are hardcoded here.
  const link = data?.data?.message?.[0]?.school_calendar_url || "";

  return (
    <div style={{}}>
      <iframe
        title="School Calendar"
        src={link}
        style={{
          border: 0,
          height: "calc(100vh - 70px)",
          width: "100%",
        }}
        frameBorder="0"
        scrolling="no"
      ></iframe>
    </div>
  );
};
