/**
 * lib/format.ts
 * ==============
 * Port modernisasi dari theme.py::format_idr / format_pct_id / format_number_id
 * (versi Streamlit lama). Hasil akhir HARUS identik -- lihat §5.7
 * implementation plan. Memakai Intl.NumberFormat("id-ID") alih-alih
 * manual string replace seperti versi Python (locale Indonesia native
 * menghasilkan "." pemisah ribuan & "," desimal secara otomatis).
 */

export function formatIdr(value: number | null | undefined, decimals = 0): string {
  if (value == null || Number.isNaN(value)) return "–";
  const formatted = new Intl.NumberFormat("id-ID", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
  return `Rp ${formatted}`;
}

export function formatPctId(
  value: number | null | undefined,
  decimals = 2,
  showSign = true,
): string {
  if (value == null || Number.isNaN(value)) return "–";
  const formatted = new Intl.NumberFormat("id-ID", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
    signDisplay: showSign ? "exceptZero" : "never",
  }).format(value);
  return `${formatted}%`;
}

export function formatNumberId(value: number | null | undefined, decimals = 0): string {
  if (value == null || Number.isNaN(value)) return "–";
  return new Intl.NumberFormat("id-ID", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/** Format tanggal "dd/mm/yyyy" gaya Indonesia dari string ISO date ("2026-08-10"). */
export function formatDateId(value: string | null | undefined): string {
  if (!value) return "–";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "–";
  return new Intl.DateTimeFormat("id-ID", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: "UTC",
  }).format(d);
}

/**
 * Format tanggal & jam sync gaya Indonesia ("21 Sep 2026, 14:30 WIB").
 * Mengunci zona waktu "Asia/Jakarta" agar selalu akurat WIB di mana pun klien berada.
 */
export function formatSyncDateTimeId(value: string | null | undefined): string {
  if (!value) return "–";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "–";

  const datePart = new Intl.DateTimeFormat("id-ID", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Jakarta",
  }).format(d);

  const timePart = new Intl.DateTimeFormat("id-ID", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Jakarta",
  })
    .format(d)
    .replace(".", ":");

  return `${datePart}, ${timePart} WIB`;
}

