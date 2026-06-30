import streamlit as st

# Page configuration
st.set_page_config(
    page_title="CareerGrid",
    page_icon="🧩",
    layout="wide"
)

# Title
st.title("🧩 CareerGrid")

st.subheader("Discover Your Career Path Through Interactive Simulations")

st.write(
    """
    Welcome to CareerGrid!

    Complete career simulations, receive AI-powered feedback,
    and get a personalized learning roadmap to help you reach your dream career.
    """
)

st.divider()

col1, col2 = st.columns(2)

with col1:
    if st.button("Login", use_container_width=True):
        st.success("Login page will be implemented next.")

with col2:
    if st.button("Sign Up", use_container_width=True):
        st.success("Registration page will be implemented next.")
        