/**
 * lib/supabase/client.ts
 * ========================
 * Singleton Supabase client -- pengganti NEXT_PUBLIC_API_BASE_URL sebagai
 * sumber data utama frontend (lihat IMPLEMENTATION_PLAN_SUPABASE_MIGRATION.md).
 *
 * Memakai anon key: AMAN diexpose ke browser karena kelima tabel di
 * schema.sql sudah RLS public-read-only (lihat §11 rencana implementasi).
 * JANGAN PERNAH taruh service_role key di sini atau di variable apa pun
 * berprefix NEXT_PUBLIC_ -- itu prefix yang di-bundle ke browser.
 *
 * Aplikasi ini sepenuhnya publik/anonim (tidak ada login pengguna), jadi
 * @supabase/supabase-js polos sudah cukup -- belum perlu @supabase/ssr.
 */
import { createClient } from "@supabase/supabase-js";

import type { Database } from "./database.types";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    "NEXT_PUBLIC_SUPABASE_URL dan NEXT_PUBLIC_SUPABASE_ANON_KEY wajib di-set di " +
      ".env.local (lihat .env.local.example).",
  );
}

export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey);
