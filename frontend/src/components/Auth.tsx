import { useEffect, useState, useRef } from 'react';

import './Auth.css';


type AuthProps = {
  setToken: React.Dispatch<React.SetStateAction<string | null>>
};
const Auth = ({ setToken } : AuthProps) => {
  const [login, setLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const confirmRef = useRef<HTMLInputElement | null>(null);

  // Check that passwords are equal
  useEffect(() => {
    confirmRef.current?.setCustomValidity(
      confirmPassword != password ? "Passwords must match" : ""
    );
  }, [confirmPassword]);

  // Attempt to login
  const subLogin: React.FormEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();

    // Send info to API
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        "email": email,
        "password": password
      })
    });
    const body = await response.json();

    // Request failed
    if (response.status != 200) {
      alert(body.detail);
      return;
    }

    localStorage.setItem("token", body.token);
    setToken(body.token);
  };

  // Attempt to create an account
  const subRegistration: React.FormEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();

    // Check form
    if (!e.currentTarget.checkValidity()) {
      return;
    }

    // Send info to API
    const response = await fetch("/api/auth/register", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        "email": email,
        "password": password
      })
    });
    const body = await response.json();

    // Request failed
    if (response.status != 200) {
      alert(body.detail);
      return;
    }

    localStorage.setItem("token", body.token);
    setToken(body.token);
  };


  // Graphics
  if (login) {
    // Display a login screen
    return (
      <div>
        <form onSubmit={subLogin}>
          <h1>Login</h1>
          <input type="email" value={email} placeholder="Email" required
            onChange={(e) => setEmail(e.target.value)} />
          <input type="password" value={password} placeholder="Password" required
            onChange={(e) => setPassword(e.target.value)} />
          <button className="submit" type="submit">Submit</button>
          <p>Don't have an account?</p>
          <button className="switch" type="button" onClick={() => setLogin(false)}>
            Register</button>
        </form>
      </div>
    );
  } else {
    // Display a registration screen
    return (
      <div>
        <form onSubmit={subRegistration}>
          <h1>Register</h1>
          <input type="email" value={email} placeholder="Email" required
            onChange={(e) => setEmail(e.target.value)} />
          <input type="password" value={password} placeholder="Password" required
            onChange={(e) => setPassword(e.target.value)} />
          <input type="password" value={confirmPassword}
            placeholder="Confirm Password" required
            onChange={(e) => setConfirmPassword(e.target.value)}
            ref={confirmRef}/>
          <button className="submit" type="submit">Submit</button>
          <p>Already have an account?</p>
          <button className="switch" type="button" onClick={() => setLogin(true)}>
            Login</button>
        </form>
      </div>
    );
  }
}

export default Auth;
