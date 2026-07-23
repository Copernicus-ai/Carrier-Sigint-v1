"""
Builds output/sigint_q2_2026.html — Promotion Game Q2 2026 update.
AT&T-only preview (VZ, TMUS pending their Q2 2026 earnings). Re-run this
script after each carrier reports, adding their figures to CARRIERS below,
to progressively fill out the 3-carrier grid.

Source: AT&T 8-K Q2 2026 (data/8K/T-8K-earnings-2026-07-22-ex99*.htm),
AT&T 10-Q Q2 2025 (data/10Q/T-10Q-Q2-2025.htm) for the prior-year balance sheet.
"""
import base64
import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLORS = {"T-Mobile": "#E20074", "Verizon": "#CD040B", "AT&T": "#009FDB"}
PERIOD_A, PERIOD_B = "Q2 2025", "Q2 2026"

# Only AT&T has reported as of this run. Add "T-Mobile"/"Verizon" dicts here
# (same shape) once they report Q2 2026, then re-run this script.
CARRIERS = ["AT&T"]

DATA = {
    "AT&T": {
        "equip_gross_loss": (183, 160),          # $M: cost of equip rev - equip rev
        "equip_loss_pct_svc_rev": (0.72, 0.62),   # %
        "subsidy_per_net_add": (456, 370),        # $ per postpaid phone net add
        "net_adds": (401, 432),                   # 000s, postpaid phone
        "postpaid_churn": (0.87, 0.86),           # %
        "service_revenue": (25292, 25977),        # $M
        "adj_ebitda": (11693, 12300),             # $M (2025 derived from +5.2% YoY)
        "fcf": (4400, 4700),                      # $M
        "subsidy_burn_rate": (7.8, 5.9),          # %  = equip_gross_loss / (fcf - divs)
    }
}


def fmt_dollar_m(v):
    if abs(v) >= 1000:
        return f"${v/1000:.1f}B"
    return f"${v:,.0f}M"


