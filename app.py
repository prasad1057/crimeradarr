from flask import Flask, request, render_template 
import pickle 
import math
import sqlite3
import requests
from flask import jsonify

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64
 
model = pickle.load (open ('Model/model2.pkl', 'rb')) 
 
app = Flask (__name__) 

API_KEY = "f5393cf7025f44e18edc70a1ed0ed5a7"
NEWS_URL = (
    "https://newsapi.org/v2/everything?"
    "q=crime OR murder OR theft OR robbery OR kidnapping OR assault OR violence"
    "&language=en&pageSize=9&sortBy=publishedAt"
    f"&apiKey={API_KEY}"
)

# Create SQLite database and table
def init_db():
    conn = sqlite3.connect('crime_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        city TEXT,
                        crime TEXT,
                        year INTEGER,
                        population REAL,
                        crime_rate REAL,
                        cases INTEGER,
                        crime_status TEXT
                      )''')
    conn.commit()
    conn.close()

init_db()


df = pd.read_excel("Dataset/new_dataset.xlsx")
df['Year'] = pd.to_numeric(df['Year'])
unique_cities = df['City'].unique().tolist()



@app.route ('/') 
def home (): 
    return render_template ("home.html") 

@app.route ('/index') 
def index (): 
    return render_template ("index.html") 

@app.route("/news")
def news():
    response = requests.get(NEWS_URL)
    data = response.json()
    articles = data.get("articles", [])
    return render_template("news.html", articles=articles)
 
 
@app.route ('/predict', methods =['POST']) 
def predict_result (): 
    
    city_names = { '0': 'Ahmedabad', '1': 'Bengaluru', '2': 'Chennai', '3': 'Coimbatore', '4': 'Delhi', '5': 'Ghaziabad', '6': 'Hyderabad', '7': 'Indore', '8': 'Jaipur', '9': 'Kanpur', '10': 'Kochi', '11': 'Kolkata', '12': 'Kozhikode', '13': 'Lucknow', '14': 'Mumbai', '15': 'Nagpur', '16': 'Patna', '17': 'Pune', '18':'Surat'}
    
    crimes_names = { '0': 'Crime Committed by Juveniles', '1': 'Crime against SC', '2': 'Crime against ST', '3': 'Crime against Senior Citizen', '4': 'Crime against children', '5': 'Crime against women', '6': 'Cyber Crimes', '7': 'Economic Offences', '8': 'Kidnapping', '9':'Murder'}
    
    population = { '0': 63.50, '1': 85.00, '2': 87.00, '3': 21.50, '4': 163.10, '5': 23.60, '6': 77.50, '7': 21.70, '8': 30.70, '9': 29.20, '10': 21.20, '11': 141.10, '12': 20.30, '13': 29.00, '14': 184.10, '15': 25.00, '16': 20.50, '17': 50.50, '18':45.80}
    
    city_code = request.form["city"] 
    crime_code = request.form['crime'] 
    year = request.form['year'] 
    pop = population[city_code] 

    # Here increasing / decreasing the population as per the year.
    # Assuming that the population growth rate is 1% per year.
    year_diff = int(year) - 2011
    pop = pop + 0.01*year_diff*pop

    
    crime_rate = model.predict([[int(year), int(city_code), float(pop), int(crime_code)]])[0]
    
    city_name = city_names[city_code] 
    
    crime_type =  crimes_names[crime_code] 
    
    if crime_rate <= 1:
        crime_status = "Very Low Crime Area" 
    elif crime_rate <= 5:
        crime_status = "Low Crime Area"
    elif crime_rate <= 15:
        crime_status = "High Crime Area"
    else:
        crime_status = "Very High Crime Area" 
    
    cases = math.ceil(crime_rate * pop)
    
    # Store data in the database
    conn = sqlite3.connect('crime_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO predictions (city, crime, year, population, crime_rate, cases, crime_status) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                   (city_name, crime_type, year, pop, crime_rate, cases, crime_status))
    conn.commit()
    conn.close()
    
    return render_template('result.html', city_name=city_name, crime_type=crime_type, year=year, crime_status=crime_status, crime_rate=crime_rate, cases=cases, population=pop)

@app.route('/history')
def show_history():
    conn = sqlite3.connect('crime_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM predictions ORDER BY id DESC")
    data = cursor.fetchall()
    conn.close()
    return render_template('history.html', data=data)

import requests
from flask import jsonify

import requests
from flask import jsonify


@app.route('/crime-news')
def get_crime_news():
    try:
        API_KEY = "f5393cf7025f44e18edc70a1ed0ed5a7"
        url = (
            "https://newsapi.org/v2/everything?"
            "q=India AND (crime OR murder OR theft OR robbery OR kidnapping OR assault OR violence)"
            "&language=en&pageSize=5&sortBy=publishedAt"
            f"&apiKey={API_KEY}"
        )

        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Filter and format each article
        news_items = []
        for article in data.get("articles", []):
            news_items.append({
                "title": article.get("title"),
                "description": article.get("description"),
                "url": article.get("url"),
                "image": article.get("urlToImage"),
                "publishedAt": article.get("publishedAt"),
                "source": article.get("source", {}).get("name")
            })

        return jsonify(news_items)

    except Exception as e:
        return jsonify({"error": str(e)})



@app.route('/dashboard')
def dashboard():
    # Load dataset
    df = pd.read_excel("Dataset/new_dataset.xlsx")

    # Convert 'Year' column to numeric
    df['Year'] = pd.to_numeric(df['Year'])

    # 📈 **Crime Trend Over the Years**
    plt.figure(figsize=(10, 5))
    sns.lineplot(x='Year', y='Crime Rate', data=df, estimator='mean', ci=None)
    plt.title("Crime Rate Trend Over the Years")
    plt.xlabel("Year")
    plt.ylabel("Crime Rate")
    
    # Save plot as base64 string
    img1 = io.BytesIO()
    plt.savefig(img1, format='png')
    img1.seek(0)
    plot1_url = base64.b64encode(img1.getvalue()).decode()

    # 🏙️ **Crime Distribution by City (Pie Chart)**
    crime_counts = df.groupby('City')['Crime Rate'].sum()
    plt.figure(figsize=(8, 8))
    crime_counts.plot.pie(autopct='%1.1f%%', startangle=90, cmap='coolwarm')
    plt.title("Crime Distribution by City")

    img2 = io.BytesIO()
    plt.savefig(img2, format='png')
    img2.seek(0)
    plot2_url = base64.b64encode(img2.getvalue()).decode()

    return render_template("dashboard.html", plot1_url=plot1_url, plot2_url=plot2_url, unique_cities=unique_cities)



@app.route('/city-trend', methods=['POST'])
def city_trend():
    selected_city = request.form['city']
    df = pd.read_excel("Dataset/new_dataset.xlsx")
    df['Year'] = pd.to_numeric(df['Year'])

    city_data = df[df["City"] == selected_city]

    # --- Plot 1: Overall Crime Rate Trend ---
    overall_trend = city_data.groupby("Year")["Crime Rate"].sum().reset_index()
    plt.figure(figsize=(8, 4))
    sns.lineplot(data=overall_trend, x="Year", y="Crime Rate", marker="o", color="orange")
    plt.title(f"Overall Crime Rate Trend in {selected_city}")
    plt.xlabel("Year")
    plt.ylabel("Crime Rate")

    img1 = io.BytesIO()
    plt.savefig(img1, format='png', bbox_inches='tight')
    img1.seek(0)
    city_plot1 = base64.b64encode(img1.getvalue()).decode()
    plt.close()  # <- fully closes the figure

    # --- Plot 2: Crime Rate by Type ---
    plt.figure(figsize=(8, 4))
    sns.lineplot(data=city_data, x="Year", y="Crime Rate", hue="Type", marker="o")
    plt.title(f"Crime Trends by Type in {selected_city}")
    plt.xlabel("Year")
    plt.ylabel("Crime Rate")
    

# Move the legend to the right side, outside the plot
    plt.legend(
    title='Type',
    bbox_to_anchor=(1.05, 1),
    loc='upper left',
    borderaxespad=0.
    )

    plt.tight_layout()  # Adjust layout so legend doesn't get cut off

    img2 = io.BytesIO()
    plt.savefig(img2, format='png', bbox_inches='tight')
    img2.seek(0)
    city_plot2 = base64.b64encode(img2.getvalue()).decode()
    plt.close()



    # Load previous dashboard plots
    df_total = df.copy()
    plt.figure(figsize=(10, 5))
    sns.lineplot(x='Year', y='Crime Rate', data=df_total, estimator='mean', ci=None)
    plt.title("Crime Rate Trend Over the Years")
    plt.xlabel("Year")
    plt.ylabel("Crime Rate")
    img3 = io.BytesIO()
    plt.savefig(img3, format='png')
    img3.seek(0)
    plot1_url = base64.b64encode(img3.getvalue()).decode()
    plt.clf()

    crime_counts = df_total.groupby('City')['Crime Rate'].sum()
    plt.figure(figsize=(8, 8))
    crime_counts.plot.pie(autopct='%1.1f%%', startangle=90, cmap='coolwarm')
    plt.title("Crime Distribution by City")
    img4 = io.BytesIO()
    plt.savefig(img4, format='png')
    img4.seek(0)
    plot2_url = base64.b64encode(img4.getvalue()).decode()
    plt.clf()

    return render_template("dashboard.html",
                           plot1_url=plot1_url,
                           plot2_url=plot2_url,
                           selected_city=selected_city,
                           city_plot1=city_plot1,
                           city_plot2=city_plot2)



import folium
from folium.plugins import HeatMap

# Coordinates for the 19 cities
city_coords = {
    'Ahmedabad': [23.0225, 72.5714],
    'Bangalore': [12.9716, 77.5946],
    'Chennai': [13.0827, 80.2707],
    'Coimbatore': [11.0168, 76.9558],
    'Delhi': [28.6139, 77.2090],
    'Hyderabad': [17.3850, 78.4867],
    'Indore': [22.7196, 75.8577],
    'Jaipur': [26.9124, 75.7873],
    'Kanpur': [26.4499, 80.3319],
    'Kochi': [9.9312, 76.2673],
    'Kolkata': [22.5726, 88.3639],
    'Lucknow': [26.8467, 80.9462],
    'Mumbai': [19.0760, 72.8777],
    'Nagpur': [21.1458, 79.0882],
    'Patna': [25.5941, 85.1376],
    'Pune': [18.5204, 73.8567],
    'Surat': [21.1702, 72.8311],
    'Thane': [19.2183, 72.9781],
    'Visakhapatnam': [17.6868, 83.2185]
}


@app.route('/heatmap', methods=['GET', 'POST'])
def heatmap():
    df = pd.read_excel("Dataset/new_dataset.xlsx")
    df['Year'] = pd.to_numeric(df['Year'])

    selected_year = request.form.get('year', df['Year'].min())
    selected_type = request.form.get('crime_type', 'All')

    filtered_df = df[df['Year'] == int(selected_year)]
    if selected_type != 'All':
        filtered_df = filtered_df[filtered_df['Type'] == selected_type]

    # Aggregate by city
    city_crime = filtered_df.groupby('City')['Crime Rate'].sum().reset_index()

    # Create base map
    import folium
    from folium.plugins import HeatMap
    import os

    m = folium.Map(location=[22.9734, 78.6569], zoom_start=5, tiles="CartoDB dark_matter")

    # Generate heatmap data
    heat_data = []
    for _, row in city_crime.iterrows():
        city = row['City']
        if city in city_coords:
            lat, lon = city_coords[city]
            weight = row['Crime Rate']
            heat_data.append([lat, lon, weight])

    HeatMap(heat_data, radius=25, blur=15, max_zoom=10).add_to(m)

    # Save map as HTML
    map_path = os.path.join("static", "heatmap_map.html")
    if os.path.exists(map_path):
        os.remove(map_path)
    m.save(map_path)


    # Get unique years and crime types for dropdown
    years = sorted(df['Year'].unique())
    crime_types = ['All'] + sorted(df['Type'].unique())

    return render_template("heatmap.html", years=years, crime_types=crime_types,
                           selected_year=int(selected_year), selected_type=selected_type)



if __name__ == '__main__':
    # app.run (debug = False, host='0.0.0.0', port=5000) 
    app.run(debug = True,port=5000)
