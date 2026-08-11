'''"""
PDF report generation for weekly/monthly progress reports.
Returns a downloadable PDF file.
"""
import io
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from db import get_db
from auth import get_current_user
from services.profile_helpers import get_profile, get_latest_analysis, get_recent_habits

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/weekly")
def generate_weekly_report(user=Depends(get_current_user), db=Depends(get_db)):
    """Generate a weekly progress report as PDF."""
    from fpdf import FPDF

    uid = user["id"]
    today = date.today()
    week_start = today - timedelta(days=6)

    profile = get_profile(db, uid)
    analysis = get_latest_analysis(db, uid)
    habits = get_recent_habits(db, uid, days=7)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "AI Fitness Platform - Weekly Progress Report", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"User: {profile.get('full_name', 'User') if profile else 'User'}", ln=True)
    pdf.cell(0, 6, f"Week: {week_start.isoformat()} to {today.isoformat()}", ln=True)
    pdf.cell(0, 6, f"Generated: {today.isoformat()}", ln=True)
    pdf.ln(5)

    # Body stats
    if analysis:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Body Analysis", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"BMI: {analysis.get('bmi', 'N/A')} ({analysis.get('bmi_category', 'N/A')})", ln=True)
        pdf.cell(0, 6, f"BMR: {analysis.get('bmr', 'N/A')} kcal", ln=True)
        pdf.cell(0, 6, f"TDEE: {analysis.get('tdee', 'N/A')} kcal", ln=True)
        pdf.cell(0, 6, f"Target Calories: {analysis.get('target_calories', 'N/A')} kcal", ln=True)
        macros = analysis.get("macros", {})
        if macros:
            pdf.cell(0, 6, f"Protein: {macros.get('protein_g', 0)}g | Carbs: {macros.get('carbs_g', 0)}g | Fat: {macros.get('fat_g', 0)}g", ln=True)
        pdf.ln(5)

    # Habit summary
    if habits:
        n = len(habits)
        workout_days = sum(1 for h in habits if h.get("workout_done"))
        avg_water = sum(h.get("water_l", 0) or 0 for h in habits) / n
        avg_sleep = sum(h.get("sleep_hours", 0) or 0 for h in habits) / n
        avg_calories = sum(h.get("calories_consumed", 0) or 0 for h in habits) / n
        avg_protein = sum(h.get("protein_g", 0) or 0 for h in habits) / n

        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Weekly Habit Summary", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Workout Days: {workout_days}/{n}", ln=True)
        pdf.cell(0, 6, f"Avg Water: {avg_water:.1f}L/day", ln=True)
        pdf.cell(0, 6, f"Avg Sleep: {avg_sleep:.1f} hrs/night", ln=True)
        pdf.cell(0, 6, f"Avg Calories: {avg_calories:.0f} kcal/day", ln=True)
        pdf.cell(0, 6, f"Avg Protein: {avg_protein:.1f}g/day", ln=True)

    pdf_output = pdf.output()
    return StreamingResponse(
        io.BytesIO(pdf_output),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=weekly_report_{today.isoformat()}.pdf"},
    )


@router.get("/monthly")
def generate_monthly_report(user=Depends(get_current_user), db=Depends(get_db)):
    """Generate a monthly progress report as PDF."""
    from fpdf import FPDF

    uid = user["id"]
    today = date.today()
    month_start = today - timedelta(days=30)

    profile = get_profile(db, uid)
    analysis = get_latest_analysis(db, uid)

    # Get 30 days of habits
    with db.cursor() as cur:
        cur.execute("""
            SELECT * FROM habit_logs WHERE user_id = %s AND log_date >= %s
            ORDER BY log_date
        """, (uid, month_start))
        habits = cur.fetchall()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "AI Fitness Platform - Monthly Progress Report", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"User: {profile.get('full_name', 'User') if profile else 'User'}", ln=True)
    pdf.cell(0, 6, f"Month: {month_start.isoformat()} to {today.isoformat()}", ln=True)
    pdf.cell(0, 6, f"Generated: {today.isoformat()}", ln=True)
    pdf.ln(5)

    if analysis:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Body Analysis", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"BMI: {analysis.get('bmi', 'N/A')} ({analysis.get('bmi_category', 'N/A')})", ln=True)
        pdf.cell(0, 6, f"Target Calories: {analysis.get('target_calories', 'N/A')} kcal/day", ln=True)
        pdf.ln(5)

    if habits:
        n = len(habits)
        workout_days = sum(1 for h in habits if (h.get("workout_done") if isinstance(h, dict) else False))
        avg_water = sum((h.get("water_l", 0) or 0) for h in habits) / n
        avg_sleep = sum((h.get("sleep_hours", 0) or 0) for h in habits) / n
        avg_calories = sum((h.get("calories_consumed", 0) or 0) for h in habits) / n

        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Monthly Habit Summary", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Total Logged Days: {n}", ln=True)
        pdf.cell(0, 6, f"Workout Days: {workout_days} ({round(workout_days/n*100)}%)", ln=True)
        pdf.cell(0, 6, f"Avg Water: {avg_water:.1f}L/day", ln=True)
        pdf.cell(0, 6, f"Avg Sleep: {avg_sleep:.1f} hrs/night", ln=True)
        pdf.cell(0, 6, f"Avg Calories: {avg_calories:.0f} kcal/day", ln=True)

    pdf_output = pdf.output()
    return StreamingResponse(
        io.BytesIO(pdf_output),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=monthly_report_{today.isoformat()}.pdf"},
    )'''

