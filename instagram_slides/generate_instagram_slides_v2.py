"""
PerisAI Instagram Campaign Generator v2
Generates 10 professional Instagram slides (1080x1350px, 4:5 ratio)
Uses Pillow with proper font fallback for emoji support
"""

from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

# Instagram standard: 1080x1350px (4:5 ratio)
WIDTH = 1080
HEIGHT = 1350

# Color palette
COLOR_PRIMARY = "#1E40AF"      # Deep blue
COLOR_ACCENT = "#DC2626"       # Red/orange
COLOR_SECONDARY = "#10B981"    # Green
COLOR_DARK = "#1F2937"         # Dark gray
COLOR_LIGHT = "#F3F4F6"        # Light gray
COLOR_WHITE = "#FFFFFF"

def create_image(bg_color=COLOR_WHITE):
    """Create base image with background color"""
    return Image.new('RGB', (WIDTH, HEIGHT), bg_color)

def get_font_with_emoji(size, bold=True):
    """Get font with emoji support - tries multiple fonts"""
    font_names = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        ("/usr/share/fonts/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/noto/NotoSans-Regular.ttf"),
    ]
    
    for font_path in font_names:
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
        except:
            pass
    
    # Fallback to default
    return ImageFont.load_default()

def add_emoji_text(draw, emoji_text_pairs, start_y, x_pos, font_size, color, line_height=60):
    """
    Add text with emoji support
    emoji_text_pairs: list of tuples like [("💼", "Your company has data"), ...]
    """
    y_pos = start_y
    font = get_font_with_emoji(font_size, bold=False)
    
    for emoji, text in emoji_text_pairs:
        line = f"{emoji} {text}"
        draw.text((x_pos, y_pos), line, font=font, fill=color)
        y_pos += line_height

def slide_1_problem():
    """Slide 1: The Problem - Is Your Data Trapped?"""
    img = create_image("#FEF2F2")  # Light red
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font_with_emoji(56, bold=True)
    draw.text((54, 100), "Is Your Data", font=title_font, fill=COLOR_ACCENT)
    draw.text((54, 180), "Trapped?", font=title_font, fill=COLOR_ACCENT)
    
    # Content with emojis
    content_font = get_font_with_emoji(28, bold=False)
    items = [
        ("💼", "Your company has data mountains"),
        ("📊", "But insights take WEEKS"),
        ("💰", "Hiring analysts = $200K+/year"),
        ("🤷", "Decisions based on Excel guesses"),
    ]
    
    y_pos = 270
    for emoji, text in items:
        draw.text((54, y_pos), f"{emoji} {text}", font=content_font, fill=COLOR_DARK)
        y_pos += 60
    
    # Bottom callout
    bottom_box = Image.new('RGB', (WIDTH - 108, 200), COLOR_ACCENT)
    img.paste(bottom_box, (54, 1050))
    draw = ImageDraw.Draw(img)
    
    cta_font = get_font_with_emoji(32, bold=True)
    small_font = get_font_with_emoji(24, bold=False)
    
    draw.text((80, 1080), "This is costing you MILLIONS 💸", font=cta_font, fill=COLOR_WHITE)
    draw.text((80, 1160), "👉 DM us if this sounds familiar", font=small_font, fill=COLOR_WHITE)
    
    return img

