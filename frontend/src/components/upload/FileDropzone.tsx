import { useRef, useState, type DragEvent, type KeyboardEvent } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  CircleCheckBig,
  CloudUpload,
  Film,
  LoaderCircle,
  Plus,
  TriangleAlert,
  Trash2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { formatBytes } from "@/lib/format";
import { ACCEPT_ATTR, type UploadItem } from "./types";

interface FileDropzoneProps {
  items: UploadItem[];
  onAddFiles: (files: File[]) => void;
  onRemove: (id: string) => void;
  error?: string | null;
}

export function FileDropzone({
  items,
  onAddFiles,
  onRemove,
  error,
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const openPicker = () => inputRef.current?.click();

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files?.length) {
      onAddFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleKey = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openPicker();
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload game film. Drag and drop a video file or activate to browse."
        onClick={openPicker}
        onKeyDown={handleKey}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragEnter={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setDragging(false);
        }}
        onDrop={handleDrop}
        className={cn(
          "group relative flex cursor-pointer flex-col items-center justify-center gap-3 overflow-hidden rounded-2xl border border-dashed px-6 py-12 text-center transition-colors",
          dragging
            ? "border-accent/60 bg-accent/[0.05]"
            : "border-line-strong bg-surface-2/40 hover:border-accent/40 hover:bg-surface-2/70",
        )}
      >
        {/* dot grid + glow texture, consistent with app shell */}
        <div className="bg-dot-grid pointer-events-none absolute inset-0 opacity-50" />
        <div
          className={cn(
            "pointer-events-none absolute left-1/2 top-1/2 h-40 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(ellipse_at_center,rgba(194,242,74,0.14),transparent_70%)] blur-xl transition-opacity",
            dragging ? "opacity-100" : "opacity-0 group-hover:opacity-60",
          )}
        />

        <span
          className={cn(
            "relative grid h-12 w-12 place-items-center rounded-xl border border-line bg-surface text-accent transition-transform",
            dragging && "scale-110",
          )}
        >
          <CloudUpload className="h-5 w-5" />
        </span>
        <div className="relative">
          <p className="text-sm font-medium text-ink">
            {dragging ? "Drop to upload" : "Drag & drop game film"}
          </p>
          <p className="mt-1 text-xs text-muted">
            or{" "}
            <span className="font-medium text-accent">browse your files</span> ·
            MP4, MOV, WEBM, MKV up to 2 GB
          </p>
        </div>

        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT_ATTR}
          multiple
          className="sr-only"
          onChange={(e) => {
            if (e.target.files?.length) {
              onAddFiles(Array.from(e.target.files));
            }
            e.target.value = "";
          }}
        />
      </div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="flex items-center gap-2 rounded-lg border border-neg/25 bg-neg/10 px-3 py-2 text-xs text-neg"
          >
            <TriangleAlert className="h-3.5 w-3.5 shrink-0" />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* File list */}
      <AnimatePresence initial={false}>
        {items.map((item) => (
          <motion.div
            key={item.id}
            layout
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.25 }}
            className={cn(
              "flex items-center gap-3 rounded-xl border bg-surface/70 p-3",
              item.status === "error"
                ? "border-neg/30"
                : "border-line",
            )}
          >
            {/* preview / thumb */}
            <div className="relative grid h-14 w-20 shrink-0 place-items-center overflow-hidden rounded-lg border border-line bg-base">
              {item.previewUrl ? (
                <video
                  src={item.previewUrl}
                  muted
                  playsInline
                  preload="metadata"
                  className="h-full w-full object-cover"
                />
              ) : (
                <Film className="h-5 w-5 text-faint" />
              )}
            </div>

            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2">
                <p className="truncate text-sm font-medium text-ink">
                  {item.name}
                </p>
                <button
                  type="button"
                  onClick={() => onRemove(item.id)}
                  className="grid h-7 w-7 shrink-0 place-items-center rounded-md text-faint transition-colors hover:bg-white/[0.05] hover:text-neg"
                  aria-label={`Remove ${item.name}`}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>

              <div className="mt-0.5 flex items-center gap-2 text-[11px] text-faint">
                <span className="tnum">{formatBytes(item.size)}</span>
                <span className="h-0.5 w-0.5 rounded-full bg-faint" />
                {item.status === "uploading" && (
                  <span className="flex items-center gap-1 text-muted">
                    <LoaderCircle className="h-3 w-3 animate-spin" />
                    Uploading {Math.round(item.progress)}%
                  </span>
                )}
                {item.status === "ready" && (
                  <span className="flex items-center gap-1 text-pos">
                    <CircleCheckBig className="h-3 w-3" />
                    Ready
                  </span>
                )}
                {item.status === "error" && (
                  <span className="flex items-center gap-1 text-neg">
                    <TriangleAlert className="h-3 w-3" />
                    {item.error ?? "Failed"}
                  </span>
                )}
              </div>

              {item.status !== "error" && (
                <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/[0.06]">
                  <motion.div
                    className={cn(
                      "h-full rounded-full",
                      item.status === "ready" ? "bg-pos" : "bg-accent",
                    )}
                    initial={false}
                    animate={{ width: `${item.progress}%` }}
                    transition={{ ease: "easeOut", duration: 0.3 }}
                  />
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      {items.length > 0 && (
        <button
          type="button"
          onClick={openPicker}
          className="flex items-center justify-center gap-1.5 rounded-lg border border-line bg-surface-2/40 py-2 text-xs font-medium text-muted transition-colors hover:border-line-strong hover:text-ink"
        >
          <Plus className="h-3.5 w-3.5" />
          Add another clip
        </button>
      )}
    </div>
  );
}
