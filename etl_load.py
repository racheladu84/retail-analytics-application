#used for operating system interaction/ file path construction
import os
import sys  #access system level functions and variables 
import django
import pandas as pd
import numpy as np

#django setup
#requires as etl runs a standalone scripts 

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "retail_analytics.settings")
django.setup()
 
#model imports
#models for database 
from analytics.models import (
    POSTransaction,
    TrendResult,
    DailySalesTrend,
    WeeklySalesTrend,
    MonthlySalesTrend,
    ProductLineTrendStatus,
    ProductMonthlyTrend,
    ForecastResult,
    WeekdaySalesTrend,
    ForecastSummary,
)
 
#file path to cleaned dataset
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cleaned data.csv")
 
 
#validate cleaned csv before proceeding
#enforces correct execution order for both scripts
def load_csv(path):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"\nCSV file not found at: {path}"
            f"\nMake sure dataset_cleaning.py has run and exported cleaned data.csv"
        )
    #parse date column as daterime 
    df = pd.read_csv(path, parse_dates=["date"])
    print(f"{len(df)} rows loaded successfully.")
    return df
 
# POS Transactions 
#loads raw transactional data into the POStransaction table

def load_pos_transactions(df):
    POSTransaction.objects.all().delete()
 #delete existing records before repopulating 


    records = []
    for _, row in df.iterrows():
        records.append(POSTransaction(
            invoice_id=row.get("invoice_id", ""),
            branch=row.get("branch", ""),
            city=row.get("city", ""),
            customer_type=row.get("customer_type", ""),
            gender=row.get("gender", ""),
            product_line=row.get("product_line", ""),
            unit_price=row.get("unit_price", 0),
            quantity=row.get("quantity", 0),
            tax_5percent=row.get("tax_5percent", 0),
            sales=row.get("sales", 0),
            date=row.get("date"),
            time=pd.to_datetime(row.get("time")).strftime("%H:%M:%S"),
            payment=row.get("payment", ""),
            cogs=row.get("cogs", 0),
            gross_margin_percentage=row.get("gross_margin_percentage", 0),
            gross_income=row.get("gross_income", 0),
            rating=row.get("rating", 0),
            stock_synthetic=row.get("stock_synthetic", 0),
        ))
        
        #inserts all records in a single database 
        
    POSTransaction.objects.bulk_create(records)
    print(f"{len(records)} POS transactions loaded.")
 
 
# daily sales 
#aggregate total sales per day and calculate percentage change
def load_daily_sales_trend(df):
    DailySalesTrend.objects.all().delete()
 
 #duplicated logic from the dataset_cleaning.py
    daily_sales = df.groupby("date")["sales"].sum().reset_index()
    daily_sales["daily_pattern"] = daily_sales["sales"].pct_change() * 100
 
    records = []
    for _, row in daily_sales.iterrows():
        
        #handles Nan for the first record where no preceding period exist
        if pd.notna(row["daily_pattern"]):
            pattern_value = round(row["daily_pattern"], 2)
        else:
            pattern_value = None
 
        records.append(DailySalesTrend(
            date=row["date"],
            sales=round(row["sales"], 2),
            daily_pattern=pattern_value,
        ))
    DailySalesTrend.objects.bulk_create(records)
    print(f"{len(records)} daily sales trend records loaded.")
 
 
#  Weekly Sales Trend 
#aggregates total sales per week and claculate week on week percenages 

def load_weekly_sales_trend(df):
    WeeklySalesTrend.objects.all().delete()

    #duplicated logic from dataset_cleaning.py
 
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    week_sales = df.groupby("week")["sales"].sum().reset_index()
    week_sales["weekly_pattern"] = week_sales["sales"].pct_change() * 100
 
    records = []
    for _, row in week_sales.iterrows():
        
        if pd.notna(row["weekly_pattern"]):
            pattern_value = round(row["weekly_pattern"], 2)
        else:
            pattern_value = None
 
        records.append(WeeklySalesTrend(
            week=int(row["week"]),
            sales=round(row["sales"], 2),
            weekly_pattern=pattern_value,
        ))
    WeeklySalesTrend.objects.bulk_create(records)
    print(f"{len(records)} weekly sales trend records loaded.")
 
 
#  Monthly Sales Trend
#aggregates total sales per month and calculate month on month change 
def load_monthly_sales_trend(df):
    MonthlySalesTrend.objects.all().delete()
 
 #duplicated logic from dataset_cleaning py
    df["month"] = df["date"].dt.month
    monthly_sales = df.groupby("month")["sales"].sum().reset_index()
    monthly_sales["monthly_pattern"] = monthly_sales["sales"].pct_change() * 100
 
    records = []
    for _, row in monthly_sales.iterrows():
        if pd.notna(row["monthly_pattern"]):
            pattern_value = round(row["monthly_pattern"], 2)
        else:
            pattern_value = None
 
        records.append(MonthlySalesTrend(
            month=int(row["month"]),
            sales=round(row["sales"], 2),
            monthly_pattern=pattern_value,
        ))
    MonthlySalesTrend.objects.bulk_create(records)
    print(f"{len(records)} monthly sales trend records loaded.")
 
 
