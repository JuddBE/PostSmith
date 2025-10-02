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
          <input type="email" value={email} placeholder="Email" required
            onChange={(e) => setEmail(e.target.value)} />
          <input type="text" value={password} placeholder="Password" required
            onChange={(e) => setPassword(e.target.value)} />
          <button class="submit" type="submit">Submit</button>
          <p>Don't have an account?</p>
          <button class="switch" type="button" onClick={() => setLogin(false)}>
            Register</button>
        </form>
      </div>
    );
  } else {
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
          <button class="submit" type="submit">Submit</button>
          <p>Already have an account?</p>
          <button class="switch" type="button" onClick={() => setLogin(true)}>
            Login</button>
        </form>
      </div>
    );
  }
}

export default Auth;
