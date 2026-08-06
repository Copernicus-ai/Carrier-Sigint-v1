"""
Builds output/sigint_q2_2026.html — Promotion Game Q2 2026 update.
All three carriers now reported: AT&T (Jul 22), T-Mobile (Jul 23), Verizon (Jul 24).

Source: 8-K earnings exhibits in data/8K/
  - T-8K-earnings-2026-07-22-ex99{1,2}.htm
  - TMUS-8K-earnings-2026-07-23-ex99{1,2}.htm
  - VZ-8K-earnings-2026-07-24-ex99.htm

Note: T-Mobile no longer discloses phone-level postpaid net adds/churn in its
earnings release (only account-level). Its "Net Adds" and "Churn" bars use
postpaid ACCOUNT net additions / account churn, flagged in the chart and notice.
"""
import base64
import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLORS = {"T-Mobile": "#E20074", "Verizon": "#CD040B", "AT&T": "#009FDB"}
PERIOD_A, PERIOD_B = "Q2 2025", "Q2 2026"

CARRIERS = ["T-Mobile", "Verizon", "AT&T"]

# equip_gross_loss = cost of equipment revenue - equipment revenue ($M)
# subsidy_per_net_add = equip_gross_loss / net_adds; None where net_adds <= 0 (not meaningful)
# subsidy_burn_rate = equip_gross_loss / (fcf - quarterly dividends paid)
DATA = {
    "AT&T": {
        "equip_gross_loss": (183, 160),
        "equip_loss_pct_svc_rev": (0.72, 0.62),
        "subsidy_per_net_add": (456, 370),
        "net_adds": (401, 432),
        "postpaid_churn": (0.87, 0.86),
        "service_revenue": (25292, 25977),
        "adj_ebitda": (11693, 12300),
        "fcf": (4400, 4700),
        "subsidy_burn_rate": (7.8, 5.9),
    },
    "T-Mobile": {
        # Postpaid ACCOUNT net adds/churn — TMUS's Q2 2026 release no longer
        # breaks out phone-level net adds/churn.
        "equip_gross_loss": (1220, 1531),
        "equip_loss_pct_svc_rev": (7.00, 8.07),
        "subsidy_per_net_add": (3836, 5527),
        "net_adds": (318, 277),
        "postpaid_churn": (0.92, 0.99),
        "service_revenue": (17438, 18983),
        "adj_ebitda": (8541, 9537),   # Core Adjusted EBITDA
        "fcf": (4596, 4797),          # Adjusted Free Cash Flow
        "subsidy_burn_rate": (33.9, 41.4),
    },
    "Verizon": {
        # Postpaid phone net adds were NEGATIVE in Q2 2025 (-9K) — subsidy
        # per net add is not meaningful for that quarter (None -> "N/M").
        "equip_gross_loss": (752, 835),
        "equip_loss_pct_svc_rev": (2.66, 2.86),
        "subsidy_per_net_add": (None, 4538),
        "net_adds": (-9, 184),
        "postpaid_churn": (0.97, 0.92),
        "service_revenue": (28249, 29229),
        "adj_ebitda": (12807, 13723),
        "fcf": (5167, 6426),
        "subsidy_burn_rate": (32.5, 23.9),
    },
}

ACCOUNT_BASIS_NOTE = {"T-Mobile"}  # carriers whose net_adds/churn are account- not phone-level


def fmt_dollar_m(v):
    if abs(v) >= 1000:
        return f"${v/1000:.1f}B"
    return f"${v:,.0f}M"


