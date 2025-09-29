import { useState, useRef } from 'react'
import './Auth.css'


const Auth = () => {
  const [login, setLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const confirmRef = useRef(null);


  const subLogin = (e) => {
    e.preventDefault();
  };
  const subRegistration = (e) => {
    e.preventDefault();
  
    if (!e.target.checkValidity()) {
      return;
    } else if (confirmPassword != password) {
      confirmRef.current.setCustomValidity("Passwords must match");
      return;
    }
  };

  if (login) {
    return (
      <div>
        <form onSubmit={subLogin}>
          <h1>Login</h1>
          <label>Email</label>
          <input type="email" value={email} required
            onChange={(e) => setEmail(e.target.value)} />
          <label>Password</label>
          <input type="text" value={password} required
            onChange={(e) => setPassword(e.target.value)} />
          <button type="button" onClick={() => setLogin(false)}>
            Register</button>
          <button type="submit">Submit</button>
        </form>
      </div>
    );
  } else {
    return (
      <div>
        <form onSubmit={subRegistration}>
          <h1>Register</h1>
          <label>Email</label>
          <input type="email" value={email} required
            onChange={(e) => setEmail(e.target.value)} />
          <label>Password</label>
          <input type="password" value={password} required
            onChange={(e) => setPassword(e.target.value)} />
          <label>Confirm Password</label>
          <input type="password" value={confirmPassword} required
            onChange={(e) => setConfirmPassword(e.target.value)}
            ref={confirmRef}/>
          <button type="button" onClick={() => setLogin(true)}>
            Login</button>
          <button type="submit">Submit</button>
        </form>
      </div>
    );
  }
}

export default Auth;
