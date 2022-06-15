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
    # Dial in - Basic

    """)
    st.sidebar.header('Input Parameters')
    def user_input_features():
        # 1st: min | 2nd: max | 3rd: default value
        id = st.sidebar.number_input('id', 0, 1000, 1)
        
        data = {'id': id,
                }
        features = pd.DataFrame(data, index=[0])
        return features

    def dataGsheet(worksheet, df):
        df_gsheet = pd.DataFrame(worksheet.get_all_records())
        df_gsheet = df_gsheet.astype(str)
        df_gsheet = df_gsheet[[
            'Id', 'Coffee','Notes', 'Height', 'Process', 'Location', 'Density',
            'Recipe Manual Brew - Intense', 'Recipe Manual Brew - Fruity',
            ]]

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

    def DensityToTemp (density):
        if density >= 350 and density <360:
            temp = 90

        if density >= 360 and density <380:
            temp = 91
        
        if density >= 380 and density <400:
            temp = 92

        if density >= 400 and density <420:
            temp = 93

        if density >= 420 and density <430:
            temp = 94

        if density >= 430 and density <450:
            temp = 95
        
        if density >= 450:
            temp = 96
        
        return temp

    df = user_input_features()
    
    #ghseet data
    st.subheader("""
    Coffee data
    """)
    df_gsheet = dataGsheet(worksheet, df)
    st.write(df_gsheet)
    st.write(df_gsheet['Notes'])
    st.write(df_gsheet['Recipe Manual Brew - Intense'])
    st.write(df_gsheet['Recipe Manual Brew - Fruity'])

    density = df_gsheet['Density']

    temp_brew = DensityToTemp(int(density))
    
    st.write(density)
    st.write("Temperature: ", temp_brew)

    flavorNotes = notesGsheet(df_gsheet)
    input_df = initDF(flavorNotes, flavor_df_temp)
    fig = flavorWheel(input_df)
    st.plotly_chart(fig)
