import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
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

#select Dial-in Basic 
worksheet_dialin = sh.worksheet("Dial-in Basic")

# data from gsheet <end>

#full tasting notes database
flavor_df_list = 'FlavorWheelRaw.csv'

def app():
    st.write("""
    # Brewing Guide
    """)

    st.sidebar.header('Input Parameters')
    radar_metrics = ['fragrance_aroma', 'acidity', 'sweetness', 'flavor', 'aftertaste']
    radar_labels = ['Aroma', 'Acidity', 'Sweetness', 'Flavor', 'After Taste']
    parallel_dimensions = [
        'dose_g', 'yield_ml', 'time_s', 'temperature', 'grinder_setting',
        'fragrance_aroma', 'acidity', 'sweetness', 'flavor', 'aftertaste', 'rating',
    ]
    
    def user_input_features():
        # 1st: min | 2nd: max | 3rd: default value
        id = st.sidebar.number_input('id', 0, 1000, 1)
        grinder_micron = st.sidebar.number_input('Micron to Grinder', 0, 2000, 720)
        dose = st.sidebar.number_input('Dose', 0.0, 1000.0, 12.0)
        strength = st.sidebar.selectbox(
            'Select Coffee Strength ', 
                (
                    '60g/L 16.67', '65g/L 15.4', '70g/L 14.3',
                    '75g/L 13.3', '80g/L 12.5', '100g/L 10'
                )
        )
        taste_profile = st.sidebar.selectbox(
            'Select Taste Profile ', 
                (
                    'Sweetness', 'Acidity', 'Balanced', 'Iced', 'Clarity'
                )
        )        
        
        data = {'id': id,
                'grinder_micron': grinder_micron,
                'strength': strength,
                'dose': dose,
                'taste_profile': taste_profile,
                }
        features = pd.DataFrame(data, index=[0])
        return features

    def dataGsheet(worksheet, df):
        df_gsheet = pd.DataFrame(worksheet.get_all_records())
        df_gsheet = df_gsheet.astype(str)
        df_gsheet = df_gsheet[[
            'id', 'Coffee','Notes', 'Height', 'Process', 'Location', 'Density','Age (rdtotoday)', 'Age (rdtofreeze)',
            ]]

        #select row based on id 
        values_list = df_gsheet.loc[df_gsheet['id'] == str(df['id'].iloc[0])]
        return values_list

    def dataGsheet2Filter(worksheet2, df):
        df_gsheet = pd.DataFrame(worksheet2.get_all_records())
        df_gsheet = df_gsheet.astype(str)
        numeric_columns = [
            'rating', 'dose_g', 'yield_ml', 'time_s', 'temperature',
            'fragrance_aroma', 'aftertaste', 'acidity', 'sweetness', 'flavor',
        ]
        df_gsheet[numeric_columns] = df_gsheet[numeric_columns].apply(
            pd.to_numeric, errors='coerce'
        )
        df_gsheet = df_gsheet[[
            'id', 'rating', 'grinder', 'grinder_setting', 'dose_g',
            'yield_ml', 'time_s','temperature',
            'brew_method', 'brew_tool', 'notes_recipe', 'notes','fragrance_aroma',
            'aftertaste', 'acidity', 'sweetness', 'flavor',
            ]]

        #select row based on id 
        # values_list = df_gsheet.loc[df_gsheet['id'] == str(df['id'].iloc[0])]
        df_gsheet["ratio"] = df_gsheet["yield_ml"] / df_gsheet["dose_g"]
        df_id = str(df['id'].iloc[0])
        values_list = df_gsheet.query("id == @df_id").sort_values(by='rating', ascending=False)
        value_list_filter = values_list[values_list['brew_method'].str.contains("Pour|Hybrid", na=False)]
        return value_list_filter

    def dataGsheet2Spro(worksheet2, df):
        df_gsheet = pd.DataFrame(worksheet2.get_all_records())
        df_gsheet = df_gsheet.astype(str)
        numeric_columns = [
            'rating', 'dose_g', 'yield_ml', 'time_s', 'temperature',
            'fragrance_aroma', 'aftertaste', 'acidity', 'sweetness', 'flavor',
        ]
        df_gsheet[numeric_columns] = df_gsheet[numeric_columns].apply(
            pd.to_numeric, errors='coerce'
        )

        df_gsheet = df_gsheet[[
            'id', 'rating', 'grinder', 'grinder_setting', 'dose_g',
            'yield_ml', 'time_s', 
            'temperature', 'brew_method', 'notes_recipe','notes','fragrance_aroma',
            'aftertaste', 'acidity', 'sweetness', 'flavor',
            ]]

        #select row based on id 
        # values_list = df_gsheet.loc[df_gsheet['id'] == str(df['id'].iloc[0])]
        df_id = str(df['id'].iloc[0])
        values_list = df_gsheet.query("id == @df_id").sort_values(by='rating', ascending=False)
        value_list_spro = values_list[values_list['brew_method'].str.contains("Espresso")]

        # For SSP MP / LS grinder only
        # value_list_MP = values_list[values_list['grinder'].str.contains("MP|LS", na=False)]
        # value_list_spro = value_list_MP[value_list_MP['brew_method'].str.contains("Espresso")]
        
        return value_list_spro

    def apply_numeric_operator_filter(df_filter, column_name, operator, value):
        if operator == '>':
            return df_filter[df_filter[column_name] > value]
        if operator == '<':
            return df_filter[df_filter[column_name] < value]
        if operator == '>=':
            return df_filter[df_filter[column_name] >= value]
        if operator == '<=':
            return df_filter[df_filter[column_name] <= value]
        if operator == '==':
            return df_filter[df_filter[column_name] == value]
        if operator == '!=':
            return df_filter[df_filter[column_name] != value]
        return df_filter

    def apply_contains_text_filter(df_filter, column_name, search_text):
        if not search_text:
            return df_filter
        return df_filter[
            df_filter[column_name].astype(str).str.contains(
                search_text, na=False, case=False
            )
        ]

    def notesGsheet(df_gsheet):
        values_list_notes = df_gsheet['Notes']
        values_list_notes = [x for xs in values_list_notes for x in xs.split(',')]
        values_list_notes = [x.strip(' ') for x in values_list_notes]
        
        return values_list_notes

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
                    input_df = pd.concat((input_df, notes_df), ignore_index=True)
        return input_df

    def flavorWheel(input_df):
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

    def recipe_radar_chart(selected_df, chart_title):
        fig = go.Figure()
        color_cycle = px.colors.qualitative.Bold

        for position, (row_index, selected_row) in enumerate(selected_df.iterrows()):
            score_values = [selected_row.get(column, 0) for column in radar_metrics]
            score_values = [value if pd.notna(value) else 0 for value in score_values]
            closed_scores = score_values + [score_values[0]]
            closed_labels = radar_labels + [radar_labels[0]]
            line_color = color_cycle[position % len(color_cycle)]
            trace_name = (
                f"idx {row_index} | id {selected_row.get('id', '')} | "
                f"rating {selected_row.get('rating', '')}"
            )

            fig.add_trace(
                go.Scatterpolar(
                    r=closed_scores,
                    theta=closed_labels,
                    fill='toself',
                    mode='lines+markers',
                    line=dict(color=line_color, width=3),
                    marker=dict(size=7, color=line_color, line=dict(color='#FFF7ED', width=1.2)),
                    fillcolor=line_color,
                    opacity=0.28,
                    hovertemplate='%{theta}: %{r}<extra>' + trace_name + '</extra>',
                    name=trace_name,
                )
            )
        
        fig.update_layout(
            title=dict(
                text=chart_title,
                x=0.5,
                xanchor='center',
                font=dict(size=24, color='#2B2118'),
            ),
            template='plotly_white',
            paper_bgcolor='#FFF9F0',
            plot_bgcolor='#FFF9F0',
            margin=dict(t=80, l=40, r=40, b=40),
            height=520,
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.08,
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

    def render_selected_recipe_dialin_visual(selected_df, chart_title_prefix):
        if selected_df.empty:
            st.info('no selected data to show')
            return

        # chart_title = f'{chart_title_prefix} Comparison'
        chart_title = ''
        recipe_radar_chart(selected_df, chart_title)

    def render_recipe_dialin_selector(history_df, selector_key, chart_title_prefix):
        if history_df.empty:
            st.info('no selected data to show')
            return

        selectable_df = history_df.copy()
        display_columns = [
            'rating', 'grinder', 'grinder_setting', 'dose_g',
            'yield_ml', 'time_s', 'temperature', 'brew_method', 'brew_tool',
            'notes_recipe', 'notes', 'fragrance_aroma', 'aftertaste',
            'acidity', 'sweetness', 'flavor',
        ]
        display_columns = [column for column in display_columns if column in selectable_df.columns]

        try:
            st.dataframe(selectable_df[display_columns], use_container_width=True)
        except TypeError:
            st.dataframe(selectable_df[display_columns])

        selected_index = st.multiselect(
            'Select index rows',
            options=selectable_df.index.tolist(),
            format_func=lambda idx: f'Index {idx}',
            key=f'{selector_key}_dialin_multiselect',
        )

        if not selected_index:
            st.info('no selected data to show')
            return

        selected_full_df = history_df.loc[selected_index].copy()
        render_selected_recipe_dialin_visual(selected_full_df, chart_title_prefix)

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
    
    def DensityCompass(density, dose, process, height):

        if density <360:
            temp = 88
            bar = 6
            Yield = 1.5 * dose
            milk = (dose*15.4*0.85) - (Yield)
            if dose >=14 and dose <19:
                grinder = 12            
            elif dose >=19 and dose <24:
                grinder = 15
            elif dose <14:
                grinder = 10
            else:
                grinder = 16           

        if density >= 360 and density <390:
            temp = 91
            bar = 7
            Yield = 2 * dose
            milk = (dose*16*0.85) - (Yield)
            if dose >=14 and dose <19:
                grinder = 11
            elif dose >=19 and dose <24:
                grinder = 13
            elif dose <14:
                grinder = 9
            else:
                grinder = 14

        if density >= 390 and density <430:
            temp = 93
            bar = 8
            Yield = 2.5 * dose
            milk = (dose*16.67*0.85) - (Yield)
            
            if dose >=14 and dose <19:
                grinder = 10
            elif dose >=19 and dose <24:
                grinder = 12
            elif dose <14:
                grinder = 8
            else:
                grinder = 13
        if density >= 430:
            temp = 95
            bar = 9
            Yield = 3 * dose
            milk = (dose*17*0.85) - (Yield)
            if dose >=14 and dose <19:
                grinder = 9
            elif dose >=19 and dose <24:
                grinder = 10
            elif dose <14:
                grinder = 7
            else:
                grinder = 11
        
        if height>1900:
            return temp, bar-1, grinder+2, Yield, milk

        if 'ash' in process:
            return temp+1, bar+1, grinder-2, Yield, milk
        
        if 'tural' in process:
            return temp-1, bar-1, grinder+2, Yield, milk
        
        return temp, bar, grinder, Yield, milk
    
    def DensityFilter(density, dose, taste_profile, process, height):

        if dose <=15:
            grinder = 53            
        elif dose >15 and dose <=20:
            grinder = 59
        elif dose >20 and dose <=30:
            grinder = 62                
        else:
            grinder = 70

        if density >=350 and density <=380:
            ratio = 14.3
            temp = 88
            grinder = grinder + 5
        elif density >=381 and density <=420:
            ratio = 15.4
            temp = 92
        elif density >420:
            ratio = 16.67
            temp = 95
            grinder = grinder - 5

        if taste_profile == 'Sweetness':
            dripper = 'Flat'
            recipe = 'Hoffman'
            grinder = grinder + 6            
        elif taste_profile == 'Acidity':
            dripper = 'Conical'
            recipe = 'Tetsu'
            grinder = grinder + 20
            ratio = ratio - 1 
        elif taste_profile == 'Balanced': 
            dripper = 'Conical'
            recipe = '5 pour'
            grinder = grinder
        elif taste_profile == 'Clarity': 
            dripper = 'Puck'
            recipe = '1-2-1 Gabi'
            grinder = grinder - 10    
        else:
            dripper = 'Conical'
            recipe = 'Iced'
            grinder = grinder - 5
            ratio = ratio - 1 

        # for decaf
        if 'Process' in process:
            return temp, ratio, grinder-8, dripper, recipe
        
        if height>1900:
            return temp, ratio, grinder+5, dripper, recipe
        
        return temp, ratio, grinder, dripper, recipe
        
    # def CoffeeProcessCheck(process):
    #     if "tural" in process:
    #         st.write("Process:", process, " - Careful! Prone to overextract ( 3 pour <93C )")

    def CoffeeWaterRatio(strength, dose):

        if strength == '60g/L 16.67':
            water = dose * 16.67
             
        if strength == '65g/L 15.4':
            water = dose * 15.4

        if strength == '70g/L 14.3':
            water = dose * 14.3

        if strength == '75g/L 13.3':
            water = dose * 13.3

        if strength == '80g/L 12.5':
            water = dose * 12.5

        if strength == '100g/L 10':
            water = dose * 10

        return int(water)

    df = user_input_features()
    
    #ghseet data
    st.sidebar.markdown('''
    ---
    Created with ❤️ by [Airkopi Café](https://lynk.id/airkopi/).
    ''')      
    st.subheader("""
    Coffee data
    """)
    df_gsheet = dataGsheet(worksheet, df)
    
    st.write(df_gsheet.T)
    if st.button("Density reference id"):
        st.write("Density 350 - id 4 \n \n Density 360 - id 26 \n \n Density 370 - id 27 \n \n Density 380 - id 3 \n \n Density 390 - id 8 \n \n Density 400 - id 9 \n \n Density 410 - id 20 \n \n Density 430 - id 38 \n \n Density 450 - id 53 \n \n Density 500 - id 56 \n \n ")
        
    density = df_gsheet['Density'].iloc[0]
    temp_brew = DensityToTemp(int(density))
    st.write("Density: ", int(density), " | Temperature: ", temp_brew)    
    process = df_gsheet['Process'].iloc[0]
    height = df_gsheet['Height'].iloc[0]
    # CoffeeProcessCheck(process)

    grinder_setting =  df['grinder_micron'].iloc[0]
    st.write("Grinder Setting: ", int(grinder_setting / 13.5), ' | C40: ', int(grinder_setting / 30), "Click", ' | ', grinder_setting, ' micron')

    strength =  df['strength'].iloc[0]
    dose = df['dose'].iloc[0]
    taste_profile = df['taste_profile'].iloc[0]

    with st.expander("Auto Recipe"):
        
        if st.button("Spro Recipe"):
            t,b,g,y,m  = DensityCompass(int(density),float(dose), process, int(height))
                    
            # st.write('Recipe :', t,'C', ' | ', b, ' b', ' | ', 
            # g, ' DF64 SSP ', ' | ', round(y,2), ' out', ' | ', round(m,2), ' milk/water (', round((m/y),2), ')  |  ',
            # 'Ratio: ', '1.5 -', float(dose)*1.5,'2 -', float(dose)*2,'2.5 -', float(dose)*2.5, '3 -', float(dose)*3,
            # '5 -', float(dose)*5,
            # )
            
            data = {'Temperature': t,
                'DF64 SSP MP': g,
                'Pressure bar': b,
                'Dose': dose,            
                'Yield': y,
                'Ratio': y/dose,
                'milk/water': m,
                'milk/water ratio': round((m/y),2),
                }
            
            data_table_og = pd.DataFrame(data, index=['estimate'])
            data_table_transpose = data_table_og.T
            st.write(data_table_transpose)
        

        if st.button("Filter Recipe"):
            # temp, ratio, grinder, dripper, recipe
            t,r,g,d,rec  = DensityFilter(int(density),float(dose), taste_profile, process, int(height))
          
            # st.write('Recipe :', t,'C', ' | ', r, ' ratio', ' | ', 
            # g, ' DF64 SSP (', g*13.5, 'micron) ', int(g*13.5/30), ' click C40', ' | ', d, ' dripper', ' | ', rec, ' recipe'
            # )

            st.write('Recommended: ', d, ' dripper', ' | ', rec, ' recipe')

            data = {'Temperature': t,
                'DF64 SSP MP': g,
                'C40': g*13.5/30,
                'Grind size micron': g*13.5,
                'Ratio': r,
                # error when transpose different data type on a single column
                # 'Dripper': d,
                # 'Recipe': rec,
                }
            
            data_table_og = pd.DataFrame(data, index=['estimate'])
            data_table_transpose = data_table_og.transpose()
            st.write(data_table_transpose)

        if st.button("Spro Dialed"):
            st.session_state.spro_dialed = True
        
        if st.session_state.get('spro_dialed', False):
            df_gsheet2 = dataGsheet2Spro(worksheet_dialin, df)
            enable_filter = st.checkbox('Enable filter')
            if enable_filter:
                spro_numeric_filter_columns = [
                    'rating', 'dose_g', 'yield_ml', 'time_s',
                    'temperature', 'fragrance_aroma', 'aftertaste', 'acidity',
                    'sweetness', 'flavor',
                ]
                spro_text_filter_columns = [
                    'grinder', 'grinder_setting', 'brew_method',
                    'notes_recipe', 'notes',
                ]

                selected_numeric_filter_columns = st.multiselect(
                    'Numeric filter columns',
                    spro_numeric_filter_columns,
                    default=[],
                    key='selected_numeric_filter_columns_spro',
                )

                for filter_column in selected_numeric_filter_columns:
                    valid_values = df_gsheet2[filter_column].dropna()
                    default_value = float(valid_values.iloc[0]) if not valid_values.empty else 0.0
                    min_value = float(valid_values.min()) if not valid_values.empty else 0.0
                    max_value = float(valid_values.max()) if not valid_values.empty else 0.0

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(filter_column)
                    with col2:
                        operator = st.selectbox(
                            f'Operator for {filter_column}',
                            ['>', '<', '>=', '<=', '==', '!='],
                            key=f'op_{filter_column}',
                        )
                    with col3:
                        value = st.number_input(
                            f'Value for {filter_column}',
                            min_value=min_value,
                            max_value=max_value,
                            value=default_value,
                            key=f'val_{filter_column}',
                        )

                    df_gsheet2 = apply_numeric_operator_filter(
                        df_gsheet2, filter_column, operator, value
                    )

                selected_text_filter_columns = st.multiselect(
                    'Text filter columns',
                    spro_text_filter_columns,
                    default=[],
                    key='selected_text_filter_columns_spro',
                )

                for filter_column in selected_text_filter_columns:
                    search_text = st.text_input(
                        f'Type text for {filter_column}',
                        key=f'search_text_{filter_column}',
                    )

                    df_gsheet2 = apply_contains_text_filter(
                        df_gsheet2, filter_column, search_text
                    )
            
            if 'selected_columns_spro' not in st.session_state:
                st.session_state.selected_columns_spro = df_gsheet2.columns.tolist()
            enable_remove_columns_spro = st.checkbox(
                'Enable remove columns',
                key='enable_remove_columns_spro',
            )
            if enable_remove_columns_spro:
                columns = st.multiselect(
                    'Select columns to display',
                    df_gsheet2.columns.tolist(),
                    default=st.session_state.selected_columns_spro,
                    key='selected_columns_spro_multiselect',
                )
                st.session_state.selected_columns_spro = columns
            else:
                columns = df_gsheet2.columns.tolist()
            st.write(df_gsheet2[columns])
            st.markdown('#### Espresso Dial-in Visualizer')
            render_recipe_dialin_selector(df_gsheet2.reset_index(drop=True), 'recipe_espresso', 'Espresso Dial-in')

        if st.button("Filter Dialed"):
            st.session_state.filter_dialed = True

        if st.session_state.get('filter_dialed', False):
            df_gsheet2_filter = dataGsheet2Filter(worksheet_dialin, df)
            enable_filter_dialed = st.checkbox('Enable filter', key='enable_filter_dialed')
            if enable_filter_dialed:
                filter_numeric_filter_columns = [
                    'rating', 'dose_g', 'yield_ml', 'time_s',
                    'temperature', 'fragrance_aroma', 'aftertaste', 'acidity',
                    'sweetness', 'flavor', 'ratio',
                ]
                filter_text_filter_columns = [
                    'grinder', 'grinder_setting', 'brew_method',
                    'brew_tool', 'notes_recipe', 'notes',
                ]

                selected_numeric_filter_columns = st.multiselect(
                    'Numeric filter columns',
                    filter_numeric_filter_columns,
                    default=[],
                    key='selected_numeric_filter_columns_filter',
                )

                for filter_column in selected_numeric_filter_columns:
                    valid_values = df_gsheet2_filter[filter_column].dropna()
                    default_value = float(valid_values.iloc[0]) if not valid_values.empty else 0.0
                    min_value = float(valid_values.min()) if not valid_values.empty else 0.0
                    max_value = float(valid_values.max()) if not valid_values.empty else 0.0

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(filter_column)
                    with col2:
                        operator = st.selectbox(
                            f'Operator for {filter_column}',
                            ['>', '<', '>=', '<=', '==', '!='],
                            key=f'filter_op_{filter_column}',
                        )
                    with col3:
                        value = st.number_input(
                            f'Value for {filter_column}',
                            min_value=min_value,
                            max_value=max_value,
                            value=default_value,
                            key=f'filter_val_{filter_column}',
                        )

                    df_gsheet2_filter = apply_numeric_operator_filter(
                        df_gsheet2_filter, filter_column, operator, value
                    )

                selected_text_filter_columns = st.multiselect(
                    'Text filter columns',
                    filter_text_filter_columns,
                    default=[],
                    key='selected_text_filter_columns_filter',
                )

                for filter_column in selected_text_filter_columns:
                    search_text = st.text_input(
                        f'Type text for {filter_column}',
                        key=f'filter_search_text_{filter_column}',
                    )

                    df_gsheet2_filter = apply_contains_text_filter(
                        df_gsheet2_filter, filter_column, search_text
                    )

            if 'selected_columns_filter' not in st.session_state:
                st.session_state.selected_columns_filter = df_gsheet2_filter.columns.tolist()
            enable_remove_columns_filter = st.checkbox(
                'Enable remove columns',
                key='enable_remove_columns_filter',
            )
            if enable_remove_columns_filter:
                columns_filter = st.multiselect(
                    'Select columns to display',
                    df_gsheet2_filter.columns.tolist(),
                    default=st.session_state.selected_columns_filter,
                    key='selected_columns_filter_multiselect',
                )
                st.session_state.selected_columns_filter = columns_filter
            else:
                columns_filter = df_gsheet2_filter.columns.tolist()
            st.write(df_gsheet2_filter[columns_filter])
            st.markdown('#### Filter Dial-in Visualizer')
            render_recipe_dialin_selector(df_gsheet2_filter.reset_index(drop=True), 'recipe_filter', 'Filter Dial-in')

    # Brewing Recipe
    coffee_water_ratio = CoffeeWaterRatio(strength, float(dose))
    st.write(
        "Coffee to Water Ratio: ", float(dose),':', coffee_water_ratio,
    )

    with st.expander("Recipe Guide"):
        if st.button("Recipe 1 Hoffman"):

            # Recipe 1 Hoffman
            st.write(
                '6-4 :', int(dose*3), ':', int(coffee_water_ratio*0.6), ':', 
                int(coffee_water_ratio), '( after 2nd pour: -',
                (int(coffee_water_ratio) - int(coffee_water_ratio*0.6)) , ')'        
            )       

        if st.button("Recipe 2 Tetsu"):
            # Recipe 2 Tetsu
            st.write(
                'Tetsu 4-6 : \n \n',
                '(', int(coffee_water_ratio*0.4), ')', 
                int(coffee_water_ratio*0.2), ':',
                int(coffee_water_ratio*0.4), ' \n \n',
                int(coffee_water_ratio*0.6), ':',
                int(coffee_water_ratio*0.8), ':',
                int(coffee_water_ratio), 
                '( ', int(coffee_water_ratio*0.6), ')', 
            )

        if st.button("Recipe 3: 5 Pour"):
            # Recipe 3 Joachim 5 Pour
            st.write(
                '5 Pour 1 cup:  \n \n ', 
                int(coffee_water_ratio*0.15), ' \n \n ',
                int(coffee_water_ratio*0.35),'(after 2nd pour: -', (int(coffee_water_ratio-coffee_water_ratio*0.35)), ')',' \n \n ',                
                int(coffee_water_ratio*0.55), '(after 3rd pour: -', (int(coffee_water_ratio-coffee_water_ratio*0.55)), ')',' \n \n ',
                int(coffee_water_ratio*0.8), ' \n \n ',
                int(coffee_water_ratio), ' \n \n ',
            )

        if st.button("Recipe 4: Iced"):
            # 35% iced
            st.write(
                'Iced Coffee:  \n \n ', 
                int(coffee_water_ratio*0.35), ' 35% iced', ' \n \n ',
                int(coffee_water_ratio*0.65),' 65% hot', ' \n \n ',
                int(coffee_water_ratio*0.65/3), ' each 3x', ' \n \n ',
            )

        if st.button("Recipe 5: Cold Immersion"):
            # 35% iced
            st.write(
                'Iced Coffee:  \n \n ', 
                int(coffee_water_ratio*0.35), ' 35% iced', ' \n \n ',
                int(coffee_water_ratio*0.65), ' \n \n ',
            )
        if st.button("Recipe 6: 1-2-1 Gabi"):
            # lance 1-2-1 puck screen gabi / no bypass hack
            st.write(
                '1-2-1 :', int(dose*4),':', coffee_water_ratio, ' ( -', int((coffee_water_ratio-(dose*4))), ') after 1st pour',
            )

    flavorNotes = notesGsheet(df_gsheet)
    input_df = initDF(flavorNotes, flavor_df_list)
    fig = flavorWheel(input_df)
    st.plotly_chart(fig, theme=None, use_container_width=True)
