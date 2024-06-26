import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import base64
import SessionState
import datetime
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
from my_method import radar_chart, dataGsheet, notesGsheet, initDF, flavorWheel

# data from gsheet <start>
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scopes
)

gc = gspread.authorize(credentials)

sh = gc.open("Coffee Stock")

#select Stock
worksheet = sh.worksheet("Stock")

# data from gsheet <end>

flavor_df_list = 'FlavorWheelRaw.csv'

def app():
    st.write("""
    # Dial in - Tasting Wheel
    """)

    st.sidebar.header('Input Parameters')

    def user_input_features():
        # 1st: min | 2nd: max | 3rd: default value
        id = st.sidebar.number_input('id', 0, 100, 1)
        dose_g = st.sidebar.number_input('Coffee weight (g)', 0.0, 100.0, 20.0)
        time_s = st.sidebar.number_input('Extraction time (s)', 0, 600, 120)
        yield_ml = st.sidebar.number_input('Yield (ml)', 0, 1000, 45)
        recipe = st.sidebar.slider('Recipe', 1, 1, 5)
        brew_method = st.sidebar.selectbox(
            'Select Brew Method', 
                (
                    'Espresso Modern', 'Espresso Turbo', 'Espresso Allonge', 'Espresso Londinium', 'Espresso Blooming', 'Espresso Over (Sprover)', 'Espresso Custom', 'Aeropress', 
                    'French press','Tubruk', 'Pour Over', 'Hybrid Percolation Immersion', 'Cupping'
                )
        )
        brew_tool = st.sidebar.selectbox(
            'Select Brew Tool', 
                (
                    'Espresso Machine', 'Nomad Espresso', 'V60 01 Plastic', 'V60 01 Ceramic', 'V60 02 Plastic', 'V60 Glass 03', 'V60 Switch Hybird', 'April Plastic',
                    'Suji Wave', 'Mokapot','Vietnam Drip', 'Cupping Bowl',
                )
        )        
        roast_profile = st.sidebar.selectbox(
            'Select roast profile', 
                (
                    'Ultra-Light', 'Light', 
                    'Medium-Light','Medium', 'Medium-Dark', 'Dark',
                )
        )
        
        roasted_days = st.sidebar.number_input('roasted_days', 0,100,5)
        temperature = st.sidebar.slider('Temperature', 80,100,93)
        sweetness = st.sidebar.slider('Sweetness', 0.0,5.0,3.0)
        acidity = st.sidebar.slider('Acidity', 0.0,5.0,3.0)
        floral = st.sidebar.slider('Floral', 0.0,5.0,3.0) 
        spicy = st.sidebar.slider('Spicy', 0.0,5.0,3.0)
        salty = st.sidebar.slider('Salty', 0.0,5.0,3.0)
        berry_fruit = st.sidebar.slider('Berry Fruit', 0.0,5.0,3.0)
        citrus_fruit = st.sidebar.slider('Citrus Fruit', 0.0,5.0,3.0)
        stone_fruit = st.sidebar.slider('Stone Fruit', 0.0,5.0,3.0)
        chocolate = st.sidebar.slider('Chocolate', 0.0,5.0,3.0)
        caramel = st.sidebar.slider('Caramel', 0.0,5.0,3.0)
        smoky = st.sidebar.slider('Smoky', 0.0,5.0,3.0)
        bitter = st.sidebar.slider('Bitter', 0.0,5.0,3.0)
        savory = st.sidebar.slider('Savory', 0.0,5.0,3.0)
        body = st.sidebar.slider('Body', 0.0,5.0,3.0)
        clean = st.sidebar.slider('Clean', 0.0,5.0,3.0)
        aftertaste = st.sidebar.slider('Aftertaste', 0.0,5.0,3.0)

        rating = st.sidebar.slider('Rating', 0,5,3)
        notes = st.sidebar.text_input('Tasting Notes', '')
        notes_recipe = st.sidebar.text_input('Recipe Notes', '')
        grinder = st.sidebar.selectbox(
            'Select Grinder', 
                (
                    'DF64', 'DF64 SSP MP', 
                    'DF64 SSP LS','FGM600AD', 'FGM600AD SSP MP', 'FGM600AD SSP LS', 
                    'FGM600AD SSP HU', 
                    'C40',
                )
        )
        grinder_setting = st.sidebar.number_input('Grinder Setting', 0,200,72)
        date_time = datetime.datetime.now()
        
        data = {'id': id,
                'dose_g': dose_g,
                'time_s': time_s,
                'yield_ml': yield_ml,
                'recipe': recipe,
                'roast_profile': roast_profile,
                'roasted_days': roasted_days,
                'temperature': temperature,
                'sweetness': sweetness,
                'acidity': acidity,
                'floral': floral,
                'spicy': spicy,
                'salty': salty,
                'berry_fruit': berry_fruit,
                'citrus_fruit': citrus_fruit,
                'stone_fruit': stone_fruit,
                'chocolate': chocolate,
                'caramel': caramel,
                'smoky': smoky,
                'bitter': bitter,
                'savory': savory,
                'body': body,
                'clean': clean,
                'aftertaste': aftertaste,
                'rating': rating,
                'notes': notes,
                'notes_recipe': notes_recipe,
                'grinder': grinder,
                'grinder_setting': grinder_setting,
                'date_time': date_time,
                'brew_method': brew_method,
                'brew_tool': brew_tool,

                }
        features = pd.DataFrame(data, index=[0])
        return features










    #user input data
    st.sidebar.markdown('''
    ---
    Created with ❤️ by [Airkopi Café](https://lynk.id/airkopi/).
    ''')    
    
    # User input data
    df = user_input_features()
    if st.button("Display Your Input"):
        st.write(df)
    
    #ghseet data
    st.subheader("""
    Coffee data
    """)
    df_gsheet = dataGsheet(worksheet, df)
    st.write(df_gsheet.T)

    flavorNotes = notesGsheet(df_gsheet)
    input_df = initDF(flavorNotes, flavor_df_list)
    fig = flavorWheel(input_df)
    st.plotly_chart(fig)

    # Magic commands implicitly `st.write()`
    # ''' _This_ is some __Markdown__ '''

    categories = ['Sweetness', 'Acidity', 'Floral', 'Spicy', 'Salty', 'Berry Fruit', 
                'Citrus Fruit', 'Stone Fruit', 'Chocolate', 'Caramel', 'Smoky', 'Bitter',
                'Savory', 'Body', 'Clean', 'After Taste']
    categories = [*categories, categories[0]]

    score1 = [df.sweetness[0], df.acidity[0], df.floral[0], df.spicy[0], df.salty[0], df.berry_fruit[0],
            df.citrus_fruit[0], df.stone_fruit[0], df.chocolate[0], df.caramel[0], df.smoky[0], df.bitter[0],
            df.savory[0], df.body[0], df.clean[0], df.aftertaste[0]]

    score1 = [*score1, score1[0]]
    coffee_name = df_gsheet['Coffee'].iloc[0]

    radar_chart(score1, categories, coffee_name)
    st.write('Tasting notes: ', df['notes'].iloc[0])

    # Create an empty dataframe
    data = df

    # persist state of dataframe
    session_state = SessionState.get(df=data)

    if st.button("Add new value"):
        # update dataframe state
        session_state.df = pd.concat([session_state.df, data], ignore_index=True)
        st.text("Updated dataframe")
        st.dataframe(session_state.df)

    download=st.button('Download data (.csv)')
    if download:
        session_state.df.drop(index=df.index[0], axis=0, inplace=True)
        csv = session_state.df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  # some strings
        linko= f'<a href="data:file/csv;base64,{b64}" download="tasting_wheel.csv">Download csv file</a>'
        st.markdown(linko, unsafe_allow_html=True)
