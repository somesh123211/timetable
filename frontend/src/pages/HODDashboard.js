import { useNavigate } from "react-router-dom";
import { signOut } from "firebase/auth";
import { auth } from "../firebase";

function HODDashboard() {

  const navigate = useNavigate();

  // 🔥 Get user from localStorage
  const user = JSON.parse(localStorage.getItem("user"));

  // ============================
  // 🎯 HANDLE YEAR SELECTION
  // ============================
  const handleSelect = (year) => {

    navigate(`/subjects/${year}`, {
      state: { department: user?.department }
    });
  };

  // ============================
  // ⚡ GENERATE TIMETABLE PAGE
  // ============================
  const handleGenerate = () => {
    navigate("/generate");
  };

  // ============================
  // 🔓 LOGOUT
  // ============================
  const handleLogout = async () => {
    await signOut(auth);
    localStorage.removeItem("user");
    navigate("/");
  };

  // ============================
  // 🖥️ UI
  // ============================

  return (

    <div style={{ textAlign: "center", marginTop: "50px" }}>

      <h2>HOD Dashboard 👑</h2>

      {/* 🔥 USER INFO */}
      <h3>Welcome {user?.name}</h3>
      <p>Department: {user?.department}</p>

      <hr />

      {/* ========================= */}
      {/* 📚 SUBJECT SETUP SECTION */}
      {/* ========================= */}

      <h3>Select Class for Subject Setup</h3>

      <button onClick={() => handleSelect("1st")}>
        1st Year
      </button>
      <br /><br />

      <button onClick={() => handleSelect("2nd")}>
        2nd Year
      </button>
      <br /><br />

      <button onClick={() => handleSelect("3rd")}>
        3rd Year
      </button>
      <br /><br />

      <button onClick={() => handleSelect("4th")}>
        4th Year
      </button>

      <hr style={{ margin: "30px 0" }} />

      {/* ========================= */}
      {/* ⚡ TIMETABLE GENERATION */}
      {/* ========================= */}

      <h3>Timetable Generation</h3>

      <button
        onClick={handleGenerate}
        style={{
          backgroundColor: "#4CAF50",
          color: "white",
          padding: "10px 20px",
          border: "none",
          cursor: "pointer"
        }}
      >
        Generate Timetable ⚡
      </button>

      <br /><br /><br />

      {/* ========================= */}
      {/* 🔓 LOGOUT */}
      {/* ========================= */}

      <button
        onClick={handleLogout}
        style={{
          backgroundColor: "red",
          color: "white",
          padding: "8px 15px",
          border: "none",
          cursor: "pointer"
        }}
      >
        Logout
      </button>

    </div>
  );
}

export default HODDashboard;