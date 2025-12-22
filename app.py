"""Streamlit UI for the AI Ingredient Safety Analyzer.

Provides a user-friendly interface for ingredient analysis
with personalized safety assessments.
"""

import io
import re
import urllib.parse
from datetime import datetime

import streamlit as st
from fpdf import FPDF
from pathlib import Path

from config.logging_config import setup_logging, setup_server_logging
from config.gemini_logger import get_gemini_logger
from state.schema import (
    ExpertiseLevel,
    RiskLevel,
    SkinType,
    UserProfile,
    ValidationResult,
)
from services.session import (
    generate_session_id,
    load_user_profile,
    save_user_profile,
)
from graph import run_analysis


# Initialize logging (application + server logs with daily rotation)
setup_logging()
setup_server_logging()

# Page configuration
st.set_page_config(
    page_title="AI Ingredient Safety Analyzer",
    page_icon="🔬",
    layout="wide",
)


def init_session_state() -> None:
    """Initialize Streamlit session state."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = generate_session_id()

    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None

    if "is_analyzing" not in st.session_state:
        st.session_state.is_analyzing = False

    if "show_logs" not in st.session_state:
        st.session_state.show_logs = False


def render_header() -> None:
    """Render page header with navigation."""
    col1, col2 = st.columns([4, 1])

    with col1:
        st.title("🔬 AI Powered Ingredient Safety Analyzer")
        st.markdown(
            "Analyze food and cosmetic ingredients for safety, "
            "personalized to your allergies, skin type and expertise."
        )

    with col2:
        st.write("")  # Spacing
        if st.button("📋 Gemini Logs", use_container_width=True):
            st.session_state.show_logs = not st.session_state.show_logs
            st.rerun()

    st.divider()


def render_input_form() -> tuple[str, str, UserProfile] | None:
    """Render the input form for ingredients and profile.

    Returns:
        Tuple of (product_name, ingredients_text, user_profile) or None.
    """
    with st.form("analysis_form"):
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Product Information")
            product_name = st.text_input(
                "Product Name (optional)",
                placeholder="e.g., Moisturizing Face Cream",
            )

            ingredients_text = st.text_area(
                "Ingredient List",
                placeholder="Paste ingredients here, separated by commas...\n\nExample: Water, Glycerin, Sodium Lauryl Sulfate, Fragrance",
                height=150,
            )

        with col2:
            st.subheader("Your Profile")

            # Load saved profile if exists
            saved_profile = load_user_profile(st.session_state.session_id)

            default_allergies = (
                saved_profile["allergies"] if saved_profile else []
            )

            allergies = st.multiselect(
                "Known Allergies",
                options=[
                    "Fragrance",
                    "Sulfates",
                    "Parabens",
                    "Formaldehyde",
                    "Peanut",
                    "Tree Nut",
                    "Milk/Dairy",
                    "Soy",
                    "Wheat/Gluten",
                    "Egg",
                    "Shellfish",
    
                ],
                default=default_allergies,
                help="Select any known allergies or sensitivities",
            )

            skin_type = st.radio(
                "Skin Type",
                options=["Normal", "Dry", "Oily", "Combination", "Sensitive"],
                index=4 if saved_profile and saved_profile["skin_type"] == SkinType.SENSITIVE else 0,
                horizontal=True,
            )

            expertise = st.radio(
                "Explanation Style",
                options=["Beginner","Intermediate", "Expert"],
                index=0,
                help="Beginner: Simple explanations. Intermediate: Some Techical details. Expert: Technical details.",
            )

        submitted = st.form_submit_button(
            "🔍 Analyze Ingredients",
            use_container_width=True,
            type="primary",
        )

        if submitted and ingredients_text.strip():
            profile = UserProfile(
                allergies=[a.lower() for a in allergies],
                skin_type=SkinType(skin_type.lower()),
                expertise=ExpertiseLevel(expertise.lower()),
            )
            # Save profile for future use
            save_user_profile(st.session_state.session_id, profile)
            return product_name or "Unnamed Product", ingredients_text, profile

    return None


def parse_ingredients(text: str) -> list[str]:
    """Parse ingredient text into list, removing duplicates.

    Args:
        text: Raw ingredient text.

    Returns:
        List of unique ingredient names (case-insensitive deduplication).
    """
    # Split by common separators
    ingredients = []
    for sep in [",", "\n", ";"]:
        if sep in text:
            ingredients = [i.strip() for i in text.split(sep)]
            break

    if not ingredients:
        ingredients = [text.strip()]

    # Clean up and remove duplicates (case-insensitive)
    seen = set()
    unique_ingredients = []
    for ingredient in ingredients:
        if ingredient and len(ingredient) > 1:
            # Normalize to lowercase for comparison
            normalized = ingredient.lower()
            if normalized not in seen:
                seen.add(normalized)
                unique_ingredients.append(ingredient)

    return unique_ingredients


def get_risk_color(risk: RiskLevel) -> str:
    """Get color for risk level.

    Args:
        risk: Risk level.

    Returns:
        Color string for display.
    """
    colors = {
        RiskLevel.LOW: "green",
        RiskLevel.MEDIUM: "orange",
        RiskLevel.HIGH: "red",
    }
    return colors.get(risk, "gray")


def get_safety_bar_color(rating: int) -> str:
    """Get color for safety rating bar.

    Args:
        rating: Safety rating 1-10.

    Returns:
        CSS color string.
    """
    if rating <= 3:
        return "#dc3545"  # Red
    elif rating <= 6:
        return "#fd7e14"  # Orange
    else:
        return "#28a745"  # Green


def render_safety_bar(rating: int, name: str) -> None:
    """Render a safety rating bar with progressive color.

    Args:
        rating: Safety rating 1-10.
        name: Ingredient name for accessibility.
    """
    color = get_safety_bar_color(rating)
    width_pct = rating * 15

    st.markdown(f"""
    <div style="margin: 5px 0;">
        <div style="background: #333; border-radius: 4px; height: 20px; width: 100%;">
            <div style="background: {color}; width: {width_pct}%; height: 100%;
                        border-radius: 4px; display: flex; align-items: center;
                        justify-content: center; color: white; font-weight: bold; font-size: 12px;">
                {rating}/10
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def inject_safety_bars_in_table(markdown_text: str, avg_score: int = 5) -> str:
    """Inject HTML safety bars into markdown table and Overall Verdict section.

    Args:
        markdown_text: The markdown text containing the ingredient analysis table.
        avg_score: Average safety score for the Overall Verdict bar.

    Returns:
        Modified markdown with safety ratings replaced by HTML bars.
    """
    lines = markdown_text.split('\n')
    result_lines = []
    in_table = False
    header_found = False
    safety_col_index = -1

    for i, line in enumerate(lines):
        # Check for Overall Verdict section and add bar next to the heading
        if line.strip().startswith('## Overall Verdict'):
            bar_color = get_safety_bar_color(avg_score)
            width_pct = avg_score * 10
            # Add bar inline next to the heading
            verdict_bar = (
                f' <div style="background:#333;border-radius:4px;height:22px;'
                f'width:150px;display:inline-block;vertical-align:middle;margin-left:10px;">'
                f'<div style="background:{bar_color};width:{width_pct}%;height:100%;'
                f'border-radius:4px;display:flex;align-items:center;'
                f'justify-content:center;color:white;font-weight:bold;font-size:11px;">'
                f'Avg Safety: {avg_score}/10</div></div>'
            )
            # Replace the heading with heading + bar
            modified_line = line.replace('## Overall Verdict', f'## Overall Verdict {verdict_bar}')
            result_lines.append(modified_line)
            continue

        # Check if this is a table row
        if '|' in line and line.strip().startswith('|'):
            cells = [c.strip() for c in line.split('|')]
            # Remove empty first/last cells from split
            cells = [c for c in cells if c or cells.index(c) not in [0, len(cells) - 1]]

            # Check for header row with Safety Rating
            if not header_found and 'Safety Rating' in line:
                header_found = True
                in_table = True
                # Find the index of Safety Rating column
                for j, cell in enumerate(cells):
                    if 'Safety Rating' in cell:
                        safety_col_index = j
                        break
                result_lines.append(line)
                continue

            # Skip separator row (contains dashes)
            if in_table and all(c.replace('-', '').replace(':', '').strip() == '' for c in cells if c):
                result_lines.append(line)
                continue

            # Process data rows
            if in_table and safety_col_index >= 0 and len(cells) > safety_col_index:
                # Extract safety rating value
                safety_cell = cells[safety_col_index]
                # Try to extract number from the cell (could be "8", "8/10", etc.)
                match = re.search(r'(\d+)', safety_cell)
                if match:
                    rating = int(match.group(1))
                    rating = max(1, min(10, rating))  # Clamp to 1-10
                    color = get_safety_bar_color(rating)
                    width_pct = rating * 10

                    # Create inline HTML bar
                    bar_html = (
                        f'<div style="background:#333;border-radius:4px;height:18px;'
                        f'width:80px;display:inline-block;vertical-align:middle;">'
                        f'<div style="background:{color};width:{width_pct}%;height:100%;'
                        f'border-radius:4px;display:flex;align-items:center;'
                        f'justify-content:center;color:white;font-weight:bold;font-size:11px;">'
                        f'{rating}/10</div></div>'
                    )

                    # Replace the safety rating in the line
                    # Split by | and replace the appropriate cell
                    parts = line.split('|')
                    # Find and replace the safety rating cell
                    cell_count = 0
                    for j, part in enumerate(parts):
                        if part.strip():
                            if cell_count == safety_col_index:
                                parts[j] = f' {bar_html} '
                                break
                            cell_count += 1
                    line = '|'.join(parts)

        else:
            # Not a table row - reset table tracking if we were in a table
            if in_table and header_found:
                in_table = False

        result_lines.append(line)

    return '\n'.join(result_lines)


