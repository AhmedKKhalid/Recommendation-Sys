import pandas as pd
import numpy as np
from pathlib import Path
import os
from haversine import haversine, Unit
from streamlit_folium import folium_static
import folium
import streamlit as st
pd.options.mode.chained_assignment = None  # default='warn'

def recommender_system():
    jp = st.text_input("Enter Jp code Pls...")
    search = st.checkbox('Submit', key='submit')
   # try:
    if search:
        response_msg=None
        current_dir=Path(__file__).parent if"__file__" in locals() else Path.cwd()
        df_path=current_dir / "All Data.xlsx"
        dfX = pd.read_excel(open(df_path,"rb"))
        df = dfX.copy()

        df['R Lat'] = df['R Lat'].str[:-1].astype(float)
        df['Real Long'] = df['Real Long'].str[:-1].astype(float)
        rawOfData = df[df['JP Code'] == jp].copy().reset_index()
        if rawOfData.shape[0] == 0:
            response_msg = '<p style="font-family:Courier; color:Red; font-size: 20px;">Sorry this JpCode is not identified in our database</p>'
            st.markdown(response_msg, unsafe_allow_html=True)
        else:
            response_msg = None
        prod_JpCodes = []
        hotel_names = []
        hotel_address = []
        latidudes = []
        longtudes = []
        countries = []
        distances = []
        categories = []
        # first filtering
        new_df = df[df['Country'] == rawOfData['Country'][0]].copy()
        new_df = new_df[new_df['Category'] >= rawOfData['Category'][0]].reset_index()
        for j in range(new_df.shape[0]):
            lat = new_df['R Lat'][j]
            long = new_df['Real Long'][j]

            # calculate the distance
            distance = haversine((rawOfData['R Lat'][0], rawOfData['Real Long'][0]), (lat, long))

            # second filtering
            if distance < 10 and distance != 0:
                prod_JpCodes.append(new_df['JP Code'][j])
                hotel_names.append(new_df['Hotel Name'][j])
                hotel_address.append(new_df['Hotel Address'][j])
                latidudes.append(new_df['R Lat'][j])
                longtudes.append(new_df['Real Long'][j])
                countries.append(new_df['Country'][j])
                categories.append(new_df['Category'][j])
                distances.append(distance)
        # grouping the data into dataframe
        suggested_dataFrame = pd.DataFrame({"JpCode": prod_JpCodes, "Hotel_Name": hotel_names,
                                            "Latitude": latidudes, "Longtude": longtudes,
                                            "Hotel_Address": hotel_address, "Country": countries,
                                            "Category": categories,
                                            "Distance": distances})

        print("{} Rows Added successfully !".format(suggested_dataFrame.shape[0]))
        suggested_dataFrame.sample(5)
        # convert distance to float to avoid the errors
        suggested_dataFrame['Distance'] = suggested_dataFrame['Distance'].astype('float64')
        # map the classes to the dataframe
        suggested_dataFrame['Class'] = suggested_dataFrame['Distance'].apply(lambda x: data_class(x))

        # third filtering
        very_close = suggested_dataFrame[suggested_dataFrame['Class'] == "Very Close"]
        fair_distance = suggested_dataFrame[suggested_dataFrame['Class'] == "Fair Distance"]
        far_distance = suggested_dataFrame[suggested_dataFrame['Class'] == "Far Distance"]

        st.markdown(f'<p style="font-family:Arial; color:black; font-size: 20px;<b>"> Very close data No.Hotels : {very_close.shape[0]} --- \nFair Distance data No.Hotels : { fair_distance.shape[0]} --- \nFar Distance : {far_distance.shape[0]} <b></p>'
                    ,unsafe_allow_html=True)


        final_reviews = very_close.copy()

        if very_close.shape[0] < 10:
            final_reviews = very_close.append(fair_distance)

        if (very_close.shape[0] + fair_distance.shape[0]) < 15:
            final_reviews = final_reviews.append(far_distance)

        if very_close.shape[0] > 20:
            final_reviews = final_reviews.sort_values(by='Distance', ascending=True)[:20]

        final_reviews = final_reviews.reset_index().drop('index', axis=1)
        st.markdown(f'<p style="font-family:Arial; color:black; font-size: 20px;<b>"> Final Data No of rows : {final_reviews.shape[0]} <b></p>')

        final_reviews['Rates'] = "Not Available"
        final_reviews['Board Type'] = "Not Available"
        final_reviews['Lowest Rate'] = "Not Available"
        print("t")
        for i in range(final_reviews.shape[0]):
            board_types = ["Room Only", "all inclusive", "bed and breakfast"]  # ======>  get it from the api
            rates = []

            for j in range(len(board_types)):
                rates.append(np.random.randint(55, 300))  # ======>  get the lowest rate for each board type

            final_reviews['Board Type'][i] = board_types
            final_reviews['Rates'][i] = rates
            final_reviews['Lowest Rate'][i] = np.min(rates)

        final_reviews = final_reviews.sort_values(by='Lowest Rate', ascending=True).reset_index()
        st.dataframe(final_reviews)
        incidents = folium.map.FeatureGroup()
        print("g")
        # My Hotel data
        nLatidude = rawOfData['R Lat'][0]
        nLongtude = rawOfData['Real Long'][0]
        sanfran_map = folium.Map(location=[nLatidude, nLongtude], zoom_start=12)

        for lat, lng, label in zip(final_reviews['Latitude'], final_reviews['Longtude'], final_reviews['Hotel_Name']):
            incidents.add_child(
                folium.features.CircleMarker(
                    [lat, lng],
                    radius=5,  # define how big you want the circle markers to be
                    color='yellow',
                    fill=True,
                    fill_color='blue',
                    fill_opacity=0.6,
                    popup=label
                )
            )
            incidents.add_child(
                folium.features.CircleMarker(
                    [nLatidude, nLongtude],
                    radius=7,  # define how big you want the circle markers to be
                    fill=True,
                    fill_color='blue',
                    fill_opacity=0.6
                )
            )

        # add incidents to map
        sanfran_map=sanfran_map.add_child(incidents)
        folium_static(sanfran_map,width=800,height=600)

    # except Exception as e:
    #     print(e)


def data_class(x):
    if x <= 2:
        return "Very Close"
    elif 2 < x < 4:
        return "Fair Distance"
    else:
        return "Far Distance"

