import streamlit as st
import pandas as pd
import base64
import SessionState
import gspread
from google.oauth2.service_account import Credentials
import pickle
from my_method import CoffeeGsheetList

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

# flavor_df_list = 'FlavorWheelNotes.csv'
base_df = 'base_df_input.csv'
filename_RF = 'rf_model.sav'
        
def app():

    def user_input_features():       
        profile = st.radio(
            "Which taste profile do you prefer?",
            ('Sweet', 'Acidic')
            )

        flavor = st.radio(
            "Which coffee flavor do you prefer?",
            ('Chocolaty / Caramel', 'Bright / Citrusy', 'Fruity')
            )

        data = {
                'Profile': profile,
                'Flavor': flavor,
                }
        features = pd.DataFrame(data, index=[0])        
        return features

    # MAIN APP #
    # st.sidebar.markdown('''
    # ---
    # Created with ❤️ by [Airkopi Café](https://lynk.id/airkopi/).
    # ''')    
    st.subheader("""
    We help you choose our tasty cup of coffee!
    """)

    base_ml_input = pd.read_csv(base_df)

    features_user = user_input_features()
    
    # ML Features 
    features_base = base_ml_input[['Profile_Acidic','Profile_Sweet','Flavor_Bright / Citrusy','Flavor_Chocolaty / Caramel','Flavor_Fruity']]  
    features = pd.get_dummies(features_user)
    features_base = features_base.append(features).fillna(0)

    # predictor / input variable
    features_data = features_base.tail(1)

    # Predict
    if st.button("Press here to see specialty coffee that suits you"):
        loaded_model_randomForest = pickle.load(open(filename_RF, "rb")) # Load Model error in cloud
        result = loaded_model_randomForest.predict(features_data)
        st.write('Great Choices! The coffee especially for you: ', result[0])
        df_gsheet = CoffeeGsheetList(worksheet, result[0])
        
        link_list = []

        for i in df_gsheet.index:

            link = df_gsheet['Card'][i]
            df_temp = pd.DataFrame(
                {
                    "url": [
                        f'<a target="_blank" href="{link}">Coffee Details</a>'
                    ]
                }
            )            
            link_list.append(df_temp['url'][0])
            # df_link = df_link.append(df_temp, ignore_index = True)

        df_gsheet['url'] = link_list
        df_gsheet = df_gsheet[['Coffee', 'Notes', 'Price', 'url']].sort_values(by='Price')
        st.write(df_gsheet.to_html(escape=False, index=False), unsafe_allow_html=True)

    # if st.button("Press here to reveal coffee tasting wheel"):
    #     flavor_wheel_df = pd.read_csv(flavor_df_list)
    #     fig = flavorWheel(flavor_wheel_df)
    #     st.plotly_chart(fig)