def generate_pdf_report(report: dict, product_name: str, avg_score: int) -> bytes:
    """Generate a formatted PDF report with colors and styled tables.

    Args:
        report: The analysis report dictionary.
        product_name: Name of the product analyzed.
        avg_score: Average safety score.

    Returns:
        PDF as bytes.
    """
    pdf = FPDF(orientation='L', format='A4')  # Landscape A4
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)

    # Color definitions (RGB)
    COLOR_RED = (220, 53, 69)      # #dc3545
    COLOR_ORANGE = (253, 126, 20)  # #fd7e14
    COLOR_GREEN = (40, 167, 69)    # #28a745
    COLOR_GRAY = (51, 51, 51)      # #333
    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    COLOR_LIGHT_GRAY = (240, 240, 240)

    def get_rating_color(rating: int) -> tuple:
        """Get color based on safety rating."""
        if rating <= 3:
            return COLOR_RED
        elif rating <= 6:
            return COLOR_ORANGE
        else:
            return COLOR_GREEN

    def safe_text(text: str, max_len: int = 80) -> str:
        """Truncate and clean text for PDF."""
        if not text:
            return ""
        text = re.sub(r'<[^>]+>', '', str(text))
        text = text.replace('**', '').replace('*', '')
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        text = ''.join(c if ord(c) < 128 else '?' for c in text)
        text = ' '.join(text.split())
        if len(text) > max_len:
            return text[:max_len-3] + "..."
        return text

    def draw_safety_bar(x: float, y: float, rating: int, width: float = 40, height: float = 6):
        """Draw a colored safety rating bar."""
        color = get_rating_color(rating)
        fill_width = (rating / 10) * width

        # Background bar (gray)
        pdf.set_fill_color(*COLOR_GRAY)
        pdf.rect(x, y, width, height, 'F')

        # Filled portion (colored)
        pdf.set_fill_color(*color)
        pdf.rect(x, y, fill_width, height, 'F')

        # Rating text
        pdf.set_xy(x, y)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*COLOR_WHITE)
        pdf.cell(width, height, f"{rating}/10", align="C")
        pdf.set_text_color(*COLOR_BLACK)

    def extract_rating(text: str) -> int:
        """Extract numeric rating from text like '7/10' or '7'."""
        match = re.search(r'(\d+)', str(text))
        if match:
            return min(10, max(1, int(match.group(1))))
        return 5

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*COLOR_BLACK)
    pdf.cell(0, 14, "Ingredient Safety Analysis Report", ln=True, align="C")
    pdf.ln(3)

    # Product name and date
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Product: {safe_text(product_name, 80)}", ln=True)
    pdf.cell(0, 7, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(5)

    # Overall Risk with colored bar
    overall_risk = report["overall_risk"].value.upper()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(80, 10, f"Overall Risk: {overall_risk}")

    # Draw overall safety bar
    bar_x = pdf.get_x() + 5
    bar_y = pdf.get_y() + 2
    draw_safety_bar(bar_x, bar_y, avg_score, width=50, height=8)
    pdf.ln(12)

    # Parse the LLM summary
    summary = report.get("summary", "")
    lines = summary.split('\n')

    # Table column widths (total ~267mm for landscape A4 minus margins)
    col_widths = [55, 60, 25, 55, 30, 42]  # Ingredient, Purpose, Rating, Concerns, Rec, Allergy
    table_started = False

    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(2)
            continue

        # Handle headers
        if line.startswith('## '):
            table_started = False
            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(*COLOR_BLACK)
            header_text = safe_text(line.replace('## ', ''), 80)
            pdf.cell(0, 8, header_text, ln=True)
            continue

        # Skip separator rows
        if '---' in line or line.startswith('IMPORTANT') or line.startswith('|--'):
            continue

        # Handle table rows
        if line.startswith('|') and '|' in line[1:]:
            cells = [c.strip() for c in line.split('|')]
            cells = [c for c in cells if c]

            if not cells:
                continue

            is_header = 'Ingredient' in str(cells[0])

            if is_header:
                table_started = True
                pdf.ln(3)
                # Draw header row with background
                pdf.set_fill_color(*COLOR_GRAY)
                pdf.set_text_color(*COLOR_WHITE)
                pdf.set_font("Helvetica", "B", 8)

                headers = ["Ingredient", "Purpose", "Safety", "Concerns", "Recommend", "Allergy Risk"]
                for i, header in enumerate(headers):
                    pdf.cell(col_widths[i], 8, header, border=1, align="C", fill=True)
                pdf.ln()
                pdf.set_text_color(*COLOR_BLACK)

            elif table_started and len(cells) >= 5:
                # Data row
                pdf.set_font("Helvetica", "", 7)
                row_y = pdf.get_y()

                # Ingredient name
                pdf.set_fill_color(*COLOR_LIGHT_GRAY)
                pdf.cell(col_widths[0], 10, safe_text(cells[0], 28), border=1, fill=True)

                # Purpose
                pdf.set_fill_color(*COLOR_WHITE)
                pdf.cell(col_widths[1], 10, safe_text(cells[1] if len(cells) > 1 else "", 30), border=1)

                # Safety Rating with colored bar
                rating = extract_rating(cells[2] if len(cells) > 2 else "5")
                rating_x = pdf.get_x()
                pdf.cell(col_widths[2], 10, "", border=1)  # Empty cell for bar
                # Draw bar inside cell
                draw_safety_bar(rating_x + 2, row_y + 2, rating, width=col_widths[2] - 4, height=6)
                pdf.set_xy(rating_x + col_widths[2], row_y)

                # Concerns
                pdf.cell(col_widths[3], 10, safe_text(cells[3] if len(cells) > 3 else "", 28), border=1)

                # Recommendation with color
                rec_text = safe_text(cells[4] if len(cells) > 4 else "", 15).upper()
                if "AVOID" in rec_text:
                    pdf.set_text_color(*COLOR_RED)
                elif "CAUTION" in rec_text:
                    pdf.set_text_color(*COLOR_ORANGE)
                else:
                    pdf.set_text_color(*COLOR_GREEN)
                pdf.set_font("Helvetica", "B", 7)
                pdf.cell(col_widths[4], 10, rec_text, border=1, align="C")
                pdf.set_text_color(*COLOR_BLACK)
                pdf.set_font("Helvetica", "", 7)

                # Allergy Risk
                allergy = safe_text(cells[5] if len(cells) > 5 else "", 20)
                if "HIGH" in allergy.upper():
                    pdf.set_text_color(*COLOR_RED)
                pdf.cell(col_widths[5], 10, allergy, border=1)
                pdf.set_text_color(*COLOR_BLACK)

                pdf.ln()
            continue

        # Regular text
        clean_line = safe_text(line, 120)
        if clean_line:
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 5, clean_line, ln=True)

    # Allergen Warnings with red styling
    if report.get("allergen_warnings"):
        pdf.ln(6)
        pdf.set_fill_color(*COLOR_RED)
        pdf.set_text_color(*COLOR_WHITE)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, " ALLERGEN WARNINGS ", ln=True, fill=True)
        pdf.set_text_color(*COLOR_BLACK)
        pdf.set_font("Helvetica", "", 9)
        for warning in report["allergen_warnings"]:
            pdf.set_text_color(*COLOR_RED)
            pdf.cell(0, 6, f"  ! {safe_text(warning, 100)}", ln=True)
        pdf.set_text_color(*COLOR_BLACK)

    # Footer
    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 5, "Generated by AI Ingredient Safety Analyzer", ln=True, align="C")

    return bytes(pdf.output())


