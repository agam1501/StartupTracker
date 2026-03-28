"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Pencil, Trash2 } from "lucide-react";
import { deleteFundingRound } from "@/lib/api";
import type { FundingRound } from "@/lib/types";
import EditFundingRoundModal from "./EditFundingRoundModal";
import DeleteConfirmation from "./DeleteConfirmation";

interface FundingRoundActionsProps {
  round: FundingRound;
}

export default function FundingRoundActions({ round }: FundingRoundActionsProps) {
  const router = useRouter();
  const [showEdit, setShowEdit] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteFundingRound(round.id);
      router.refresh();
      setShowDelete(false);
    } catch {
      setDeleting(false);
    }
  }

  return (
    <>
      <div className="flex gap-1">
        <button
          onClick={() => setShowEdit(true)}
          className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          title="Edit round"
        >
          <Pencil className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={() => setShowDelete(true)}
          className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-600"
          title="Delete round"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>

      {showEdit && (
        <EditFundingRoundModal round={round} onClose={() => setShowEdit(false)} />
      )}

      {showDelete && (
        <DeleteConfirmation
          title="Delete Funding Round"
          message={`Delete this ${round.round_type} round? This action cannot be undone.`}
          onConfirm={handleDelete}
          onCancel={() => setShowDelete(false)}
          loading={deleting}
        />
      )}
    </>
  );
}
