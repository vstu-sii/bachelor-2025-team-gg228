import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { getMe } from "./api";

type AuthContextType = {
  token: string | null;
  me: { id: string; email: string; role: string; is_active: boolean } | null;
  setToken: (t: string | null) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(
    localStorage.getItem("token")
  );
  const [me, setMe] = useState<AuthContextType["me"]>(null);

  const setToken = (t: string | null) => {
    setTokenState(t);
    if (t) localStorage.setItem("token", t);
    else localStorage.removeItem("token");
  };

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (!token) {
        setMe(null);
        return;
      }
      try {
        const data = await getMe(token);
        if (!cancelled) setMe(data);
      } catch {
        if (!cancelled) {
          setMe(null);
          setToken(null);
        }
      }
    };
    run();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const value = useMemo(
    () => ({
      token,
      me,
      setToken,
      logout: () => setToken(null),
    }),
    [token, me]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
