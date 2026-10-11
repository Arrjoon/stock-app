import { PageHeader } from "@/components/layout/page-header";

type Props = {
  params: Promise<{ id: string }>;
};

export default async function CompanyPage({ params }: Props) {
  const { id } = await params;

  return (
    <div className="grid gap-6">
      <PageHeader
        kicker="Company"
        title={id.toUpperCase()}
        description="Prices, news, and behavior summary will appear on this page."
      />
    </div>
  );
}
