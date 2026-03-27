import { Rss } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import SourceForm from "@/components/SourceForm";
import SourceToggle from "@/components/SourceToggle";
import { getSources } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { MonitoredSource } from "@/lib/types";

export default async function SourcesPage() {
  let sources: MonitoredSource[] = [];
  let error: string | null = null;

  try {
    const data = await getSources({ page_size: 100 });
    sources = data.items;
  } catch {
    error = "Failed to load sources. Is the backend running?";
  }

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Sources</h1>
        <p className="text-sm text-gray-500">
          Manage monitored RSS feeds and webpages.
        </p>
      </div>

      <div className="mb-6">
        <SourceForm />
      </div>

      {error ? (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4 text-sm text-red-700">{error}</CardContent>
        </Card>
      ) : sources.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <Rss className="mb-4 h-12 w-12 text-gray-300" />
          <p className="text-lg font-medium text-gray-900">No sources yet</p>
          <p className="mt-1 text-sm text-gray-500">
            Add an RSS feed or webpage above to start monitoring.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  URL
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Type
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Last Checked
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Active
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {sources.map((source) => (
                <tr key={source.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                    {source.name}
                  </td>
                  <td className="max-w-xs truncate px-4 py-3 text-sm text-gray-500">
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      {source.url.replace(/^https?:\/\//, "")}
                    </a>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        source.source_type === "rss"
                          ? "bg-orange-100 text-orange-700"
                          : "bg-purple-100 text-purple-700"
                      }`}
                    >
                      {source.source_type === "rss" ? "RSS" : "Webpage"}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                    {source.last_checked_at
                      ? formatDate(source.last_checked_at)
                      : "Never"}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3">
                    <SourceToggle
                      sourceId={source.id}
                      initialActive={source.active}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
