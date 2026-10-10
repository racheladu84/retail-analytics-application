import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))



import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np 
print("pandas has been sucessful") # test to see if pandas has been succesfully installed 

import pandas as pd
#access the cvs in  folder 
# loads the raw supermarket sales CSV dataset into a pandas dataFrame
df = pd.read_csv(os.path.join(BASE_DIR, "Dataset", "Raw dataset", "Retaildata", "SuperMarket Analysis.csv"))

#df = pd.read_csv(r"C:\Users\rache\OneDrive\Desktop\Dissertation work\Dataset\Raw dataset\Retaildata\SuperMarket Analysis.csv")


# verification - displays first 10 rows, shape and data types of raw dataset
print(df.head(10))
print(df.shape)
print(df.dtypes)

#standarsing column names

df.columns =(
    df.columns
    .str.strip() #strip any white speaced before and after the word#
    .str.lower() #convert all string to lowercase
    .str.replace(" ", "_") #replace spaces with an _#
    .str.replace("%","percent")
)

# verification - confirms column names have been standardised correctly
print(df.columns)


#converting date and time to datetime
df["date"] = pd.to_datetime(df["date"]) 

#extract only the time
df["time"] = pd.to_datetime(df["time"].astype(str), errors='coerce').dt.strftime("%H:%M:%S")

#convert categorical columns
categorical_cols = ["branch","city","customer_type","gender","product_line","payment"]
for col in categorical_cols:
    df[col] = df[col].astype("category")


df.info()

# check for missing values across all columns
print (df.isnull().sum())

# verification - confirms no duplicate rows exist in the dataset
print("Duplicated rows:", df.duplicated().sum())

pd.set_option('display.max_columns', None)
print(df.describe().T)


#outlier detection for the core metrics 
#calculating outliers for sale to detect any unusual valuess

def outlier_detection(df,column):
    #calculate quartile 
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)

    #calculate the IQR
    IQR = Q3 - Q1

    #calculate the bounds
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    #finding the outlier
    outliers = df[df[column] > upper_bound]

    print(f"Outlier Analysis for {column}")

    # verification — prints outlier analysis results for the column
    print("Lower bound:", lower_bound)
    print("Upper bound:", upper_bound)
    print("Max value:", df[column].max()) # shows the largest value 
    print("Number of outliers:", len(outliers)) #how many outliers there are 

    return outliers 

outlier_detection(df,"sales")
outlier_detection(df,"quantity")

#sales boxplot
df.boxplot(column = "sales")
plt.title("Box Plot of sales")
plt.show()

#quantity boxplot 
df.boxplot(column = "quantity")
plt.title("Box plot of quantity")
plt.show()

print((df["quantity"] <=0).sum())  

print((df["sales"] <=0).sum())  

print(df["product_line"].unique())


#synthetic stock column creation

# original dataset contains no stock level information
# synthetic stock generated using a rule based approach grounded in retail logic
# average quantity sold per product line multiplied by 12

avg_num = df.groupby("product_line")["quantity"].mean().round()
df["stock_synthetic"] = (
    df.groupby("product_line")["quantity"]
    .transform("mean")
    .round()
    .mul(12) #12 day stock average
    .astype(int)
)

# verification - confirms stock synthetic column generated correctly per product line
print(df.groupby("product_line")[["quantity","stock_synthetic"]].mean())
print(df.head(5))

# verification - confirms stock_synthetic column exists in DataFrame
print("stock Column has been sucessfully added:", "stock_synthetic" in df.columns)

#check for missing values in the stock column
missing_values = df["stock_synthetic"].isnull().sum()
print("missing values in stock_synthetic:", missing_values)
print("rows:")
print(df[["product_line", "quantity", "stock_synthetic"]].head(10))



#feature enginnering
# five temporal features extracted from date and time columns
df["hour"] = pd.to_datetime(df["time"], format="%H:%M:%S").dt.hour
df["month"]= df["date"].dt.month
df["year"]= df["date"].dt.year
df["day_of_week"] = df  ["date"].dt.day_name()
df["week"]= df ["date"].dt.isocalendar().week


# verification — confirms all temporal features extracted correctly
print(df.columns)
print(df[['date', 'time', 'week', 'month', 'hour', 'day_of_week']].head())


########Data transformation for trend detection dashboard ############

#daily sales aggregation 
daily_sales = df.groupby('date', as_index=False)['sales'].sum()
#weekly sales aggregation 
week_sales = df.groupby('week', as_index=False)['sales'].sum()
#montly sale aggeragation
monthly_sales = df.groupby('month', as_index=False)['sales'].sum()

#product line sales over time - for best and worst producline line identification
productline_overview = (
    df.groupby('product_line', as_index=False)[['sales', 'quantity']]
    .sum()
)


# product line sales trend over time - used for rolling average trend classification
productline_trend = (
    df.groupby(['date', 'product_line'], as_index=False)[['sales', 'quantity']]
    .sum()
)


