import streamlit as st
from multiapp import MultiApp
from apps import basic, sca_form, rec_coffee,recipe # import your app modules here

app = MultiApp()
st.set_page_config(page_title='Airkopi Barista App')

st.markdown("""
# Coffee Brewing App
Created with ❤️ by [Airkopi Café](https://lynk.id/airkopi/)
""")

st.subheader("""
Main Feature
1. Brewing Guide - Guidance to brew coffee
2. Basic Cupping Form - Take notes in digital form when dial-in coffee for any brewing method
3. SCA Cupping Form - SCA form
4. Coffee Recommendation - Reccomend coffee based on your preferred taste
""")

# Add all your application here
app.add_app("Brewing Guide", recipe.app)
app.add_app("Basic Cupping Form", basic.app)
app.add_app("SCA Cupping Form", sca_form.app)
app.add_app("Coffee Recommendation", rec_coffee.app)

# The main app
app.run()
