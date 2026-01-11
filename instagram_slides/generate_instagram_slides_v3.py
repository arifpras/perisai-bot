"""
PerisAI Instagram Campaign Generator v3
Uses larger fonts and emoji-friendly approach
1080x1350px (4:5 ratio) Instagram slides
"""

from PIL import Image, ImageDraw, ImageFont
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

def get_font(size):
    """Get bold font"""
    fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for font_path in fonts:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                pass
    return ImageFont.load_default()

def get_font_regular(size):
    """Get regular font"""
    fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for font_path in fonts:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                pass
    return ImageFont.load_default()

def slide_1_problem():
    """Slide 1: The Problem"""
    img = create_image("#FEF2F2")
    draw = ImageDraw.Draw(img)
    
    # Title - LARGE FONTS
    title_font = get_font(72)
    draw.text((54, 100), "Is Your Data", font=title_font, fill=COLOR_ACCENT)
    draw.text((54, 200), "Trapped?", font=title_font, fill=COLOR_ACCENT)
    
    # Content - LARGER FONTS
    content_font = get_font_regular(42)
    emoji_font = get_font_regular(48)
    
    items = [
        ("💼", "Your company has data"),
        ("📊", "But insights take WEEKS"),
        ("💰", "Hiring = $200K+/year"),
        ("🤷", "Excel guesses instead"),
    ]
    
    y_pos = 330
    for emoji, text in items:
        draw.text((54, y_pos), emoji, font=emoji_font, fill=COLOR_DARK)
        draw.text((130, y_pos), text, font=content_font, fill=COLOR_DARK)
        y_pos += 95
    
    # Bottom callout
    bottom_box = Image.new('RGB', (WIDTH - 108, 200), COLOR_ACCENT)
    img.paste(bottom_box, (54, 1050))
    draw = ImageDraw.Draw(img)
    
    cta_font = get_font(40)
    small_font = get_font_regular(32)
    
    draw.text((80, 1080), "This costs you MILLIONS", font=cta_font, fill=COLOR_WHITE)
    draw.text((80, 1160), "👉 DM us if familiar", font=small_font, fill=COLOR_WHITE)
    
    return img

def slide_2_vision():
    """Slide 2: The Vision"""
    img = create_image(COLOR_PRIMARY)
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font(64)
    draw.text((54, 80), "What If Analytics", font=title_font, fill=COLOR_WHITE)
    draw.text((54, 170), "Took 2 Minutes?", font=title_font, fill=COLOR_WHITE)
    
    small_font = get_font_regular(36)
    micro_font = get_font_regular(28)
    emoji_font = get_font_regular(56)
    
    # Old way
    draw.text((54, 300), "❌ OLD WAY (weeks)", font=small_font, fill=COLOR_ACCENT)
    draw.text((54, 370), "Data → SQL → Analyst → Reports", font=micro_font, fill=COLOR_LIGHT)
    
    # Arrow
    draw.text((480, 440), "⬇️", font=emoji_font, fill=COLOR_SECONDARY)
    
    # New way
    draw.text((54, 530), "✅ NEW WAY (seconds)", font=small_font, fill=COLOR_SECONDARY)
    draw.text((54, 600), "Ask → Bot → Answer", font=micro_font, fill=COLOR_LIGHT)
    
    # Example box
    example_box = Image.new('RGB', (WIDTH - 108, 300), COLOR_WHITE)
    img.paste(example_box, (54, 720))
    draw = ImageDraw.Draw(img)
    
    example_font = get_font_regular(32)
    emoji_font = get_font_regular(40)
    
    draw.text((80, 750), '"Show loan defaults"', font=example_font, fill=COLOR_PRIMARY)
    draw.text((80, 820), "🤖 AI analyzes data", font=example_font, fill=COLOR_DARK)
    draw.text((80, 890), "📈 Instant insights", font=example_font, fill=COLOR_DARK)
    
    draw.text((54, 1100), "No code. Just ask.", font=get_font(44), fill=COLOR_WHITE)
    
    return img

