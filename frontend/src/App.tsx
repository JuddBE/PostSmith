import { useEffect, useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import './App.css'

import Auth from './components/Auth'
import Chat from './components/Chat'



function App() {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On token change, try authenticating
  useEffect(() => {
    // No initial token
    if (token === null) {
      setLoading(false);
      return
    }

    // Use token to request user information
    const requestData = async () => {
      setLoading(true);
      const response = await fetch("/api/auth/token", {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
      const body = await response.json();

      if (response.status == 200) {
        setUser(body);
      } else {
        localStorage.removeItem("token");
      }
      setLoading(false);
    };

    // Call the async behavior
    requestData();
  }, [token]);

  // Waiting on response
  if (loading) {
    return (<h2>Loading...</h2>);
  }

  // App routing
  return (
    <Router>
      {user !== null ? (
        // Accessible to people with accounts
        <Routes>
          <Route path="/*" element={<Chat user={user} />} />
        </Routes>
      ) : (
        // Accessible to people without accounts
        <Routes>
          <Route path="/*" element={<Auth setToken={setToken} />} />
        </Routes>
      )}
    </Router>
  );
}


export default App;