"""
PDF report generation for weekly/monthly progress reports.
Returns downloadable PDF files.
"""
import io
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from db import get_db
from auth import get_current_user

from services.profile_helpers import (
    get_profile,
    get_latest_analysis,
    get_recent_habits,
)

from services.report_generator import (
    build_weekly_report,
    build_monthly_report,
)


router = APIRouter(
    prefix="/api/reports",
    tags=["reports"],
)


# ============================================================
# WEEKLY REPORT
# ============================================================

@router.get("/weekly")
def generate_weekly_report(
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Generate the styled weekly progress report."""

    uid = user["id"]

    today = date.today()

    # --------------------------------------------------------
    # Fetch data
    # --------------------------------------------------------

    profile = get_profile(db, uid)

    analysis = get_latest_analysis(
        db,
        uid,
    )

    habits = get_recent_habits(
        db,
        uid,
        days=7,
    )

    # --------------------------------------------------------
    # Build styled PDF
    # --------------------------------------------------------

    pdf_output = build_weekly_report(
        profile=profile,
        analysis=analysis,
        habits=habits,
        today=today,
    )

    # --------------------------------------------------------
    # Return PDF
    # --------------------------------------------------------

    return StreamingResponse(
        io.BytesIO(pdf_output),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f"attachment; "
                f"filename=weekly_report_{today.isoformat()}.pdf"
            )
        },
    )


# ============================================================
# MONTHLY REPORT
# ============================================================

@router.get("/monthly")
def generate_monthly_report(
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Generate the styled monthly progress report."""

    uid = user["id"]

    today = date.today()

    month_start = today - timedelta(days=29)

    # --------------------------------------------------------
    # Fetch profile + analysis
    # --------------------------------------------------------

    profile = get_profile(
        db,
        uid,
    )

    analysis = get_latest_analysis(
        db,
        uid,
    )

    # --------------------------------------------------------
    # Fetch 30 days of habits
    # --------------------------------------------------------

    with db.cursor() as cur:

        cur.execute(
            """
            SELECT *
            FROM habit_logs
            WHERE user_id = %s
              AND log_date >= %s
              AND log_date <= %s
            ORDER BY log_date ASC
            """,
            (
                uid,
                month_start,
                today,
            ),
        )

        habits = cur.fetchall()

    # --------------------------------------------------------
    # Build styled PDF
    # --------------------------------------------------------

    pdf_output = build_monthly_report(
        profile=profile,
        analysis=analysis,
        habits=habits,
        start_date=month_start,
        today=today,
    )

    # --------------------------------------------------------
    # Return PDF
    # --------------------------------------------------------

    return StreamingResponse(
        io.BytesIO(pdf_output),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f"attachment; "
                f"filename=monthly_report_{today.isoformat()}.pdf"
            )
        },
    )