def bar_panel(ax, title, values_by_carrier, fmt, star_carriers=None):
    x = list(range(len(CARRIERS) * 2))
    labels = []
    heights = []
    display_heights = []
    colors = []
    texts = []
    for c in CARRIERS:
        a, b = values_by_carrier[c]
        for v in (a, b):
            if v is None:
                heights.append(0)
                display_heights.append(0)
                texts.append("N/M")
            else:
                heights.append(v)
                display_heights.append(v)
                texts.append(fmt(v))
        colors += [COLORS[c], COLORS[c]]
        labels += [PERIOD_A, PERIOD_B]

    bars = ax.bar(x, display_heights, color=colors, width=0.55)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    title_suffix = " *" if star_carriers else ""
    ax.set_title(title + title_suffix, fontsize=12, fontweight="bold", loc="left", pad=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e2e8f0", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    non_none = [h for h in heights if h is not None]
    ymin = min(0, min(non_none) if non_none else 0)
    ymax = max(non_none) if non_none else 1
    pad = (ymax - ymin) * 0.22 if (ymax - ymin) > 0 else 1
    ax.set_ylim(ymin - (pad * 0.15 if ymin < 0 else 0), ymax + pad)
    for rect, v, txt in zip(bars, heights, texts):
        y = rect.get_height()
        va = "bottom" if y >= 0 else "top"
        ax.annotate(
            txt,
            (rect.get_x() + rect.get_width() / 2, y),
            ha="center", va=va, fontsize=9.5, fontweight="bold",
            color=rect.get_facecolor() if v != 0 or txt == "N/M" else "#a0aec0",
        )
    if ymin < 0:
        ax.axhline(0, color="#cbd5e0", linewidth=0.8, zorder=1)


def build_page1():
    fig = plt.figure(figsize=(15.5, 20), dpi=100)
    fig.patch.set_facecolor("#ffffff")
    gs = fig.add_gridspec(3, 3, left=0.05, right=0.97, top=0.90, bottom=0.06, hspace=0.55, wspace=0.28)

    panels = [
        ("Equipment Gross Loss ($M)", "equip_gross_loss", lambda v: f"${v:.0f}M", None),
        ("Equip Loss % of Service Revenue", "equip_loss_pct_svc_rev", lambda v: f"{v:.2f}%", None),
        ("Subsidy Cost per Net Add ($)", "subsidy_per_net_add", lambda v: f"${v:,.0f}", None),
        ("Net Adds (000s, postpaid phone)", "net_adds", lambda v: f"{v:+.0f}K", ACCOUNT_BASIS_NOTE),
        ("Postpaid Phone Churn (%)", "postpaid_churn", lambda v: f"{v:.2f}%", ACCOUNT_BASIS_NOTE),
        ("Service Revenue ($M)", "service_revenue", fmt_dollar_m, None),
        ("Adj. EBITDA ($M)", "adj_ebitda", fmt_dollar_m, None),
        ("Free Cash Flow ($M)", "fcf", fmt_dollar_m, None),
        ("Subsidy Burn Rate (%)", "subsidy_burn_rate", lambda v: f"{v:.1f}%", None),
    ]

    for i, (title, key, fmt, star) in enumerate(panels):
        ax = fig.add_subplot(gs[i // 3, i % 3])
        vals = {c: DATA[c][key] for c in CARRIERS}
        bar_panel(ax, title, vals, fmt, star_carriers=star)

    fig.text(0.05, 0.965, "Device Subsidy Economics | All 3 Carriers Reported | Q2 2025 vs Q2 2026", fontsize=15, color="#4a5568")
    fig.text(0.94, 0.975, "1/1", fontsize=11, color="#a0aec0", ha="right")

    y0 = 0.965
    chip_w, chip_h = 0.085, 0.022
    x = 0.60
    for name in ["T-Mobile", "Verizon", "AT&T"]:
        color = COLORS[name]
        fig.patches.append(matplotlib.patches.FancyBboxPatch(
            (x, y0 - chip_h), chip_w, chip_h, boxstyle="round,pad=0.002,rounding_size=0.004",
            transform=fig.transFigure, facecolor=color, edgecolor="none"))
        fig.text(x + chip_w / 2, y0 - chip_h / 2, name, fontsize=8.5, color="#ffffff",
                  ha="center", va="center", fontweight="bold")
        x += chip_w + 0.015

    fig.text(0.05, 0.028,
              "* Net Adds / Churn panels: T-Mobile figures are postpaid ACCOUNT basis (phone-level net adds/churn "
              "no longer disclosed in its earnings release); AT&T and Verizon are postpaid PHONE basis. "
              "\"N/M\" = not meaningful (Verizon had negative postpaid phone net adds in Q2 2025).",
              fontsize=7.5, color="#a0aec0")
    fig.text(0.05, 0.012,
              "SIGINT Intelligence Platform  ·  Source: SEC EDGAR 8-K Q2 2026 (AT&T filed Jul 22; T-Mobile filed Jul 23; Verizon filed Jul 24, 2026)  ·  "
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
  .new-badge{{background:#38a169;font-size:0.72rem;padding:3px 8px;border-radius:3px;
              color:#fff;font-weight:600;display:inline-block;margin-left:8px;vertical-align:middle;}}
  nav.back-link{{padding:10px 40px;background:#edf2f7;font-size:0.82rem;}}
  nav.back-link a{{color:var(--att);text-decoration:none;font-weight:600;}}
  .notice{{margin:16px 40px 0;padding:14px 18px;background:#ecfdf5;border:1px solid #34d399;
           border-radius:6px;font-size:0.82rem;color:#065f46;line-height:1.6;}}
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
  <h1>THE PROMOTION GAME &mdash; Q2 2026 UPDATE <span class="new-badge">All 3 Reported</span></h1>
  <p class="sub">Device Subsidy Economics in U.S. Wireless &nbsp;|&nbsp; Q2 2025 vs Q2 2026</p>
  <div class="meta">AT&amp;T filed Jul 22 &nbsp;|&nbsp; T-Mobile filed Jul 23 &nbsp;|&nbsp; Verizon filed Jul 24, 2026 &nbsp;|&nbsp; SIGINT Intelligence Platform &nbsp;|&nbsp; Refreshed {now}</div>
  <div class="badge-row">
    <span class="badge" style="background:var(--tmo);">T-Mobile</span>
    <span class="badge" style="background:var(--vz);">Verizon</span>
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
  <strong>All three carriers have now reported Q2 2026 results.</strong> T-Mobile's Q2 2026 release dropped
  phone-level postpaid net add/churn disclosure in favor of account-level metrics only &mdash; its Net Adds and
  Churn bars reflect postpaid <em>accounts</em>, not phones, and are flagged with an asterisk in the chart.
  Verizon posted negative postpaid phone net adds in Q2 2025 (&minus;9K), so its Subsidy Cost per Net Add for
  that quarter is not meaningful and shown as "N/M."
</div>
<div class="content">
        <div class="page">
          <div class="page-label">Page 1 — Subsidy Economics (T-Mobile, Verizon, AT&amp;T)</div>
          <img src="data:image/png;base64,{page1_b64}" alt="Page 1 — Subsidy Economics"/>
        </div>
</div>
<footer>
  SIGINT Intelligence Platform &nbsp;&middot;&nbsp; Source: SEC EDGAR 8-K Filings Q2 2026 (all three carriers filed Jul 22&ndash;24, 2026)
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
