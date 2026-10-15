import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('securecare_token') || null);
  const [loading, setLoading] = useState(true);

  // Initialize and check current user
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('securecare_token');
      if (storedToken) {
        try {
          const res = await api.get('/auth/me');
          setUser(res.data);
        } catch (err) {
          console.error("Token verification failed:", err);
          localStorage.removeItem('securecare_token');
          localStorage.removeItem('securecare_user');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (username_or_email, password) => {
    const res = await api.post('/auth/login', {
      username: username_or_email,
      password,
    });
    const accessToken = res.data.access_token;
    localStorage.setItem('securecare_token', accessToken);
    setToken(accessToken);

    // Fetch user profile
    const profileRes = await api.get('/auth/me');
    setUser(profileRes.data);
    localStorage.setItem('securecare_user', JSON.stringify(profileRes.data));
    return profileRes.data;
  };

  const register = async (payload) => {
    await api.post('/auth/register', payload);
    // Automatically log in following registration
    return await login(payload.username, payload.password);
  };

  const logout = () => {
    localStorage.removeItem('securecare_token');
    localStorage.removeItem('securecare_user');
    setToken(null);
    setUser(null);
  };

  // Instant Persona Switcher for evaluation and demo
  const switchPersona = async (persona) => {
    const creds = {
      admin: { user: 'admin', pass: 'AdminSecure123!' },
      doctor: { user: 'dr_priya', pass: 'DoctorSecure123!' },
      patient: { user: 'manual_patient', pass: 'PatientSecure123!' },
    };

    const target = creds[persona.toLowerCase()];
    if (!target) return;

    return await login(target.user, target.pass);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user?.role || null,
        token,
        isAuthenticated: !!user,
        loading,
        login,
        register,
        logout,
        switchPersona,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
