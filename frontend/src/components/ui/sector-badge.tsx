import { cn } from "@/lib/utils";

const SECTOR_COLORS: Record<string, string> = {
  "AI/ML": "bg-violet-100 text-violet-700",
  "Fintech": "bg-emerald-100 text-emerald-700",
  "Healthcare/Biotech": "bg-rose-100 text-rose-700",
  "SaaS/Enterprise": "bg-blue-100 text-blue-700",
  "E-Commerce/Retail": "bg-orange-100 text-orange-700",
  "Climate/Energy": "bg-green-100 text-green-700",
  "Cybersecurity": "bg-red-100 text-red-700",
  "EdTech": "bg-yellow-100 text-yellow-700",
  "Real Estate/PropTech": "bg-amber-100 text-amber-700",
  "Transportation/Logistics": "bg-cyan-100 text-cyan-700",
  "Media/Entertainment": "bg-pink-100 text-pink-700",
  "Food/Agriculture": "bg-lime-100 text-lime-700",
  "Hardware/Robotics": "bg-slate-100 text-slate-700",
  "Crypto/Web3": "bg-indigo-100 text-indigo-700",
  "Other": "bg-gray-100 text-gray-700",
};

export function SectorBadge({ sector }: { sector: string | null }) {
  if (!sector) return null;

  const colorClass = SECTOR_COLORS[sector] || "bg-gray-100 text-gray-700";

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        colorClass
      )}
    >
      {sector}
    </span>
  );
}
