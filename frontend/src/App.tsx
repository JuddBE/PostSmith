import { useEffect, useState } from 'react'
import './App.css'

import Auth from './components/Auth'
import Chat from './components/Chat'

function App() {
  const [authenticated, setAuthenticated] = useState(null);

  // Check credentials
  useEffect(() => {
    checkAuth(setAuthenticated);
  }, []);


  // Waiting for details or failed to log in
  if (authenticated === null) {
    return (
      <>
        <p>Loading...</p>
      </>
    );
  } else if (authenticated == false) {
    return <Auth />;
  }

  // Main app component
  return (
    <>
      <div>
        <Chat />
      </div>
    </>
  );
}

// Check token against server, then give app a status update
const checkAuth = (setAuthenticated) => {
  const token = localStorage.getItem("token");
  if (token) {
    validateToken(token);
  } else {
    setAuthenticated(false);
  }

  const validateToken = () => {
    result = false;
    setAuthenticated(result);
  }
}

export default App