def slide_2_vision():
    """Slide 2: The Vision"""
    img = create_image(COLOR_PRIMARY)
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font_with_emoji(48, bold=True)
    draw.text((54, 80), "What If Analytics", font=title_font, fill=COLOR_WHITE)
    draw.text((54, 160), "Took 2 Minutes?", font=title_font, fill=COLOR_WHITE)
    
    small_font = get_font_with_emoji(26, bold=False)
    micro_font = get_font_with_emoji(20, bold=False)
    
    # Old way
    draw.text((54, 280), "OLD WAY (weeks)", font=small_font, fill=COLOR_ACCENT)
    draw.text((54, 330), "Data → SQL → Analyst → Reports → Decisions", font=micro_font, fill=COLOR_LIGHT)
    
    # Arrow
    arrow_font = get_font_with_emoji(48, bold=False)
    draw.text((480, 400), "⬇️", font=arrow_font, fill=COLOR_SECONDARY)
    
    # New way
    draw.text((54, 480), "NEW WAY (seconds)", font=small_font, fill=COLOR_SECONDARY)
    draw.text((54, 530), "Ask Question → AI Bot → Answer", font=micro_font, fill=COLOR_LIGHT)
    
    # Example
    example_box = Image.new('RGB', (WIDTH - 108, 280), COLOR_WHITE)
    img.paste(example_box, (54, 680))
    draw = ImageDraw.Draw(img)
    
    example_font = get_font_with_emoji(24, bold=False)
    large_example = get_font_with_emoji(26, bold=False)
    
    draw.text((80, 700), "\"Show loan defaults by branch\"", font=large_example, fill=COLOR_PRIMARY)
    draw.text((80, 760), "🤖 PerisAI analyzes your data", font=example_font, fill=COLOR_DARK)
    draw.text((80, 810), "📈 Harvard-style table appears", font=example_font, fill=COLOR_DARK)
    draw.text((80, 860), "💡 AI explains the context", font=example_font, fill=COLOR_DARK)
    
    draw.text((54, 1020), "No code. No training. Just ask.", font=get_font_with_emoji(28, bold=True), fill=COLOR_WHITE)
    draw.text((54, 1080), "#DataIntelligence #AI", font=get_font_with_emoji(22, bold=False), fill=COLOR_LIGHT)
    
    return img

def slide_3_personas():
    """Slide 3: Meet Kei & Kin"""
    img = create_image(COLOR_LIGHT)
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font_with_emoji(52, bold=True)
    draw.text((54, 80), "Your Dual AI", font=title_font, fill=COLOR_PRIMARY)
    draw.text((54, 150), "Dream Team", font=title_font, fill=COLOR_PRIMARY)
    
    # Kei section
    kei_box = Image.new('RGB', (400, 500), COLOR_PRIMARY)
    img.paste(kei_box, (54, 280))
    draw = ImageDraw.Draw(img)
    
    header_font = get_font_with_emoji(36, bold=True)
    subheader_font = get_font_with_emoji(24, bold=False)
    body_font = get_font_with_emoji(18, bold=False)
    
    draw.text((74, 300), "KEI", font=header_font, fill=COLOR_WHITE)
    draw.text((74, 360), "The Quant Guru", font=subheader_font, fill=COLOR_WHITE)
    draw.text((74, 420), "• MIT-trained", font=body_font, fill=COLOR_LIGHT)
    draw.text((74, 460), "• Gives: Numbers & stats", font=body_font, fill=COLOR_LIGHT)
    draw.text((74, 500), "• ARIMA, GARCH, etc.", font=body_font, fill=COLOR_LIGHT)
    draw.text((74, 540), "• Says: \"The correlation...\"", font=body_font, fill=COLOR_LIGHT)
    
    # Kin section
    kin_box = Image.new('RGB', (400, 500), COLOR_SECONDARY)
    img.paste(kin_box, (626, 280))
    draw = ImageDraw.Draw(img)
    
    draw.text((646, 300), "KIN", font=header_font, fill=COLOR_WHITE)
    draw.text((646, 360), "The Story Analyst", font=subheader_font, fill=COLOR_WHITE)
    draw.text((646, 420), "• CFA + PhD Economist", font=body_font, fill=COLOR_LIGHT)
    draw.text((646, 460), "• Gives: Insights & context", font=body_font, fill=COLOR_LIGHT)
    draw.text((646, 500), "• Why it matters", font=body_font, fill=COLOR_LIGHT)
    draw.text((646, 540), "• Says: \"This means...\"", font=body_font, fill=COLOR_LIGHT)
    
    # Bottom
    draw.text((54, 840), "Rigor + Narrative in ONE", font=get_font_with_emoji(28, bold=True), fill=COLOR_DARK)
    draw.text((54, 1000), "\"Give me both perspectives\"", font=get_font_with_emoji(24, bold=False), fill=COLOR_PRIMARY)
    
    return img

