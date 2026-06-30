import streamlit as st

st.set_page_config(
    page_title="CareerGrid",
    page_icon="🧩",
    layout="wide"
)

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
/* Main page spacing */
.block-container {
    padding-top: 2rem;
    padding-left: 4rem;
    padding-right: 4rem;
}

/* Hide Streamlit default menu/footer */
#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

/* Navbar */
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 1.2rem;
    border-bottom: 1px solid #E2E8F0;
}

.logo {
    font-size: 28px;
    font-weight: 800;
    color: #1E3A8A;
}

.logo span {
    color: #7ED957;
}

/* Hero */
.hero {
    background: linear-gradient(135deg, #EEF6FF 0%, #FFFFFF 100%);
    padding: 60px;
    border-radius: 28px;
    margin-top: 35px;
    box-shadow: 0px 10px 30px rgba(30, 58, 138, 0.08);
}

.hero-title {
    font-size: 58px;
    font-weight: 900;
    color: #1E3A8A;
    line-height: 1.1;
    margin-bottom: 20px;
}

.hero-text {
    font-size: 20px;
    color: #475569;
    line-height: 1.7;
    margin-bottom: 30px;
}

.puzzle-box {
    font-size: 170px;
    text-align: center;
    padding-top: 30px;
}

/* Section title */
.section-title {
    font-size: 34px;
    font-weight: 800;
    color: #0F172A;
    margin-top: 50px;
    margin-bottom: 25px;
}

/* Cards */
.info-card {
    background-color: white;
    padding: 32px;
    border-radius: 24px;
    box-shadow: 0px 8px 25px rgba(15, 23, 42, 0.08);
    border: 1px solid #E2E8F0;
    min-height: 220px;
    transition: 0.3s ease;
}

.info-card:hover {
    transform: translateY(-6px);
    box-shadow: 0px 12px 35px rgba(30, 58, 138, 0.16);
}

.card-icon {
    font-size: 40px;
    margin-bottom: 15px;
}

.card-title {
    font-size: 23px;
    font-weight: 800;
    color: #1E40AF;
    margin-bottom: 12px;
}

.card-text {
    font-size: 16px;
    color: #64748B;
    line-height: 1.6;
}

/* Streamlit buttons */
.stButton > button {
    border-radius: 14px;
    padding: 0.7rem 1.2rem;
    font-weight: 700;
    border: 1px solid #BFDBFE;
    color: #1E3A8A;
}

.stButton > button:hover {
    border-color: #1E40AF;
    color: #1E40AF;
    background-color: #EFF6FF;
}
</style>
""", unsafe_allow_html=True)


# ---------- NAVBAR ----------
st.markdown("""
<div class="navbar">
    <div class="logo"><span>🧩</span> CareerGrid</div>
</div>
""", unsafe_allow_html=True)

nav1, nav2, nav3, nav4 = st.columns([6, 1, 1, 1])

with nav2:
    st.button("Home", use_container_width=True)

with nav3:
    st.button("Login", use_container_width=True)

with nav4:
    st.button("Sign Up", use_container_width=True)


# ---------- HERO SECTION ----------
st.markdown('<div class="hero">', unsafe_allow_html=True)

left, right = st.columns([1.5, 1])

with left:
    st.markdown("""
    <div class="hero-title">
        Build Your Career Path with Confidence
    </div>

    <div class="hero-text">
        CareerGrid helps students explore careers through interactive simulations,
        AI-powered performance analysis, and personalized learning roadmaps.
    </div>
    """, unsafe_allow_html=True)

    if st.button("Get Started", use_container_width=False):
        st.success("Next step: Login page will open here.")

with right:
    st.markdown('<div class="puzzle-box">🧩</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# ---------- HOW IT WORKS ----------
st.markdown('<div class="section-title">How CareerGrid Works</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class="info-card">
        <div class="card-icon">🎯</div>
        <div class="card-title">1. Choose a Career</div>
        <div class="card-text">
            Select the career path you want to explore, such as software engineering,
            data science, cybersecurity, or UI/UX design.
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="info-card">
        <div class="card-icon">🧪</div>
        <div class="card-title">2. Complete a Simulation</div>
        <div class="card-text">
            Try a realistic task related to your selected career and show how you
            think, solve problems, and make decisions.
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class="info-card">
        <div class="card-icon">🗺️</div>
        <div class="card-title">3. Get Your Roadmap</div>
        <div class="card-text">
            Receive AI feedback, recommended skills, and a personalized learning
            roadmap to guide your next steps.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")

st.info("Current phase: Landing page UI. Next step: Login and Sign Up navigation.")