# weekday sales aggregation - used for busy day analysis
days_trend = (
    df.groupby('day_of_week', as_index=False)[['sales', 'quantity']]
    .sum()
)

#forces an order within the days 
day_ordering = ['Monday','Tuesday', 'Wednesday','Thursday','Friday','Saturday','Sunday']
days_trend = days_trend.set_index('day_of_week').reindex(day_ordering).reset_index()

# verification — confirms aggregated dataFrames produced correctly
print(daily_sales.head())
print(week_sales.head())
print(monthly_sales.head())
print(productline_trend.head())
print(days_trend.head())

##########################data transformation - forecasting###############


# aggregation - groups daily quantity sold per product line
# sorted chronologically - required for correct rolling average calculation

daily_productline_demand = df.groupby(['date','product_line'])['quantity'].sum().reset_index()
daily_productline_demand = daily_productline_demand.sort_values(['product_line','date'])


# verification — confirms daily product line demand DataFrame produced correctly
print(daily_productline_demand.head())
print(daily_productline_demand.columns)

# calculate average stock level per product line from synthetic stock column
available_stock = df.groupby('product_line')['stock_synthetic'].mean().reset_index()
#rename stock_synthetic to current_stock in the column for readablility 
available_stock = available_stock.rename(columns={'stock_synthetic': 'current_stock'})
print(available_stock.head())
print(available_stock.columns)



########################ROLLING AVERAGE TIME SERIES FOR FORECASTING for the next 7 days####################################
# 7 day rolling average applied per product line independently
# final rolling average value extracted as demand baseline
# multiplied by 7 to project expected demand for the next 7 days


# list used rather than building DataFrame row by row inside the loop
# appending to a list is significantly faster than repeatedly recreating a DataFrame
# dataFrame created once from the completed list after the loop finishes
forecast_output = []

#loop through each product list
for product in daily_productline_demand ['product_line'].unique():
    productline_data = daily_productline_demand[daily_productline_demand['product_line'] == product].copy()

    # sort chronologically - required for correct rolling average calculation
    productline_data = productline_data.sort_values('date')

    #create the 7 day rolling average and extract the last value of the rolling average as the baseline 
    rolling_average = productline_data['quantity'].rolling(window=7).mean().iloc[-1]




    #fallback if less than 7 days
    # prevents NaN values from propagating into forecast and inventory calculations

    if pd.isna(rolling_average):
        rolling_average = productline_data['quantity'].mean()  


    # multiply daily baseline by 7 to project total demand for the next 7 days
    forecast_7_day = rolling_average * 7   

    forecast_output.append({ 'product_line':product,'forecast_7_day': round(forecast_7_day,1)})

  # convert forecast output list back to DataFrame
forecast_7_day_df = pd.DataFrame(forecast_output)

print(forecast_7_day_df.head())


#merge forecast result with available stock
# classifies each product line as lowstock, overstock or normal_stock
inventory_outcome_df= pd.merge(forecast_7_day_df, available_stock , on= 'product_line' )

#low stock condition -  forecast demand exceeds available stock
inventory_outcome_df ['low_stock'] = inventory_outcome_df['forecast_7_day'] > inventory_outcome_df['current_stock']
#overstock condition - available stock exceeds twice the forecast demand
inventory_outcome_df ['over_stock'] = inventory_outcome_df['current_stock'] > (inventory_outcome_df['forecast_7_day'] *2)

# apply inventory risk labels using np.select conditional classification
conditions = [
    inventory_outcome_df['low_stock'],
    inventory_outcome_df['over_stock']
]
choices = ['lowstock','overstock']
inventory_outcome_df['stock_status'] = np.select(conditions,choices,default= 'normal_stock')

# verification - displays inventory risk classification results per product line
inventory_view = inventory_outcome_df[['product_line','forecast_7_day', 'current_stock', 'stock_status']]
print(inventory_view)



#overall trend detection logic#
# applies 7 day rolling average to total daily sales
# compares first valid rolling average (baseline) to last (current)
# classifies overall business trend as increasing, decreasing or normal

daily_sales['rolling_avg'] = daily_sales['sales'].rolling(window=7).mean()

# extract first valid rolling average - represents opening 7 day average
baseline_rolling = daily_sales['rolling_avg'].dropna().iloc[0]
# extract last rolling average - represents closing 7 day average
current_rolling = daily_sales['rolling_avg'].dropna().iloc[-1]

#classify overall trend by comparing baseline to current rolling average
if current_rolling > baseline_rolling:
    trend = 'increasing'
elif current_rolling < baseline_rolling:
    trend = 'decreasing'

else:

    trend = 'normal'

    # verification - confirms overall trend classification and rolling average values
print("overall trend:" , trend)
print("Baseline rolling average:", round (baseline_rolling,1))
print("Current rolling average,", round (current_rolling,1))