def slide_4_banking():
    """Slide 4: Banking Use Case"""
    img = create_image("#ECFDF5")  # Light green
    draw = ImageDraw.Draw(img)
    
    # Title with emoji
    emoji_font = get_font_with_emoji(60, bold=False)
    title_font = get_font_with_emoji(48, bold=True)
    
    draw.text((54, 80), "🏦", font=emoji_font, fill=COLOR_SECONDARY)
    draw.text((54, 160), "Treasury Teams", font=title_font, fill=COLOR_PRIMARY)
    draw.text((54, 240), "Love This", font=title_font, fill=COLOR_PRIMARY)
    
    # Subtitle
    draw.text((54, 330), "Auction Forecasting Case Study", font=get_font_with_emoji(24, bold=False), fill=COLOR_DARK)
    
    # Problem
    small_font = get_font_with_emoji(22, bold=False)
    draw.text((54, 420), "OLD: Guess demand", font=small_font, fill=COLOR_ACCENT)
    draw.text((80, 460), "Miss pricing windows", font=small_font, fill=COLOR_ACCENT)
    draw.text((80, 500), "Leave $M on the table", font=small_font, fill=COLOR_ACCENT)
    
    # Solution box
    solution_box = Image.new('RGB', (WIDTH - 108, 320), COLOR_SECONDARY)
    img.paste(solution_box, (54, 580))
    draw = ImageDraw.Draw(img)
    
    header = get_font_with_emoji(28, bold=True)
    body = get_font_with_emoji(22, bold=False)
    
    draw.text((80, 600), "PerisAI Way:", font=header, fill=COLOR_WHITE)
    draw.text((80, 660), "🤖 Forecast demand 1-3 months ahead", font=body, fill=COLOR_WHITE)
    draw.text((80, 710), "📊 ML ensemble (80% accurate)", font=body, fill=COLOR_WHITE)
    draw.text((80, 760), "💰 Save $10M+/year in pricing", font=body, fill=COLOR_WHITE)
    
    draw.text((54, 1040), "\"We cut forecasting time by 90%\"", font=get_font_with_emoji(26, bold=False), fill=COLOR_DARK)
    draw.text((54, 1100), "Treasury Director", font=get_font_with_emoji(20, bold=False), fill=COLOR_PRIMARY)
    
    return img

def slide_5_investor():
    """Slide 5: Investor Use Case"""
    img = create_image("#EFF6FF")  # Light blue
    draw = ImageDraw.Draw(img)
    
    # Title
    emoji_font = get_font_with_emoji(60, bold=False)
    title_font = get_font_with_emoji(44, bold=True)
    
    draw.text((54, 80), "📈", font=emoji_font, fill=COLOR_PRIMARY)
    draw.text((54, 160), "5-Minute Analysis", font=title_font, fill=COLOR_PRIMARY)
    draw.text((54, 230), "Instead of 5 Hours", font=title_font, fill=COLOR_PRIMARY)
    
    draw.text((54, 320), "For Fund Managers", font=get_font_with_emoji(24, bold=False), fill=COLOR_DARK)
    
    # Comparison
    small_font = get_font_with_emoji(22, bold=False)
    micro_font = get_font_with_emoji(20, bold=False)
    
    draw.text((54, 400), "Traditional:", font=small_font, fill=COLOR_ACCENT)
    draw.text((80, 440), "Excel grind → 2-5 hours per analysis", font=micro_font, fill=COLOR_DARK)
    
    draw.text((54, 500), "PerisAI:", font=small_font, fill=COLOR_SECONDARY)
    draw.text((80, 540), "One question → 10 seconds", font=micro_font, fill=COLOR_DARK)
    
    # Questions
    draw.text((54, 620), "Portfolio Managers Ask:", font=get_font_with_emoji(24, bold=False), fill=COLOR_PRIMARY)
    
    questions = [
        ("✅", "\"Compare 5Y vs 10Y yields\""),
        ("✅", "\"Detect structural breaks\""),
        ("✅", "\"What's the volatility forecast?\""),
        ("✅", "\"Are these bonds cointegrated?\""),
    ]
    
    y_pos = 670
    for symbol, question in questions:
        draw.text((80, y_pos), f"{symbol} {question}", font=micro_font, fill=COLOR_DARK)
        y_pos += 40
    
    # Impact box
    impact_box = Image.new('RGB', (WIDTH - 108, 180), COLOR_PRIMARY)
    img.paste(impact_box, (54, 900))
    draw = ImageDraw.Draw(img)
    
    impact_font = get_font_with_emoji(24, bold=False)
    draw.text((80, 930), "⏰ 8+ hours saved per analyst/week", font=impact_font, fill=COLOR_WHITE)
    draw.text((80, 980), "💰 $100K+ annual efficiency gains", font=impact_font, fill=COLOR_WHITE)
    
    return img