def slide_3_personas():
    """Slide 3: Kei & Kin"""
    img = create_image(COLOR_LIGHT)
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font(64)
    draw.text((54, 80), "Your Dual AI Team", font=title_font, fill=COLOR_PRIMARY)
    
    # Kei section
    kei_box = Image.new('RGB', (400, 500), COLOR_PRIMARY)
    img.paste(kei_box, (54, 220))
    draw = ImageDraw.Draw(img)
    
    header_font = get_font(48)
    body_font = get_font_regular(26)
    
    draw.text((74, 250), "⚙️ KEI", font=header_font, fill=COLOR_WHITE)
    draw.text((74, 340), "The Quant", font=body_font, fill=COLOR_WHITE)
    draw.text((74, 380), "• MIT trained", font=body_font, fill=COLOR_LIGHT)
    draw.text((74, 430), "• Numbers & stats", font=body_font, fill=COLOR_LIGHT)
    draw.text((74, 480), "• ARIMA, GARCH", font=body_font, fill=COLOR_LIGHT)
    
    # Kin section
    kin_box = Image.new('RGB', (400, 500), COLOR_SECONDARY)
    img.paste(kin_box, (626, 220))
    draw = ImageDraw.Draw(img)
    
    draw.text((646, 250), "📖 KIN", font=header_font, fill=COLOR_WHITE)
    draw.text((646, 340), "The Storyteller", font=body_font, fill=COLOR_WHITE)
    draw.text((646, 380), "• CFA + PhD Econ", font=body_font, fill=COLOR_LIGHT)
    draw.text((646, 430), "• Context & meaning", font=body_font, fill=COLOR_LIGHT)
    draw.text((646, 480), "• Why it matters", font=body_font, fill=COLOR_LIGHT)
    
    # Bottom
    draw.text((54, 800), "Use /both for Rigor + Narrative", font=get_font_regular(36), fill=COLOR_DARK)
    draw.text((54, 1000), '"Give me both perspectives"', font=get_font_regular(32), fill=COLOR_PRIMARY)
    
    return img

def slide_4_banking():
    """Slide 4: Banking"""
    img = create_image("#ECFDF5")
    draw = ImageDraw.Draw(img)
    
    # Title
    emoji_font = get_font_regular(72)
    title_font = get_font(56)
    
    draw.text((54, 70), "🏦", font=emoji_font, fill=COLOR_SECONDARY)
    draw.text((54, 160), "Treasury Teams", font=title_font, fill=COLOR_PRIMARY)
    draw.text((54, 260), "Love This", font=title_font, fill=COLOR_PRIMARY)
    
    # Subtitle
    draw.text((54, 360), "Auction Forecasting", font=get_font_regular(32), fill=COLOR_DARK)
    
    # Problem
    problem_font = get_font_regular(34)
    draw.text((54, 450), "❌ OLD: Guess demand", font=problem_font, fill=COLOR_ACCENT)
    draw.text((80, 520), "Miss pricing windows", font=problem_font, fill=COLOR_ACCENT)
    draw.text((80, 590), "Leave $M on table", font=problem_font, fill=COLOR_ACCENT)
    
    # Solution box
    solution_box = Image.new('RGB', (WIDTH - 108, 300), COLOR_SECONDARY)
    img.paste(solution_box, (54, 700))
    draw = ImageDraw.Draw(img)
    
    header = get_font(36)
    body = get_font_regular(28)
    
    draw.text((80, 730), "✅ PerisAI Way:", font=header, fill=COLOR_WHITE)
    draw.text((80, 820), "🤖 Forecast 1-3 months", font=body, fill=COLOR_WHITE)
    draw.text((80, 890), "📊 80% accurate", font=body, fill=COLOR_WHITE)
    draw.text((80, 960), "💰 Save $10M+/year", font=body, fill=COLOR_WHITE)
    
    return img

def slide_5_investor():
    """Slide 5: Investor"""
    img = create_image("#EFF6FF")
    draw = ImageDraw.Draw(img)
    
    # Title
    emoji_font = get_font_regular(72)
    title_font = get_font(56)
    
    draw.text((54, 70), "📈", font=emoji_font, fill=COLOR_PRIMARY)
    draw.text((54, 160), "5-Minute", font=title_font, fill=COLOR_PRIMARY)
    draw.text((54, 260), "Analysis", font=title_font, fill=COLOR_PRIMARY)
    draw.text((54, 360), "vs 5 Hours", font=get_font_regular(36), fill=COLOR_DARK)
    
    # Comparison
    small_font = get_font_regular(32)
    micro_font = get_font_regular(28)
    
    draw.text((54, 480), "Traditional:", font=small_font, fill=COLOR_ACCENT)
    draw.text((80, 540), "Excel grind → 2-5 hours", font=micro_font, fill=COLOR_DARK)
    
    draw.text((54, 630), "PerisAI:", font=small_font, fill=COLOR_SECONDARY)
    draw.text((80, 690), "One question → 10 seconds", font=micro_font, fill=COLOR_DARK)
    
    # Questions
    draw.text((54, 810), "Questions They Ask:", font=small_font, fill=COLOR_PRIMARY)
    
    questions_font = get_font_regular(26)
    y_pos = 880
    questions = [
        "✅ Compare 5Y vs 10Y yields",
        "✅ Detect structural breaks",
        "✅ Volatility forecast?",
        "✅ Bond cointegration?",
    ]
    
    for q in questions:
        draw.text((80, y_pos), q, font=questions_font, fill=COLOR_DARK)
        y_pos += 50
    
    return img

