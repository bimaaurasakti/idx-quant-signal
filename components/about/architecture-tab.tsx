import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Server,
  Clock,
  ShieldAlert,
  CheckCircle2,
  Cpu,
  Layers,
  Sparkles,
} from "lucide-react";

export function ArchitectureTab() {
  return (
    <div className="flex flex-col gap-4">
      {/* Visual Pipeline Flow */}
      <Card className="border-border bg-surface-1">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex size-7 items-center justify-center rounded-md bg-blue-500/10 text-blue-400">
                <Cpu className="size-4" />
              </div>
              <CardTitle className="text-[14.5px] font-semibold text-text-primary">
                Arsitektur Pipeline — &ldquo;1 Sumber Data yang Sama&rdquo;
              </CardTitle>
            </div>
            <Badge variant="outline" className="border-blue-500/30 bg-blue-500/10 text-[11px] text-blue-400">
              Zero-Proxy Architecture
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 text-xs">
          <p className="text-text-secondary leading-relaxed">
            Dashboard ini tidak membebani browser dengan melakukan fetch Yahoo Finance berulang kali tiap kali dibuka. Seluruh pengunjung membaca data langsung dari <strong className="text-text-primary">Supabase PostgreSQL</strong> menggunakan public anon key dengan Row Level Security (RLS) ketat (hanya izin baca).
          </p>

          {/* Visual Step Cards */}
          <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-4">
            <div className="flex flex-col gap-2 rounded-lg border border-border bg-surface-0 p-3">
              <div className="flex items-center justify-between">
                <span className="flex size-6 items-center justify-center rounded-full bg-surface-2 text-[11px] font-bold text-text-primary">
                  1
                </span>
                <Badge variant="outline" className="text-[10px] text-text-secondary">
                  Market Source
                </Badge>
              </div>
              <div className="font-semibold text-text-primary">Yahoo Finance</div>
              <div className="text-[11px] text-text-secondary">
                Data candle harian resmi (OHLCV) seluruh konstituen IDX30, LQ45, dan IHSG (^JKSE).
              </div>
            </div>

            <div className="flex flex-col gap-2 rounded-lg border border-blue-500/30 bg-blue-500/5 p-3">
              <div className="flex items-center justify-between">
                <span className="flex size-6 items-center justify-center rounded-full bg-blue-500/20 text-[11px] font-bold text-blue-400">
                  2
                </span>
                <Badge variant="outline" className="border-blue-500/30 text-[10px] text-blue-400">
                  Worker Engine
                </Badge>
              </div>
              <div className="font-semibold text-text-primary">GitHub Actions</div>
              <div className="text-[11px] text-text-secondary">
                Eksekusi Python: hitung sinyal kuantitatif, trailing SL/TP posisi aktif, dan simpan data via service key.
              </div>
            </div>

            <div className="flex flex-col gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-3">
              <div className="flex items-center justify-between">
                <span className="flex size-6 items-center justify-center rounded-full bg-emerald-500/20 text-[11px] font-bold text-emerald-400">
                  3
                </span>
                <Badge variant="outline" className="border-emerald-500/30 text-[10px] text-emerald-400">
                  Central DB
                </Badge>
              </div>
              <div className="font-semibold text-text-primary">Supabase (PostgreSQL)</div>
              <div className="text-[11px] text-text-secondary">
                Tabel harga historis, sinyal harian, dan posisi aktif tersimpan aman dengan Row Level Security publik.
              </div>
            </div>

            <div className="flex flex-col gap-2 rounded-lg border border-purple-500/30 bg-purple-500/5 p-3">
              <div className="flex items-center justify-between">
                <span className="flex size-6 items-center justify-center rounded-full bg-purple-500/20 text-[11px] font-bold text-purple-400">
                  4
                </span>
                <Badge variant="outline" className="border-purple-500/30 text-[10px] text-purple-400">
                  Client UI
                </Badge>
              </div>
              <div className="font-semibold text-text-primary">Next.js Frontend</div>
              <div className="text-[11px] text-text-secondary">
                Membaca langsung dari Supabase melalui browser tanpa latency backend proxy, menjamin angka selalu sinkron.
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Dual Schedule Execution */}
      <Card className="border-border bg-surface-1">
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <div className="flex size-7 items-center justify-center rounded-md bg-amber-500/10 text-amber-400">
              <Clock className="size-4" />
            </div>
            <CardTitle className="text-[14.5px] font-semibold text-text-primary">
              Model Eksekusi Terjadwal (Dual Workflow Schedule)
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 text-xs">
          <p className="text-text-secondary leading-relaxed">
            Untuk menghindari sinyal palsu dari candle setengah hari bursa, jadwal otomatisasi GitHub Actions dibagi secara disiplin menjadi dua sesi terpisah:
          </p>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {/* Mid-day Session */}
            <div className="flex flex-col gap-2 rounded-lg border border-border bg-surface-0 p-3.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="size-4 text-amber-400" />
                  <span className="font-mono font-semibold text-text-primary">12:37 WIB (Sesi Istirahat)</span>
                </div>
                <Badge variant="outline" className="border-amber-500/30 bg-amber-500/10 text-[10.5px] text-amber-400">
                  --monitor-only
                </Badge>
              </div>
              <p className="text-text-secondary text-[11.5px] leading-relaxed">
                Mode pengawasan murni untuk mengevaluasi posisi aktif (<code className="text-text-primary">OPEN</code>). Memeriksa apakah target <strong className="text-emerald-400">TP1 (+2.0 ATR)</strong> atau Stop Loss tersentuh di sesi 1.
              </p>
              <div className="flex items-center gap-1.5 rounded bg-surface-2/60 p-2 text-[11px] text-amber-300">
                <ShieldAlert className="size-3.5 shrink-0" />
                <span><strong>Proteksi Noise:</strong> Sesi ini DILARANG memicu sinyal BUY baru dari candle setengah hari.</span>
              </div>
            </div>

            {/* EOD Session */}
            <div className="flex flex-col gap-2 rounded-lg border border-emerald-500/30 bg-surface-0 p-3.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="size-4 text-emerald-400" />
                  <span className="font-mono font-semibold text-text-primary">16:34 WIB (Pasca Market Tutup)</span>
                </div>
                <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-[10.5px] text-emerald-400">
                  Master EOD Run
                </Badge>
              </div>
              <p className="text-text-secondary text-[11.5px] leading-relaxed">
                Eksekusi utama harian setelah pasar resmi tutup. Mengambil data candle harian final yang sudah utuh, menghitung indikator lengkap, menguji Market Regime IHSG, dan men-screen sinyal baru jika slot portofolio tersedia.
              </p>
              <div className="flex items-center gap-1.5 rounded bg-surface-2/60 p-2 text-[11px] text-emerald-300">
                <CheckCircle2 className="size-3.5 shrink-0" />
                <span><strong>Validitas Penuh:</strong> Keputusan entri baru hanya diambil berdasarkan data penutupan final resmi.</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Universe & Backtest Lab Status */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <Card className="border-border bg-surface-1">
          <CardContent className="flex flex-col gap-2 p-4 text-xs">
            <div className="flex items-center gap-2 font-semibold text-text-primary">
              <Layers className="size-4 text-blue-400" />
              <span>Universe Saham: IDX30 &amp; LQ45</span>
            </div>
            <p className="text-text-secondary leading-relaxed">
              Dashboard memantau konstituen resmi indeks <strong className="text-text-primary">LQ45</strong> (45 saham paling likuid dan berkapitalisasi besar di BEI) yang otomatis mencakup seluruh <strong className="text-text-primary">30 saham IDX30</strong>. Seluruh saham dipertahankan agar screener tetap memiliki pilihan emiten berkualitas likuiditas tinggi.
            </p>
          </CardContent>
        </Card>

        <Card className="border-border bg-surface-1">
          <CardContent className="flex flex-col gap-2 p-4 text-xs">
            <div className="flex items-center gap-2 font-semibold text-text-primary">
              <Sparkles className="size-4 text-purple-400" />
              <span>Modernisasi Backtest Lab</span>
            </div>
            <p className="text-text-secondary leading-relaxed">
              Modul Backtest Lab sedang dimodernisasi agar dapat menjalankan simulasi interaktif langsung dari tabel harga historis Supabase di sisi client, tanpa memerlukan server komputasi terpisah.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
