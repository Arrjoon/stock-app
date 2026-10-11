import { PageHeader } from "@/components/layout/page-header";

export default function AdminPage() {
  return (
    <div className="grid gap-6">
      <PageHeader
        kicker="Admin"
        title="Admin"
        description="Watchlist, crawl runs, and user management will be added here."
      />
    </div>
  );
}
