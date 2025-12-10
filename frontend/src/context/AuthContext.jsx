import React, { createContext, useState, useContext, useEffect } from "react";
import { api } from "../api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem("token");
      if (token) {
        api.setToken(token);
        try {
          const userData = await api.getCurrentUser();
          setUser(userData);
        } catch (error) {
          console.error("Failed to load user:", error);
          // If token is invalid, clear it
          localStorage.removeItem("token");
          api.setToken(null);
        }
      }
      setLoading(false);
    };
    loadUser();
  }, []);

  const refreshUser = async () => {
    try {
      const userData = await api.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error("Failed to refresh user:", error);
    }
  };

  const login = async (username, password) => {
    try {
      const data = await api.login(username, password);
      const { access_token } = data;

      if (!access_token) {
        return false;
      }

      localStorage.setItem("token", access_token);
      api.setToken(access_token);

      // Fetch full user details including roles
      const userData = await api.getCurrentUser();
      setUser(userData);
      return true;
    } catch (error) {
      console.error("Login failed:", error);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    api.setToken(null);
    setUser(null);
  };

  const register = async (username, password) => {
    try {
      await api.register(username, password);
      return true;
    } catch (error) {
      console.error("Registration failed:", error);
      // Re-throw the error so callers can access the error message
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, register, refreshUser, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext(AuthContext);
