import pandas as pd
import hydralit_components as hc
import streamlit as st
import plotly.graph_objects as go
st.set_page_config(layout='wide',initial_sidebar_state='collapsed')

max_hours = st.sidebar.number_input('Max hours', min_value=0, max_value=12, value=9)
min_hours = st.sidebar.number_input('Min hours', min_value=3, max_value=8, value=4)
# transform into int
max_hours = int(max_hours)
min_hours = int(min_hours)

def menu():
    # Images
    markd = '''
    <img src="https://www.dishoom.com/assets/img/roundel-seva.png" width = "120" heigth = "120" >
    '''
    st.markdown(markd, unsafe_allow_html=True)

    # Menu
    menu_data = [
       
                {'id':'Generate Rota','label':"Modeling"},
                {'id':'Adjust','label':"Adjust Shifts"},
                {'id':'Rota','label':"Rota"},
               
                ]

    # Specify the theme
    over_theme = {'menu_background': '#ebd2b9',
                    'txc_inactive': '#6e7074' ,
                    'txc_active':'#6e7074'}

    menu_id = hc.nav_bar(
        menu_definition=menu_data,
        override_theme=over_theme,
        hide_streamlit_markers=True, # Will show the st hamburger as well as the navbar now!
        sticky_nav=False,           # At the top or not
        sticky_mode='sticky',      # jumpy or not-jumpy, but sticky or pinned
    )
    return menu_id