def slide_6_features():
    """Slide 6: Features Overview"""
    img = create_image(COLOR_LIGHT)
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font_with_emoji(52, bold=True)
    draw.text((54, 80), "Features at a", font=title_font, fill=COLOR_PRIMARY)
    draw.text((54, 150), "Glance", font=title_font, fill=COLOR_PRIMARY)
    
    features = [
        ("📊", "Auto Database Connection", "Any SQL, CSV, or API"),
        ("🤖", "7+ Analytics", "ARIMA, GARCH, Cointegration..."),
        ("📉", "ML Forecasting", "Predict 3-12 months ahead"),
        ("📄", "Export Everything", "HTML, Excel, API access"),
        ("🌐", "Natural Language", "Ask in plain English"),
    ]
    
    feature_title = get_font_with_emoji(24, bold=False)
    feature_desc = get_font_with_emoji(18, bold=False)
    
    y_pos = 280
    for emoji, title, desc in features:
        draw.text((54, y_pos), f"{emoji} {title}", font=feature_title, fill=COLOR_PRIMARY)
        draw.text((100, y_pos + 40), desc, font=feature_desc, fill=COLOR_DARK)
        y_pos += 120
    
    # Bottom
    bottom_box = Image.new('RGB', (WIDTH - 108, 140), COLOR_ACCENT)
    img.paste(bottom_box, (54, 1100))
    draw = ImageDraw.Draw(img)
    
    bottom_font = get_font_with_emoji(28, bold=True)
    sub_font = get_font_with_emoji(20, bold=False)
    
    draw.text((80, 1130), "Deploy in 2-4 weeks", font=bottom_font, fill=COLOR_WHITE)
    draw.text((80, 1180), "(vs 6-12 months traditional)", font=sub_font, fill=COLOR_WHITE)
    
    return img

def slide_7_pricing():
    """Slide 7: Pricing"""
    img = create_image("#FFFBEB")  # Light yellow
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font_with_emoji(48, bold=True)
    draw.text((54, 80), "Cost Less Than", font=title_font, fill=COLOR_PRIMARY)
    draw.text((54, 160), "1 Analyst", font=title_font, fill=COLOR_PRIMARY)
    
    # Alternatives
    alt_font = get_font_with_emoji(22, bold=False)
    draw.text((54, 280), "Bloomberg Terminal: $300K/year", font=alt_font, fill=COLOR_ACCENT)
    draw.text((54, 330), "Tableau: $500K+ setup", font=alt_font, fill=COLOR_ACCENT)
    draw.text((54, 380), "Hire Analyst: $200K+/year", font=alt_font, fill=COLOR_ACCENT)
    
    # PerisAI pricing
    price_box1 = Image.new('RGB', (400, 240), COLOR_SECONDARY)
    img.paste(price_box1, (54, 480))
    draw = ImageDraw.Draw(img)
    
    price_header = get_font_with_emoji(28, bold=True)
    price_amount = get_font_with_emoji(32, bold=True)
    price_detail = get_font_with_emoji(18, bold=False)
    
    draw.text((74, 510), "PerisAI SaaS", font=price_header, fill=COLOR_WHITE)
    draw.text((74, 570), "$5K–$50K/month", font=price_amount, fill=COLOR_WHITE)
    draw.text((74, 630), "Unlimited analytics", font=price_detail, fill=COLOR_WHITE)
    
    # Custom pricing
    price_box2 = Image.new('RGB', (400, 240), COLOR_PRIMARY)
    img.paste(price_box2, (626, 480))
    draw = ImageDraw.Draw(img)
    
    draw.text((646, 510), "Custom Bot", font=price_header, fill=COLOR_WHITE)
    draw.text((646, 570), "$50K–$500K", font=price_amount, fill=COLOR_WHITE)
    draw.text((646, 630), "One-time deployment", font=price_detail, fill=COLOR_WHITE)
    
    # ROI
    roi_font = get_font_with_emoji(24, bold=False)
    draw.text((54, 800), "Data-driven decisions = Multi-million savings", font=roi_font, fill=COLOR_DARK)
    
    draw.text((54, 950), "\"We saved $200K in Year 1\"", font=get_font_with_emoji(26, bold=False), fill=COLOR_PRIMARY)
    draw.text((54, 1010), "XYZ Fund Manager", font=get_font_with_emoji(20, bold=False), fill=COLOR_DARK)
    
    return img

