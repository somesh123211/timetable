import { useState } from "react";
import { collection, getDocs, addDoc, serverTimestamp } from "firebase/firestore";
import { db } from "../firebase";
import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";
import { doc, setDoc, getDoc } from "firebase/firestore";

function GenerateTimetable() {

  const [year, setYear] = useState("");
  const [timetable, setTimetable] = useState(null);
  const [loading, setLoading] = useState(false);
  const [buffer, setBuffer] = useState(null);

  const user = JSON.parse(localStorage.getItem("user")) || {};

  const days = ["M", "T", "W", "TH", "F", "S"];

  const timeSlots = [
    "9:00-10:00",
    "10:00-11:00",
    "11:15-12:15",
    "12:15-1:15",
    "2:15-3:15",
    "3:15-4:15"
  ];

  // =========================
  // GENERATE
  // =========================
  const handleGenerate = async () => {

    if (!year) return alert("Select year");

    setLoading(true);

    try {

      // 🔥 GET SUBJECTS
const snapshot = await getDocs(collection(db, "subjects"));

const subjects = snapshot.docs
  .map(doc => {
    const data = doc.data();

    let facultyId = data.faculty_id;

    if (!facultyId && data.other_faculty_id) {
      facultyId = data.other_faculty_id;
    }

    return {
      ...data,
      faculty_id: facultyId || "",
      subject_name: data.subject_name || "",
      room: data.room || "CLASS"
    };
  })
  .filter(s => s.dept === user?.department && s.year === year);


// 🔥 NEW PART (ADD THIS)
const snapshotTT = await getDocs(collection(db, "timetables"));

const existing = snapshotTT.docs.map(doc => doc.data());

console.log("🔥 Existing Timetables:", existing);


// 🔥 API CALL (UPDATED)
const res = await fetch("http://127.0.0.1:5000/generate", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    subjects,
    existing_timetables: existing   // ✅ IMPORTANT
  })
});

      const data = await res.json();
      setTimetable(data.timetable);

    } catch (err) {
      console.error("Generate Error:", err);
      alert("Backend not running / CORS issue");
    }

    setLoading(false);
  };

  // =========================
  // UPDATE SLOT AFTER SHUFFLE
  // =========================
  const updateSlots = (tt) => {

    return tt.map((day, dIndex) =>
      day.map((slot, sIndex) => {

        if (slot.COMMON) {
          slot.COMMON.slot = `${days[dIndex]}${sIndex + 1}`;
        }

        Object.keys(slot).forEach(k => {
          if (k !== "COMMON" && slot[k]) {

            if (slot[k].type === "lab") {
              slot[k].slot = [
                `${days[dIndex]}${sIndex + 1}`,
                `${days[dIndex]}${sIndex + 2}`
              ];
            } else {
              slot[k].slot = `${days[dIndex]}${sIndex + 1}`;
            }
          }
        });

        return slot;
      })
    );
  };

  // =========================
  // CONVERT ARRAY → OBJECT
  // =========================
  const convertTTToObject = (tt) => {

    const obj = {};

    tt.forEach((day, dIndex) => {
      obj[`day${dIndex}`] = {};

      day.forEach((slot, sIndex) => {
        obj[`day${dIndex}`][`slot${sIndex}`] = slot;
      });
    });

    return obj;
  };

  // =========================
  // DRAG LOGIC
  // =========================
  const handleDragEnd = (result) => {

    if (!result.destination) return;

    const src = result.source.droppableId;
    const dest = result.destination.droppableId;

    const newTT = JSON.parse(JSON.stringify(timetable));

    // TABLE → BUFFER
    if (dest === "buffer" && src !== "buffer") {

      if (!src.includes("-")) return;

      const [d, s] = src.split("-");
      setBuffer(newTT[d][s]);
      newTT[d][s] = { COMMON: null };

      setTimetable(newTT);
      return;
    }

    // BUFFER → TABLE
    if (src === "buffer" && dest !== "buffer") {

      if (!buffer || !dest.includes("-")) return;

      const [d, s] = dest.split("-");
      const temp = newTT[d][s];

      newTT[d][s] = buffer;
      setBuffer(temp || null);

      setTimetable(newTT);
      return;
    }

    // NORMAL SWAP
    if (src !== "buffer" && dest !== "buffer") {

      if (!src.includes("-") || !dest.includes("-")) return;

      const [sDay, sSlot] = src.split("-");
      const [dDay, dSlot] = dest.split("-");

      const temp = newTT[sDay][sSlot];
      newTT[sDay][sSlot] = newTT[dDay][dSlot];
      newTT[dDay][dSlot] = temp;

      setTimetable(newTT);
    }
  };

  // =========================
  // FINALIZE
  // =========================
  

