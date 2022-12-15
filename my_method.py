import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px

def radar_chart(score, category, name): #(score taken from user input, category is label name of that score, name is coffee selected)
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
    plt.rgrids([1, 2, 3, 4, 5])
    plt.legend()
    plt.show()
    st.pyplot(plt)

def dataGsheet(worksheet, df): # (worksheet is 1st Gsheet, df is user input form)
    df_gsheet = pd.DataFrame(worksheet.get_all_records())
    df_gsheet = df_gsheet.astype(str)
    df_gsheet = df_gsheet[[
        'id', 'Coffee','Age (days)', 'Age (rdtofreeze)', 'Notes', 'Process', 'Roast Profile', 
        'Density']]

    #select row based on id 
    values_list = df_gsheet.loc[df_gsheet['id'] == str(df['id'].iloc[0])]
    return values_list #return pandas df

#Select flavor notes based on id
def notesGsheet(df_gsheet):
    values_list_notes = df_gsheet['Notes']
    values_list_notes = [x for xs in values_list_notes for x in xs.split(',')]
    values_list_notes = [x.strip(' ') for x in values_list_notes]
    return values_list_notes #return tasting notes [' ', ' ', ] 1d array

#Matching and selecting flavor notes from database
def initDF(notes, flavorWheelList):
    flavor_df_list = pd.read_csv(flavorWheelList)
    flavor_df_list = flavor_df_list.reset_index()  # make sure indexes pair with number of rows
    header = [{'Parent':10, 'Child':100, 'Grandchild': 1000}]
    input_df = pd.DataFrame(header)
    input_df.drop(input_df.index, inplace=True)
    for index, row in flavor_df_list.iterrows():
        for i in notes:
            if i == row['Grandchild']:
                input_data = {'Parent':[row['Parent']], 'Child':[row['Child']], 'Grandchild': [i]}
                notes_df = pd.DataFrame(input_data)
                input_df = input_df.append(notes_df, ignore_index = True)

    return input_df # return df 3 columns - selected tasting notes, in FlavorWheelRaw.csv format

# Initiate flavor wheel that matched and selected
def flavorWheel(input_df): # input in FlavorWheelRaw.csv format
    fig = px.sunburst(input_df, path=['Parent', 'Child', 'Grandchild'])
    fig.update_layout(
        width=400, 
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