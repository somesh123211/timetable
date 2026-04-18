import { useEffect, useState } from "react";
import { collection, getDocs } from "firebase/firestore";
import { db } from "../firebase";

function Dashboard() {

  const [timetable, setTimetable] = useState([]);

  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const teacherId = user?.id;

  const days = ["MON", "TUE", "WED", "THU", "FRI", "SAT"];

  const timeSlots = [
    "9:00-10:00",
    "10:00-11:00",
    "11:15-12:15",
    "12:15-1:15",
    "2:15-3:15",
    "3:15-4:15"
  ];

  const getSlotIndex = (code) => {
    if (!code) return null;
    const num = parseInt(code.replace(/\D/g, ""));
    return isNaN(num) ? null : num - 1;
  };

  // 🔥 CHECK SAME SESSION (IMPORTANT FIX)
  const getSession = (index) => {
    if (index <= 1) return "morning";
    if (index <= 3) return "mid";
    return "afternoon";
  };

  useEffect(() => {

    const fetchTimetable = async () => {

      try {

        if (!teacherId) return;

        const snap = await getDocs(collection(db, "timetables"));
        if (snap.empty) return;

        const latestDoc = snap.docs[snap.docs.length - 1];
        const rawTT = latestDoc.data().timetable;

        let teacherTT = Array(6).fill(0).map(() =>
          Array(6).fill(null)
        );

        const dayOrder = ["day0","day1","day2","day3","day4","day5"];

        dayOrder.forEach((dayKey, dIndex) => {

          const day = rawTT[dayKey];
          if (!day) return;

          Object.values(day).forEach((slot) => {

            if (!slot) return;

            const entriesToCheck = [];

            if (slot.teacherId) entriesToCheck.push(slot);
            if (slot.COMMON) entriesToCheck.push(slot.COMMON);

            ["B1","B2","B3"].forEach(batch => {
              if (slot[batch]) entriesToCheck.push(slot[batch]);
            });

            entriesToCheck.forEach((entry) => {

              if (!entry || entry.teacherId !== teacherId) return;

              let slots = entry.slot;

              if (!Array.isArray(slots)) {
                slots = [slots];
              }

              // 🔥 SORT
              slots = slots
                .map(s => ({
                  code: s,
                  index: getSlotIndex(s)
                }))
                .filter(s => s.index !== null && s.index >= 0 && s.index <= 5)
                .sort((a, b) => a.index - b.index);

              if (slots.length === 0) return;

              let finalSlots = [slots[0]];

              // 🔥 ONLY IF CONTINUOUS + SAME SESSION
              if (
                slots[1] &&
                slots[1].index === slots[0].index + 1 &&
                getSession(slots[0].index) === getSession(slots[1].index)
              ) {
                finalSlots.push(slots[1]);
              }

              finalSlots.forEach((s) => {

                const colIndex = s.index;

                if (!teacherTT[dIndex][colIndex]) {
                  teacherTT[dIndex][colIndex] = [];
                }

                teacherTT[dIndex][colIndex].push({
                  subject: entry.subject,
                  room: entry.room || "Class",
                  type: entry.type
                });

              });

            });

          });

        });

        setTimetable(teacherTT);

      } catch (err) {
        console.error(err);
      }
    };

    fetchTimetable();

  }, [teacherId]);

  return (
    <div style={{ textAlign: "center", marginTop: "30px" }}>

      <h2>Faculty Dashboard 👨‍🏫</h2>
      <p>Welcome: <b>{user?.email}</b></p>

      <br />

      <table style={{ margin: "auto", borderCollapse: "collapse", width: "90%" }} border="1">

        <thead>
          <tr>
            <th>Day</th>
            {timeSlots.map((t, i) => <th key={i}>{t}</th>)}
          </tr>
        </thead>

        <tbody>
          {days.map((day, dIndex) => (
            <tr key={dIndex}>
              <td><b>{day}</b></td>

              {(timetable[dIndex] || Array(6).fill(null)).map((slot, sIndex) => (

                <td key={sIndex} style={{ minWidth: "140px", height: "90px", padding: "6px" }}>

                  {slot ? (

                    (() => {
                      const uniqueEntries = [
                        ...new Map(
                          slot.map(item => [
                            item.subject + item.room + item.type,
                            item
                          ])
                        ).values()
                      ];

                      return uniqueEntries.map((entry, i) => (
                        <div key={i} style={{
                          background: entry.type === "lab" ? "#f8d7a3" : "#cfe2d8",
                          margin: "4px 0",
                          padding: "6px",
                          borderRadius: "6px"
                        }}>
                          <b>{entry.subject}</b><br />
                          {entry.room}
                        </div>
                      ));
                    })()

                  ) : "---"}

                </td>

              ))}

            </tr>
          ))}
        </tbody>

      </table>

    </div>
  );
}

export default Dashboard;