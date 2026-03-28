"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Pencil, Trash2 } from "lucide-react";
import { deleteCompany } from "@/lib/api";
import type { CompanyDetail } from "@/lib/types";
import EditCompanyModal from "./EditCompanyModal";
import DeleteConfirmation from "./DeleteConfirmation";

interface CompanyActionsProps {
  company: CompanyDetail;
}

export default function CompanyActions({ company }: CompanyActionsProps) {
  const router = useRouter();
  const [showEdit, setShowEdit] = useState(false);
  const [showDelete, setShowDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteCompany(company.id);
      router.push("/");
    } catch {
      setDeleting(false);
    }
  }

  return (
    <>
      <div className="flex gap-1">
        <button
          onClick={() => setShowEdit(true)}
          className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          title="Edit company"
        >
          <Pencil className="h-4 w-4" />
        </button>
        <button
          onClick={() => setShowDelete(true)}
          className="rounded-lg p-2 text-gray-400 hover:bg-red-50 hover:text-red-600"
          title="Delete company"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>

      {showEdit && (
        <EditCompanyModal company={company} onClose={() => setShowEdit(false)} />
      )}

      {showDelete && (
        <DeleteConfirmation
          title="Delete Company"
          message={`Are you sure you want to delete "${company.name}"? This will also delete all associated funding rounds. This action cannot be undone.`}
          onConfirm={handleDelete}
          onCancel={() => setShowDelete(false)}
          loading={deleting}
        />
      )}
    </>
  );
}
