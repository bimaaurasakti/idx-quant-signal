import { Card, CardContent } from "@/components/ui/card";
import { PageHeader } from "@/components/shared/page-header";

const SECTION_CLASS = "flex flex-col gap-2 text-[13.5px] leading-relaxed text-text-secondary";
const H3_CLASS = "text-[15px] font-semibold text-text-primary";

export default function AboutPage() {
  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="ℹ️ Metodologi & Batasan Jujur" />

      <Card>
        <CardContent className={SECTION_CLASS}>
          <h3 className={H3_CLASS}>Arsitektur — kenapa &ldquo;1 sumber data yang sama&rdquo;?</h3>
          <p>
            Dashboard ini tidak melakukan fetch yfinance sendiri tiap kali dibuka. Frontend
            membaca data <strong className="text-text-primary">langsung dari Supabase</strong>{" "}
            lewat <code>@supabase/supabase-js</code> (anon key, dibatasi Row Level Security yang
            cuma mengizinkan baca) — tanpa backend API terpisah di tengah. Alurnya:
          </p>
          <pre className="overflow-x-auto rounded-md border border-border bg-surface-2 p-3 font-mono text-[11.5px] leading-6 text-text-secondary">
{`GitHub Actions (cron, ~16:30 WIB tiap hari bursa)
        |
        v
worker_fetch_and_update.py  ->  fetch yfinance, hitung sinyal + backtest
        |
        v   (tulis via service_role key, bypass RLS)
   Supabase (Postgres + PostgREST, RLS baca-publik)
        |
        v   (baca via anon key, langsung dari browser)
Next.js frontend (dashboard ini)  ->  @supabase/supabase-js langsung`}
          </pre>
          <p>
            Semua pengunjung — siapa pun, kapan pun — melihat angka yang persis sama, karena
            semua membaca dari tabel yang sama pula. Ini juga menghindari setiap pengunjung
            memicu rate limit Yahoo Finance sendiri-sendiri.
          </p>
          <p>
            <strong className="text-text-primary">🧪 Backtest Lab</strong> sedang dalam
            pengembangan ulang. Sebelumnya dihitung oleh backend terpisah; sekarang sedang
            dipindahkan supaya bisa jalan langsung dari data harga historis di Supabase tanpa
            backend tambahan. Sementara proses ini berlangsung, halamannya nonaktif — bagian lain
            dashboard tidak terpengaruh sama sekali.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className={SECTION_CLASS}>
          <h3 className={H3_CLASS}>🎯 Universe Saham: IDX30 &amp; LQ45</h3>
          <p>
            Dashboard ini secara default HANYA memantau saham-saham yang menjadi konstituen resmi indeks{" "}
            <strong className="text-text-primary">LQ45</strong> (45 saham paling likuid &amp;
            berkapitalisasi besar di BEI) — yang otomatis mencakup seluruh{" "}
            <strong className="text-text-primary">30 saham IDX30</strong>.
          </p>
          <p>
            BEI me-review &amp; me-rebalance komposisi kedua indeks ini setiap kuartal. Anda tetap bisa
            menambah saham lain di luar universe default lewat <code>custom_tickers.txt</code>.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className={SECTION_CLASS}>
          <h3 className={H3_CLASS}>Bagaimana sinyal dihasilkan? (Screener &amp; Detail Saham)</h3>
          <p>
            Multi-confirmation signal: BUY/SELL hanya muncul kalau minimal 2 dari 3 kondisi searah —{" "}
            <strong className="text-text-primary">Trend</strong> (harga &gt; SMA50 &gt; SMA200),{" "}
            <strong className="text-text-primary">Momentum</strong> (MACD cross + RSI di zona sehat),{" "}
            <strong className="text-text-primary">Volume</strong> (≥20% di atas rata-rata 20 hari).
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className={SECTION_CLASS}>
          <h3 className={H3_CLASS}>Bagaimana &ldquo;Ongoing Position&rdquo; bekerja?</h3>
          <ol className="list-decimal space-y-1 pl-5">
            <li>
              Sinyal BUY muncul di penutupan hari ini → status <strong className="text-text-primary">PENDING_ENTRY</strong>.
            </li>
            <li>
              Hari bursa berikutnya, worker eksekusi entry di harga <strong className="text-text-primary">Open</strong> →
              status <strong className="text-text-primary">OPEN</strong>, TP/SL dihitung dari ATR saat sinyal muncul
              (TP = entry + 2×ATR, SL = entry − 1×ATR).
            </li>
            <li>
              Setiap hari bursa, worker cek TP/SL/sinyal SELL/batas waktu (20 hari bursa) → posisi ditutup,
              otomatis hilang dari &ldquo;Ongoing Position&rdquo;.
            </li>
          </ol>
          <p>
            <strong className="text-text-primary">Dua aturan keras yang selalu dijaga</strong>: Long-only
            (sinyal SELL tidak pernah membuka posisi baru), dan maks 1 posisi aktif per emiten.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className={SECTION_CLASS}>
          <h3 className={H3_CLASS}>Kamus istilah</h3>
          <ul className="list-disc space-y-1 pl-5">
            <li><strong className="text-text-primary">Winrate</strong>: % trade yang profit dari seluruh trade historis.</li>
            <li><strong className="text-text-primary">Expectancy</strong>: (winrate × avg profit) − (lossrate × avg loss).</li>
            <li><strong className="text-text-primary">Profit Factor</strong>: total profit ÷ total loss. &gt;1 = profitable secara agregat.</li>
            <li><strong className="text-text-primary">Max Drawdown</strong>: penurunan terbesar puncak-ke-lembah pada equity curve backtest.</li>
            <li><strong className="text-text-primary">Total Return (Sum)</strong>: SUM(return_pct) seluruh trade historis, tidak dikompund.</li>
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardContent className={SECTION_CLASS}>
          <h3 className={H3_CLASS}>Kenapa ini BUKAN &ldquo;kelas Renaissance Technologies&rdquo;</h3>
          <ul className="list-disc space-y-1 pl-5">
            <li><strong className="text-text-primary">Data</strong>: yfinance = data harian/delayed. RenTech pakai data tick-by-tick, order book, dan data alternatif eksklusif puluhan tahun.</li>
            <li><strong className="text-text-primary">Eksekusi</strong>: dashboard ini tidak terhubung ke broker — sinyal dieksekusi manual.</li>
            <li><strong className="text-text-primary">Riset</strong>: strategi di sini trend-following klasik yang dikenal luas.</li>
            <li><strong className="text-text-primary">Skala</strong>: cocok untuk trading personal, bukan mengelola miliaran dolar.</li>
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardContent className={SECTION_CLASS}>
          <h3 className={H3_CLASS}>Keterbatasan data</h3>
          <ul className="list-disc space-y-1 pl-5">
            <li>Universe terbatas 45 konstituen IDX30/LQ45.</li>
            <li>Beberapa saham IDX punya data kosong/tidak lengkap di Yahoo Finance.</li>
            <li>Backtest tidak memperhitungkan biaya transaksi, pajak, atau slippage nyata.</li>
            <li>
              Ini alat bantu keputusan, <strong className="text-text-primary">bukan pengganti riset
              fundamental dan manajemen risiko yang disiplin</strong>.
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
