import { useState } from "react";
import { useNavigate } from "react-router-dom";

// 🔥 Firebase imports
import { createUserWithEmailAndPassword } from "firebase/auth";
import { auth, db } from "../firebase";
import { doc, setDoc } from "firebase/firestore";

function Register() {
  const [name, setName] = useState("");
  const [dept, setDept] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState(""); // ✅ NEW

  const navigate = useNavigate();

  const departments = [
    "Civil Engineering",
    "Computer Science and Engineering",
    "Electronics & Telecommunication",
    "Electrical Engineering",
    "Information Technology",
    "Mechanical Engineering",
    "Artificial Intelligence",
    "Computer Science & Engineering (Data Science)",
    "Industrial IOT",
    "Computer Science & Engineering (Cyber Security)",
    "Computer Science and Business Systems(TCS)",
    "Robotics and Artificial Intelligence",
    "1st year (ALL BRANCHES)"
  ];

  const handleRegister = async () => {
    if (!name || !dept || !password || !email) {
      alert("Fill all fields");
      return;
    }

    try {
      // 🔥 Create user in Firebase Auth
      const userCred = await createUserWithEmailAndPassword(auth, email, password);
      const uid = userCred.user.uid;

      // 🔥 Save extra data in Firestore
      await setDoc(doc(db, "users", uid), {
        name,
        email,
        department: dept,
        role: "faculty" // default role
      });

      alert("Registered Successfully 🚀");

      navigate("/"); // go to login

    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div style={{ textAlign: "center" }}>
      <h2>Register</h2>

      <input
        placeholder="Name"
        onChange={(e) => setName(e.target.value)}
      /><br /><br />

      {/* 🔥 NEW EMAIL FIELD */}
      <input
        placeholder="Email"
        onChange={(e) => setEmail(e.target.value)}
      /><br /><br />

      {/* Department Dropdown */}
      <select onChange={(e) => setDept(e.target.value)}>
        <option value="">Select Department</option>
        {departments.map((d, index) => (
          <option key={index} value={d}>{d}</option>
        ))}
      </select><br /><br />

      <input
        type="password"
        placeholder="Password"
        onChange={(e) => setPassword(e.target.value)}
      /><br /><br />

      <button onClick={handleRegister}>Register</button><br /><br />

      <button onClick={() => navigate("/")}>Go to Login</button>
    </div>
  );
}

export default Register;