const handleFinalize = async () => {

  if (!timetable) return alert("No timetable");

  const updatedTT = updateSlots(JSON.parse(JSON.stringify(timetable)));
  const safeTT = convertTTToObject(updatedTT);

  const department = user?.department || "unknown";
  const className = year;

  // 🔥 UNIQUE DOC ID
  const docId = `${department}_${className}`;

  const docRef = doc(db, "timetables", docId);

  try {

    // 🔥 CHECK IF ALREADY EXISTS
    const existing = await getDoc(docRef);

    if (existing.exists()) {
      alert("❌ Timetable already finalized for this class.\nDelete it first to regenerate.");
      return;
    }

    // ✅ SAVE ONLY ONCE
    await setDoc(docRef, {
      className,
      department,
      createdBy: user?.id || "guest",
      timetable: safeTT,
      createdAt: serverTimestamp(),
      finalized: true
    });

    alert("✅ Timetable finalized and saved!");

  } catch (err) {
    console.error("Firebase Error:", err);
    alert("❌ Firebase save failed");
  }
};

  return (
    <div style={{ textAlign: "center", marginTop: "30px" }}>

      <h2>Generate Timetable ⚡</h2>

      <select onChange={(e) => setYear(e.target.value)}>
        <option value="">Select Year</option>
        <option value="1st">1st</option>
        <option value="2nd">2nd</option>
        <option value="3rd">3rd</option>
        <option value="4th">4th</option>
      </select>

      <br /><br />

      <button onClick={handleGenerate}>Generate</button>

      {loading && <p>Generating...</p>}

      {timetable && (

        <>
          <DragDropContext onDragEnd={handleDragEnd}>

            {/* BUFFER */}
            <Droppable droppableId="buffer">
              {(provided) => (
                <div ref={provided.innerRef} {...provided.droppableProps}
                  style={{ border: "2px dashed black", padding: "20px", margin: "20px auto", width: "200px" }}>

                  <b>Shuffle Box</b>

                  {buffer && (
                    <Draggable draggableId="buffer-item" index={0}>
                      {(provided) => (
                        <div ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          style={{ background: "#ffc107", padding: "10px" }}>
                          {buffer.COMMON?.subject || "Lab Slot"}
                        </div>
                      )}
                    </Draggable>
                  )}

                  {provided.placeholder}
                </div>
              )}
            </Droppable>

            {/* TABLE */}
            <table border="1" style={{ margin: "auto" }}>
              <thead>
                <tr>
                  <th>Day</th>
                  {timeSlots.map((t, i) => <th key={i}>{t}</th>)}
                </tr>
              </thead>

              <tbody>
                {timetable.map((dayData, dayIndex) => (
                  <tr key={dayIndex}>
                    <td><b>{days[dayIndex]}</b></td>

                    {dayData.map((slot, slotIndex) => (
                      <Droppable key={slotIndex} droppableId={`${dayIndex}-${slotIndex}`}>
                        {(provided) => (
                          <td ref={provided.innerRef} {...provided.droppableProps}>

                            <Draggable draggableId={`${dayIndex}-${slotIndex}`} index={0}>
                              {(provided) => (
                                <div ref={provided.innerRef}
                                  {...provided.draggableProps}
                                  {...provided.dragHandleProps}>

                                  {slot.COMMON && (
                                    <div style={{ background: "#d1e7dd" }}>
                                      {slot.COMMON.subject}
                                    </div>
                                  )}

                                  {Object.keys(slot).map((k) => {
                                    if (k === "COMMON") return null;
                                    const e = slot[k];
                                    if (!e) return null;

                                    return (
                                      <div key={k} style={{ background: "#f8d7da" }}>
                                        {k}: {e.subject}
                                      </div>
                                    );
                                  })}

                                </div>
                              )}
                            </Draggable>

                            {provided.placeholder}

                          </td>
                        )}
                      </Droppable>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>

          </DragDropContext>

          <br />

          <button onClick={handleFinalize}
            style={{ background: "green", color: "white", padding: "10px" }}>
            Finalize ✅
          </button>
        </>
      )}

    </div>
  );
}

export default GenerateTimetable;