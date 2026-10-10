from django.db import models
from django.db import models


# ten models representing the ten database tables in the system
# divided into two categories:
#POSTransaction: stores raw transactional data from the cleaned CSV
#nine analytical tables  store pre-aggregated results computed by etl_load.py


# stores raw dataset from the POS dataset
class POSTransaction(models.Model):
    invoice_id = models.CharField(max_length=20)
    branch = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    customer_type = models.CharField(max_length=50)
    gender = models.CharField(max_length=20)
    product_line = models.CharField(max_length=100)
    unit_price = models.FloatField()
    quantity = models.IntegerField()
    tax_5percent = models.FloatField()
    sales = models.FloatField()
    date = models.DateField()
    time = models.TimeField()
    payment = models.CharField(max_length=50)
    cogs = models.FloatField()
    gross_margin_percentage = models.FloatField()
    gross_income = models.FloatField()
    rating = models.FloatField()
    stock_synthetic = models.FloatField()

    class Meta:
        ordering = ['date']  

    def __str__(self):
        return f"{self.invoice_id} - {self.product_line}"


# stores overall trend detection results
#for the five KPI cards on the trend detection dashboard
# ordered by most recently created to ensure latest results are retrieved first
class TrendResult(models.Model):
    overall_trend  = models.CharField(max_length=20)
    best_productline = models.CharField(max_length=100)
    best_productline_sale = models.FloatField()
    worst_productline = models.CharField(max_length=100)
    worst_productline_sale = models.FloatField()
    peak_day = models.CharField(max_length=20)        
    slowest_day = models.CharField(max_length=20) 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] #ordered chronologically

    def __str__(self):
        return f"Trend - {self.created_at}"


# stores daily sales and day on day growth
#null= true, blank = true on daily pattern daily_pattern accomodates the first record 
class DailySalesTrend(models.Model):
    date  = models.DateField()
    sales = models.FloatField()
    daily_pattern = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['date'] #ordered chronologically

    def __str__(self):
        return f"Daily - {self.date}"


# stores weekly sales and week on week growth
# null=True, blank=True on weekly_pattern accommodates the first record
# where no preceding week exists for percentage change calculation
class WeeklySalesTrend(models.Model):
    week = models.IntegerField()
    sales = models.FloatField()
    weekly_pattern = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['week'] #ordered by  week number

    def __str__(self):
        return f"Week - {self.week}"


# stores monthly sales and month 
# null=True, blank=True on monthly_pattern accommodates the first record
# where no preceding month exists for percentage change calculation
class MonthlySalesTrend(models.Model):
    month = models.IntegerField()
    sales = models.FloatField()
    monthly_pattern = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['month']  #odered by month number

    def __str__(self):
        return f"Month - {self.month}"


# stores overall trend status per product line
class ProductLineTrendStatus(models.Model):
    product_line = models.CharField(max_length=100)
    trend_status = models.CharField(max_length=20) #increeasing, decreasing and normal
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['product_line']  #ordered alpahbetically 

    def __str__(self):
        return f"{self.product_line} - {self.trend_status}"


# stores monthly growth per product line
# null=True, blank=True on monthly_growth accommodates the first month record
# where no preceding month exists for percentage change calculation

class ProductMonthlyTrend(models.Model):
    product_line   = models.CharField(max_length=100)
    month = models.IntegerField()
    sales = models.FloatField()
    monthly_growth = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['month', 'product_line'] #ordered by by month then product line 

    def __str__(self):
        return f"{self.product_line} - Month {self.month}"
    
   
     #stores total sales per day of week across the full dataset period
class WeekdaySalesTrend(models.Model):
    day_of_week = models.CharField(max_length=20)
    sales = models.FloatField()


    class Meta:
        ordering = ['day_of_week']  # ordered alphabetically by day name


    def __str__(self):
        return f"{self.day_of_week} - {self.sales}"


# stores 7 day demand forecast, available stock and inventory risk classification
# per product line — calculated using 7 day rolling average of historical demand
# for the forecasting dashboard charts and restock table
class ForecastResult(models.Model):
    product_line = models.CharField(max_length=100)  #product line name 
    forecast_quantity = models.FloatField() #7 day demand forecast quantity 
    available_stock  = models.FloatField() ## synthetically generated stock level
    stock_status = models.CharField(max_length=20) # lowstock, overstock or normal_stock
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['product_line']  # ordered alphabetically

    def __str__(self):
        return f"{self.product_line} - {self.stock_status}"
    
# stores forecast KPI summary for forecast dashboard
# single record updated on each ETL run
# for three KPI cards on the Forecasting dashboard
# total forecast units KPI is calculated at request time in the view 

class ForecastSummary(models.Model):
    low_stock_count = models.IntegerField()
    overstock_count = models.IntegerField()
    normal_stock_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    # orders records by most recently created first
    # ensures ForecastSummary.objects.first() always retrieves
    # the most recently loaded ETL results without explicit ordering in the view

    class Meta:
        ordering = ['-created_at']


    # controls how each record is displayed in the django admin panel
    # displays the creation timestamp for easy identification of each ETL run

    def __str__(self):
        return f"Forecast Summary - {self.created_at}"