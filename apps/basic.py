import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import base64
import SessionState
import datetime
import os
import gspread
from google.oauth2.service_account import Credentials
from my_method import radar_chart, dataGsheet, notesGsheet, initDF, flavorWheel

try:
    from streamlit_mic_recorder import speech_to_text
except ImportError:
    speech_to_text = None

# data from gsheet <start>

# Auth start
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scopes
)

gc = gspread.authorize(credentials)
# Auth end

#Gsheet file name
sh = gc.open("Coffee Stock") 

#select Stock
worksheet = sh.worksheet("Stock")

#select Dial-in Basic 
worksheet_dialin = sh.worksheet("Dial-in Basic")

# data from gsheet <end>

flavor_df_list = 'FlavorWheelRaw.csv'


def mic_input_enabled():
    mic_toggle = os.getenv('ENABLE_MIC_INPUT')
    if mic_toggle is not None:
        return mic_toggle.lower() == 'true'
    return os.getenv('PORT') is None


def sidebar_voice_text_input(label, state_key, default_value=''):
    input_key = f'{state_key}_input'
    mic_key = f'{state_key}_mic'
    handled_key = f'{state_key}_mic_handled'

    if input_key not in st.session_state:
        st.session_state[input_key] = default_value

    if speech_to_text is None or not mic_input_enabled():
        st.sidebar.text_input(label, key=input_key)
        if speech_to_text is None:
            st.sidebar.caption('Mic unavailable: install `streamlit-mic-recorder` and restart the app.')
        else:
            st.sidebar.caption('Mic is disabled in this web deployment for stability.')
        return st.session_state[input_key]

    with st.sidebar:
        transcript = speech_to_text(
            language='en',
            start_prompt=f'🎤 {label}',
            stop_prompt=f'⏹️ {label}',
            just_once=True,
            use_container_width=True,
            key=mic_key,
        )

    if transcript and st.session_state.get(handled_key) != transcript:
        existing_text = st.session_state.get(input_key, '').strip()
        st.session_state[input_key] = (
            f'{existing_text} {transcript}'.strip() if existing_text else transcript
        )
        st.session_state[handled_key] = transcript

    st.sidebar.text_input(label, key=input_key)

    return st.session_state[input_key]

def app():
    st.write("""
    # Dial in - Basic
    """)
    
    st.sidebar.header('Input Parameters')
    
    def user_input_features():
        # 1st: min | 2nd: max | 3rd: default value
        id = st.sidebar.number_input('id', 0, 1000, 1)
        dose_g = st.sidebar.number_input('Coffee weight (g)', 0.0, 100.0, 20.0)
        time_s = st.sidebar.number_input('Extraction time (s)', 0, 600, 120)
        yield_ml = st.sidebar.number_input('Yield (ml)', 0, 1000, 45)
        recipe = st.sidebar.slider('Recipe', 1, 1, 5)
        brew_method = st.sidebar.selectbox(
            'Select Brew Method', 
                (
                    'Pour Over', 'Aeropress', 'French Press', 'Tubruk', 'Hybrid Percolation Immersion', 'Cupping','No Bypass'
                    'Espresso', 'Espresso Modern', 'Espresso Turbo', 'Espresso Allonge', 'Espresso Londinium', 'Espresso Blooming', 
                    'Espresso Over (Sprover)', "Espresso Extractamundo Dos!", 'Espresso Milk', 'Espresso Adaptive (Medium)', 'SOUP', 
                    
                )
        )
        brew_tool = st.sidebar.selectbox(
            'Select Brew Tool', 
                (
                    'Espresso Machine', 'Nomad Espresso', 'Origami Plastic 01 - Conical', 'Origami Plastic 01 - Flat',
                    'V60 01 RAN','V60 01 Plastic', 'V60 01 Ceramic', 'V60 02 Plastic', 'V60 Glass 03', 
                    'V60 Switch', 'April Plastic', 'Pulsar', 'Mugen Switch','Mugen',
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
        roasted_days = st.sidebar.number_input('Roasted Days', 0,100,5)
        temperature = st.sidebar.slider('Temperature', 80,100,93)
        fragrance_aroma = st.sidebar.slider('Fragrance/Aroma', 0.0,5.0,3.0)
        acidity = st.sidebar.slider('Acidity', 0.0,5.0,3.0)
        sweetness = st.sidebar.slider('Sweetness', 0.0,5.0,3.0)
        flavor = st.sidebar.slider('Flavor', 0.0,5.0,3.0)    
        body = st.sidebar.slider('Body', 0.0,5.0,3.0)
        aftertaste = st.sidebar.slider('Aftertaste', 0.0,5.0,3.0)
        rating = st.sidebar.slider('Rating', 0.0,5.0,3.0)
        notes = sidebar_voice_text_input('Tasting Notes', 'basic_notes')
        notes_recipe = sidebar_voice_text_input('Recipe Notes', 'basic_notes_recipe')
        grinder = st.sidebar.selectbox(
            'Select Grinder', 
                (                     
                    'DF64 SSP LS', 'FGM600AD SSP MP', 'C40', 'FGM AF74', 'DF64', 'GR 74'
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
                'fragrance_aroma': fragrance_aroma,
                'aftertaste': aftertaste,
                'acidity': acidity,
                'body': body,
                'sweetness': sweetness,
                'flavor': flavor,
                'rating': rating,
                'notes': notes,
                'notes_recipe': notes_recipe,
                'grinder': grinder,
                'grinder_setting': grinder_setting,
                'brew_tool': brew_tool,
                'date_time': date_time,
                'brew_method': brew_method,
                }
        features = pd.DataFrame(data, index=[0])
        return features

    # MAIN APP #
    st.sidebar.markdown('''
    ---
    Created with ❤️ by [Airkopi Café](https://lynk.id/airkopi/).
    ''')
    
    # User input data
    df = user_input_features()
    if st.button("Display Your Input"):
        st.write(df)
    
    # Gsheet data
    st.subheader("""
    Coffee data
    """)
    df_gsheet = dataGsheet(worksheet, df)
    st.write(df_gsheet.T)

    flavorNotes = notesGsheet(df_gsheet)
    input_df = initDF(flavorNotes, flavor_df_list)
    fig = flavorWheel(input_df)
    st.plotly_chart(fig, theme=None, use_container_width=True)

    categories = ['Aroma', 'Acidity', 'Sweetness', 'Flavor', 'Body', 'After Taste']
    categories = [*categories, categories[0]]

    score1 = [df.fragrance_aroma[0], df.acidity[0], df.sweetness[0], df.flavor[0], df.body[0], df.aftertaste[0]]
    score1 = [*score1, score1[0]]
    coffee_name = df_gsheet['Coffee'].iloc[0]

    radar_chart(score1, categories, coffee_name)
    st.write('Tasting notes: ', df['notes'].iloc[0])

    # Create an empty dataframe
    data = df

    # persist state of dataframe
    session_state = SessionState.get(df=data)
    
    if st.button("Spreadsheet Upload Basic"):
        df['date_time'] = df['date_time'].astype(str)
        dial_in_data = df.values.flatten().tolist()
        # st.write(dial_in_data)
        worksheet_dialin.append_row(dial_in_data, table_range='A1')
        st.write('Basic form has been uploaded!')


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
        linko= f'<a href="data:file/csv;base64,{b64}" download="basic.csv">Download csv file</a>'
        st.markdown(linko, unsafe_allow_html=True)

