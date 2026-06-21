export interface GameDetails {
  team: string;
  opponent: string;
  date: string;
  homeAway: "home" | "away";
  venue: string;
  competition: string;
  season: string;
  scoreFor: string;
  scoreAgainst: string;
  notes: string;
}

export type UploadStatus = "uploading" | "ready" | "error";

export interface UploadItem {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  previewUrl?: string;
  progress: number;
  status: UploadStatus;
  error?: string;
}

const ACCEPTED_EXT = ["mp4", "mov", "webm", "mkv", "m4v", "avi"];

/** Validate a file as an accepted video. Returns an error string or null. */
export function validateVideo(file: File): string | null {
  const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
  const isVideoMime = file.type.startsWith("video/");
  const isAcceptedExt = ACCEPTED_EXT.includes(ext);
  if (!isVideoMime && !isAcceptedExt) {
    return "Unsupported file — upload a video (mp4, mov, webm, mkv).";
  }
  if (file.size > 2 * 1024 * 1024 * 1024) {
    return "File exceeds the 2 GB limit.";
  }
  return null;
}

export const ACCEPT_ATTR = "video/*,.mp4,.mov,.webm,.mkv,.m4v,.avi";
