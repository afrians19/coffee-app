import streamlit as st
import pandas as pd
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

flavor_df_list = 'FlavorWheelRaw.csv'

def app():
    st.write("""
    # Brewing Guide
    """)

    st.sidebar.header('Input Parameters')
    
    def user_input_features():
        # 1st: min | 2nd: max | 3rd: default value
        id = st.sidebar.number_input('id', 0, 1000, 1)
        grinder_micron = st.sidebar.number_input('Micron to Grinder', 0, 2000, 720)
        dose = st.sidebar.number_input('Dose', 0.0, 1000.0, 12.0)
        strength = st.sidebar.selectbox(
            'Select Coffee Strength ', 
                (
                    '60g/L 16.67 Intense (L)', '65g/L 15.4 Intense (M)', '70g/L 14.3 Fruity (L / MD)',
                    '80g/L 12.5', '100g/L 10'
                )
        )

        data = {'id': id,
                'grinder_micron': grinder_micron,
                'strength': strength,
                'dose': dose,
                }
        features = pd.DataFrame(data, index=[0])
        return features

    def dataGsheet(worksheet, df):
        df_gsheet = pd.DataFrame(worksheet.get_all_records())
        df_gsheet = df_gsheet.astype(str)
        df_gsheet = df_gsheet[[
            'id', 'Coffee','Notes', 'Age (rdtotoday)', 'Age (rdtofreeze)', 'Height', 'Process', 'Location', 'Density',
            'Recipe Manual Brew - Intense', 'Recipe Manual Brew - Fruity',
            ]]

        #select row based on id 
        values_list = df_gsheet.loc[df_gsheet['id'] == str(df['id'].iloc[0])]
        return values_list

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
                    input_df = input_df.append(notes_df, ignore_index = True)
        return input_df

    def flavorWheel(input_df):
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

    def CoffeeProcessCheck(process):
        if "Natural" in process:
            st.write("Process:", process, " - Careful! Prone to overextract ( 3 pour <93C )")

    def CoffeeWaterRatio(strength, dose):

        if strength == '60g/L 16.67 Intense (L)':
            water = dose * 16.67
             
        if strength == '65g/L 15.4 Intense (M)':
            water = dose * 15.4

        if strength == '70g/L 14.3 Fruity (L / MD)':
            water = dose * 14.3

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
    st.write(df_gsheet)
    st.write('Intense Recipe: ', df_gsheet['Recipe Manual Brew - Intense'].iloc[0])
    st.write('Fruity Recipe: ', df_gsheet['Recipe Manual Brew - Fruity'].iloc[0])
    
    density = df_gsheet['Density'].iloc[0]
    temp_brew = DensityToTemp(int(density))
    st.write("Density: ", int(density), " | Temperature: ", temp_brew)
        
    process = df_gsheet['Process'].iloc[0]
    CoffeeProcessCheck(process)

    grinder_setting =  df['grinder_micron'].iloc[0]
    st.write("Grinder Setting: ", int(grinder_setting / 13.5), ' | C40: ', int(grinder_setting / 30), "Click")

    strength =  df['strength'].iloc[0]
    dose = df['dose'].iloc[0]

    # Brewing Recipe
    coffee_water_ratio = CoffeeWaterRatio(strength, float(dose))
    st.write(
        "Coffee to Water Ratio: ", float(dose),':', coffee_water_ratio,
    )

    if st.button("Recipe 1 Hoffman"):

        # Recipe 1 Hoffman
        st.write('6-4 :', int(dose*3), ':', int(coffee_water_ratio*0.6), ':', 
        int(coffee_water_ratio), '( -',
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

    if st.button("Recipe 3: 5 Pour 1 cup"):
        # Recipe 3 Joachim 5 Pour (single dose)
        st.write(
            '5 Pour 1 cup:  \n \n ', 
            int(coffee_water_ratio*0.15), ' \n \n ',
            int(coffee_water_ratio*0.35), ' \n \n ',
            '(after 2nd pour: -', (int(coffee_water_ratio-coffee_water_ratio*0.35)), ')',' \n \n ',
            int(coffee_water_ratio*0.55), ' \n \n ',
            '(after 3rd pour: -', (int(coffee_water_ratio-coffee_water_ratio*0.55)), ')',
            int(coffee_water_ratio*0.8), ' \n \n ',
            int(coffee_water_ratio), ' \n \n ',
        )        

    flavorNotes = notesGsheet(df_gsheet)
    input_df = initDF(flavorNotes, flavor_df_list)
    fig = flavorWheel(input_df)
    st.plotly_chart(fig)