import streamlit as st
from multiapp import MultiApp

app = MultiApp()
st.set_page_config(page_title='Airkopi Barista App')

from apps import basic, sca_form, rec_coffee, recipe # import your app modules here

st.markdown("""
<div class="header-container">
    <h1>☕ Coffee Brewing App</h1>
    <p>Created with ❤️ by <a href="https://lynk.id/airkopi/" target="_blank" style="color: #FAF7F2; text-decoration: underline;">Airkopi Café</a></p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="coffee-card">
    <h3 style="margin-top: 0; font-family: 'Playfair Display', serif; color: #2D2219;">Main Features</h3>
    <ol style="margin-bottom: 0; padding-left: 20px; line-height: 1.8; color: #2D2219; font-family: 'Plus Jakarta Sans', sans-serif;">
        <li><strong>Brewing Guide</strong> — Guidance to brew coffee</li>
        <li><strong>Basic Cupping Form</strong> — Take notes in digital form when dialing in coffee for any brewing method</li>
        <li><strong>SCA Cupping Form</strong> — Standard Specialty Coffee Association cupping form</li>
        <li><strong>Coffee Recommendation</strong> — Recommend coffee based on your preferred taste</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# Add all your applications here
app.add_app("Brewing Guide", recipe.app)
app.add_app("Basic Cupping Form", basic.app)
app.add_app("SCA Cupping Form", sca_form.app)
app.add_app("Coffee Recommendation", rec_coffee.app)

# The main app
app.run()
