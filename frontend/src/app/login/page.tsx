import { PageHeader } from "@/components/layout/page-header";

import { LoginForm } from "./login-form";

export default function LoginPage() {
  return (
    <div className="grid gap-6">
      <PageHeader
        kicker="Auth"
        title="Login"
        description="Sign in with a demo account. Viewer is read-only. Analyst and admin can recategorize news."
      />
      <LoginForm />
    </div>
  );
}
