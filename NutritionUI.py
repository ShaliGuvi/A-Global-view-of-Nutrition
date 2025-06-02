import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import pycountry
import numpy as np
import plotly.express as px
import streamlit as st
import pymysql
import altair as alt

st.title('A Global View on Obesity and Malnutrition')

# Initialize session state for navigation
if "page" not in st.session_state:
    st.session_state.page = "Obesity Status"  # default page

# Sidebar with buttons inside a container
with st.sidebar.container(border=True):
    st.header("**Nutrition Paradox**")
    if st.button("Obesity Status"):
        st.session_state.page = "Obesity Status"
    if st.button("Malnutrition Status"):
        st.session_state.page = "Malnutrition Status"
    if st.button("A Global View on Both"):
        st.session_state.page = "A Global View on Both"

#database connection

connection = pymysql.connect(
    host = "localhost",
    user = "root",
    password = "Wonder*555",  #your actual password of your sql profile
    database = "market" #it should match with the database created in mysql
    
)


cursor = connection.cursor()

# Render based on selected page
if st.session_state.page == "Obesity Status":

    Query = st.selectbox("Select your Query", ["1.Top 5 regions with the highest average obesity levels in the most recent year(2022)",
                                        "2.Top 5 countries with highest obesity estimates",
                                        "3.Obesity trend in India over the years(Mean_estimate)",
                                        "4.Average obesity by gender",
                                        "5.Country count by obesity level category and age group",
                                        "6.Top 5 countries least reliable countries(with highest CI_Width) and Top 5 most consistent countries (smallest average CI_Width)",
                                        "7.Average obesity by age group",
                                        "8.Top 10 Countries with consistent low obesity (low average + low CI)over the years",
                                        "9.Countries where female obesity exceeds male by large margin (same year)",
                                        "10.Global average obesity percentage per year"])
    
    if Query == "1.Top 5 regions with the highest average obesity levels in the most recent year(2022)":

        cursor.execute("""select Year, Region, AVG(Mean_Estimate) AS Avg_obesity
                            from nutrition.obesity
                            Where Year = 2022
                            group by Region
                            order by Avg_obesity DESC
                            Limit 5;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0]for i in cursor.description])
        st.dataframe(df)
        st.bar_chart(data=df.set_index('Region')['Avg_obesity'])
    
    elif Query == "2.Top 5 countries with highest obesity estimates":
        
        cursor.execute("""select Country, AVG(Mean_Estimate) AS Avg_obesity
                            from nutrition.obesity
                            group by Country
                            order by Avg_obesity DESC
                            Limit 5;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0]for i in cursor.description])
        st.dataframe(df)
        st.bar_chart(data=df.set_index('Country')['Avg_obesity'])

    elif Query == "3.Obesity trend in India over the years(Mean_estimate)":

        cursor.execute("""select Year, AVG(Mean_Estimate) AS Avg_obesity_india
                            from nutrition.obesity
                            Where Country = "India"
                            group by Year
                            order by Avg_obesity_india;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        fig = px.line(df, x='Year', y='Avg_obesity_india',
              title='Obesity Trend in India Over the Years',
              markers=True)
        st.plotly_chart(fig, use_container_width=True)
    
    elif Query == "4.Average obesity by gender":

        cursor.execute("""select Gender, AVG(Mean_Estimate) AS AVG_obesity
                            from nutrition.obesity
                            group by Gender
                            order by AVG_obesity;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        fig = px.bar(df, x='Gender', y='AVG_obesity',
             title='Average Obesity by Gender',
             color='Gender')
        st.plotly_chart(fig, use_container_width=True)
    
    elif Query == "5.Country count by obesity level category and age group":

        cursor.execute("""select obesity_level, age_group, count(DISTINCT Country) AS Total_country
                            from nutrition.obesity
                            group by obesity_level, age_group
                            order by age_group;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        fig = px.density_heatmap(df, x='age_group', y='obesity_level',
                                z='Total_country', color_continuous_scale='Viridis',
                                title='Country Count Heatmap by Obesity Level and Age Group')
        st.plotly_chart(fig, use_container_width=True)
    
    elif Query == "6.Top 5 countries least reliable countries(with highest CI_Width) and Top 5 most consistent countries (smallest average CI_Width)":

        cursor.execute("""SELECT 'Least Reliable' AS Category, Country, Avg_CI_Width
                            FROM (
                            SELECT Country, AVG(CI_Width) AS Avg_CI_Width
                            FROM nutrition.obesity
                            GROUP BY Country
                            ORDER BY Avg_CI_Width DESC
                            LIMIT 5
                            ) AS top5

                            UNION ALL

                            SELECT 'Most Consistent' AS Category, Country, Avg_CI_Width
                            FROM (
                                SELECT Country, AVG(CI_Width) AS Avg_CI_Width
                                FROM nutrition.obesity
                                GROUP BY Country
                                ORDER BY Avg_CI_Width ASC
                                LIMIT 5
                            ) AS bottom5;
                            """)
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        fig = px.bar(df, y='Country', x='Avg_CI_Width', color='Category',
             orientation='h',
             title='Top 5 Least Reliable vs Most Consistent Countries (CI Width)')
        st.plotly_chart(fig, use_container_width=True)
    
    elif Query == "7.Average obesity by age group":

        cursor.execute("""select age_group, AVG(Mean_Estimate) AS AVG_obesity
                            from nutrition.obesity
                            group by age_group
                            order by AVG_obesity;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        df.set_index('age_group', inplace=True)
        st.bar_chart(df['AVG_obesity'])
        

    elif Query == "8.Top 10 Countries with consistent low obesity (low average + low CI)over the years":

        cursor.execute("""select Country, Year,
	                        Avg(Mean_Estimate) AS AVG_obesity, 
                            AVG(CI_Width) AS AVG_CI_Width,
                            RANK() over (order by Avg(Mean_Estimate)) + 
                            RANK() over (order by AVG(CI_Width)) AS combined_score     /* Low Mean and CI value gets high Rank */
                            from nutrition.obesity
                            group by Country, Year
                            order by combined_score ASC
                            Limit 10;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        fig = px.scatter(df, x='AVG_obesity', y='AVG_CI_Width', color='Country',
                 size='combined_score', hover_data=['Year'],
                 title='Obesity vs CI Width (Top 10 Consistent Countries)')
        st.plotly_chart(fig, use_container_width=True)

    elif Query == "9.Countries where female obesity exceeds male by large margin (same year)":

        cursor.execute("""SELECT
                            f.Country,
                            f.Year,
                            f.Mean_Estimate AS female_obesity,
                            m.Mean_Estimate AS male_obesity,
                            f.Mean_Estimate - m.Mean_Estimate AS difference
                        FROM
                            nutrition.obesity AS f,
                            nutrition.obesity AS m
                        WHERE
                            f.Country = m.Country
                            AND f.Year = m.Year
                            AND f.Gender = 'Female'
                            AND m.Gender = 'Male'
                            AND f.Mean_Estimate - m.Mean_Estimate >= 30
                        ORDER BY
                            difference DESC;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        # Combine Country and Year into one label for clarity
        df['Country_Year'] = df['Country'] + ' (' + df['Year'].astype(str) + ')'
        fig = px.bar(df, y='Country_Year', x='difference',
                    title='Countries Where Female Obesity Exceeds Male by ≥ 30',
                    color='difference',
                    orientation='h')
        st.plotly_chart(fig, use_container_width=True)

    elif Query == "10.Global average obesity percentage per year":

        cursor.execute("""select Year, AVG(Mean_Estimate) * 100 AS AVG_obesity
                            from nutrition.obesity
                            group by Year
                            order by AVG_obesity;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        df.set_index('Year', inplace=True)
        st.line_chart(df['AVG_obesity'])

    

elif st.session_state.page == "Malnutrition Status":

    Query = st.selectbox("Select your Query", ["11.Avg. malnutrition by age group",
                                        "12.Top 5 countries with highest malnutrition(mean_estimate)",
                                        "13.Malnutrition trend in African region over the years",
                                        "14.Gender-based average malnutrition",
                                        "15.Malnutrition level-wise (average CI_Width by age group)",
                                        "16.Yearly malnutrition change in specific countries(India, Nigeria, Brazil)",
                                        "17.Regions with lowest malnutrition averages",
                                        "18.Countries with increasing malnutrition",
                                        "19.Min/Max malnutrition levels year-wise comparison",
                                        "20.High CI_Width flags for monitoring(CI_width > 5)"])
    
    if Query == "11.Avg. malnutrition by age group":

        cursor.execute("""select age_group, AVG(Mean_Estimate) AS AVG_Malnutrition
                            from nutrition.malnutrition
                            group by age_group
                            order by age_group;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        df_chart = df.set_index('age_group')
        st.bar_chart(df_chart)
    
    elif Query == "12.Top 5 countries with highest malnutrition(mean_estimate)":

        cursor.execute("""select Country, AVG(Mean_Estimate) AS AVG_malnutrition
                            from nutrition.malnutrition
                            group by Country
                            order by AVG_malnutrition DESC
                            Limit 5;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        # Create a horizontal bar chart
        fig, ax = plt.subplots()
        ax.barh(df['Country'], df['AVG_malnutrition'], color='salmon')
        ax.set_xlabel('Average Malnutrition')
        ax.set_title('Top 5 Countries with Highest Malnutrition (Mean Estimate)')
        ax.invert_yaxis()  # Highest at the top

        # Display the plot in Streamlit
        st.pyplot(fig)

    elif Query == "13.Malnutrition trend in African region over the years":

        cursor.execute("""select Year, AVG(Mean_Estimate) AS AVG_Malnutrition
                            from nutrition.malnutrition
                            Where Region = 'Africa'
                            group by Year
                            order by Year;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        st.line_chart(df.set_index('Year'))

    elif Query == "14.Gender-based average malnutrition":

        cursor.execute("""select Gender, AVG(Mean_Estimate) AS AVG_malnutrition
                            from nutrition.malnutrition
                            group by Gender
                            order by AVG_malnutrition;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        # Built-in Streamlit bar chart
        df_chart = df.set_index('Gender')
        st.bar_chart(df_chart)

    elif Query == "15.Malnutrition level-wise (average CI_Width by age group)":

        cursor.execute("""select malnutrition_level, age_group, AVG(CI_Width) AS AVG_CI_Width
                            from nutrition.malnutrition
                            group by malnutrition_level, age_group
                            order by malnutrition_level;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        # Pivot the DataFrame for plotting
        df_pivot = df.pivot(index='age_group', columns='malnutrition_level', values='AVG_CI_Width')
        st.line_chart(df_pivot)

    elif Query == "16.Yearly malnutrition change in specific countries(India, Nigeria, Brazil)":

        cursor.execute("""select Year, Country, AVG(Mean_Estimate) AS AVG_malnutrition
                            from nutrition.malnutrition
                            Where Country IN ('Kenya','Nigeria','Sierra Leone')
                            group by Country, Year
                            order by Country, Year;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        # Pivot for built-in line chart
        df_pivot = df.pivot(index='Year', columns='Country', values='AVG_malnutrition')
        st.area_chart(df_pivot)

    elif Query == "17.Regions with lowest malnutrition averages":

        cursor.execute("""select Region, AVG(Mean_Estimate) AS AVG_malnutrition
                            from nutrition.malnutrition
                            group by Region
                            Having AVG(Mean_Estimate) < 10
                            order by AVG_malnutrition;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        df_chart = df.set_index('Region')
        st.bar_chart(df_chart)


    elif Query == "18.Countries with increasing malnutrition":

        cursor.execute("""SELECT 
                                Country,
                                MIN(Mean_Estimate) AS Earliest_Malnutrition,
                                MAX(Mean_Estimate) AS Latest_Malnutrition,
                                (MAX(Mean_Estimate) - MIN(Mean_Estimate)) AS Result
                            FROM 
                                nutrition.malnutrition
                            GROUP BY 
                                Country
                            HAVING 
                                (MAX(Mean_Estimate) - MIN(Mean_Estimate)) > 0
                            ORDER BY 
                                Result DESC;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        st.bar_chart(df.set_index('Country')['Result'])
    
    elif Query == "19.Min/Max malnutrition levels year-wise comparison":

        cursor.execute("""select Year, MIN(Mean_Estimate) AS Min_Malnutrition, MAX(Mean_Estimate) AS Max_Malnutrition
                            from nutrition.malnutrition
                            group by Year
                            order by Year;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        # Pivot data for plotting with Year as index and Min/Max as columns
        df_pivot = df.set_index('Year')
        st.line_chart(df_pivot)

    elif Query == "20.High CI_Width flags for monitoring(CI_width > 5)":

        cursor.execute("""select CI_Width, Country, Year, age_group	
                            from nutrition.malnutrition
                            Where CI_Width > 5
                            order by CI_Width DESC;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        # Aggregate average CI_Width per Country
        df_agg = df.groupby('Country')['CI_Width'].mean().sort_values(ascending=False).to_frame()
        # Bar chart for average CI_Width by Country
        st.bar_chart(df_agg)
    
elif st.session_state.page == "A Global View on Both":
    
    Query = st.selectbox("Select your Query", ["21.Obesity vs malnutrition comparison by country(any 5 countries)",
                                        "22.Gender-based disparity in both obesity and malnutrition",
                                        "23.Region-wise avg estimates side-by-side(Africa and America)",
                                        "24.Countries with obesity up & malnutrition down",
                                        "25.Age-wise trend analysis"])
    if Query == "21.Obesity vs malnutrition comparison by country(any 5 countries)":

        cursor.execute("""select 
                            a.Country,
                            a.Year,
                            a.obesity_level,
                            b.malnutrition_Level
                        from 
                            nutrition.obesity a
                        JOIN
                            nutrition.malnutrition b
                            ON a.Country = b.Country and a.Year = b.Year
                        Where 
                            a.Country IN ('Uganda', 'Central African Republic', 'South Africa', 'Nigeria', 'Algeria')
                        order by
                            a.Country, a.Year;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        # Melt the DataFrame to long format for Plotly Express
        df_long = df.melt(id_vars=['Country', 'Year'], 
                        value_vars=['obesity_level', 'malnutrition_Level'], 
                        var_name='Measure', value_name='Value')
        # Plot dual line chart with lines colored by Measure and faceted by Country
        fig = px.line(df_long, x='Year', y='Value', color='Measure',
                    facet_col='Country', facet_col_wrap=3,
                    markers=True,
                    title='Obesity vs Malnutrition Comparison by Country')
        fig.update_layout(height=600, width=900)
        st.plotly_chart(fig, use_container_width=True)
    
    elif Query == "22.Gender-based disparity in both obesity and malnutrition":

        cursor.execute("""Select a.Gender,
                                AVG(CASE WHEN a.obesity_level = 'Low' THEN 1 
                                        WHEN a.obesity_level = 'Moderate' THEN 2
                                        WHEN a.obesity_level = 'High' THEN 3
                                        ELSE NULL END) AS Avg_Obesity_Score,
                                AVG(CASE WHEN b.Malnutrition_level = 'Low' THEN 1
                                        WHEN b.Malnutrition_level = 'Moderate' THEN 2
                                        WHEN b.Malnutrition_level = 'High' THEN 3
                                        ELSE NULL END) AS Avg_Malnutrition_Score
                            from 
                                nutrition.obesity a
                            JOIN
                                nutrition.malnutrition b
                                ON a.Country = b.Country and a.Year = b.Year and a.Gender = b.Gender
                            Group by a.Gender
                            order by a.Gender;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        df_chart = df.set_index('Gender')
        fig, ax = plt.subplots()

        ax.bar(df_chart.index, df_chart['Avg_Obesity_Score'], label='Avg Obesity Score')
        ax.bar(df_chart.index, df_chart['Avg_Malnutrition_Score'], bottom=df_chart['Avg_Obesity_Score'], label='Avg Malnutrition Score')

        ax.set_ylabel('Average Score')
        ax.set_title('Gender-based Disparity in Obesity and Malnutrition')
        ax.legend()
        st.pyplot(fig)
    
    elif Query == "23.Region-wise avg estimates side-by-side(Africa and America)":

        cursor.execute("""select 
                                a.Region,
                                a.Mean_Estimate,
                                b.Mean_estimate
                            from 
                                nutrition.obesity a
                            JOIN
                                nutrition.malnutrition b
                                ON a.Country = b.Country and a.Region = b.Region
                            Where 
                                a.Region IN ('Africa','Americas')
                            order by
                                a.Region;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        

    elif Query == "24.Countries with obesity up & malnutrition down":

        cursor.execute("""WITH years AS (
                                    SELECT MIN(Year) AS earliest_year, MAX(Year) AS latest_year FROM nutrition.obesity
                                ),

                                obesity_summary AS (
                                    SELECT
                                        o.Country,
                                        AVG(CASE WHEN o.Year = y.earliest_year THEN o.Mean_Estimate END) AS avg_obesity_earliest,
                                        AVG(CASE WHEN o.Year = y.latest_year THEN o.Mean_Estimate END) AS avg_obesity_latest
                                    FROM
                                        nutrition.obesity o
                                        CROSS JOIN years y
                                    GROUP BY
                                        o.Country
                                ),

                                malnutrition_summary AS (
                                    SELECT
                                        m.Country,
                                        AVG(CASE WHEN m.Year = y.earliest_year THEN m.Mean_Estimate END) AS avg_malnutrition_earliest,
                                        AVG(CASE WHEN m.Year = y.latest_year THEN m.Mean_Estimate END) AS avg_malnutrition_latest
                                    FROM
                                        nutrition.malnutrition m
                                        CROSS JOIN years y
                                    GROUP BY
                                        m.Country
                                )

                                SELECT
                                    o.Country,
                                    o.avg_obesity_earliest,
                                    o.avg_obesity_latest,
                                    m.avg_malnutrition_earliest,
                                    m.avg_malnutrition_latest
                                FROM
                                    obesity_summary o
                                    JOIN malnutrition_summary m ON o.Country = m.Country
                                WHERE
                                    o.avg_obesity_latest > o.avg_obesity_earliest
                                    AND m.avg_malnutrition_latest < m.avg_malnutrition_earliest
                                ORDER BY
                                    (o.avg_obesity_latest - o.avg_obesity_earliest) DESC;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        # Reshape df for grouped bar chart
        df_long = pd.melt(df, id_vars=['Country'], 
                        value_vars=['avg_obesity_earliest', 'avg_obesity_latest', 'avg_malnutrition_earliest', 'avg_malnutrition_latest'],
                        var_name='Measure', value_name='Value')

        # Separate Measure into Type and Time for clarity
        df_long[['Type', 'Time']] = df_long['Measure'].str.rsplit('_', n=1, expand=True)

        # Pivot for grouped bars by Country and Time
        df_pivot = df_long.pivot_table(index=['Country', 'Time'], columns='Type', values='Value').reset_index()
        fig = px.bar(df_pivot, x='Country', y=['avg_obesity', 'avg_malnutrition'],
                    color_discrete_map={'avg_obesity': 'red', 'avg_malnutrition': 'blue'},
                    barmode='group',
                    title="Obesity and Malnutrition Averages (Earliest vs Latest)")
        st.plotly_chart(fig)

    elif Query == "25.Age-wise trend analysis":

        cursor.execute("""SELECT
                                a.Age_Group,
                                a.Year,
                                AVG(a.Mean_Estimate) AS Avg_Obesity,
                                AVG(b.Mean_Estimate) AS Avg_Malnutrition
                            FROM
                                nutrition.obesity a
                            JOIN
                                nutrition.malnutrition b
                                ON a.Country = b.Country
                                AND a.Year = b.Year
                                AND a.age_group = b.age_group
                            GROUP BY
                                a.Age_Group,
                                b.Year
                            ORDER BY
                                a.age_group,
                                a.Year;""")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
        st.dataframe(df)
        fig = px.treemap(df, 
                 path=['Age_Group', 'Year'], 
                 values='Avg_Obesity',
                 title='Age-wise and Year-wise Avg Obesity Decomposition')

        st.plotly_chart(fig)

    
    

    