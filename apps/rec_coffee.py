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

#select Stock
worksheet = sh.worksheet("Stock")

# data from gsheet <end>

# flavor_df_list = 'FlavorWheelNotes.csv'
base_df = 'base_df_input.csv'
filename_RF = 'rf_model_solve_error.sav'
        
def app():

    def user_input_features():       
        profile = st.radio(
            "Which taste profile do you prefer? \n \n",
            ('Sweet', 'Acidic')
            )

        flavor = st.radio(
            "Which coffee flavor do you prefer? \n \n",
            ('Chocolaty / Caramel', 'Bright / Citrusy', 'Fruity')
            )

        data = {
                'Profile': profile,
                'Flavor': flavor,
                }
        features = pd.DataFrame(data, index=[0])        
        return features

    # MAIN APP #

    st.subheader("""
    We help you choose our tasty cup of coffee!
    """)

    st.text('\n')

    base_ml_input = pd.read_csv(base_df)

    features_user = user_input_features()
    
    # ML Features 
    features_base = base_ml_input[['Profile_Acidic','Profile_Sweet','Flavor_Bright / Citrusy','Flavor_Chocolaty / Caramel','Flavor_Fruity']]  
    features = pd.get_dummies(features_user)
    features_base = pd.concat([features_base, features], ignore_index=True).fillna(0)


    # predictor / input variable
    features_data = features_base.tail(1)
        
    # Predict
    if st.button("Press here to see specialty coffee that suits you"):
        loaded_model_randomForest = pickle.load(open(filename_RF, "rb")) # Load Model error in cloud - tried library and python ver
        result = loaded_model_randomForest.predict(features_data)
        st.write('Great Choices! The coffee especially for you: ', result[0])
        df_gsheet = CoffeeGsheetList(worksheet, result[0])
        
        
        # error outputing url clickable, code from here 
        # header = [{'url':'temp'}]
        # link_list = pd.DataFrame(header)
        # link_list.drop(link_list.index, inplace=True)

        # for i in df_gsheet.index:

        #     link = df_gsheet['Card'][i]
        #     df_temp = pd.DataFrame(
        #         {
        #             "url": [
        #                 f'<a target="_blank" href="{link}">Coffee Details</a>'
        #             ]
        #         }
        #     )
        #     link_list = pd.concat([link_list, df_temp], ignore_index=True)

        # df_gsheet = pd.concat([df_gsheet, link_list], axis=1)
        # df_gsheet['url'] = link_list.values

        # til here

        df_gsheet = df_gsheet[['Coffee', 'Notes', 'Price']].sort_values(by='Price')
        st.write(df_gsheet.to_html(escape=False, index=False), unsafe_allow_html=True)

    st.write("Check out this: [Specialty Coffee Experience](https://sway.office.com/Lr2aWABAz1aCc9tC)")

    # if st.button("Press here to reveal coffee tasting wheel"):
    #     flavor_wheel_df = pd.read_csv(flavor_df_list)
    #     fig = flavorWheel(flavor_wheel_df)
    #     st.plotly_chart(fig)