#percentage change calculations 
# feature derivation — pct_change calculates percentage change between consecutive periods
# produces daily_pattern, weekly_pattern and monthly_pattern columns
# used as visualisation metric in sales trend charts


#daily percentage change
daily_sales['daily_pattern'] = daily_sales['sales'].pct_change() * 100

print(daily_sales[['date', 'sales','daily_pattern']])

#weekly percentage change
week_sales ['weekly_pattern'] = week_sales['sales'].pct_change() * 100
print(week_sales[['week', 'sales','weekly_pattern']])

#monthly percentage change
monthly_sales ['monthly_pattern'] = monthly_sales['sales'].pct_change() * 100
print(monthly_sales[['month', 'sales','monthly_pattern']])



#worst and best product logic
# identifies best and worst performing product lines by total sales

best_productline = productline_overview.sort_values('sales',ascending=False).iloc[0]['product_line']
worst_productline = productline_overview.sort_values('sales',ascending=True).iloc[0]['product_line']

best_productline_sale = productline_overview.sort_values('sales', ascending=False).iloc[0]['sales']
worst_productline_sale  = productline_overview.sort_values('sales',ascending=True).iloc[0]['sales']

#rank all productline by total sales 
productline_overview ['sale_rank'] = productline_overview['sales'].rank(ascending=False).astype(int)

# verification - confirms best and worst product line identified correctly
print("Best product line:", best_productline)
print("best product line sales:", best_productline_sale)

print("worst product line:", worst_productline)
print("worst productline sale:", worst_productline_sale)


#busy day logic 
# identifies peak and slowest trading days by total sales per day of week
# duplicated logic - implemented in etl_load.py for database population

peak_day = days_trend.sort_values ('sales',ascending=False).iloc[0]['day_of_week']
slowest_day = days_trend.sort_values ('sales',ascending=True).iloc[0]['day_of_week']

# verification — confirms peak and slowest day identified correctly
print("Peak day:", peak_day)
print("slowest day:", slowest_day)



#Product line trend status logic 
# applies 7 day rolling average per product line independently
# compares opening 7 day average to closing 7 day average
# classifies each product line trend as increasing, decreasing or normal
# duplicated logic — implemented in etl_load.py for database population

productline_trend_status = []

#loop through each product list
for product in productline_trend['product_line'].unique():
    
    productline_data = productline_trend[productline_trend['product_line'] == product].copy()

    # sort chronologically - required for correct rolling average calculation
    productline_data = productline_data.sort_values('date')

# apply 7 day rolling average to smooth short term fluctuation
    productline_data['rolling_avg'] = productline_data['sales'].rolling(window=7).mean()


# extract first valid rolling average -represents opening 7 day average
    baseline = productline_data["rolling_avg"].dropna().iloc[0]
 # extract last rolling average — represents closing 7 day average
    current = productline_data['rolling_avg'].dropna().iloc[-1]


# classify trend by comparing opening to closing rolling average
    if current > baseline:
        trend_status = "increasing"
    elif current < baseline:
        trend_status = 'decreasing'

    else:
        trend_status = "normal"


    productline_trend_status.append({
        'product_line': product,
        'trend_status': trend_status
    })
    
    # convert product line trend status list to DataFrame
productline_trend_status_df = pd.DataFrame(productline_trend_status)

# verification - confirms product line trend status classified correctly
print(productline_trend_status_df)

    

# Product line monthly trend ;ogic #####
# extracts month from date column and aggregates monthly sales per product line
# calculates month on month growth rate using pct_change
# duplicated logic - implemented in etl_load.py for database population

productline_trend['month'] = productline_trend['date'].dt.month

# aggregate monthly sales per product line
productline_trend_monthly = (productline_trend.groupby(['month','product_line'],as_index=False)["sales"].sum() )

#calculate month on month growth per productline
productline_trend_monthly['monthly_growth'] = (
    productline_trend_monthly.groupby("product_line")['sales'].pct_change () * 100) .round(2)

# verification — confirms monthly product line trend calculated correctly
print(productline_trend_monthly[['month','product_line','sales','monthly_growth']].to_string(index=False))


# verification — confirms all expected columns present in each DataFrame
print(df.columns.tolist())
print(daily_sales.columns.tolist())
print(week_sales.columns.tolist())
print(monthly_sales.columns.tolist())
print(productline_trend_monthly.columns.tolist())
print(forecast_7_day_df.columns.tolist())
print(inventory_outcome_df.columns.tolist())
print(productline_trend_status_df.columns.tolist())

# export cleaned data to CSV for ETL loading
df.to_csv(os.path.join(BASE_DIR, "cleaned data.csv"), index=False)

#df.to_csv(r"C:\Users\rache\OneDrive\Desktop\Dissertation work\cleaned data.csv", index=False)
print("cleaned data exported successfully!")

