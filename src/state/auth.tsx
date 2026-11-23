import type { JSX } from "@solidjs/web";
import { createContext, createMemo, createSignal, untrack, useContext } from "solid-js";
import { api, configureApiAuth, type Schemas, unwrap } from "@/api/client";
import { useToast } from "@/state/toast";

const TOKEN_KEY = "omnitest_jwt";

function readToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

interface AuthContextValue {
  token: () => string | null;
  user: () => Schemas["UserResponse"] | null;
  isAdmin: () => boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  loginDemo: (role: "student" | "admin") => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>();

export function AuthProvider(props: { children: JSX.Element }) {
  const toast = useToast();
  const [token, setToken] = createSignal<string | null>(readToken());

  const persistToken = (next: string | null) => {
    setToken(next);
    try {
      if (next) localStorage.setItem(TOKEN_KEY, next);
      else localStorage.removeItem(TOKEN_KEY);
    } catch {
      // Ignore restricted storage errors.
    }
  };

  const logout = () => {
    if (untrack(token)) toast.push("Signed out.", "info");
    persistToken(null);
  };

  configureApiAuth(
    () => token(),
    () => persistToken(null),
  );

  const user = createMemo<Schemas["UserResponse"] | null>(async () => {
    const activeToken = token();
    if (!activeToken) return null;
    try {
      return await unwrap(api.GET("/api/v1/auth/me"));
    } catch {
      return null;
    }
  });

  const isAdmin = () => user()?.role === "admin";

  const login = async (email: string, password: string) => {
    const data = await unwrap(api.POST("/api/v1/auth/login", { body: { email, password } }), true);
    persistToken(data.access_token);
    toast.push(`Signed in as ${data.email}`, "success");
  };

  const register = async (email: string, password: string, fullName: string) => {
    const data = await unwrap(
      api.POST("/api/v1/auth/register", { body: { email, password, full_name: fullName } }),
      true,
    );
    persistToken(data.access_token);
    toast.push("Account created! Welcome to OmniTest.", "success");
  };

  const loginDemo = async (role: "student" | "admin") => {
    const email = role === "admin" ? "admin@omnitest.com" : "student@omnitest.com";
    const password = role === "admin" ? "AdminPass123!" : "StudentPass123!";
    await login(email, password);
  };

  return (
    <AuthContext value={{ token, user, isAdmin, login, register, loginDemo, logout }}>{props.children}</AuthContext>
  );
}

export function useAuth(): AuthContextValue {
  return useContext(AuthContext);
}
