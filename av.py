import pandas as pd
import streamlit as st
st.set_page_config(layout="wide")
from Esteban import Esteban_


path_1 = 'Algorithm/Labour_Model_Hours_w32_w35.csv'
path_2 = 'Algorithm/Labour_Model_Hours_w36_w39.csv'
path_3 = 'Algorithm/Labour_Model_Hours_w40_w43.csv'

# Read the data
df_1 = pd.read_csv(path_1)
df_2 = pd.read_csv(path_2)
df_3 = pd.read_csv(path_3)

# merge the data
df = pd.concat([df_1, df_2, df_3], axis=0)

# how many nan
num_nan = df.isna().sum()
df = df.dropna()
# add month and day columns
df['Month'] = pd.to_datetime(df['Date (DDMMYYYY)']).dt.month
# add day name column
df['Day'] = pd.to_datetime(df['Date (DDMMYYYY)']).dt.day_name()

with st.expander('Show all data'):
    st.write(df)

# get unique restaurants
restaurants = df['Site Code'].unique()
# get unique months
months = df['Month'].unique()
# get unique days
days = df['Day'].unique()
# get unique departments
departments = df['Department'].unique()

# solve it for d1
#site_code = 'D1'
#department = 'Expo'
#month = 9
#day = 'Monday'

data = df
# filter the data
hours_counter_generated = {} # for each hour it will count how many people start at that hour
hours_counter_budget = {} # for each hour it will count how many people start at that hour
for i in range(len(restaurants)):
    with st.expander(f'{restaurants[i]}'):
        site_code = restaurants[i]
        data_restaurant = data[data['Site Code'] == site_code]
        for department in departments:
            data_department = data_restaurant[data_restaurant['Department'] == department]
            for month in months:
                data_month = data_department[data_department['Month'] == month]
                # add day name column
                for day in days:
                    st.write(f'{site_code} - {department} - {month} - {day}')
                    data_day = data_month[data_month['Day'] == day]
                    # take the averages hour by hour rounding the values
                    data_to_save = data_day.groupby('Hour').mean().round(0)
                    st.write(data_to_save)
                    st.write('---')
                    #data_to_save.to_csv(f'data_averages/{site_code}_{department}_{month}_{day}.csv')


                    '''ADDING Calculate hours counter'''
                    # 1. create an appropriate rota
                    # 1.1 Get constraint, open_time, min_hours, max_hours to run the algorithm
                    contraints = data_to_save['Labour Model Hours'].values
                    print(contraints)
                    open_time = 8
                    min_hours = 4
                    max_hours = 9
                    esteban = Esteban_(contraints)
                    rota, shifts = esteban.solving_(open_time, min_hours, max_hours)
                    st.write(f'Generated Rota: {rota}')
                    st.write(f'Generated Shifts: {shifts}')
                    # get all the starting hours
                    starting_hours = [shift[0] for shift in shifts]
                    # count how many people start at each hour
                    for hour in starting_hours:
                        if hour in hours_counter_generated:
                            hours_counter_generated[hour] += 1
                        else:
                            hours_counter_generated[hour] = 1
                    st.write(f'Generated Rota Hours Counter: {hours_counter_generated}')
                    st.write('---')

                    # check the budget rota
                    budget_rota = data_to_save['Budget Rota Hours'].values
                    # as list of int
                    budget_rota = [int(x) for x in budget_rota]
                    st.write(f'Budget Rota: {budget_rota}')
                    # get all the starting hours
                    starting_hours = [shift[0] for shift in budget_rota]
                    # count how many people start at each hour
                    for hour in starting_hours:
                        if hour in hours_counter_budget:
                            hours_counter_budget[hour] += 1
                        else:
                            hours_counter_budget[hour] = 1
                    st.write(f'Budget Rota Hours Counter: {hours_counter_budget}')
                    st.write('---')

                    



                    # 1.2 Run the algorithm

                    # 2. Count how many people start at each hour in the Generated Rota
                    # 3. Count how many people start at each hour in the Averaged Budget Rota
                    # 4. Compare the two

