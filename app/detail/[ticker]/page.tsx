import { DetailClient } from "./detail-client";

// Next.js 16: `params` adalah Promise (async dynamic API) -- wrapper Server
// Component ini SATU-SATUNYA tempat yang mem-await-nya, lalu meneruskan
// `ticker` sebagai prop biasa ke Client Component yang berisi seluruh hook.
export default async function DetailPage({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker } = await params;
  return <DetailClient ticker={ticker.toUpperCase()} />;
}