# Product Line Trend Status#
#applies a 7 day rolling for each product line for trend classifucation 

def load_product_line_trend_status(df):
    ProductLineTrendStatus.objects.all().delete()
 
 #duplicated logic from dataset_cleaning.py
    productline_trend = df.groupby(["date", "product_line"])["sales"].sum().reset_index()
 
    records = []
    for product in productline_trend["product_line"].unique():
        productline_data = productline_trend[productline_trend["product_line"] == product].copy()
        productline_data = productline_data.sort_values("date")
        productline_data["rolling_avg"] = productline_data["sales"].rolling(window=7).mean()
 
        baseline = productline_data["rolling_avg"].dropna().iloc[0]
        current = productline_data["rolling_avg"].dropna().iloc[-1]
 
        if current > baseline:
            trend_status = "increasing"
        elif current < baseline:
            trend_status = "decreasing"
        else:
            trend_status = "normal"
 
        records.append(ProductLineTrendStatus(
            product_line=product,
            trend_status=trend_status,
        ))
    ProductLineTrendStatus.objects.bulk_create(records)
    print(f"{len(records)} product line trend status records loaded.")
 
 
# Product Monthly Trend
#aggregate monthly sales per product line and calculates monthly growth rate 

def load_product_monthly_trend(df):
    ProductMonthlyTrend.objects.all().delete()
 
 #duplicated logic from dataset_cleaning.py
    df["month"] = df["date"].dt.month
    productline_trend_monthly = (
        df.groupby(["month", "product_line"], as_index=False)["sales"].sum()
    )
    productline_trend_monthly["monthly_growth"] = (
        productline_trend_monthly.groupby("product_line")["sales"].pct_change() * 100
    ).round(2)
 
    records = []
    for _, row in productline_trend_monthly.iterrows():
        if pd.notna(row["monthly_growth"]):
            #handles Nans for the first month where no preceding period exist 
            growth_value = round(row["monthly_growth"], 2)
        else:
            growth_value = None
 
        records.append(ProductMonthlyTrend(
            product_line=row["product_line"],
            month=int(row["month"]),
            sales=round(row["sales"], 2),
            monthly_growth=growth_value,
        ))
    ProductMonthlyTrend.objects.bulk_create(records)
    print(f"{len(records)} product monthly trend records loaded.")


    # Weekday Sales Trend 
    # for busy day analysis 
def load_weekday_sales_trend(df):
    WeekdaySalesTrend.objects.all().delete()

    #duplicated logic from dataset_cleaning.py
 
    df["day_of_week"] = df["date"].dt.day_name()
    days_trend = df.groupby("day_of_week")["sales"].sum().reset_index()
 
    records = []
    for _, row in days_trend.iterrows():
        records.append(WeekdaySalesTrend(
            day_of_week=row["day_of_week"],
            sales=round(row["sales"], 2),
        ))
    WeekdaySalesTrend.objects.bulk_create(records)
    print(f"{len(records)} weekday sales trend records loaded.")
 
 

 
 
# Forecast Result
#calculates 7 day demand forecast per product line using rolling average

def load_forecast_results(df):
    ForecastResult.objects.all().delete()

    #duplicated logic from dataset_cleaning.py
 
    daily_productline_demand = df.groupby(["date", "product_line"])["quantity"].sum().reset_index()
    daily_productline_demand = daily_productline_demand.sort_values(["product_line", "date"])
 
    available_stock = df.groupby("product_line")["stock_synthetic"].mean().reset_index()
    available_stock = available_stock.rename(columns={"stock_synthetic": "current_stock"})
 
    forecast_output = []
    for product in daily_productline_demand["product_line"].unique():
        productline_data = daily_productline_demand[
            daily_productline_demand["product_line"] == product
        ].copy()
        productline_data = productline_data.sort_values("date")
 
        rolling_average = productline_data["quantity"].rolling(window=7).mean().iloc[-1]
        if pd.isna(rolling_average):
            rolling_average = productline_data["quantity"].mean()
 
        forecast_7_day = rolling_average * 7
        forecast_output.append({
            "product_line": product,
            "forecast_7_day": round(forecast_7_day, 1)
        })
 
    forecast_7_day_df = pd.DataFrame(forecast_output)
    inventory_outcome_df = pd.merge(forecast_7_day_df, available_stock, on="product_line")
 
    inventory_outcome_df["low_stock"] = (
        inventory_outcome_df["forecast_7_day"] > inventory_outcome_df["current_stock"]
    )
    inventory_outcome_df["over_stock"] = (
        inventory_outcome_df["current_stock"] > (inventory_outcome_df["forecast_7_day"] * 2)
    )
 
    conditions = [
        inventory_outcome_df["low_stock"],
        inventory_outcome_df["over_stock"]
    ]
    choices = ["lowstock", "overstock"]
    inventory_outcome_df["stock_status"] = np.select(conditions, choices, default="normal_stock")
 
    records = []
    for _, row in inventory_outcome_df.iterrows():
        records.append(ForecastResult(
            product_line=row["product_line"],
            forecast_quantity=row["forecast_7_day"],
            available_stock=row["current_stock"],
            stock_status=row["stock_status"],
        ))
    ForecastResult.objects.bulk_create(records)
    print(f"{len(records)} forecast results loaded.")
 
 