def render_results(result: dict) -> None:
    """Render analysis results.

    Args:
        result: Workflow result state.
    """
    st.divider()

    # Check for errors
    if result.get("error"):
        st.error(f"Analysis failed: {result['error']}")
        return

    report = result.get("analysis_report")
    if not report:
        st.warning("No analysis report generated.")
        return

    feedback = result.get("critic_feedback", {})

    # Status banner with execution time
    exec_time = result.get("execution_time", 0)
    time_str = f" ({exec_time:.1f}s)" if exec_time > 0 else ""

    if feedback.get("result") == ValidationResult.APPROVED:
        st.success(f"✅ Analysis Complete - Quality Verified{time_str}")
    elif feedback.get("result") == ValidationResult.ESCALATED:
        st.warning(f"⚠️ Analysis Complete - Reduced Confidence{time_str}")
    else:
        st.info(f"ℹ️ Analysis Complete{time_str}")

    # Get average safety score for the colored bar
    avg_score = report.get("average_safety_score", 5)
    overall_risk = report["overall_risk"]

    # Quick stats and Stage timings in collapsible expander
    with st.expander("📊 Quick Stats & Timings", expanded=False):
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Display Overall Risk with colored bar
            risk_label = overall_risk.value.upper()
            bar_color = get_safety_bar_color(avg_score)
            st.metric("Overall Risk", risk_label)
            # Add colored bar based on average safety score
            width_pct = avg_score * 10
            st.markdown(f"""
            <div style="background:#333;border-radius:4px;height:20px;width:100%;margin-top:-10px;">
                <div style="background:{bar_color};width:{width_pct}%;height:100%;
                            border-radius:4px;display:flex;align-items:center;
                            justify-content:center;color:white;font-weight:bold;font-size:12px;">
                    {avg_score}/10
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.metric("Ingredients Analyzed", len(report["assessments"]))

        with col3:
            st.metric("Allergen Warnings", len(report["allergen_warnings"]))

        with col4:
            if exec_time > 0:
                st.metric("Total Time", f"{exec_time:.1f}s")

        # Stage timings
        stage_timings = result.get("stage_timings")
        if stage_timings:
            st.markdown("#### ⏱️ Stage Timings")
            timing_cols = st.columns(3)

            with timing_cols[0]:
                research_time = stage_timings.get("research_time", 0)
                st.metric("🔍 Research", f"{research_time:.2f}s")

            with timing_cols[1]:
                analysis_time = stage_timings.get("analysis_time", 0)
                st.metric("📝 Analysis", f"{analysis_time:.2f}s")

            with timing_cols[2]:
                critic_time = stage_timings.get("critic_time", 0)
                st.metric("✅ Validation", f"{critic_time:.2f}s")

    # LLM-generated analysis with markdown tables
    # The summary now contains the full analysis from the LLM
    # Inject safety bars into the table for visual representation
    st.markdown("---")
    summary_with_bars = inject_safety_bars_in_table(report["summary"], avg_score)
    st.markdown(summary_with_bars, unsafe_allow_html=True)

    # Allergen warnings from structured assessment (additional prominence)
    if report["allergen_warnings"]:
        st.markdown("---")
        st.subheader("🚨 Your Allergen Alerts")
        for warning in report["allergen_warnings"]:
            st.error(warning)

    # Collapsible detailed assessments (no safety bars - those are in the main table)
    with st.expander("📊 Detailed Ingredient Assessments", expanded=False):
        for assessment in report["assessments"]:
            icon = "🚨" if assessment["is_allergen_match"] else "🧪"
            risk_label = assessment["risk_level"].value.upper()

            st.markdown(f"### {icon} {assessment['name']} - {risk_label}")

            if assessment["is_allergen_match"]:
                st.error("**AVOID** - Matches your declared allergies!")

            st.markdown(assessment["rationale"])

            if assessment["alternatives"]:
                st.markdown("**Suggested Alternatives:**")
                for alt in assessment["alternatives"]:
                    st.markdown(f"- {alt}")

            st.markdown("---")

    # Debug info (collapsed)
    with st.expander("🔧 Debug Information"):
        # Build gate status for display
        gate_status = {}
        if feedback:
            gate_status = {
                "completeness": "PASS" if feedback.get("completeness_ok", True) else "FAIL",
                "format": "PASS" if feedback.get("format_ok", True) else "FAIL",
                "allergens": "PASS" if feedback.get("allergens_ok", True) else "FAIL",
                "consistency": "PASS" if feedback.get("consistency_ok", True) else "FAIL",
                "tone": "PASS" if feedback.get("tone_ok", True) else "FAIL",
            }

        # Build timing info
        timing_info = {}
        if stage_timings:
            timing_info = {
                "research_seconds": round(stage_timings.get("research_time", 0), 3),
                "analysis_seconds": round(stage_timings.get("analysis_time", 0), 3),
                "critic_seconds": round(stage_timings.get("critic_time", 0), 3),
            }

        st.json({
            "session_id": st.session_state.session_id,
            "routing_history": result.get("routing_history", []),
            "retry_count": result.get("retry_count", 0),
            "stage_timings": timing_info,
            "validation_gates": gate_status,
            "failed_gates": feedback.get("failed_gates", []) if feedback else [],
            "critic_feedback": feedback.get("feedback", "") if feedback else "",
        })

    # PDF Download and Share section
    st.markdown("---")
    st.subheader("📤 Export & Share")

    col1, col2 = st.columns(2)

    with col1:
        # Generate PDF
        product_name = report.get("product_name", "Unknown Product")
        pdf_bytes = generate_pdf_report(report, product_name, avg_score)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ingredient_report_{timestamp}.pdf"

        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True,
        )

    with col2:
        # Generate shareable text summary
        overall_risk = report["overall_risk"].value.upper()
        share_text = f"""🔬 Ingredient Safety Analysis Report

📊 Overall Risk: {overall_risk}
⭐ Safety Score: {avg_score}/10
📝 Ingredients Analyzed: {len(report['assessments'])}

Generated by AI Ingredient Safety Analyzer
"""
        # Copy to clipboard button using Streamlit's native approach
        st.download_button(
            label="📋 Download Summary (TXT)",
            data=share_text,
            file_name=f"ingredient_summary_{timestamp}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # Share via system (using mailto and other links)
    st.markdown("#### Share via:")
    share_cols = st.columns(3)

    # URL encode the share text
    encoded_text = urllib.parse.quote(share_text)

    with share_cols[0]:
        email_link = f"mailto:?subject=Ingredient%20Safety%20Report&body={encoded_text}"
        st.markdown(f'<a href="{email_link}" target="_blank"><button style="width:100%;padding:10px;cursor:pointer;">📧 Email</button></a>', unsafe_allow_html=True)

    with share_cols[1]:
        # WhatsApp share
        whatsapp_link = f"https://wa.me/?text={encoded_text}"
        st.markdown(f'<a href="{whatsapp_link}" target="_blank"><button style="width:100%;padding:10px;cursor:pointer;">💬 WhatsApp</button></a>', unsafe_allow_html=True)

    with share_cols[2]:
        # Twitter/X share
        twitter_link = f"https://twitter.com/intent/tweet?text={encoded_text}"
        st.markdown(f'<a href="{twitter_link}" target="_blank"><button style="width:100%;padding:10px;cursor:pointer;">🐦 Twitter/X</button></a>', unsafe_allow_html=True)


def render_gemini_logs() -> None:
    """Render the Gemini logs page."""
    st.subheader("📋 Gemini API Logs")
    st.markdown("View all Gemini API interactions (latest first)")

    # Back button
    if st.button("← Back to Analyzer"):
        st.session_state.show_logs = False
        st.rerun()

    st.divider()

    gemini_logger = get_gemini_logger()

    # Show available dates
    available_dates = gemini_logger.get_available_dates()

    if not available_dates:
        st.info("No Gemini logs found yet. Run an analysis to generate logs.")
        return

    # Date selector
    selected_date = st.selectbox(
        "Select Date",
        options=available_dates,
        index=0,
        format_func=lambda x: f"{x} {'(Today)' if x == available_dates[0] else ''}",
    )

    # Load and display logs
    log_file = gemini_logger.log_dir / f"gemini_{selected_date}.log"

    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                log_content = f.read()

            if log_content.strip():
                # Count entries
                entry_count = log_content.count("TIMESTAMP:")
                st.caption(f"Found {entry_count} log entries")

                # Auto-refresh option
                auto_refresh = st.checkbox("Auto-refresh (every 5 seconds)", value=False)
                if auto_refresh:
                    st.rerun()

                # Display logs in a scrollable container
                st.code(log_content, language=None)

                # Download button
                st.download_button(
                    label="📥 Download Logs",
                    data=log_content,
                    file_name=f"gemini_logs_{selected_date}.txt",
                    mime="text/plain",
                )
            else:
                st.info("Log file is empty.")

        except Exception as e:
            st.error(f"Error reading logs: {e}")
    else:
        st.warning(f"No log file found for {selected_date}")


def main() -> None:
    """Main application entry point."""
    init_session_state()
    render_header()

    # Show logs page or main analyzer
    if st.session_state.show_logs:
        render_gemini_logs()
        return

    # Input form
    form_result = render_input_form()

    if form_result:
        product_name, ingredients_text, profile = form_result
        ingredients = parse_ingredients(ingredients_text)

        if len(ingredients) < 1:
            st.error("Please enter at least one ingredient.")
            return

        import time
        start_time = time.time()

        with st.spinner(f"Analyzing {len(ingredients)} ingredients..."):
            result = run_analysis(
                session_id=st.session_state.session_id,
                product_name=product_name,
                ingredients=ingredients,
                allergies=profile["allergies"],
                skin_type=profile["skin_type"].value,
                expertise=profile["expertise"].value,
            )
            # Store execution time in result
            result["execution_time"] = time.time() - start_time
            st.session_state.analysis_result = result

    # Display results if available
    if st.session_state.analysis_result:
        render_results(st.session_state.analysis_result)


if __name__ == "__main__":
    main()
