import { PageHeader } from "@/components/layout/page-header";

export default function LoginPage() {
  return (
    <div className="grid gap-6">
      <PageHeader
        kicker="Auth"
        title="Login"
        description="JWT login will be wired here. Use POST /api/auth/login when the form is added."
      />
    </div>
  );
}