def slide_8_indonesia():
    """Slide 8: Indonesia Opportunity"""
    img = create_image("#FEF3C7")  # Light amber
    draw = ImageDraw.Draw(img)
    
    # Title
    emoji_font = get_font_with_emoji(60, bold=False)
    title_font = get_font_with_emoji(48, bold=True)
    
    draw.text((54, 80), "🇮🇩", font=emoji_font, fill=COLOR_PRIMARY)
    draw.text((54, 160), "Built for", font=title_font, fill=COLOR_PRIMARY)
    draw.text((54, 230), "Emerging Markets", font=title_font, fill=COLOR_PRIMARY)
    
    # Why Indonesia
    draw.text((54, 330), "Why PerisAI Started Here", font=get_font_with_emoji(26, bold=False), fill=COLOR_DARK)
    
    facts = [
        "📊 300+ Indonesian enterprises with data but NO insights",
        "💔 Talent shortage: Only 200 data scientists vs 5K+ companies",
        "💰 TAM: $45M+ untapped market in Indonesia alone",
    ]
    
    fact_font = get_font_with_emoji(22, bold=False)
    y_pos = 400
    for fact in facts:
        draw.text((54, y_pos), fact, font=fact_font, fill=COLOR_DARK)
        y_pos += 80
    
    # Proof
    proof_box = Image.new('RGB', (WIDTH - 108, 280), COLOR_PRIMARY)
    img.paste(proof_box, (54, 700))
    draw = ImageDraw.Draw(img)
    
    header = get_font_with_emoji(26, bold=True)
    body = get_font_with_emoji(20, bold=False)
    
    draw.text((80, 730), "We're Already Proving It:", font=header, fill=COLOR_WHITE)
    draw.text((80, 790), "• Bank Indonesia data integration", font=body, fill=COLOR_WHITE)
    draw.text((80, 830), "• Ministry of Finance forecasts", font=body, fill=COLOR_WHITE)
    draw.text((80, 870), "• Real treasury users (beta)", font=body, fill=COLOR_WHITE)
    draw.text((80, 910), "• 80%+ forecast accuracy", font=body, fill=COLOR_WHITE)
    
    return img

def slide_9_team():
    """Slide 9: Team & Roadmap"""
    img = create_image(COLOR_LIGHT)
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font_with_emoji(48, bold=True)
    draw.text((54, 80), "The Team &", font=title_font, fill=COLOR_PRIMARY)
    draw.text((54, 150), "What's Next", font=title_font, fill=COLOR_PRIMARY)
    
    # Team
    header_font = get_font_with_emoji(26, bold=False)
    body_font = get_font_with_emoji(20, bold=False)
    
    draw.text((54, 280), "Our Team:", font=header_font, fill=COLOR_PRIMARY)
    team_points = [
        "✓ Data scientists from top finance",
        "✓ Full-stack engineers (proven track)",
        "✓ Former BI & MOF advisors",
    ]
    y_pos = 340
    for point in team_points:
        draw.text((80, y_pos), point, font=body_font, fill=COLOR_DARK)
        y_pos += 50
    
    # Proof
    draw.text((54, 580), "Already Built:", font=header_font, fill=COLOR_SECONDARY)
    draw.text((80, 640), "Working bond bot (beta with real users)", font=body_font, fill=COLOR_DARK)
    draw.text((80, 680), "15+ years of Indonesian bond data", font=body_font, fill=COLOR_DARK)
    draw.text((80, 720), "80%+ forecast accuracy proven", font=body_font, fill=COLOR_DARK)
    
    # Roadmap
    draw.text((54, 820), "2026 Roadmap", font=header_font, fill=COLOR_PRIMARY)
    draw.text((80, 880), "Q1-Q2: 5-10 early adopters + cases", font=body_font, fill=COLOR_DARK)
    draw.text((80, 920), "Q3-Q4: 20+ paying customers", font=body_font, fill=COLOR_DARK)
    draw.text((80, 960), "2027: Regional expansion", font=body_font, fill=COLOR_DARK)
    
    quote_font = get_font_with_emoji(28, bold=True)
    draw.text((54, 1060), "\"This isn't a pitch.\"", font=quote_font, fill=COLOR_PRIMARY)
    draw.text((54, 1120), "\"This is proof.\"", font=quote_font, fill=COLOR_PRIMARY)
    
    return img

