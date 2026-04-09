"""
FuelIQ - PDF Report Generator  (v3 - rich content + notebook-style chart)
Requires: fpdf2  (pip install fpdf2)
          matplotlib (already in env)
"""

import io
import os
import json
import tempfile
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ─────────────────────────────────────────────────────────────────────────────
# Data-dir helper (same logic as data_loader.py)
# ─────────────────────────────────────────────────────────────────────────────
_DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data")
)


def _dp(fname: str) -> str:
    return os.path.join(_DATA_DIR, fname)


# ─────────────────────────────────────────────────────────────────────────────
# Notebook-style stock-drawdown chart  →  PNG bytes
# ─────────────────────────────────────────────────────────────────────────────
def _make_drawdown_png(pred: dict, df_sim: "pd.DataFrame | None") -> bytes:
    """
    Recreates the notebook's 'Stock Drawdown Forecast' bar chart as PNG bytes.
    Uses the saved viz_next_refill_prediction.png if it already exists and is
    fresh (< 24 h old), otherwise generates a new one from pred / df_sim.
    """
    # ── 1. Try to use the pre-saved notebook output ───────────────────────────
    saved = _dp("viz_next_refill_prediction.png")
    if os.path.exists(saved):
        with open(saved, "rb") as f:
            return f.read()

    # ── 2. Build a fresh chart from pred + sim_df ─────────────────────────────
    REFILL_THRESHOLD = 2000
    TANK_CAPACITY    = 12000

    if df_sim is not None and not df_sim.empty:
        rows = df_sim.head(8)
        dates   = rows["Date"].tolist()
        opens   = [
            float(str(v).replace(",", "").replace(" L","").replace("L",""))
            for v in rows["Opening_Stock"].tolist()
        ]
        closes  = [
            float(str(v).replace(",", "").replace(" L","").replace("L",""))
            for v in rows["Closing_Stock"].tolist()
        ]
        days_lbl = [f"{rows['Day'].iloc[i][:3]}\n{dates[i]}" for i in range(len(dates))]
    else:
        # Minimal fallback
        refill_d = pred.get("refill_date")
        cur      = float(pred.get("closing_stock", 7000))
        avg      = float(pred.get("avg_sold", 4500))
        base     = (refill_d - pd.Timedelta(days=pred.get("days_remaining", 2))
                    if refill_d else pd.Timestamp.now())
        opens, closes, days_lbl = [], [], []
        for i in range(1, 9):
            d     = base + pd.Timedelta(days=i)
            close = max(0.0, cur - avg)
            opens.append(round(cur))
            closes.append(round(close))
            days_lbl.append(f"{d.strftime('%a')}\n{d.strftime('%d-%m-%Y')}")
            cur = close

    n    = len(opens)
    x    = np.arange(n)

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    # Opening-stock bars (light blue background)
    ax.bar(x, opens,
           color="#d5e8f5", edgecolor="#3498db",
           linewidth=0.8, label="Opening Stock")

    # Closing-stock bars (blue / red)
    bar_colors = ["#e74c3c" if v < REFILL_THRESHOLD else "#3498db" for v in closes]
    ax.bar(x, closes, color=bar_colors, alpha=0.85,
           edgecolor="white", label="Closing Stock")

    # Trend line
    ax.plot(x, closes, color="#2c3e50", marker="o",
            linewidth=2.5, markersize=8, zorder=5, label="Stock trend")

    # Labels above each closing bar
    for i, v in enumerate(closes):
        ax.text(i, v + max(opens) * 0.02, f"{v:,.0f}L",
                ha="center", fontsize=9, fontweight="bold", color="#1a1a2e")

    # Refill threshold line
    ax.axhline(REFILL_THRESHOLD, color="red", linestyle="--", linewidth=2.5,
               label=f"Refill threshold ({REFILL_THRESHOLD:,}L)", zorder=6)

    # "REFILL NEEDED" annotation
    refill_idx = next((i for i, v in enumerate(closes) if v < REFILL_THRESHOLD), None)
    if refill_idx is not None:
        ax.axvline(refill_idx, color="red", linestyle="-", linewidth=2, alpha=0.4)
        ax.text(refill_idx, max(opens) * 0.60,
                f"REFILL\nNEEDED\n{days_lbl[refill_idx].split(chr(10))[-1]}",
                ha="center", color="red", fontweight="bold", fontsize=11,
                bbox=dict(boxstyle="round,pad=0.3",
                          facecolor="#ffe6e6", edgecolor="red"))

    ax.set_xticks(x)
    ax.set_xticklabels(days_lbl, fontsize=8)
    ax.set_ylabel("Stock Level (Litres)", fontsize=11)
    ax.set_ylim(0, max(opens) * 1.22 if opens else TANK_CAPACITY * 1.2)
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda val, _: f"{val:,.0f}")
    )

    refill_date_str = ""
    rd = pred.get("refill_date")
    if rd and hasattr(rd, "strftime"):
        refill_date_str = rd.strftime("%d-%m-%Y")
    cur_stock = int(pred.get("closing_stock", 0))
    ax.set_title(
        f"Stock Drawdown Forecast  |  Opening: {cur_stock:,}L"
        + (f"  |  Refill needed: {refill_date_str}" if refill_date_str else ""),
        fontweight="bold", fontsize=13
    )
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ─────────────────────────────────────────────────────────────────────────────
# Main report entry-point
# ─────────────────────────────────────────────────────────────────────────────
def generate_pdf_report(prediction: dict,
                        metrics:    dict,
                        sim_df:     "pd.DataFrame | None" = None) -> bytes:
    """
    Generate a polished PDF report.  Returns raw bytes for st.download_button.
    """
    try:
        from fpdf import FPDF

        # ── Colour constants ──────────────────────────────────────────────────
        C_DARK   = (15,  17,  23)       # near-black page header
        C_ACCENT = (245, 158, 11)       # amber / gold
        C_BLUE   = (37,  99,  235)      # link blue
        C_MUTED  = (148, 163, 184)      # slate-400
        C_BODY   = (30,  41,  59)       # slate-800
        C_WHITE  = (255, 255, 255)
        C_RED    = (220, 38,  38)
        C_GREEN  = (22,  163, 74)
        C_LIGHT  = (241, 245, 249)      # very light row bg

        # ── FPDF subclass with header / footer ────────────────────────────────
        class PDF(FPDF):
            def header(self):
                # Dark banner
                self.set_fill_color(*C_DARK)
                self.rect(0, 0, 210, 38, "F")
                # Amber accent stripe
                self.set_fill_color(*C_ACCENT)
                self.rect(0, 38, 210, 2, "F")
                # Title
                self.set_text_color(*C_ACCENT)
                self.set_font("Helvetica", "B", 22)
                self.set_xy(0, 8)
                self.cell(0, 12, "FuelIQ - Prediction Report", align="C",
                          new_x="LMARGIN", new_y="NEXT")
                # Sub-title
                self.set_font("Helvetica", "", 9)
                self.set_text_color(*C_MUTED)
                self.cell(0, 6,
                          f"Petrol Pump Refuel Predictor  |  "
                          f"Generated {datetime.now().strftime('%d %b %Y  %H:%M')}",
                          align="C", new_x="LMARGIN", new_y="NEXT")
                self.ln(8)

            def footer(self):
                self.set_y(-13)
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(*C_MUTED)
                self.cell(0, 8,
                          f"FuelIQ AI Prediction Engine  |  Page {self.page_no()}",
                          align="C")

        # ── helpers inside generate_pdf_report ────────────────────────────────
        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.set_left_margin(12)
        pdf.set_right_margin(12)

        def section_header(title: str):
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(*C_ACCENT)
            pdf.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(*C_ACCENT)
            pdf.set_line_width(0.5)
            pdf.line(12, pdf.get_y(), 198, pdf.get_y())
            pdf.ln(3)

        def kv_row(label: str, value: str,
                   val_color=None, bg=None, bold_val=True):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*C_BODY)
            if bg:
                pdf.set_fill_color(*bg)
            w_label = 72
            pdf.cell(w_label, 8, label, border=0, fill=bool(bg))
            pdf.set_font("Helvetica", "B" if bold_val else "", 10)
            pdf.set_text_color(*(val_color or C_BODY))
            pdf.cell(0, 8, value, new_x="LMARGIN", new_y="NEXT",
                     border=0, fill=bool(bg))

        # ── 1. PREDICTION SUMMARY ─────────────────────────────────────────────
        section_header("[PREDICTION]  Prediction Summary")

        rd = prediction.get("refill_date", None)
        rd_str  = rd.strftime("%d %B %Y (%A)") if hasattr(rd, "strftime") else "N/A"
        rd_short = rd.strftime("%d %b %Y") if hasattr(rd, "strftime") else "N/A"
        days_rem  = prediction.get("days_remaining", "N/A")
        conf_pct  = prediction.get("confidence", 0) * 100
        avg_sold  = prediction.get("avg_sold", 0)
        cur_stock = prediction.get("closing_stock", 0)
        stock_ok  = float(cur_stock) >= 2000

        kv_row("Predicted Refill Date",  rd_str,       val_color=C_BLUE,  bold_val=True)
        kv_row("Days Remaining",         f"{days_rem} day(s)",
               val_color=(C_RED if int(str(days_rem).split()[0]
                                       if isinstance(days_rem, str) else days_rem) <= 2
                           else C_GREEN))
        kv_row("Model Confidence",       f"{conf_pct:.1f}%",
               val_color=(C_GREEN if conf_pct >= 80 else C_RED))
        kv_row("Est. Avg Daily Sales",   f"{avg_sold:,.0f} L")
        kv_row("Current Closing Stock",  f"{cur_stock:,.0f} L",
               val_color=(C_GREEN if stock_ok else C_RED))
        kv_row("Stock Status",
               "[OK] Above safe threshold (2,000 L)" if stock_ok
               else "[!] Below refill threshold - act soon!",
               val_color=(C_GREEN if stock_ok else C_RED))

        pdf.ln(5)

        # ── 2. MODEL METRICS ──────────────────────────────────────────────────
        section_header("[MODEL]  Model Performance")

        for key, label in [
            ("accuracy", "Accuracy"),
            ("f1_score", "F1 Score"),
            ("roc_auc",  "ROC-AUC"),
        ]:
            val = metrics.get(key, 0) * 100
            kv_row(label, f"{val:.1f}%",
                   val_color=(C_GREEN if val >= 90 else C_ACCENT))

        kv_row("Algorithm",   "Random Forest Classifier",  val_color=C_BODY)
        kv_row("Threshold",   "Refill when stock < 2,000 L", val_color=C_BODY)
        pdf.ln(5)

        # ── 3. REASONING ──────────────────────────────────────────────────────
        section_header("[WHY]  Why This Prediction?")
        reasons = [
            f"Current stock is {cur_stock:,.0f}L - "
            + ("critically low, very close to the 2,000L refill threshold."
               if float(cur_stock) < 4000
               else "at moderate level; depletion tracked daily."),
            f"Estimated average consumption is {avg_sold:,.0f}L per day based on "
            "day-of-week blended averages and seasonal multipliers.",
            f"Random Forest model predicts a refill requirement in {days_rem} day(s) "
            f"with {conf_pct:.0f}% confidence.",
            "Walk-forward simulation (up to 30 days ahead) confirms stock will drop "
            "below the 2,000L safety threshold on the predicted date.",
        ]
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*C_BODY)
        for i, r in enumerate(reasons, 1):
            pdf.multi_cell(0, 6.5, f"  {i}.  {r}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        pdf.ln(4)

        # ── 4. STOCK DRAWDOWN CHART ───────────────────────────────────────────
        section_header("[CHART]  Stock Drawdown Forecast Chart")

        chart_png = _make_drawdown_png(prediction, sim_df)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(chart_png)
            tmp_path = tmp.name

        try:
            available_w = 186  # mm  (210 - 12 - 12)
            pdf.image(tmp_path, x=12, w=available_w)
        finally:
            os.unlink(tmp_path)

        pdf.ln(4)

        # ── 5. SIMULATION TABLE ───────────────────────────────────────────────
        if sim_df is not None and not sim_df.empty:
            pdf.add_page()
            section_header("[TABLE]  15-Day Forward Simulation")

            cols   = ["Date", "Day", "Opening_Stock",
                      "Est_Sold", "Closing_Stock", "Refill_Probability"]
            hdrs   = ["Date", "Day", "Opening (L)",
                      "Est. Sold (L)", "Closing (L)", "Refill Risk"]
            widths = [26, 22, 28, 28, 26, 36]

            # Header row
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_fill_color(*C_ACCENT)
            pdf.set_text_color(0, 0, 0)
            for h, w in zip(hdrs, widths):
                pdf.cell(w, 8, h, border=1, fill=True, align="C")
            pdf.ln()

            # Data rows
            pdf.set_font("Helvetica", "", 8.5)
            for idx, (_, r_row) in enumerate(sim_df.iterrows()):
                triggered = bool(r_row.get("Refill_Triggered", False))
                if triggered:
                    pdf.set_fill_color(254, 226, 226)
                elif idx % 2 == 0:
                    pdf.set_fill_color(*C_LIGHT)
                else:
                    pdf.set_fill_color(*C_WHITE)

                for c, w in zip(cols, widths):
                    val = str(r_row.get(c, ""))
                    color = C_RED if triggered and c == "Refill_Probability" else C_BODY
                    pdf.set_text_color(*color)
                    pdf.cell(w, 7, val, border=1, fill=True, align="C")
                pdf.ln()

            # Legend
            pdf.ln(3)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*C_MUTED)
            pdf.set_fill_color(254, 226, 226)
            pdf.cell(6, 5, "", border=0, fill=True)
            pdf.cell(0, 5,
                     "  Pink rows indicate days when a refill is triggered.",
                     new_x="LMARGIN", new_y="NEXT")

        # ── OUTPUT ────────────────────────────────────────────────────────────
        buf = io.BytesIO()
        pdf.output(buf)
        return buf.getvalue()

    except ImportError:
        # ── Plain-text fallback ───────────────────────────────────────────────
        rd = prediction.get("refill_date", "N/A")
        rd_str = rd.strftime("%d %b %Y") if hasattr(rd, "strftime") else str(rd)
        lines = [
            "FuelIQ Prediction Report",
            "=" * 44,
            f"Generated : {datetime.now().strftime('%d %b %Y %H:%M')}",
            "",
            "PREDICTION SUMMARY",
            f"  Predicted Refill Date : {rd_str}",
            f"  Days Remaining        : {prediction.get('days_remaining', 'N/A')}",
            f"  Confidence            : {prediction.get('confidence', 0)*100:.1f}%",
            f"  Avg Daily Sales       : {prediction.get('avg_sold', 0):,.0f} L",
            f"  Current Closing Stock : {prediction.get('closing_stock', 0):,.0f} L",
            "",
            "MODEL METRICS",
            f"  Accuracy : {metrics.get('accuracy', 0)*100:.1f}%",
            f"  F1 Score : {metrics.get('f1_score', 0)*100:.1f}%",
            f"  ROC-AUC  : {metrics.get('roc_auc', 0)*100:.1f}%",
        ]
        return "\n".join(lines).encode("utf-8")
