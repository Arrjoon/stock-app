import { PageHeader } from "@/components/layout/page-header";

export default function ComparePage() {
  return (
    <div className="grid gap-6">
      <PageHeader
        kicker="Compare"
        title="Compare companies"
        description="Side-by-side price, volume, and news comparison will be added here."
      />
    </div>
  );
}