def slide_10_cta():
    """Slide 10: Call to Action"""
    img = create_image(COLOR_PRIMARY)
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font_with_emoji(56, bold=True)
    draw.text((54, 100), "Join The", font=title_font, fill=COLOR_SECONDARY)
    draw.text((54, 180), "Data Revolution", font=title_font, fill=COLOR_SECONDARY)
    
    # CTA box
    cta_box = Image.new('RGB', (WIDTH - 108, 300), COLOR_SECONDARY)
    img.paste(cta_box, (54, 320))
    draw = ImageDraw.Draw(img)
    
    header = get_font_with_emoji(32, bold=True)
    body = get_font_with_emoji(24, bold=False)
    sub = get_font_with_emoji(22, bold=False)
    
    draw.text((80, 350), "What's Next?", font=header, fill=COLOR_WHITE)
    draw.text((80, 420), "DM us for a 5-min demo", font=body, fill=COLOR_WHITE)
    draw.text((80, 470), "See your data analyzed live", font=sub, fill=COLOR_WHITE)
    
    # Offer
    offer_box = Image.new('RGB', (WIDTH - 108, 240), COLOR_ACCENT)
    img.paste(offer_box, (54, 680))
    draw = ImageDraw.Draw(img)
    
    offer_header = get_font_with_emoji(24, bold=True)
    offer_body = get_font_with_emoji(20, bold=False)
    
    draw.text((80, 710), "First 10 Companies Get:", font=offer_header, fill=COLOR_WHITE)
    draw.text((80, 770), "✓ 50% discount Year 1", font=offer_body, fill=COLOR_WHITE)
    draw.text((80, 810), "✓ Custom integration support", font=offer_body, fill=COLOR_WHITE)
    
    # Bottom CTA
    cta_font = get_font_with_emoji(32, bold=True)
    draw.text((54, 1000), "Stop guessing.", font=cta_font, fill=COLOR_WHITE)
    draw.text((54, 1060), "Start analyzing.", font=cta_font, fill=COLOR_WHITE)
    
    # Contact
    contact = get_font_with_emoji(24, bold=False)
    draw.text((54, 1150), "hello@perisai.io", font=contact, fill=COLOR_LIGHT)
    draw.text((54, 1200), "Link in bio", font=contact, fill=COLOR_LIGHT)
    
    return img

def generate_all_slides(output_dir="instagram_slides"):
    """Generate all 10 slides"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    slides = [
        ("01_the_problem.png", slide_1_problem),
        ("02_the_vision.png", slide_2_vision),
        ("03_kei_kin.png", slide_3_personas),
        ("04_banking.png", slide_4_banking),
        ("05_investor.png", slide_5_investor),
        ("06_features.png", slide_6_features),
        ("07_pricing.png", slide_7_pricing),
        ("08_indonesia.png", slide_8_indonesia),
        ("09_team_roadmap.png", slide_9_team),
        ("10_cta.png", slide_10_cta),
    ]
    
    for filename, slide_func in slides:
        print(f"Generating {filename}...")
        try:
            img = slide_func()
            filepath = os.path.join(output_dir, filename)
            img.save(filepath, quality=95)
            print(f"  ✓ Saved to {filepath}")
        except Exception as e:
            print(f"  ✗ Error generating {filename}: {e}")
    
    print(f"\n✅ All 10 slides generated in '{output_dir}/' directory!")
    print(f"\n📱 Ready to upload to Instagram (1080x1350px, 4:5 ratio)")
    print(f"\n💡 Tip: Create a carousel post on Instagram or post as Story series")

if __name__ == "__main__":
    generate_all_slides()
