import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px

def CoffeeGsheetList(worksheet, predictedData): #display rec. coffee
    df_gsheet = pd.DataFrame(worksheet.get_all_records())
    df_gsheet = df_gsheet.astype(str)
    df_gsheet = df_gsheet[[
        'id', 'Coffee', 'Notes', 'Card', 'Category', 'Price'            
        ]]

    #select row based on Category
    df_gsheet = df_gsheet.loc[df_gsheet['Category'] == predictedData].loc[df_gsheet['Price'] != '']
    display_df = df_gsheet[['Coffee', 'Notes', 'Price', 'Card']]

    return display_df
    
def radar_chart(score, category, name): #(score taken from user input, category is label name of that score, name is coffee selected)
    label_loc = np.linspace(start=0, stop=2 * np.pi, num=len(score))
    plt.figure(figsize=(6, 6))
    plt.subplot(polar=True)
    ax = plt.subplot(polar=True)
    # change the label below to coffee x
    title = f"Coffee: {name} "
    plt.title(title, size=20, y=1.05)

    plt.plot(label_loc, score, color='green', linewidth=1)
    plt.fill(label_loc, score, color='green', alpha=0.25)
    font = {
        'family' : 'normal',
        'size'   : 10}
    plt.rc('font', **font)
    title = f"Coffee: {name} "
    plt.title(title, size=20, y=1.05)
    plt.thetagrids(np.degrees(label_loc), labels=category)

    plt.rgrids([1, 2, 3, 4, 5])
    plt.legend()
    plt.show()
    st.pyplot(plt)

def radar_chart_compare(score, category, name): #(score taken from user input, category is label name of that score, name is coffee selected)
    label_loc = np.linspace(start=0, stop=2 * np.pi, num=len(score))
    plt.figure(figsize=(6, 6))
    plt.subplot(polar=True)
    ax = plt.subplot(polar=True)
    # change the label below to coffee x
    title = f"Coffee: {name} "
    plt.title(title, size=20, y=1.05)

    plt.plot(label_loc, score, color='green', linewidth=1)
    plt.fill(label_loc, score, color='green', alpha=0.25)

    #start - additional code for multiple graph
    score2 = score

    for i in range(len(score2)):
        score2[i] += 1 
 
    plt.plot(label_loc, score2, color='green', linewidth=1)
    plt.fill(label_loc, score2, color='green', alpha=0.25)
    
    #end - additional code for multiple graph
    
    font = {
        'family' : 'normal',
        'size'   : 10}
    plt.rc('font', **font)
    title = f"Coffee: {name} "
    plt.title(title, size=20, y=1.05)
    plt.thetagrids(np.degrees(label_loc), labels=category)

    plt.rgrids([1, 2, 3, 4, 5])
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    plt.show()
    st.pyplot(plt)

def dataGsheet(worksheet, df): # (worksheet is 1st Gsheet, df is user input form)
    df_gsheet = pd.DataFrame(worksheet.get_all_records())
    df_gsheet = df_gsheet.astype(str)
    df_gsheet = df_gsheet[[
        'id', 'Coffee', 'Notes', 'Process', 'Roast Profile', 'Age (rdtotoday)', 'Age (rdtofreeze)','Density'
        ]]

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
                input_df = pd.concat([input_df, notes_df], ignore_index=True)

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