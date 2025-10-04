// src/pages/Signup.jsx
import React from "react";

function Signup() {
  return (
    <div className="container-fluid vh-100 bg-light">
      <div className="row h-100">

        {/* Left side: branding */}
        <div className="col-md-6 d-flex flex-column justify-content-center align-items-start ps-5 bg-dark text-white">
          <h1 className="fw-bold display-4">PostSmith</h1>
          <p className="lead" style={{ maxWidth: "400px" }}>
            Join PostSmith and take control of your social media.
            Schedule posts, analyze engagement, and optimize your content — all in one place.
          </p>
        </div>

        {/* Right side: form */}
        <div className="col-md-6 d-flex flex-column justify-content-center px-5">
          <h2 className="fw-semibold mb-4 fs-4 text-info">Create Account</h2>

          <form>
            <div className="mb-3">
              <label className="form-label fw-semibold">Full Name</label>
              <input type="text" className="form-control border-0 border-bottom" />
            </div>
            <div className="mb-3">
              <label className="form-label fw-semibold">Email Address</label>
              <input type="email" className="form-control border-0 border-bottom" />
            </div>
            <div className="mb-4">
              <label className="form-label fw-semibold">Password</label>
              <input type="password" className="form-control border-0 border-bottom" />
            </div>
            <button className="btn btn-primary w-100 mb-3">Create Account</button>

            <div className="text-center">
              <span className="text-muted">Already have an account? </span>
              <a href="/login" className="fw-semibold text-info">Sign in →</a>
            </div>
          </form>
        </div>

      </div>
    </div>
  );
}

export default Signup;
