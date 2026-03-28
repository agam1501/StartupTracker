"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { X } from "lucide-react";
import { updateFundingRound } from "@/lib/api";
import type { FundingRound } from "@/lib/types";

interface EditFundingRoundModalProps {
  round: FundingRound;
  onClose: () => void;
}

export default function EditFundingRoundModal({
  round,
  onClose,
}: EditFundingRoundModalProps) {
  const router = useRouter();
  const [roundType, setRoundType] = useState(round.round_type);
  const [amountUsd, setAmountUsd] = useState(round.amount_usd || "");
  const [valuationUsd, setValuationUsd] = useState(round.valuation_usd || "");
  const [announcedDate, setAnnouncedDate] = useState(round.announced_date || "");
  const [sourceUrl, setSourceUrl] = useState(round.source_url || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!roundType.trim()) return;
    setError("");
    setLoading(true);
    try {
      await updateFundingRound(round.id, {
        round_type: roundType.trim(),
        amount_usd: amountUsd ? Number(amountUsd) : null,
        valuation_usd: valuationUsd ? Number(valuationUsd) : null,
        announced_date: announcedDate || null,
        source_url: sourceUrl.trim() || null,
      });
      router.refresh();
      onClose();
    } catch {
      setError("Failed to update funding round.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Edit Funding Round</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">Round Type</label>
            <input
              type="text"
              required
              value={roundType}
              onChange={(e) => setRoundType(e.target.value)}
              placeholder="Series A, Seed, etc."
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">
                Amount (USD)
              </label>
              <input
                type="number"
                value={amountUsd}
                onChange={(e) => setAmountUsd(e.target.value)}
                placeholder="10000000"
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">
                Valuation (USD)
              </label>
              <input
                type="number"
                value={valuationUsd}
                onChange={(e) => setValuationUsd(e.target.value)}
                placeholder="50000000"
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">Announced Date</label>
            <input
              type="date"
              value={announcedDate}
              onChange={(e) => setAnnouncedDate(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-gray-500">Source URL</label>
            <input
              type="url"
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              placeholder="https://..."
              className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
