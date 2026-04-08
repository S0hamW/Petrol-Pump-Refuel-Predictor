"""
FuelIQ — PDF Report Generator
Uses fpdf2 (pip install fpdf2)
"""

import io
from datetime import datetime


def generate_pdf_report(prediction: dict, metrics: dict, sim_df=None) -> bytes:
    """
    Generate a PDF report with key prediction & model info.
    Returns bytes that can be used with st.download_button.
    """
    try:
        from fpdf import FPDF

        class PDF(FPDF):
            def header(self):
                self.set_fill_color(15, 17, 23)
                self.rect(0, 0, 210, 40, "F")
                self.set_text_color(245, 158, 11)
                self.set_font("Helvetica", "B", 22)
                self.set_y(10)
                self.cell(0, 12, "FuelIQ Prediction Report", align="C", new_x="LMARGIN", new_y="NEXT")
                self.set_font("Helvetica", "", 9)
                self.set_text_color(148, 163, 184)
                self.cell(0, 6, "Petrol Pump Refuel Predictor", align="C", new_x="LMARGIN", new_y="NEXT")
                self.ln(8)

            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(148, 163, 184)
                self.cell(0, 10, f"Generated on {datetime.now().strftime('%d %b %Y %H:%M')}  |  FuelIQ v1.0", align="C")

        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # ── Section: Prediction ──────────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(245, 158, 11)
        pdf.cell(0, 10, "Prediction Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(245, 158, 11)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        def row(label, value, accent=False):
            pdf.set_font("Helvetica", "B" if accent else "", 10)
            pdf.set_text_color(30, 41, 59)
            pdf.cell(70, 8, label, border=0)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(37, 99, 235 if not accent else 245)
            pdf.cell(0, 8, str(value), new_x="LMARGIN", new_y="NEXT", border=0)
            pdf.set_text_color(30, 41, 59)

        refill_date = prediction.get("refill_date", "N/A")
        if hasattr(refill_date, "strftime"):
            refill_date = refill_date.strftime("%d %B %Y")
        days_remaining = prediction.get("days_remaining", "N/A")
        confidence = prediction.get("confidence", 0) * 100
        avg_sold = prediction.get("avg_sold", 0)
        closing = prediction.get("closing_stock", 0)

        data_rows = [
            ("Predicted Refill Date", refill_date, True),
            ("Days Remaining", f"{days_remaining} days"),
            ("Model Confidence", f"{confidence:.1f}%"),
            ("Avg Daily Sales (Est.)", f"{avg_sold:,.0f} L"),
            ("Current Closing Stock", f"{closing:,.0f} L"),
        ]
        for r in data_rows:
            row(*r)

        pdf.ln(6)

        # ── Section: Model Metrics ───────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(245, 158, 11)
        pdf.cell(0, 10, "Model Performance", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(245, 158, 11)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        for key, label in [("accuracy", "Accuracy"), ("f1_score", "F1 Score"), ("roc_auc", "ROC-AUC")]:
            val = metrics.get(key, 0)
            row(label, f"{val * 100:.1f}%")

        pdf.ln(6)

        # ── Section: Reasoning ───────────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(245, 158, 11)
        pdf.cell(0, 10, "Why This Prediction?", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(245, 158, 11)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        reasons = [
            f"Low stock alert: Closing stock ({closing:,.0f}L) is approaching refill threshold (2,000L).",
            f"High sales trend: Average daily consumption is ~{avg_sold:,.0f}L.",
            "Model signals: Random Forest classifier predicts refill within estimated window.",
        ]
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 41, 59)
        for i, r in enumerate(reasons, 1):
            pdf.multi_cell(0, 7, f"{i}. {r}", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(6)

        # ── Section: Simulation Table ────────────────────────────────────────
        if sim_df is not None and not sim_df.empty:
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(245, 158, 11)
            pdf.cell(0, 10, "15-Day Simulation (First 7 Days)", new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(245, 158, 11)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)

            cols = ["Date", "Day", "Opening_Stock", "Est_Sold", "Closing_Stock", "Refill_Probability"]
            widths = [30, 22, 30, 25, 30, 35]
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_fill_color(245, 158, 11)
            pdf.set_text_color(0, 0, 0)
            for c, w in zip(cols, widths):
                pdf.cell(w, 8, c.replace("_", " "), border=1, fill=True)
            pdf.ln()

            pdf.set_font("Helvetica", "", 9)
            for _, r_row in sim_df.head(7).iterrows():
                pdf.set_text_color(30, 41, 59)
                fill = r_row.get("Refill_Triggered", False)
                if fill:
                    pdf.set_fill_color(254, 226, 226)
                else:
                    pdf.set_fill_color(255, 255, 255)
                for c, w in zip(cols, widths):
                    pdf.cell(w, 7, str(r_row.get(c, "")), border=1, fill=True)
                pdf.ln()

        buf = io.BytesIO()
        pdf.output(buf)
        return buf.getvalue()

    except ImportError:
        # Fallback: simple text report as bytes
        lines = [
            "FuelIQ Prediction Report",
            "=" * 40,
            f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}",
            "",
            "PREDICTION SUMMARY",
            f"  Predicted Refill Date : {prediction.get('refill_date', 'N/A')}",
            f"  Days Remaining        : {prediction.get('days_remaining', 'N/A')}",
            f"  Confidence            : {prediction.get('confidence', 0)*100:.1f}%",
            "",
            "MODEL METRICS",
            f"  Accuracy : {metrics.get('accuracy', 0)*100:.1f}%",
            f"  F1 Score : {metrics.get('f1_score', 0)*100:.1f}%",
            f"  ROC-AUC  : {metrics.get('roc_auc', 0)*100:.1f}%",
        ]
        return "\n".join(lines).encode("utf-8")