def bar_panel(ax, title, values_by_carrier, fmt, ylabel=None):
    x = range(len(CARRIERS) * 2)
    labels = []
    heights = []
    colors = []
    for c in CARRIERS:
        a, b = values_by_carrier[c]
        heights += [a, b]
        colors += [COLORS[c], COLORS[c]]
        labels += [PERIOD_A, PERIOD_B]

    bars = ax.bar(x, heights, color=colors, width=0.55)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_title(title, fontsize=12, fontweight="bold", loc="left", pad=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e2e8f0", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ymax = max(heights) if max(heights) > 0 else 1
    ax.set_ylim(0, ymax * 1.22 if ymax > 0 else 1)
    for rect, v in zip(bars, heights):
        ax.annotate(
            fmt(v),
            (rect.get_x() + rect.get_width() / 2, rect.get_height()),
            ha="center", va="bottom", fontsize=9.5, fontweight="bold",
            color=rect.get_facecolor(),
        )


def build_page1():
    fig = plt.figure(figsize=(15.5, 20), dpi=100)
    fig.patch.set_facecolor("#ffffff")
    gs = fig.add_gridspec(3, 3, left=0.05, right=0.97, top=0.90, bottom=0.05, hspace=0.55, wspace=0.28)

    panels = [
        ("Equipment Gross Loss ($M)", "equip_gross_loss", lambda v: f"${v:.0f}M"),
        ("Equip Loss % of Service Revenue", "equip_loss_pct_svc_rev", lambda v: f"{v:.2f}%"),
        ("Subsidy Cost per Net Add ($)", "subsidy_per_net_add", lambda v: f"${v:,.0f}"),
        ("Net Adds (000s, postpaid phone)", "net_adds", lambda v: f"{v:+.0f}K"),
        ("Postpaid Phone Churn (%)", "postpaid_churn", lambda v: f"{v:.2f}%"),
        ("Service Revenue ($M)", "service_revenue", fmt_dollar_m),
        ("Adj. EBITDA ($M)", "adj_ebitda", fmt_dollar_m),
        ("Free Cash Flow ($M)", "fcf", fmt_dollar_m),
        ("Subsidy Burn Rate (%)", "subsidy_burn_rate", lambda v: f"{v:.1f}%"),
    ]

    for i, (title, key, fmt) in enumerate(panels):
        ax = fig.add_subplot(gs[i // 3, i % 3])
        vals = {c: DATA[c][key] for c in CARRIERS}
        bar_panel(ax, title, vals, fmt)

    # Header band
    fig.text(0.05, 0.965, "Device Subsidy Economics | AT&T Preview | Q2 2025 vs Q2 2026", fontsize=15, color="#4a5568")
    fig.text(0.94, 0.975, "1/1", fontsize=11, color="#a0aec0", ha="right")

    y0 = 0.965
    chip_w, chip_h = 0.085, 0.022
    x = 0.60
    for name in ["T-Mobile", "Verizon", "AT&T"]:
        pending = name not in CARRIERS
        color = COLORS[name] if not pending else "#cbd5e0"
        fig.patches.append(matplotlib.patches.FancyBboxPatch(
            (x, y0 - chip_h), chip_w, chip_h, boxstyle="round,pad=0.002,rounding_size=0.004",
            transform=fig.transFigure, facecolor=color, edgecolor="none"))
        label = name if not pending else f"{name} (pending)"
        fig.text(x + chip_w / 2, y0 - chip_h / 2, label, fontsize=8.5, color="#ffffff" if not pending else "#4a5568",
                  ha="center", va="center", fontweight="bold")
        x += chip_w + 0.015

    fig.text(0.05, 0.015,
              "SIGINT Intelligence Platform  ·  Source: SEC EDGAR 8-K Q2 2026 (AT&T filed Jul 22 2026); Verizon/T-Mobile pending  ·  "
              "For institutional use; illustrative purposes only",
              fontsize=8, color="#a0aec0")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def build_html(page1_b64):
    now = datetime.now().strftime("%B %d, %Y  %H:%M")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SIGINT — Q2 2026 Carrier Update</title>
<style>
  :root{{--ink:#1a1a2e;--gray1:#4a5568;--gray2:#a0aec0;--bg:#f7f8fa;--card:#ffffff;
         --tmo:#E20074;--vz:#CD040B;--att:#009FDB;--border:#e2e8f0;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
        background:var(--bg);color:var(--ink);}}
  header{{background:var(--ink);color:#fff;padding:28px 40px 20px;}}
  header h1{{font-size:1.9rem;font-weight:700;letter-spacing:-0.02em;}}
  header p.sub{{color:#a0aec0;font-size:0.85rem;margin-top:6px;}}
  .meta{{font-size:0.78rem;color:#718096;margin-top:8px;}}
  .badge-row{{display:flex;gap:10px;margin-top:14px;}}
  .badge{{padding:4px 14px;border-radius:4px;font-size:0.80rem;font-weight:700;color:#fff;}}
  .badge.pending{{background:#cbd5e0;color:#4a5568;}}
  .new-badge{{background:#38a169;font-size:0.72rem;padding:3px 8px;border-radius:3px;
              color:#fff;font-weight:600;display:inline-block;margin-left:8px;vertical-align:middle;}}
  .preview-badge{{background:#d97706;font-size:0.72rem;padding:3px 8px;border-radius:3px;
              color:#fff;font-weight:700;display:inline-block;margin-left:8px;vertical-align:middle;
              text-transform:uppercase;letter-spacing:0.05em;}}
  nav.back-link{{padding:10px 40px;background:#edf2f7;font-size:0.82rem;}}
  nav.back-link a{{color:var(--att);text-decoration:none;font-weight:600;}}
  .notice{{margin:16px 40px 0;padding:14px 18px;background:#fef3c7;border:1px solid #fbbf24;
           border-radius:6px;font-size:0.82rem;color:#92400e;line-height:1.6;}}
  .content{{max-width:1100px;margin:0 auto;padding:30px 40px;}}
  .page{{background:var(--card);border:1px solid var(--border);border-radius:8px;
         margin-bottom:30px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.06);}}
  .page-label{{background:#f0f4f8;padding:8px 16px;font-size:0.78rem;
               color:var(--gray1);font-weight:600;border-bottom:1px solid var(--border);}}
  .page img{{width:100%;display:block;}}
  footer{{background:var(--ink);color:#718096;text-align:center;
          padding:16px;font-size:0.75rem;}}
</style>
</head>
<body>
<header>
  <h1>THE PROMOTION GAME &mdash; Q2 2026 UPDATE <span class="preview-badge">Preview</span></h1>
  <p class="sub">Device Subsidy Economics in U.S. Wireless &nbsp;|&nbsp; Q2 2025 vs Q2 2026</p>
  <div class="meta">AT&amp;T reported &nbsp;|&nbsp; Verizon reports Jul 23 2026 &nbsp;|&nbsp; T-Mobile reports late Jul 2026 &nbsp;|&nbsp; SIGINT Intelligence Platform &nbsp;|&nbsp; Refreshed {now}</div>
  <div class="badge-row">
    <span class="badge pending" style="background:var(--tmo);">T-Mobile (pending)</span>
    <span class="badge pending" style="background:var(--vz);">Verizon (pending)</span>
    <span class="badge" style="background:var(--att);">AT&amp;T</span>
  </div>
</header>
<nav class="back-link">
  &larr; <a href="../index.html">SIGINT Home</a>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="sigint_q1_2026.html">Q1 2026 Update</a>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="sigint_promotion_game.html">FY2023&ndash;FY2025 Annual</a>
</nav>
<div class="notice">
  <strong>This page updates in place as each carrier reports.</strong> AT&amp;T's Q2 2026 results (filed Jul 22 2026) are in.
  Verizon reports Jul 23 2026 and T-Mobile reports in the following week — their bars will be added to these same charts once filed.
</div>
<div class="content">
        <div class="page">
          <div class="page-label">Page 1 — Subsidy Economics (AT&amp;T)</div>
          <img src="data:image/png;base64,{page1_b64}" alt="Page 1 — Subsidy Economics"/>
        </div>
</div>
<footer>
  SIGINT Intelligence Platform &nbsp;&middot;&nbsp; Source: SEC EDGAR 8-K Filings Q2 2026 (AT&amp;T filed July 2026)
  &nbsp;&middot;&nbsp; For institutional use; illustrative purposes only
</footer>
</body>
</html>
"""


if __name__ == "__main__":
    import matplotlib.patches  # noqa: E402  (needed for FancyBboxPatch)
    page1_b64 = build_page1()
    html = build_html(page1_b64)
    out_path = "output/sigint_q2_2026.html"
    with open(out_path, "w") as f:
        f.write(html)
    print(f"Wrote {out_path} ({len(html)} bytes)")
