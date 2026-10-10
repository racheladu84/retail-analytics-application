# Register your models here.
#registers all ten models to the django admin panel
# allows the superuser to view, add, edit and delete records for each table
# used during development to verify ETL pipeline populated tables correctly


from django.contrib import admin

## import all ten models from the analytics application

from django.contrib import admin
from .models import (
    POSTransaction,
    TrendResult,
    DailySalesTrend,
    WeeklySalesTrend,
    MonthlySalesTrend,
    ProductLineTrendStatus,
    ProductMonthlyTrend,
    ForecastResult,
    WeekdaySalesTrend,
    ForecastSummary
)

# register each model with the admin site
# each registered model appears as a separate section in the admin panel
admin.site.register(POSTransaction)
admin.site.register(TrendResult)
admin.site.register(DailySalesTrend)
admin.site.register(WeeklySalesTrend)
admin.site.register(MonthlySalesTrend)
admin.site.register(ProductLineTrendStatus)
admin.site.register(ProductMonthlyTrend)
admin.site.register(ForecastResult)
admin.site.register(WeekdaySalesTrend)
admin.site.register(ForecastSummary)