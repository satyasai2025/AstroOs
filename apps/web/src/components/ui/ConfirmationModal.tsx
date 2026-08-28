"use client";

import type { ReactNode } from "react";
import { Modal } from "./Modal";
import { Button } from "./Button";

export interface ConfirmationModalProps {
  open: boolean;
  title: string;
  description: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "primary" | "gold";
  isLoading?: boolean;
  error?: string | null;
  onConfirm: () => void;
  onClose: () => void;
}

export function ConfirmationModal({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "primary",
  isLoading = false,
  error = null,
  onConfirm,
  onClose,
}: ConfirmationModalProps) {
  return (
    <Modal
      open={open}
      title={title}
      onClose={isLoading ? undefined : onClose}
      width={460}
      footer={
        <div className="flex w-full items-center justify-end gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            disabled={isLoading}
          >
            {cancelLabel}
          </Button>
          <Button
            variant={variant}
            size="sm"
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? "Processing…" : confirmLabel}
          </Button>
        </div>
      }
    >
      <div className="space-y-3">
        <div className="text-sm text-slate-700 dark:text-slate-300">
          {description}
        </div>
        {error && (
          <div className="rounded-md border border-rose-500/30 bg-rose-500/10 p-2.5 text-xs font-medium text-rose-400">
            {error}
          </div>
        )}
      </div>
    </Modal>
  );
}