#  Forecast Summary 
#calculates aggregated KPI counts for forecasting dashboard
#for the kpis cards on the forecasting dashboard 

def load_forecast_summary(df):
    ForecastSummary.objects.all().delete()

    #duplicated logic from dataset_cleaning.py
 
    daily_productline_demand = df.groupby(["date", "product_line"])["quantity"].sum().reset_index()
    available_stock = df.groupby("product_line")["stock_synthetic"].mean().reset_index()
    available_stock = available_stock.rename(columns={"stock_synthetic": "current_stock"})
 
    forecast_output = []
    for product in daily_productline_demand["product_line"].unique():
        productline_data = daily_productline_demand[
            daily_productline_demand["product_line"] == product
        ].copy().sort_values("date")
 
        rolling_average = productline_data["quantity"].rolling(window=7).mean().iloc[-1]
        if pd.isna(rolling_average):
            rolling_average = productline_data["quantity"].mean()
 
        forecast_output.append({
            "product_line": product,
            "forecast_7_day": round(rolling_average * 7, 1)
        })
 
    forecast_7_day_df = pd.DataFrame(forecast_output)
    inventory_outcome_df = pd.merge(forecast_7_day_df, available_stock, on="product_line")
 
    inventory_outcome_df["low_stock"] = inventory_outcome_df["forecast_7_day"] > inventory_outcome_df["current_stock"]
    inventory_outcome_df["over_stock"] = inventory_outcome_df["current_stock"] > (inventory_outcome_df["forecast_7_day"] * 2)
 
    conditions = [inventory_outcome_df["low_stock"], inventory_outcome_df["over_stock"]]
    choices = ["lowstock", "overstock"]
    inventory_outcome_df["stock_status"] = np.select(conditions, choices, default="normal_stock")
 
 #counts the number of prodcut line in each inventory risk category 
    low_stock_count = int((inventory_outcome_df["stock_status"] == "lowstock").sum())
    overstock_count = int((inventory_outcome_df["stock_status"] == "overstock").sum())
    normal_stock_count = int((inventory_outcome_df["stock_status"] == "normal_stock").sum())
 
 #creates a single summary records
 #uses object create rather than bulk
 #as one summmary record is needed for the KPI cards
    ForecastSummary.objects.create(
        low_stock_count=low_stock_count,
        overstock_count=overstock_count,
        normal_stock_count=normal_stock_count,
    )
    print("Forecast summary loaded.")
 
 

#Trend Result
#calculates the overall kpis

def load_trend_result(df):
    TrendResult.objects.all().delete()

    #duplicated logic from dataset cleaning py
 
    daily_sales = df.groupby("date")["sales"].sum().reset_index()
    daily_sales["rolling_avg"] = daily_sales["sales"].rolling(window=7).mean()
 
    baseline_rolling = daily_sales["rolling_avg"].dropna().iloc[0]
    current_rolling = daily_sales["rolling_avg"].dropna().iloc[-1]
 
    if current_rolling > baseline_rolling:
        overall_trend = "increasing"
    elif current_rolling < baseline_rolling:
        overall_trend = "decreasing"
    else:
        overall_trend = "normal"
 
    productline_overview = df.groupby("product_line")["sales"].sum().reset_index()
    best_productline = productline_overview.sort_values("sales", ascending=False).iloc[0]["product_line"]
    best_productline_sale = productline_overview.sort_values("sales", ascending=False).iloc[0]["sales"]
    worst_productline = productline_overview.sort_values("sales", ascending=True).iloc[0]["product_line"]
    worst_productline_sale = productline_overview.sort_values("sales", ascending=True).iloc[0]["sales"]
 
    df["day_of_week"] = df["date"].dt.day_name()
    days_trend = df.groupby("day_of_week")["sales"].sum().reset_index()
    peak_day = days_trend.sort_values("sales", ascending=False).iloc[0]["day_of_week"]
    slowest_day = days_trend.sort_values("sales", ascending=True).iloc[0]["day_of_week"]
 
 #creates a single trend result

    TrendResult.objects.create(
        overall_trend=overall_trend,
        best_productline=best_productline,
        best_productline_sale=round(best_productline_sale, 2),
        worst_productline=worst_productline,
        worst_productline_sale=round(worst_productline_sale, 2),
        peak_day=peak_day,
        slowest_day=slowest_day,
    )
    print("Trend result loaded.")
 
 #  Main block
 #executes all load functions
 #Pos transaction first as a source data for all calculate
if __name__ == "__main__":
    

    df = load_csv(CSV_PATH)

    load_pos_transactions(df)
    load_daily_sales_trend(df)
    load_weekly_sales_trend(df)
    load_monthly_sales_trend(df)
    load_product_line_trend_status(df)
    load_product_monthly_trend(df)
    load_weekday_sales_trend(df)
    load_forecast_results(df)
    load_forecast_summary(df)
    load_trend_result(df)

    print("\nAll data loaded.\n")