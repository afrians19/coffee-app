import streamlit as st
from multiapp import MultiApp
from apps import basic, sca_form, tasting_wheel,recipe # import your app modules here

app = MultiApp()
st.set_page_config(page_title='Sensory Scoresheet')

st.markdown("""
# Sensory Scoresheet
""")

st.subheader("""
Scoresheet Forms
0. Recipe
1. Basic
2. SCA Cupping Form
3. Tasting Wheel
""")

st.text('This is a digital version for taking notes when you dial-in coffee in any brewing method.')
st.text('You can also visualize and download the data.')

# Add all your application here
app.add_app("Recipe", recipe.app)
app.add_app("Basic", basic.app)
app.add_app("SCA Form", sca_form.app)
app.add_app("Tasting Wheel", tasting_wheel.app)

# The main app
app.run()
