import { useParams } from "react-router-dom";
import { useState, useEffect } from "react";

import {
  collection,
  addDoc,
  getDocs,
  deleteDoc,
  doc
} from "firebase/firestore";
import { db } from "../firebase";

function SubjectPage() {

  // ================== ROUTE PARAM ==================
  const { year } = useParams();

  // ================== BASIC STATES ==================
  const [numSubjects, setNumSubjects] = useState(0);
  const [students, setStudents] = useState("");
  const [batches, setBatches] = useState("");
  const [showGrid, setShowGrid] = useState(false);

  // ================== MAIN DATA ==================
  const [subjects, setSubjects] = useState([]);

  // ================== DROPDOWNS ==================
  const [facultyList, setFacultyList] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [rooms, setRooms] = useState([]);

  // ================== LOCK STATE ==================
  const [isLocked, setIsLocked] = useState(true);

  // ================== USER ==================
  const user = JSON.parse(localStorage.getItem("user"));



  // ============================================================
  // 🔥 FETCH USERS + ROOMS (NO CHANGE)
  // ============================================================

  useEffect(() => {

    const fetchData = async () => {

      const usersSnap = await getDocs(collection(db, "users"));
      const roomSnap = await getDocs(collection(db, "rooms"));

      const users = usersSnap.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));

      setAllUsers(users);

      // SAME DEPT FACULTY
      const filteredFaculty = users.filter(
        u =>
          u.role === "faculty" &&
          u.department?.toLowerCase() ===
          user?.department?.toLowerCase()
      );

      setFacultyList(filteredFaculty);

      // ROOMS
      const roomsData = roomSnap.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));

      setRooms(roomsData);

    };

    if (user) fetchData();

  }, [user]);



  // ============================================================
  // 🔥 LOAD SUBJECTS FROM DATABASE (ONLY FIX HERE)
  // ============================================================

  useEffect(() => {

    // ✅ ONLY FIX — STOP FETCH WHEN UNLOCKED
    if (!isLocked) return;

    const fetchSubjects = async () => {

      const snapshot = await getDocs(collection(db, "subjects"));

      const data = snapshot.docs
        .map(doc => ({ id: doc.id, ...doc.data() }))
        .filter(
          s =>
            s.dept === user?.department &&
            s.year === year
        );

      if (data.length > 0) {

        const formatted = data.map(d => ({
          id: d.id,
          name: d.subject_name || "",
          code: d.subject_code || "",
          faculty: d.faculty_id || "",
          otherDept: d.other_department || "",
          otherFaculty: d.other_faculty_id || "",
          type: d.type || "theory",
          room: d.room || "",
          batchRequired: d.batch_required || "no",
          hours: String(d.hours || "")
        }));

        setSubjects(formatted);
        setShowGrid(true);

        setStudents(data[0].students);
        setBatches(data[0].batches);
      }
    };

    if (user) fetchSubjects();

  }, [user, year, isLocked]); // 🔥 dependency added



  // ============================================================
  // 🧱 CREATE GRID
  // ============================================================

  const createGrid = () => {

    let arr = [];

    for (let i = 0; i < numSubjects; i++) {
      arr.push({
        name: "",
        code: "",
        faculty: "",
        otherDept: "",
        otherFaculty: "",
        type: "theory",
        room: "",
        batchRequired: "no",
        hours: ""
      });
    }

    setSubjects(arr);
    setShowGrid(true);
    setIsLocked(false);
  };



  // ============================================================
  // ✏️ HANDLE CHANGE
  // ============================================================

  const handleChange = (index, field, value) => {

    if (isLocked) return;

    setSubjects(prev => {

      const updated = [...prev];

      updated[index] = {
        ...updated[index],
        [field]: value
      };

      return updated;
    });
  };



  // ============================================================
  // 🔥 SAVE DATA
  // ============================================================

  const handleSave = async () => {

    try {

      const snapshot = await getDocs(collection(db, "subjects"));

      const oldDocs = snapshot.docs.filter(
        d =>
          d.data().dept === user?.department &&
          d.data().year === year
      );

      // DELETE OLD
      for (let d of oldDocs) {
        await deleteDoc(doc(db, "subjects", d.id));
      }

      // INSERT NEW
      for (let sub of subjects) {

        await addDoc(collection(db, "subjects"), {

          dept: user?.department,
          year,
          students,
          batches,

          subject_name: sub.name,
          subject_code: sub.code,

          faculty_id: sub.faculty || null,
          other_department: sub.otherDept || null,
          other_faculty_id: sub.otherFaculty || null,

          type: sub.type,
          room: sub.room,
          batch_required: sub.batchRequired,

          hours: Number(sub.hours)
        });
      }

      alert("Saved successfully ✅");

      setIsLocked(true);

    } catch (err) {
      console.error(err);
      alert("Error saving");
    }
  };



  // ============================================================
  // 🖥️ UI
  // ============================================================

  return (

    <div style={{ textAlign: "center", marginTop: "30px" }}>

      <h2>{year} Year - Subject Setup</h2>



      {/* LOCK / UNLOCK */}
      {showGrid && (
        <>
          {isLocked ? (
            <button onClick={() => setIsLocked(false)}>🔓 Unlock</button>
          ) : (
            <button onClick={() => setIsLocked(true)}>🔒 Lock</button>
          )}
          <br /><br />
        </>
      )}



      {/* STEP 1 */}
      {!showGrid && (
        <>
          <input
            placeholder="No of Subjects"
            onChange={(e) => setNumSubjects(e.target.value)}
          /><br /><br />

          <input
            placeholder="Students"
            onChange={(e) => setStudents(e.target.value)}
          /><br /><br />

          <input
            placeholder="Batches"
            onChange={(e) => setBatches(e.target.value)}
          /><br /><br />

          <button onClick={createGrid}>Next</button>
        </>
      )}



      {/* GRID */}
      {showGrid && (
        <>
          <table border="1" style={{ margin: "auto" }}>

            <thead>
              <tr>
                <th>Name</th>
                <th>Code</th>
                <th>Faculty</th>
                <th>Other Dept</th>
                <th>Other Faculty</th>
                <th>Type</th>
                <th>Room</th>
                <th>Batch</th>
                <th>Hours</th>
              </tr>
            </thead>



            <tbody>
              {subjects.map((sub, index) => {

                const filteredRooms = rooms.filter(r =>
                  sub.type === "lab"
                    ? r.type === "lab"
                    : r.type === "classroom"
                );

                const otherFacultyList = allUsers.filter(
                  u =>
                    u.role === "faculty" &&
                    u.department === sub.otherDept
                );

                return (

                  <tr key={index}>

                    <td>
                      <input
                        value={sub.name || ""}
                        disabled={isLocked}
                        onChange={(e) =>
                          handleChange(index, "name", e.target.value)
                        }
                      />
                    </td>

                    <td>
                      <input
                        value={sub.code || ""}
                        disabled={isLocked}
                        onChange={(e) =>
                          handleChange(index, "code", e.target.value)
                        }
                      />
                    </td>

                    <td>
                      <select
                        value={sub.faculty || ""}
                        disabled={isLocked}
                        onChange={(e) =>
                          handleChange(index, "faculty", e.target.value)
                        }
                      >
                        <option value="">Select</option>
                        {facultyList.map(f => (
                          <option key={f.id} value={f.id}>{f.name}</option>
                        ))}
                      </select>
                    </td>

                    <td>
                      <select
                        value={sub.otherDept || ""}
                        disabled={isLocked}
                        onChange={(e) =>
                          handleChange(index, "otherDept", e.target.value)
                        }
                      >
                        <option value="">Select</option>
                        {[...new Set(allUsers.map(u => u.department))].map(d => (
                          <option key={d}>{d}</option>
                        ))}
                      </select>
                    </td>

                    <td>
                      <select
                        value={sub.otherFaculty || ""}
                        disabled={isLocked}
                        onChange={(e) =>
                          handleChange(index, "otherFaculty", e.target.value)
                        }
                      >
                        <option value="">Select</option>
                        {otherFacultyList.map(f => (
                          <option key={f.id} value={f.id}>{f.name}</option>
                        ))}
                      </select>
                    </td>

                    <td>
                      <select
                        value={sub.type}
                        disabled={isLocked}
                        onChange={(e) =>
                          handleChange(index, "type", e.target.value)
                        }
                      >
                        <option value="theory">Theory</option>
                        <option value="lab">Lab</option>
                      </select>
                    </td>

                    <td>
                      <select
                        value={sub.room || ""}
                        disabled={isLocked}
                        onChange={(e) =>
                          handleChange(index, "room", e.target.value)
                        }
                      >
                        <option value="">Select</option>
                        {filteredRooms.map(r => (
                          <option key={r.id}>{r.name}</option>
                        ))}
                      </select>
                    </td>

                    <td>
                      <select
                        value={sub.batchRequired}
                        disabled={isLocked}
                        onChange={(e) =>
                          handleChange(index, "batchRequired", e.target.value)
                        }
                      >
                        <option value="no">No</option>
                        <option value="yes">Yes</option>
                      </select>
                    </td>

                    <td>
                      <input
                        type="number"
                        value={sub.hours || ""}
                        disabled={isLocked}
                        onChange={(e) =>
                          handleChange(index, "hours", e.target.value)
                        }
                      />
                    </td>

                  </tr>
                );
              })}
            </tbody>

          </table>

          <br />

          {!isLocked && (
            <button onClick={handleSave}>Save Changes</button>
          )}
        </>
      )}

    </div>
  );
}

export default SubjectPage;