def main():
    # 1. Get data
    path_1 = 'Labour_Model_Hours_w32_w35.csv'
    path_2 = 'Labour_Model_Hours_w36_w39.csv'
    path_3 = 'Labour_Model_Hours_w40_w43.csv'
    # read the data
    df_1 = pd.read_csv(path_1)
    df_2 = pd.read_csv(path_2)
    df_3 = pd.read_csv(path_3)
    # merge the data
    df = pd.concat([df_1, df_2, df_3], axis=0)

    # 2. Clean the data
    df = df.dropna()

    # 3. Add month and day columns
    df['Month'] = pd.to_datetime(df['Date (DDMMYYYY)']).dt.month
    # add day name column
    df['Day'] = pd.to_datetime(df['Date (DDMMYYYY)']).dt.day_name()

    with st.expander('Show all data'):
        st.write(df)

    #4. UI FOR FILTERING
    # get unique restaurants
    restaurants = df['Site Code'].unique()
    # get unique months
    months = df['Month'].unique()
    # get unique days
    days = df['Day'].unique()
    # get unique departments
    departments = df['Department'].unique()

    with st.sidebar.expander('Selections'):
        site_code = st.selectbox('Select a restaurant', restaurants)
        department = st.selectbox('Select a department', departments)
        month = st.selectbox('Select a month', months)
        day = st.selectbox('Select a day', days)

    # 5. Filter the data from User selections
    data = df[df['Site Code'] == site_code]
    data = data[data['Department'] == department]
    data = data[data['Month'] == month]
    data = data[data['Day'] == day]

    # Data is ready to be worked with.
    # take the averages hour by hour rounding the values
    data_to_save = data.groupby('Hour').mean().round(0)
    constraints = data_to_save['Labour Model Hours'].values
    budget = data_to_save['Budget Rota Hours']

    months_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    with st.expander(f'Average {day} in {site_code} - {department} - {months_names[month]}'):
        st.write(data_to_save)

    # 6. Save the data to the DB
    '''Insert DB connection here and save the data to the DB'''
    from database import insert_data, delete_data
    delete_data()
    # iterate over the data and save it
    for index, row in data_to_save.iterrows():
        # get the values
        hour = index
        labour_model_hours = row['Labour Model Hours']
        actual_hours = row["Actual Hours '22"]
        budget_rota_hours = row['Budget Rota Hours']
        insert_data(site_code, department, int(month), day, actual_hours, budget_rota_hours, labour_model_hours)
    
    # 7. Plot the data
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Bar(x=data_to_save.index, y=data_to_save['Labour Model Hours'], name='Labour Model Hours'))
    # add actuals and budget
    fig.add_trace(go.Bar(x=data_to_save.index, y=data_to_save["Actual Hours '22"], name='Actuals'))
    fig.add_trace(go.Scatter(x=data_to_save.index, y=data_to_save['Budget Rota Hours'],name='Budget'))           
    fig.update_layout(title=f'Averages - Labour Model Hours for {site_code} - {department} - {month} - {day}',
                        xaxis_title='Hour',    
                            yaxis_title='Labour Model Hours')
    st.plotly_chart(fig, use_container_width=True)

    # 8. Generate the rota
    from Esteban import Esteban_
    # get parameters
    open_time = data_to_save.index.min()
    constraints = data_to_save['Labour Model Hours'].values
    esteban = Esteban_(constraints)
    rota, shifts = esteban.solving_(open_time, min_hours, max_hours)
    
    # 9. Plot the rota
    import plotly.graph_objects as go
    fig = go.Figure()
    hours = [i+open_time for i in range(len(rota))]
    fig.add_trace(go.Bar(x=hours, y=rota, name='Generated Rota'))
    # add actuals and budget
    fig.add_trace(go.Bar(x=hours, y=data_to_save["Labour Model Hours"], name='Labour Model Hours'))
    fig.add_trace(go.Scatter(x=hours, y=data_to_save['Budget Rota Hours'],name='Budget'))

    fig.update_layout(title=f'Rota for {site_code} - {department} - {month} - {day}',
                            xaxis_title='Hour', 
                            yaxis_title='Labour Model Hours')

    st.plotly_chart(fig, use_container_width=True)
    st.write('---')

    # 10. Generate the shifts
    from database import insert_shift_data, delete_shift_data
    delete_shift_data()
    data_frame = pd.DataFrame(columns=['Employees','Start', 'End'])
    for i, shift in enumerate(shifts):
        employee = f'{department} - {i}'
        start = int(shift[0])
        end = int(shift[1])
        data_frame = data_frame.append({'Employees': employee, 'Start': start, 'End': end}, ignore_index=True)
        # append on database
        insert_shift_data(site_code, department, int(month), day, start, end)


    # calculate hours over budget
    hours_over_budget = data_to_save['Labour Model Hours'].sum() - data_to_save['Budget Rota Hours'].sum()
    # calculate hours over labour model
    hours_over_labour_model = sum(rota) - data_to_save['Labour Model Hours'].sum()

    # create a tornado chart with difference between budget and rota hour by hour

    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Bar(x=data_to_save.index, y=data_to_save['Budget Rota Hours'] - data_to_save['Labour Model Hours'], name='Budget - Labour Model Hours', orientation='v', opacity=0.5))
    # values under zero are red, values over zero are green blue and bold if 0
    fig.update_traces(marker_color=['red' if _y < 0 else 'green' if _y != 0 else 'blue' for _y in data_to_save['Budget Rota Hours'] - data_to_save['Labour Model Hours']])
    fig.update_traces(marker_line_width=[5 if _y == 0 else 1 for _y in data_to_save['Budget Rota Hours'] - data_to_save['Labour Model Hours']])

    fig.update_layout(title=f'Budget VS Generated Rota- {site_code} - {department} - {month} - {day}',
                            xaxis_title='Hour', 
                            yaxis_title='Labour Model Hours')   

    c1,c2 = st.columns(2)
    c1.subheader('Shift Structure')
    c1.write(data_frame)
    c1.write(f'Hours over budget: {hours_over_budget}')
    c1.write(f'Hours over labour model: {hours_over_labour_model}')
    c2.plotly_chart(fig, use_container_width=True)
    return data_frame, open_time, max_hours, min_hours, department, constraints, budget

