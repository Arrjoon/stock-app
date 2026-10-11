import { CompanyDashboard } from "@/components/market/company-dashboard";

type Props = {
  params: Promise<{ id: string }>;
};

export default async function CompanyPage({ params }: Props) {
  const { id } = await params;
  return <CompanyDashboard companyKey={id} />;
}
