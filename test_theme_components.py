"""
Test manual untuk theme.py & components.py (fondasi redesign UI, Fase 0).
Jalankan: python test_theme_components.py
Tidak butuh koneksi Supabase / Streamlit runtime -- gaya sama dengan
test_tickers_idx.py / test_position_manager.py.
"""
import plotly.graph_objects as go
import theme
import components

errors = []


def check(label, cond):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {label}")
    if not cond:
        errors.append(label)


print("=== theme.py ===")
check("COLORS punya 18 token (cocok dgn tabel §3.1 & §13)", len(theme.COLORS) == 18)
check("signal_colors('BUY') -> hijau", theme.signal_colors("BUY")["fg"] == theme.COLORS["bullish"])
check("signal_colors('sell') case-insensitive", theme.signal_colors("sell")["fg"] == theme.COLORS["bearish"])
check("signal_colors('HOLD') -> kuning", theme.signal_colors("HOLD")["fg"] == theme.COLORS["neutral"])
check("signal_colors(None) tidak crash -> netral", theme.signal_colors(None)["label"] == "–")
check("signal_colors('NO_DATA') -> netral", theme.signal_colors("NO_DATA")["label"] == "–")
check("direction_from_signal('BUY') -> bullish", theme.direction_from_signal("BUY") == "bullish")
check("direction_from_signal('SELL') -> bearish", theme.direction_from_signal("SELL") == "bearish")
check("direction_from_signal('HOLD') -> neutral", theme.direction_from_signal("HOLD") == "neutral")

check("format_idr(1234567.8, 2) == 'Rp 1.234.567,80'", theme.format_idr(1234567.8, 2) == "Rp 1.234.567,80")
check("format_idr(5000) == 'Rp 5.000'", theme.format_idr(5000) == "Rp 5.000")
check("format_idr(0) == 'Rp 0'", theme.format_idr(0) == "Rp 0")
check("format_idr(None) == '–'", theme.format_idr(None) == "–")
check("format_idr(-1500) == 'Rp -1.500'", theme.format_idr(-1500) == "Rp -1.500")

check("format_pct_id(1.4) == '+1,40%'", theme.format_pct_id(1.4) == "+1,40%")
check("format_pct_id(-8.2) == '-8,20%'", theme.format_pct_id(-8.2) == "-8,20%")
check("format_pct_id(0, show_sign=True) tanpa '+'", theme.format_pct_id(0) == "0,00%")
check("format_pct_id(None) == '–'", theme.format_pct_id(None) == "–")

check("format_number_id(1234567) == '1.234.567'", theme.format_number_id(1234567) == "1.234.567")

css = theme.get_global_css()
check("get_global_css() mengandung <style>", "<style>" in css and "</style>" in css)
check("get_global_css() mengandung semua CSS var --iqs-*", all(
    f"--iqs-{k}" in css for k in ["bg-base", "bg-surface", "text-primary", "brand", "font-sans", "font-mono"]
))
check("get_global_css() TIDAK menarget data-testid internal (kecuali stButton yg didokumentasikan)",
      css.count('data-testid') <= 1)

fig = go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[1, 4, 9])])
fig2 = theme.apply_chart_theme(fig, height=400)
check("apply_chart_theme() return objek Figure yg sama", fig2 is fig)
check("apply_chart_theme() set paper_bgcolor sesuai token", fig.layout.paper_bgcolor == theme.COLORS["bg_surface"])
check("apply_chart_theme() set height", fig.layout.height == 400)

check("CANDLESTICK_COLORS punya 4 key", set(theme.CANDLESTICK_COLORS.keys()) == {
    "increasing_line_color", "increasing_fillcolor", "decreasing_line_color", "decreasing_fillcolor"
})

print("\n=== components.py (fungsi *_html, tidak butuh Streamlit runtime) ===")
m3of3 = components.confirmation_meter_html(3, 3, "bullish")
check("meter 3/3 bullish -> 3x span, semua hijau, 0x abu2", m3of3.count("<span") == 4  # 1 wrapper + 3 bar
      and m3of3.count(theme.COLORS["bullish"]) == 3 and theme.COLORS["border_strong"] not in m3of3)

m2of3 = components.confirmation_meter_html(2, 3, "bullish")
check("meter 2/3 bullish -> 2 hijau + 1 abu2", m2of3.count(theme.COLORS["bullish"]) == 2
      and m2of3.count(theme.COLORS["border_strong"]) == 1)

m_bear = components.confirmation_meter_html(3, 3, "bearish")
check("meter bearish pakai warna merah, bukan hijau", theme.COLORS["bearish"] in m_bear and theme.COLORS["bullish"] not in m_bear)

m_clip = components.confirmation_meter_html(99, 3, "bullish")
check("meter dgn filled > total di-clip aman (tetap 3 bar, semua hijau)",
      m_clip.count(theme.COLORS["bullish"]) == 3)

badge_buy = components.signal_badge_html("BUY")
check("badge BUY mengandung teks 'Buy' & warna hijau", "Buy" in badge_buy and theme.COLORS["bullish"] in badge_buy)
badge_sell = components.signal_badge_html("SELL")
check("badge SELL mengandung teks 'Sell' & warna merah", "Sell" in badge_sell and theme.COLORS["bearish"] in badge_sell)
badge_none = components.signal_badge_html(None)
check("badge tanpa sinyal tidak crash", "–" in badge_none)

esc = components._esc("<script>alert(1)</script>")
check("_esc() mem-HTML-escape input mentah (anti-breakage markup)", "<script>" not in esc and "&lt;script&gt;" in esc)

print(f"\n{'='*60}")
if errors:
    print(f"GAGAL: {len(errors)} pengecekan tidak lolos -> {errors}")
    raise SystemExit(1)
print("SEMUA VERIFIKASI FASE 0 PASS ✅ (theme.py + components.py)")
print(f"{'='*60}")
