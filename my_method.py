import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go


def _prepare_radar_values(score, category):
    score_values = list(score)
    category_values = list(category)

    if len(score_values) > 1 and len(category_values) > 1:
        if score_values[0] == score_values[-1] and category_values[0] == category_values[-1]:
            score_values = score_values[:-1]
            category_values = category_values[:-1]

    closed_scores = score_values + [score_values[0]]
    closed_categories = category_values + [category_values[0]]
    return score_values, category_values, closed_scores, closed_categories

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
    _, category_values, closed_scores, closed_categories = _prepare_radar_values(score, category)

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=closed_scores,
            theta=closed_categories,
            fill='toself',
            mode='lines+markers',
            line=dict(color='#B45309', width=3),
            marker=dict(size=7, color='#F59E0B', line=dict(color='#FFF7ED', width=1.5)),
            fillcolor='rgba(245, 158, 11, 0.28)',
            hovertemplate='%{theta}: %{r}<extra></extra>',
            name=name,
        )
    )
    fig.update_layout(
        title=dict(
            text=f'Coffee Profile: {name}',
            x=0.5,
            xanchor='center',
            font=dict(size=24, color='#2B2118'),
        ),
        template='plotly_white',
        paper_bgcolor='#FFF9F0',
        plot_bgcolor='#FFF9F0',
        margin=dict(t=80, l=40, r=40, b=40),
        height=520,
        showlegend=False,
        polar=dict(
            bgcolor='#FFF9F0',
            radialaxis=dict(
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                tickfont=dict(size=12, color='#6B5B4D'),
                gridcolor='#E8D9C8',
                gridwidth=1,
                linecolor='#D8C3A5',
                angle=90,
            ),
            angularaxis=dict(
                tickfont=dict(size=16, color='#2B2118'),
                gridcolor='#E8D9C8',
                linecolor='#D8C3A5',
                direction='clockwise',
                rotation=90,
            ),
        ),
        hoverlabel=dict(
            bgcolor='#FFFDF8',
            font=dict(color='#2B2118', size=14),
        ),
    )
    st.plotly_chart(fig, theme=None, use_container_width=True)

def radar_chart_compare(score, category, name): #(score taken from user input, category is label name of that score, name is coffee selected)
    score_values, category_values, closed_scores, closed_categories = _prepare_radar_values(score, category)
    comparison_scores = [min(value + 1, 5) for value in score_values]
    closed_comparison_scores = comparison_scores + [comparison_scores[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=closed_scores,
            theta=closed_categories,
            fill='toself',
            mode='lines+markers',
            line=dict(color='#B45309', width=3),
            marker=dict(size=7, color='#F59E0B', line=dict(color='#FFF7ED', width=1.5)),
            fillcolor='rgba(245, 158, 11, 0.24)',
            hovertemplate='%{theta}: %{r}<extra>Current</extra>',
            name='Current',
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=closed_comparison_scores,
            theta=closed_categories,
            fill='toself',
            mode='lines+markers',
            line=dict(color='#2563EB', width=3),
            marker=dict(size=7, color='#60A5FA', line=dict(color='#EFF6FF', width=1.5)),
            fillcolor='rgba(37, 99, 235, 0.16)',
            hovertemplate='%{theta}: %{r}<extra>Comparison</extra>',
            name='Comparison',
        )
    )
    fig.update_layout(
        title=dict(
            text=f'Coffee Profile: {name}',
            x=0.5,
            xanchor='center',
            font=dict(size=24, color='#2B2118'),
        ),
        template='plotly_white',
        paper_bgcolor='#FFF9F0',
        plot_bgcolor='#FFF9F0',
        margin=dict(t=80, l=40, r=40, b=40),
        height=520,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.05,
            xanchor='center',
            x=0.5,
        ),
        polar=dict(
            bgcolor='#FFF9F0',
            radialaxis=dict(
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                tickfont=dict(size=12, color='#6B5B4D'),
                gridcolor='#E8D9C8',
                gridwidth=1,
                linecolor='#D8C3A5',
                angle=90,
            ),
            angularaxis=dict(
                tickfont=dict(size=16, color='#2B2118'),
                gridcolor='#E8D9C8',
                linecolor='#D8C3A5',
                direction='clockwise',
                rotation=90,
            ),
        ),
        hoverlabel=dict(
            bgcolor='#FFFDF8',
            font=dict(color='#2B2118', size=14),
        ),
    )
    st.plotly_chart(fig, theme=None, use_container_width=True)

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
    flavor_palette = {
        'Floral': '#7C3AED',
        'Fruity': '#2563EB',
        'Green/vegetative': '#2F855A',
        'Nutty/Cocoa': '#92400E',
        'Other': '#475569',
        'Roasted': '#9A3412',
        'Sour': '#D97706',
        'Spices': '#B91C1C',
        'Sweet': '#DB2777',
    }
    fig = px.sunburst(
        input_df,
        path=['Parent', 'Child', 'Grandchild'],
        color='Parent',
        color_discrete_map=flavor_palette,
    )
    fig.update_traces(
        textfont=dict(color='#FFF7ED', size=16),
        insidetextorientation='auto',
        hovertemplate='<b>%{label}</b><br>Group: %{parent}<extra></extra>',
        marker=dict(line=dict(color='#F5E6D3', width=1.2)),
    )
    fig.update_layout(
        autosize=True,
        height=520,
        template='plotly_white',
        paper_bgcolor='#FFF9F0',
        plot_bgcolor='#FFF9F0',
        margin=dict(t=70, l=10, r=10, b=10),
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
            color='#2B2118',
            ),
        hoverlabel=dict(
            bgcolor='#FFFDF8',
            font=dict(color='#2B2118', size=14),
        ),
        uniformtext=dict(
            minsize=10,
            mode='hide',
        ),
        )
    return fig