def slide_6_features():
    """Slide 6: Features"""
    img = create_image(COLOR_LIGHT)
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font(64)
    draw.text((54, 80), "Features at a", font=title_font, fill=COLOR_PRIMARY)
    draw.text((54, 170), "Glance", font=title_font, fill=COLOR_PRIMARY)
    
    features = [
        ("📊", "Auto Database Connection"),
        ("🤖", "7+ Analytics Methods"),
        ("📉", "ML Forecasting"),
        ("📄", "Export Everything"),
        ("🌐", "Natural Language Interface"),
    ]
    
    emoji_font = get_font_regular(48)
    feature_font = get_font_regular(32)
    
    y_pos = 310
    for emoji, title in features:
        draw.text((54, y_pos), emoji, font=emoji_font, fill=COLOR_PRIMARY)
        draw.text((130, y_pos), title, font=feature_font, fill=COLOR_PRIMARY)
        y_pos += 140
    
    # Bottom
    bottom_box = Image.new('RGB', (WIDTH - 108, 140), COLOR_ACCENT)
    img.paste(bottom_box, (54, 1120))
    draw = ImageDraw.Draw(img)
    
    bottom_font = get_font(36)
    sub_font = get_font_regular(24)
    
    draw.text((80, 1150), "Deploy in 2-4 weeks", font=bottom_font, fill=COLOR_WHITE)
    draw.text((80, 1210), "(vs 6-12 months traditional)", font=sub_font, fill=COLOR_WHITE)
    
    return img

def slide_7_pricing():
    """Slide 7: Pricing"""
    img = create_image("#FFFBEB")
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font(56)
    draw.text((54, 80), "Cost Less Than", font=title_font, fill=COLOR_PRIMARY)
    draw.text((54, 170), "1 Analyst", font=title_font, fill=COLOR_PRIMARY)
    
    # Alternatives
    alt_font = get_font_regular(30)
    draw.text((54, 300), "❌ Bloomberg: $300K/yr", font=alt_font, fill=COLOR_ACCENT)
    draw.text((54, 370), "❌ Tableau: $500K+ setup", font=alt_font, fill=COLOR_ACCENT)
    draw.text((54, 440), "❌ Analyst: $200K+/yr", font=alt_font, fill=COLOR_ACCENT)
    
    # PerisAI pricing
    price_box1 = Image.new('RGB', (400, 240), COLOR_SECONDARY)
    img.paste(price_box1, (54, 550))
    draw = ImageDraw.Draw(img)
    
    price_header = get_font(32)
    price_amount = get_font(48)
    price_detail = get_font_regular(22)
    
    draw.text((74, 570), "SaaS", font=price_header, fill=COLOR_WHITE)
    draw.text((74, 630), "$5K–$50K/mo", font=price_amount, fill=COLOR_WHITE)
    
    # Custom pricing
    price_box2 = Image.new('RGB', (400, 240), COLOR_PRIMARY)
    img.paste(price_box2, (626, 550))
    draw = ImageDraw.Draw(img)
    
    draw.text((646, 570), "Custom Bot", font=price_header, fill=COLOR_WHITE)
    draw.text((646, 630), "$50K–$500K", font=price_amount, fill=COLOR_WHITE)
    
    draw.text((54, 900), "Data-driven = Multi-million savings", font=get_font_regular(34), fill=COLOR_DARK)
    draw.text((54, 1050), '"Saved $200K Year 1"', font=get_font_regular(32), fill=COLOR_PRIMARY)
    
    return img