def shift_adjustments():
    # need constraints and shifts
    from database import get_data, get_shift_data
    constraints_table = get_data()
    day = constraints_table[0][3]
    site_code = constraints_table[0][0]
    month = constraints_table[0][2]
    constraints = []   
    budget = []     
    actuals = []
    hours = []
    for i, constraint in enumerate(constraints_table):
        constraints.append(int(constraint[-1]))
        budget.append(int(constraint[-2]))
        actuals.append(int(constraint[-3]))
        hours.append(int(constraint[2]))
        department = constraint[1]

    open_time = min(hours)

    
    shifts_table = get_shift_data()
    shifts = pd.DataFrame(columns=['Employees','Start', 'End'])
    for i, shift in enumerate(shifts_table):
        employee = i
        start = int(float(shift[-2]))
        end = int(float(shift[-1]))
        shifts = shifts.append({'Employees': employee, 'Start': start, 'End': end}, ignore_index=True)

    def validity_shift_checker(sl, min_hours=4, max_hours=8):
        # shift have to be at least four hours and at most max hours
        if sl[1] - sl[0] >= min_hours and sl[1] - sl[0] <= max_hours:
            return True
        else:
            if sl[1] - sl[0] < min_hours:
                st.warning('Shift too short')
            else:
                st.warning('Shift too long')
            return False
        
    # create a slider view of the shifts
    c1, c2 = st.columns(2)
    with c1:
        sliders = []
        # get hour max
        hour_max = shifts['End'].max()
        for index, row in shifts.iterrows():
            # create a slider for each row
            st.write(f'{index} : {row["Start"]} - {row["End"]}')
            sl = st.slider('',min_value=int(open_time), max_value=int(hour_max), value=(int(row['Start']), int(row['End'])), key=index)
            if validity_shift_checker(sl, min_hours=min_hours, max_hours=max_hours):
                sliders.append(sl)
    

    # create a new dataframe with the sliders
    new_shifts = pd.DataFrame(sliders, columns=['Start', 'End'])
    # add the index
    new_shifts['index'] = new_shifts.index
    # modify column
    new_shifts['index'] = new_shifts['index'].apply(lambda x: f'{department} :  {x}')
    # set as index
    new_shifts.set_index('index', inplace=True)
    # add a column to the shifts dataframe
    new_shifts['length'] = new_shifts['End'] - new_shifts['Start']
    # add a column for the cost of labour
    new_shifts['cost'] = new_shifts['length'] * 9.50
    # show the new shifts
    hours = []
    # iterate through the new shifts
    for index, row in new_shifts.iterrows():
        shift = [i for i in range(int(row['Start']), int(row['End']))]
        hours.extend(shift)
    # count occurences
    # import counter
    from collections import Counter
    occurences = Counter(hours)
    #st.write(occurences)
    # plot the occurences
    fig = go.Figure()
    fig.add_trace(go.Bar(x=list(occurences.keys()), y=list(occurences.values())))
    # add labour model
    fig.add_trace(go.Bar(x=[
        i+open_time for i in range(len(constraints))], y=constraints, name='Labour Model Hours'))
    # add budget
    fig.add_trace(go.Scatter
                    (x=[i+open_time for i in range(len(constraints))], y=budget, name='Budget Hours'))
    # show the graph

    c2.plotly_chart(fig)
    c2.write(new_shifts, use_container_width=True)

    if st.button('Save'):
        st.write('Saving')
        # delete rota data of the same day
        from database import delete_rota_data_same_day
        delete_rota_data_same_day(day)

        # save rota to database
        from database import insert_rota_data
        # iterate through the new shifts
        for index, row in new_shifts.iterrows():
            st.write(row['Start'], row['End'])
            #site_code text, departments text, month text, day text, start_time text, end_time text
            insert_rota_data(site_code, department, month, day, row['Start'], row['End'])

    return new_shifts

def rota_():
    # connect to database
    from database import get_rota_data
    # get rota data
    rota_data = get_rota_data()
    # create a dataframe
    # check unique days
    days = []
    for i in rota_data:
        days.append(i[3])
    days = list(set(days))
    # sort days
    days.sort()

    for day in days:
        # iterate through the rota data
        with st.expander(f'{day}'):
            for i in rota_data:
                if i[3] == day:
                    st.write(i)



    # if button delete
    if st.button('Delete'):
        st.write('Deleting')
        # delete rota data
        from database import delete_rota_data
        delete_rota_data()

if __name__ == '__main__':
    choosen = menu()
    if choosen == 'Generate Rota':
        main()
    elif choosen == 'Adjust':
        st.write('Adjusting Shifts')
        shift_adjustments()
    elif choosen == 'Rota':
        st.write('Rota')
        rota_()

