const COLORS: Record<string, string> = {
  "Pre-Seed": "bg-purple-100 text-purple-800",
  Seed: "bg-green-100 text-green-800",
  "Series A": "bg-blue-100 text-blue-800",
  "Series B": "bg-indigo-100 text-indigo-800",
  "Series C": "bg-orange-100 text-orange-800",
  "Series D": "bg-red-100 text-red-800",
  Unknown: "bg-gray-100 text-gray-800",
};

export default function Badge({ label }: { label: string }) {
  const color = COLORS[label] || COLORS["Unknown"];
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${color}`}
    >
      {label}
    </span>
  );
}