def slide_8_indonesia():
    """Slide 8: Indonesia"""
    img = create_image("#FEF3C7")
    draw = ImageDraw.Draw(img)
    
    # Title
    emoji_font = get_font_regular(72)
    title_font = get_font(56)
    
    draw.text((54, 70), "🇮🇩", font=emoji_font, fill=COLOR_PRIMARY)
    draw.text((54, 160), "Built for", font=title_font, fill=COLOR_PRIMARY)
    draw.text((54, 260), "Emerging Markets", font=title_font, fill=COLOR_PRIMARY)
    
    # Why Indonesia
    draw.text((54, 370), "Why PerisAI Here:", font=get_font_regular(32), fill=COLOR_DARK)
    
    fact_font = get_font_regular(28)
    facts = [
        "📊 300+ enterprises with data",
        "💔 Shortage: 200 scientists vs 5K+ companies",
        "💰 TAM: $45M+ untapped",
    ]
    
    y_pos = 450
    for fact in facts:
        draw.text((54, y_pos), fact, font=fact_font, fill=COLOR_DARK)
        y_pos += 90
    
    # Proof
    proof_box = Image.new('RGB', (WIDTH - 108, 280), COLOR_PRIMARY)
    img.paste(proof_box, (54, 800))
    draw = ImageDraw.Draw(img)
    
    header = get_font(30)
    body = get_font_regular(24)
    
    draw.text((80, 830), "Already Proven:", font=header, fill=COLOR_WHITE)
    draw.text((80, 890), "✓ BI data integration", font=body, fill=COLOR_WHITE)
    draw.text((80, 940), "✓ MOF forecasts", font=body, fill=COLOR_WHITE)
    draw.text((80, 990), "✓ 80%+ accuracy", font=body, fill=COLOR_WHITE)
    
    return img

def slide_9_team():
    """Slide 9: Team"""
    img = create_image(COLOR_LIGHT)
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font(56)
    draw.text((54, 80), "The Team &", font=title_font, fill=COLOR_PRIMARY)
    draw.text((54, 170), "What's Next", font=title_font, fill=COLOR_PRIMARY)
    
    # Team
    header_font = get_font_regular(32)
    body_font = get_font_regular(26)
    
    draw.text((54, 320), "Our Team:", font=header_font, fill=COLOR_PRIMARY)
    team = [
        "✓ Top finance data scientists",
        "✓ Full-stack engineers",
        "✓ Former BI & MOF advisors",
    ]
    y_pos = 400
    for point in team:
        draw.text((80, y_pos), point, font=body_font, fill=COLOR_DARK)
        y_pos += 60
    
    # Proof
    draw.text((54, 650), "Already Built:", font=header_font, fill=COLOR_SECONDARY)
    proof = [
        "✓ Working bond bot (real users)",
        "✓ 15+ years bond data",
        "✓ 80%+ accuracy proven",
    ]
    y_pos = 730
    for point in proof:
        draw.text((80, y_pos), point, font=body_font, fill=COLOR_DARK)
        y_pos += 60
    
    # Roadmap
    draw.text((54, 980), "2026 Roadmap:", font=header_font, fill=COLOR_PRIMARY)
    draw.text((80, 1050), "Q1-Q2: Early adopters", font=body_font, fill=COLOR_DARK)
    draw.text((80, 1100), "Q3-Q4: 20+ customers", font=body_font, fill=COLOR_DARK)
    
    return img

def slide_10_cta():
    """Slide 10: Call to Action"""
    img = create_image(COLOR_PRIMARY)
    draw = ImageDraw.Draw(img)
    
    # Title
    title_font = get_font(64)
    draw.text((54, 100), "Join The Data", font=title_font, fill=COLOR_SECONDARY)
    draw.text((54, 200), "Revolution", font=title_font, fill=COLOR_SECONDARY)
    
    # CTA box
    cta_box = Image.new('RGB', (WIDTH - 108, 300), COLOR_SECONDARY)
    img.paste(cta_box, (54, 340))
    draw = ImageDraw.Draw(img)
    
    header = get_font(40)
    body = get_font_regular(32)
    
    draw.text((80, 370), "What's Next?", font=header, fill=COLOR_WHITE)
    draw.text((80, 460), "DM us for a demo", font=body, fill=COLOR_WHITE)
    draw.text((80, 540), "See your data analyzed", font=body, fill=COLOR_WHITE)
    
    # Offer
    offer_box = Image.new('RGB', (WIDTH - 108, 260), COLOR_ACCENT)
    img.paste(offer_box, (54, 750))
    draw = ImageDraw.Draw(img)
    
    offer_header = get_font(32)
    offer_body = get_font_regular(26)
    
    draw.text((80, 780), "First 10 Companies:", font=offer_header, fill=COLOR_WHITE)
    draw.text((80, 860), "✓ 50% discount Year 1", font=offer_body, fill=COLOR_WHITE)
    draw.text((80, 920), "✓ Custom integration", font=offer_body, fill=COLOR_WHITE)
    
    # Bottom CTA
    draw.text((54, 1100), "Stop guessing.", font=get_font(44), fill=COLOR_WHITE)
    draw.text((54, 1180), "Start analyzing. 🚀", font=get_font(44), fill=COLOR_WHITE)
    
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
            print(f"  ✓ Saved")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n✅ All 10 slides ready!")
    print(f"📱 Instagram 4:5 ratio (1080x1350px)")
    print(f"📁 Location: {output_dir}/")

if __name__ == "__main__":
    generate_all_slides()
