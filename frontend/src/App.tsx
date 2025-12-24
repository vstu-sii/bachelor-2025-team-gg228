import { Suspense, lazy } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { AuthProvider } from "./auth";

const SearchPage = lazy(() => import("./pages/SearchPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const RegisterPage = lazy(() => import("./pages/RegisterPage"));
const AdminPage = lazy(() => import("./pages/AdminPage"));

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Layout>
          <Suspense
            fallback={
              <div className="rounded-3xl border border-white/10 bg-white/5 p-8 text-sm text-slate-300 backdrop-blur">
                Загрузка…
              </div>
            }
          >
            <Routes>
              <Route path="/" element={<SearchPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/panel" element={<AdminPage />} />
            </Routes>
          </Suspense>
        </Layout>
      </BrowserRouter>
    </AuthProvider>
  );
}
