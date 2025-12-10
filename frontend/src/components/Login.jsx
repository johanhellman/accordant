import React, { useState } from "react";
import { ArrowLeft } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { api } from "../api";
import Logo from "./Logo";
import "./Login.css";

const Login = ({ onBackToLanding }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);

  // Registration Mode: 'default' (just register), 'create_org', 'join_org'
  // For MVP, let's default to 'create_org' or 'join_org' choice if registering?
  // Or keep it simple: Register first, then ask?
  // Let's do it all in one flow for better UX.
  const [regMode, setRegMode] = useState("create_org"); // 'create_org' | 'join_org'

  const [orgName, setOrgName] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [inviteCode, setInviteCode] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { login, register, refreshUser } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isRegistering) {
        // 1. Register
        await register(username, password);

        // 2. Login immediately
        const loginSuccess = await login(username, password);
        if (!loginSuccess) {
          throw new Error("Registration successful, but auto-login failed.");
        }

        // 3. Handle Org Action
        if (regMode === "create_org") {
          if (!orgName || !ownerEmail) {
            // Should be validated by required props, but just in case
            throw new Error("Organization details required");
          }
          await api.createOrg(orgName, ownerEmail);
        } else if (regMode === "join_org") {
          if (!inviteCode) {
            throw new Error("Invite code required");
          }
          await api.joinOrg(inviteCode);
        }

        // 4. Refresh User to get new Org ID and Roles
        await refreshUser();
      } else {
        // Login Flow
        const success = await login(username, password);
        if (!success) {
          throw new Error("Login failed. Please check your credentials.");
        }
      }
    } catch (err) {
      console.error(err);
      setError(err.message || "An error occurred");
      // If registration succeeded but org creation failed, the user is created but in default org/no org.
      // They can login and maybe fix it later?
      // For now, let's just show error.
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        {onBackToLanding && (
          <button
            type="button"
            className="back-to-landing-btn"
            onClick={onBackToLanding}
            disabled={loading}
          >
            <ArrowLeft className="back-icon" />
            Back to Landing Page
          </button>
        )}

        <div className="login-logo">
          <Logo size="lg" />
        </div>

        <h2>{isRegistering ? "Create Account" : "Login"}</h2>
        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          {isRegistering && (
            <div className="registration-options">
              <div className="mode-toggle">
                <button
                  type="button"
                  className={`mode-btn ${regMode === "create_org" ? "active" : ""}`}
                  onClick={() => setRegMode("create_org")}
                >
                  Create Organization
                </button>
                <button
                  type="button"
                  className={`mode-btn ${regMode === "join_org" ? "active" : ""}`}
                  onClick={() => setRegMode("join_org")}
                >
                  Join Existing
                </button>
              </div>

              {regMode === "create_org" && (
                <>
                  <div className="form-group">
                    <label htmlFor="orgName">Organization Name</label>
                    <input
                      type="text"
                      id="orgName"
                      value={orgName}
                      onChange={(e) => setOrgName(e.target.value)}
                      required={isRegistering && regMode === "create_org"}
                      placeholder="My Company"
                      disabled={loading}
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="ownerEmail">Owner Email</label>
                    <input
                      type="email"
                      id="ownerEmail"
                      value={ownerEmail}
                      onChange={(e) => setOwnerEmail(e.target.value)}
                      required={isRegistering && regMode === "create_org"}
                      placeholder="admin@example.com"
                      disabled={loading}
                    />
                  </div>
                </>
              )}

              {regMode === "join_org" && (
                <div className="form-group">
                  <label htmlFor="inviteCode">Invitation Code</label>
                  <input
                    type="text"
                    id="inviteCode"
                    value={inviteCode}
                    onChange={(e) => setInviteCode(e.target.value)}
                    required={isRegistering && regMode === "join_org"}
                    placeholder="Enter code..."
                    disabled={loading}
                  />
                </div>
              )}
            </div>
          )}

          <button type="submit" className="submit-btn btn btn-primary" disabled={loading}>
            {loading ? "Processing..." : isRegistering ? "Register & Continue" : "Login"}
          </button>
        </form>

        <p className="toggle-text">
          {isRegistering ? "Already have an account?" : "Don't have an account?"}{" "}
          <button
            type="button"
            className="toggle-btn"
            onClick={() => {
              setIsRegistering(!isRegistering);
              setError("");
            }}
            disabled={loading}
          >
            {isRegistering ? "Login here" : "Register here"}
          </button>
        </p>
      </div>
    </div>
  );
};

export default Login;
