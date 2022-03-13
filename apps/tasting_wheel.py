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

#select Stock (first sheet)
worksheet = sh.sheet1

# data from gsheet <end>

flavor_df_temp = 'FlavorWheelRaw.csv'

def app():
    st.write("""
    # Dial in - Tasting Wheel
    """)

    st.sidebar.header('Input Parameters')

    def user_input_features():
        # 1st: min | 2nd: max | 3rd: default value
        id = st.sidebar.number_input('id', 0, 100, 1)
        dose_g = st.sidebar.number_input('Coffee weight (g)', 0.0, 100.0, 20.0)
        time_s = st.sidebar.number_input('Extraction time (s)', 0, 300, 120)
        yield_ml = st.sidebar.number_input('Yield (ml)', 0, 1000, 45)
        recipe = st.sidebar.slider('Recipe', 1, 1, 5)
        brew_method = st.sidebar.selectbox(
            'Select Brew Method', 
                (
                    'Modern Espresso', 'Espresso Turbo', 'Espresso Allonge', 'Espresso Londinium', 'Espresso Blooming', 'Espresso Custom', 'Espresso Manual', 'Aeropress', 
                    'French press','Tubruk', 'Pour Over', 'Hybrid Percolation Immersion', 'Cupping'
                ))        
        roast_profile = st.sidebar.selectbox(
            'Select roast profile', 
                (
                    'Cinnamon (Ultra Light)', 'New England Roast (Light)', 
                    'American (Medium)','City (Medium)', 'Full City (Medium Dark)', 'Espresso (Dark)', 'French (Dark)', 'Viennese (Dark)', 
                    'Italian (Dark)'
                ))
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
        notes = st.sidebar.text_input('Tasting Notes', 'Tasting Notes')
        notes_recipe = st.sidebar.text_input('Recipe Notes', 'Recipe Notes')
        notes_grinder = st.sidebar.text_input('Grinder Notes', 'Grinder Notes')
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
                'notes_grinder': notes_grinder,
                'date_time': date_time,
                'brew_method': brew_method,
                }
        features = pd.DataFrame(data, index=[0])
        return features

    def radar_chart(score, category, name):
        label_loc = np.linspace(start=0, stop=2 * np.pi, num=len(score))
        plt.figure(figsize=(8, 8))
        plt.subplot(polar=True)
        # change the label below to coffee x
        plt.plot(label_loc, score)
        # plt.plot(label_loc, score2, label='score 2')
        # plt.plot(label_loc, score3, label='score 3')
        title = f"Coffee: {name} "
        plt.title(title, size=20, y=1.05)
        lines, labels = plt.thetagrids(np.degrees(label_loc), labels=category)
        plt.legend()
        plt.show()
        st.pyplot(plt)

    def dataGsheet(worksheet, df):
        df_gsheet = pd.DataFrame(worksheet.get_all_records())
        df_gsheet = df_gsheet.astype(str)
        df_gsheet = df_gsheet[[
            'Id', 'Coffee', 'Notes', 'Process', 'Profilroast', 
            'Density', 'Age(days)', 'Age(rdtofreeze)']]

        #select row based on id 
        values_list = df_gsheet.loc[df_gsheet['Id'] == str(df['id'].iloc[0])]
        return values_list

    def notesGsheet(df_gsheet):
        values_list_notes = df_gsheet['Notes']
        values_list_notes = [x for xs in values_list_notes for x in xs.split(',')]
        values_list_notes = [x.strip(' ') for x in values_list_notes]
        
        return values_list_notes

    def initDF(notes, flavorWheelList):
        flavor_df_temp = pd.read_csv(flavorWheelList)
        flavor_df_temp = flavor_df_temp.reset_index()  # make sure indexes pair with number of rows
        header = [{'Parent':10, 'Child':100, 'Grandchild': 1000}]
        input_df = pd.DataFrame(header)
        input_df.drop(input_df.index, inplace=True)
        for index, row in flavor_df_temp.iterrows():
            for i in notes:
                if i == row['Grandchild']:
                    input_data = {'Parent':[row['Parent']], 'Child':[row['Child']], 'Grandchild': [i]}
                    notes_df = pd.DataFrame(input_data)
                    input_df = input_df.append(notes_df, ignore_index = True)
        return input_df

    def flavorWheel(input_df):
        fig = px.sunburst(input_df, path=['Parent', 'Child', 'Grandchild'])
        fig.update_layout(
            title={
                'text': "Coffee Tasting Notes",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
                },

            font=dict(
                family="eczar semibold",
                size=18,
                )
            )
        return fig

    #user input data
    st.subheader("""
    Your input
    """)
    df = user_input_features()
    st.write(df)
    
    #ghseet data
    st.subheader("""
    Coffee data
    """)
    df_gsheet = dataGsheet(worksheet, df)
    st.write(df_gsheet)

    flavorNotes = notesGsheet(df_gsheet)
    input_df = initDF(flavorNotes, flavor_df_temp)
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
    # st.text("Original dataframe")

    # with every interaction, the script runs from top to bottom
    # resulting in the empty dataframe
    # st.dataframe(data) 

    # persist state of dataframe
    session_state = SessionState.get(df=data)

    # random value to append; could be a num_input widget if you want
    # random_value = np.random.randn()

    if st.button("Add new value"):
        # update dataframe state
        session_state.df = session_state.df.append(data, ignore_index=True)
        st.text("Updated dataframe")
        st.dataframe(session_state.df)

    download=st.button('Download data (.csv)')
    if download:
        session_state.df.drop(index=df.index[0], axis=0, inplace=True)
        csv = session_state.df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()  # some strings
        linko= f'<a href="data:file/csv;base64,{b64}" download="tasting_wheel.csv">Download csv file</a>'
        st.markdown(linko, unsafe_allow_html=True)
