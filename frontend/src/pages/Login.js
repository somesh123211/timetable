import { useState } from "react";
import { useNavigate } from "react-router-dom";

// 🔥 Firebase imports
import { signInWithEmailAndPassword } from "firebase/auth";
import { auth, db } from "../firebase";
import { doc, getDoc } from "firebase/firestore";

function Login() {

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const navigate = useNavigate();

  // ============================
  // 🔐 HANDLE LOGIN
  // ============================

  const handleLogin = async () => {

    if (!email || !password) {
      alert("Enter email & password");
      return;
    }

    try {
      // 🔥 Firebase Auth
      const userCred = await signInWithEmailAndPassword(auth, email, password);
      const uid = userCred.user.uid;

      // 🔥 Firestore fetch
      const docRef = doc(db, "users", uid);
      const docSnap = await getDoc(docRef);

      if (!docSnap.exists()) {
        alert("User data not found in database");
        return;
      }

      const userData = docSnap.data();

      // 🔍 DEBUG (VERY IMPORTANT)
      console.log("🔥 FULL USER DATA:", userData);
      console.log("🔥 UID:", uid);

      // ✅ FINAL USER OBJECT (FIXED)
      const finalUser = {
        id: uid,                          // ✅ used in timetable matching
        email: userData.email,
        name: userData.name,
        role: userData.role,
        department: userData.department || ""   // ✅ FIX ADDED
      };

      // 🔥 SAVE TO LOCAL STORAGE
      localStorage.setItem("user", JSON.stringify(finalUser));

      alert("Login successful 🚀");

      // ============================
      // 🚀 ROLE BASED NAVIGATION
      // ============================

      if (
        email.toLowerCase().startsWith("hod") ||
        userData.role === "hod"
      ) {
        navigate("/hod-dashboard");
      } else {
        navigate("/dashboard");
      }

    } catch (err) {
      console.error(err);
      alert("Login failed: " + err.message);
    }
  };

  // ============================
  // 🖥️ UI
  // ============================

  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
      <h2>Login</h2>

      {/* EMAIL */}
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <br /><br />

      {/* PASSWORD */}
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <br /><br />

      <button onClick={handleLogin}>Login</button>

      <br /><br />

      <button onClick={() => navigate("/register")}>
        Go to Register
      </button>
    </div>
  );
}

export default Login;