import useStudentList from "../components/queries/useStudentList";
export const SchoolCalendar = () => {
    const { data } = useStudentList();
    const schoolName = data?.data?.message[0].school;
    let link = "";
    if (schoolName?.includes?.("Shivane"))
        link = "https://calendar.google.com/calendar/embed?src=walnutedu.in_ndjs5sbbvmet7pql5uo0d7od7k%40group.calendar.google.com&ctz=Asia%2FKolkata";
    if (schoolName?.includes?.("Fursungi"))
        link = "https://calendar.google.com/calendar/embed?src=walnutedu.in_69b68ihorsqas2l6fk8sok67bo%40group.calendar.google.com&ctz=Asia%2FKolkata";
    if (schoolName?.includes?.("Wakad"))
        link = "https://calendar.google.com/calendar/embed?src=c_a891ga1muqinh5jjal0on14hs0%40group.calendar.google.com&ctz=Asia%2FKolkata";

    return (
        <div style={{ overflowX: "auto" }}>
            <iframe
                title="School Calendar"
                src={link}
                style={{
                    border: 0,
                    height: "calc(100vh - 70px)",
                    width: "max(100%, 80vh)",
                }}
                frameBorder="0"
                scrolling="no"
            ></iframe>
        </div>

    );
};


