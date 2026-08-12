"""
Reusable PDF report generator for weekly/monthly fitness reports.
Uses: fpdf2 matplotlib
"""

import io
from datetime import date, timedelta
from typing import Any
import matplotlib
matplotlib.use("Agg")  # Important for servers without a display.
import matplotlib.pyplot as plt
from fpdf import FPDF
from fpdf.fonts import FontFace

COLORS = {
    "primary": (47, 111, 79),         # #2f6f4f
    "primary_dark": (35, 79, 57),     # #234f39
    "primary_light": (226, 239, 231),
    "warning": (180, 83, 9),          # #b45309
    "warning_light": (255, 247, 237),
    "danger": (179, 38, 30),          # #b3261e
    "danger_light": (254, 242, 242),
    "purple": (124, 58, 237),         # #7c3aed
    "cyan": (8, 145, 178),            # #0891b2
    "text": (31, 41, 55),             # #1f2937
    "muted": (107, 114, 128),         # #6b7280
    "border": (229, 231, 235),        # #e5e7eb
    "background": (249, 250, 251),    # #f9fafb
    "white": (255, 255, 255),
    "green": (16, 185, 129),
}

def safe_number(value, default=0):
    """Safely convert a database value to a number."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def format_number(value, decimals=1):
    """Format numeric values nicely."""
    if value is None:
        return "N/A"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)
    if decimals == 0:
        return f"{value:.0f}"
    return f"{value:.{decimals}f}"

def get_bmi_category(bmi):
    """Return a human-readable BMI category."""
    if bmi is None:
        return "N/A"
    bmi = safe_number(bmi, None)
    if bmi is None:
        return "N/A"
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obesity"

def get_value(row: Any, key: str, default=None):
    """Supports both dictionaries and objects returned by database drivers."""
    if row is None:
        return default
    if isinstance(row, dict):
        return row.get(key, default)
    try:
        return row[key]
    except (KeyError, TypeError, IndexError):
        return getattr(row, key, default)

# PDF CLASS
class FitnessReportPDF(FPDF):
    def __init__(self, report_type="Weekly"):
        super().__init__(
            orientation="P",
            unit="mm",
            format="A4",
        )
        self.report_type = report_type
        self.set_margins(left=12, top=14, right=12)
        self.set_auto_page_break(auto=True, margin=14)
        self.alias_nb_pages()

    def header(self):
        """Automatically called at the top of every page."""
        self.set_fill_color(*COLORS["primary"])
        self.rect(0, 0, self.w, 4, style="F")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*COLORS["primary"])
        self.cell(0, 5, "AI FITNESS PLATFORM", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*COLORS["border"])
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)

    def footer(self):
        """Automatically called at the bottom of every page."""
        self.set_y(-10)
        self.set_draw_color(*COLORS["border"])
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(1)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*COLORS["muted"])
        self.cell(
            0, 4,
            f"{self.report_type} Progress Report    Page {self.page_no()}/{{nb}}",
            align="C",
        )

    def report_title(self, title: str, subtitle: str = ""):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*COLORS["primary_dark"])
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

        if subtitle:
            self.set_font("Helvetica", "", 8.5)
            self.set_text_color(*COLORS["muted"])
            self.cell(0, 5, subtitle, new_x="LMARGIN", new_y="NEXT")

        self.ln(2)

    def section_header(self, title: str):
        """Reusable section heading."""
        self.ln(2)
        self.set_fill_color(*COLORS["primary_light"])
        self.rect(self.l_margin, self.get_y(), self.epw, 7, style="F")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*COLORS["primary_dark"])
        self.set_xy(self.l_margin + 3, self.get_y() + 1)
        self.cell(self.epw - 6, 5, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def metric_card(self, label: str, value: str, x: float, y: float, width: float, height: float = 18, accent=None):
        """Draw one dashboard-style metric card with proper sizing."""
        accent = accent or COLORS["primary"]
        self.set_fill_color(*COLORS["white"])
        self.set_draw_color(*COLORS["border"])
        self.set_line_width(0.3)
        self.rect(x, y, width, height, style="DF")

        self.set_fill_color(*accent)
        self.rect(x, y, 2, height, style="F")

        self.set_xy(x + 4, y + 2)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*COLORS["muted"])
        self.cell(width - 6, 4, label.upper())

        self.set_xy(x + 4, y + 8)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*COLORS["text"])
        self.cell(width - 6, 6, str(value))

    def metric_grid(self, metrics):
        """Draw multiple metric cards cleanly inside available space."""
        columns = 3
        gap = 3
        width = (self.epw - (gap * (columns - 1))) / columns
        height = 18
        start_x = self.l_margin
        start_y = self.get_y()

        for index, metric in enumerate(metrics):
            label = metric[0]
            value = metric[1]
            accent = metric[2] if len(metric) > 2 else COLORS["primary"]

            row = index // columns
            col = index % columns

            x = start_x + col * (width + gap)
            y = start_y + row * (height + gap)

            self.metric_card(label, value, x, y, width, height, accent)

        rows = (len(metrics) + columns - 1) // columns
        self.set_y(start_y + rows * height + (rows - 1) * gap + 3)

    def info_table(self, rows):
        """Two-column key/value table."""
        self.set_font("Helvetica", "", 8.5)
        headings = ("Metric", "Value")
        table_rows = [headings, *[(str(label), str(value)) for label, value in rows]]

        heading_style = FontFace(
            emphasis="B",
            color=COLORS["white"],
            fill_color=COLORS["primary"],
        )

        with self.table(
            table_rows,
            col_widths=(45, 100),
            width=self.epw,
            text_align=("LEFT", "LEFT"),
            headings_style=heading_style,
            cell_fill_color=COLORS["background"],
            cell_fill_mode="ROWS",
            line_height=4.5,
            padding=1.5,
            borders_layout="INTERNAL",
        ):
            pass

        self.ln(2)

    def habit_table(self, habits):
        """Daily habit log table."""
        rows = [[
            "Date", "Weight", "Workout", "Water", "Sleep", "Calories", "Protein"
        ]]

        for habit in habits:
            log_date = get_value(habit, "log_date", "")
            if hasattr(log_date, "isoformat"):
                log_date = log_date.isoformat()

            workout = get_value(habit, "workout_done", False)

            rows.append([
                str(log_date),
                f"{safe_number(get_value(habit, 'weight_kg'), 0):.1f}" if get_value(habit, "weight_kg") is not None else "-",
                "Yes" if workout else "No",
                f"{safe_number(get_value(habit, 'water_l'), 0):.1f} L",
                f"{safe_number(get_value(habit, 'sleep_hours'), 0):.1f} h",
                f"{safe_number(get_value(habit, 'calories_consumed'), 0):.0f}",
                f"{safe_number(get_value(habit, 'protein_g'), 0):.0f} g",
            ])

        heading_style = FontFace(
            emphasis="B",
            color=COLORS["white"],
            fill_color=COLORS["primary"],
        )

        with self.table(
            rows,
            col_widths=(28, 20, 20, 20, 20, 28, 24),
            width=self.epw,
            text_align=("LEFT", "CENTER", "CENTER", "CENTER", "CENTER", "RIGHT", "RIGHT"),
            headings_style=heading_style,
            cell_fill_color=(248, 250, 252),
            cell_fill_mode="ROWS",
            line_height=4,
            padding=1,
            borders_layout="INTERNAL",
            repeat_headings=1,
        ):
            pass

        self.ln(2)

    def add_chart(self, title, labels, values, color=None, ylabel=""):
        """Create a compact line chart using matplotlib and embed it directly into the PDF."""
        if not values:
            return

        color = color or "#2f6f4f"
        fig, ax = plt.subplots(figsize=(8, 1.8), dpi=150)
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        ax.plot(
            range(len(values)), values,
            color=color, linewidth=2,
            marker="o", markersize=3,
        )
        ax.fill_between(range(len(values)), values, alpha=0.08, color=color)
        ax.set_title(title, fontsize=10, fontweight="bold", color="#1f2937", loc="left")

        if ylabel:
            ax.set_ylabel(ylabel, fontsize=7.5, color="#6b7280")

        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=6.5, rotation=45, ha="right")
        ax.tick_params(axis="y", labelsize=6.5, colors="#6b7280")
        ax.grid(axis="y", linestyle="--", alpha=0.25)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#e5e7eb")
        ax.spines["bottom"].set_color("#e5e7eb")

        fig.tight_layout()
        image_buffer = io.BytesIO()
        fig.savefig(image_buffer, format="png", bbox_inches="tight")
        plt.close(fig)
        image_buffer.seek(0)

        self.image(image_buffer, x=self.l_margin, w=self.epw)
        self.ln(2)

    def add_bar_chart(self, title, labels, values, color=None, ylabel=""):
        """Create a compact bar chart."""
        if not values:
            return

        color = color or "#2f6f4f"
        fig, ax = plt.subplots(figsize=(8, 1.8), dpi=150)
        fig.patch.set_facecolor("white")

        ax.bar(range(len(values)), values, color=color, width=0.65)
        ax.set_title(title, fontsize=10, fontweight="bold", color="#1f2937", loc="left")

        if ylabel:
            ax.set_ylabel(ylabel, fontsize=7.5, color="#6b7280")

        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=6.5, rotation=45, ha="right")
        ax.grid(axis="y", linestyle="--", alpha=0.25)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        fig.tight_layout()
        image_buffer = io.BytesIO()
        fig.savefig(image_buffer, format="png", bbox_inches="tight")
        plt.close(fig)
        image_buffer.seek(0)

        self.image(image_buffer, x=self.l_margin, w=self.epw)
        self.ln(2)

    def note_box(self, title, text, color=None):
        """Draw an informational box with accurate dynamic wrapping bounds."""
        color = color or COLORS["primary"]
        self.set_font("Helvetica", "", 8)
        
        # Calculate height dynamically based on text content to avoid overflow cuts
        line_width = self.epw - 12
        lines = self.get_string_width(text) / line_width
        # Approximate lines + padding
        computed_lines = max(2, int(lines) + 2)
        height = max(18, computed_lines * 4 + 8)

        # Check if box fits on current page, otherwise let FPDF handle page break cleanly
        if self.get_y() + height > self.h - self.b_margin:
            self.add_page()

        start_y = self.get_y()
        self.set_fill_color(*COLORS["background"])
        self.set_draw_color(*COLORS["border"])
        self.rect(self.l_margin, start_y, self.epw, height, style="DF")

        self.set_fill_color(*color)
        self.rect(self.l_margin, start_y, 2, height, style="F")

        self.set_xy(self.l_margin + 5, start_y + 3)
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*COLORS["text"])
        self.cell(self.epw - 8, 4, title, new_x="LMARGIN", new_y="NEXT")

        self.set_x(self.l_margin + 5)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*COLORS["muted"])
        self.multi_cell(self.epw - 10, 4, text)
        self.set_y(start_y + height + 3)


# ============================================================
# DATA CALCULATIONS
# ============================================================

def calculate_habit_stats(habits, period_days=None):
    """Calculate reusable habit statistics."""
    if not habits:
        return {
            "days": 0,
            "period_days": period_days or 0,
            "workout_days": 0,
            "workout_pct": 0,
            "avg_water": 0,
            "avg_sleep": 0,
            "avg_calories": 0,
            "avg_protein": 0,
        }

    n = len(habits)
    workout_days = sum(1 for h in habits if get_value(h, "workout_done", False))

    avg_water = sum(safe_number(get_value(h, "water_l"), 0) for h in habits) / n
    avg_sleep = sum(safe_number(get_value(h, "sleep_hours"), 0) for h in habits) / n
    avg_calories = sum(safe_number(get_value(h, "calories_consumed"), 0) for h in habits) / n
    avg_protein = sum(safe_number(get_value(h, "protein_g"), 0) for h in habits) / n

    denominator = period_days or n
    workout_pct = round(workout_days / denominator * 100) if denominator else 0

    return {
        "days": n,
        "period_days": denominator,
        "workout_days": workout_days,
        "workout_pct": workout_pct,
        "avg_water": avg_water,
        "avg_sleep": avg_sleep,
        "avg_calories": avg_calories,
        "avg_protein": avg_protein,
    }

def extract_chart_data(habits, field):
    """Extract dates + values for a chart."""
    labels = []
    values = []

    for habit in habits:
        value = get_value(habit, field)
        if value is None:
            continue

        log_date = get_value(habit, "log_date", "")
        if hasattr(log_date, "strftime"):
            label = log_date.strftime("%m-%d")
        else:
            label = str(log_date)[5:10]

        labels.append(label)
        values.append(safe_number(value))

    return labels, values


# ============================================================
# WEEKLY PDF
# ============================================================

def build_weekly_report(profile, analysis, habits, today):
    pdf = FitnessReportPDF(report_type="Weekly")
    pdf.add_page()

    user_name = get_value(profile, "full_name", "User") or "User"
    week_start = today - timedelta(days=6)

    pdf.report_title(
        "Weekly Progress Report",
        f"{user_name}  -  {week_start.isoformat()} -> {today.isoformat()}"
    )

    pdf.info_table([
        ("Report period", f"{week_start} -> {today}"),
        ("Primary goal", get_value(profile, "primary_goal", "Not specified")),
        ("Current weight", f"{safe_number(get_value(profile, 'current_weight_kg')):.1f} kg" if get_value(profile, "current_weight_kg") is not None else "N/A"),
        ("Target weight", f"{safe_number(get_value(profile, 'target_weight_kg')):.1f} kg" if get_value(profile, "target_weight_kg") is not None else "N/A"),
    ])

    if analysis:
        pdf.section_header("Body Analysis")
        bmi = get_value(analysis, "bmi")
        bmr = get_value(analysis, "bmr")
        tdee = get_value(analysis, "tdee")
        target_calories = get_value(analysis, "target_calories")
        bmi_category = get_value(analysis, "bmi_category") or get_bmi_category(bmi)

        pdf.metric_grid([
            ("BMI", f"{format_number(bmi, 1)} ({bmi_category})", COLORS["warning"]),
            ("BMR", f"{format_number(bmr, 0)} kcal", COLORS["primary"]),
            ("TDEE", f"{format_number(tdee, 0)} kcal", COLORS["cyan"]),
            ("Target Calories", f"{format_number(target_calories, 0)} kcal", COLORS["purple"]),
        ])

        macros = get_value(analysis, "macros", {})
        if macros:
            pdf.info_table([
                ("Protein target", f"{format_number(get_value(macros, 'protein_g'), 1)} g"),
                ("Carbohydrate target", f"{format_number(get_value(macros, 'carbs_g'), 1)} g"),
                ("Fat target", f"{format_number(get_value(macros, 'fat_g'), 1)} g"),
            ])

    stats = calculate_habit_stats(habits, period_days=7)
    pdf.section_header("Weekly Habit Summary")

    pdf.metric_grid([
        ("Logged Days", f"{stats['days']}/7", COLORS["primary"]),
        ("Workout Days", str(stats["workout_days"]), COLORS["green"]),
        ("Workout Completion", f"{stats['workout_pct']}%", COLORS["primary"]),
        ("Avg Water", f"{stats['avg_water']:.1f} L", COLORS["cyan"]),
        ("Avg Sleep", f"{stats['avg_sleep']:.1f} h", COLORS["purple"]),
        ("Avg Calories", f"{stats['avg_calories']:.0f}", COLORS["warning"]),
        ("Avg Protein", f"{stats['avg_protein']:.1f} g", COLORS["primary"]),
    ])

    if habits:
        pdf.section_header("Progress Trends")
        for field, title, color, unit in [
            ("weight_kg", "Weight Trend", "#2f6f4f", "kg"),
            ("water_l", "Water Intake", "#0891b2", "Litres"),
            ("protein_g", "Protein Intake", "#7c3aed", "grams")
        ]:
            labels, values = extract_chart_data(habits, field)
            if values:
                pdf.add_chart(title, labels, values, color=color, ylabel=unit)

        pdf.section_header("Daily Habit Log")
        pdf.habit_table(list(reversed(habits)))

    pdf.note_box(
        "Progress reminder",
        "Use this report to identify trends rather than judging a single day. "
        "Consistency across workouts, nutrition, sleep and hydration is more meaningful than any isolated value.",
    )

    return bytes(pdf.output())


# ============================================================
# MONTHLY PDF
# ============================================================

def build_monthly_report(profile, analysis, habits, start_date, today):
    pdf = FitnessReportPDF(report_type="Monthly")
    pdf.add_page()

    user_name = get_value(profile, "full_name", "User") or "User"

    pdf.report_title(
        "Monthly Progress Report",
        f"{user_name}  -  {start_date} -> {today}",
    )

    pdf.section_header("Profile Overview")
    pdf.info_table([
        ("Primary goal", get_value(profile, "primary_goal", "Not specified")),
        ("Experience level", get_value(profile, "experience_level", "Not specified")),
        ("Activity level", get_value(profile, "activity_level", "Not specified")),
        ("Current weight", f"{safe_number(get_value(profile, 'current_weight_kg')):.1f} kg" if get_value(profile, "current_weight_kg") is not None else "N/A"),
        ("Target weight", f"{safe_number(get_value(profile, 'target_weight_kg')):.1f} kg" if get_value(profile, "target_weight_kg") is not None else "N/A"),
    ])

    if analysis:
        pdf.section_header("Body Analysis")
        bmi = get_value(analysis, "bmi")
        bmi_category = get_value(analysis, "bmi_category") or get_bmi_category(bmi)

        pdf.metric_grid([
            ("BMI", f"{format_number(bmi, 1)} ({bmi_category})", COLORS["warning"]),
            ("BMR", f"{format_number(get_value(analysis, 'bmr'), 0)} kcal", COLORS["primary"]),
            ("TDEE", f"{format_number(get_value(analysis, 'tdee'), 0)} kcal", COLORS["cyan"]),
            ("Target Calories", f"{format_number(get_value(analysis, 'target_calories'), 0)} kcal", COLORS["purple"]),
        ])

    stats = calculate_habit_stats(habits)

    pdf.section_header("Monthly Performance")
    pdf.metric_grid([
        ("Logged Days", str(stats["days"]), COLORS["primary"]),
        ("Workout Days", str(stats["workout_days"]), COLORS["green"]),
        ("Workout %", f"{stats['workout_pct']}%", COLORS["primary"]),
        ("Avg Water", f"{stats['avg_water']:.1f} L", COLORS["cyan"]),
        ("Avg Sleep", f"{stats['avg_sleep']:.1f} h", COLORS["purple"]),
        ("Avg Calories", f"{stats['avg_calories']:.0f}", COLORS["warning"]),
    ])

    pdf.section_header("Monthly Trends")

    for field, title, chart_type, color, unit in [
        ("weight_kg", "Weight Trend", "line", "#2f6f4f", "kg"),
        ("calories_consumed", "Calories Consumed", "bar", "#b45309", "kcal"),
        ("protein_g", "Protein Intake", "line", "#7c3aed", "grams")
    ]:
        labels, values = extract_chart_data(habits, field)
        if values:
            if chart_type == "bar":
                pdf.add_bar_chart(title, labels, values, color=color, ylabel=unit)
            else:
                pdf.add_chart(title, labels, values, color=color, ylabel=unit)

    if habits:
        pdf.section_header("Daily Habit History")
        pdf.habit_table(habits)

    pdf.section_header("Report Summary")
    pdf.note_box(
        "Consistency matters",
        f"You logged {stats['days']} day(s) during this reporting period and completed workouts on "
        f"{stats['workout_days']} day(s). Your average daily water intake was {stats['avg_water']:.1f} L and average sleep "
        f"was {stats['avg_sleep']:.1f} hours.",
    )

    return bytes(pdf.output())