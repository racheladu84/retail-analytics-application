# views.py represents the View component of Django's MVT architecture
# acts as the bridge between the Model and Template layers
# receives incoming HTTP requests, applies business logic,
# queries the database via the ORM and passes prepared data to the templates

import plotly.express as px   #high level plotly chart 
import plotly.graph_objects as go #low level chart for group bar chart
from plotly.io import to_html  #converts plotly charts for grouped bar chart 
from plotly.subplots import make_subplots   # creates multi panel subplot 
import pandas as pd
from django.db.models import Sum  # Django ORM aggregation - used for product line ranking
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages  # Django messages framework - passes errors to templates

#import all nine analytical models required by the dashboard views
from analytics.models import (
    TrendResult,  #overall trend KPI results
    DailySalesTrend,
    WeeklySalesTrend,
    MonthlySalesTrend,
    ProductLineTrendStatus,
    ProductMonthlyTrend,
    WeekdaySalesTrend,
    ForecastResult,
    ForecastSummary,   # aggregated KPI counts for forecasting dashboard
)
 
 # development verification - confirms views.py has been loaded by Django
print("VIEWS.PY LOADED")
 
 
# Login View #####
def login_view(request):
    print("LOGIN VIEW CALLED")
    print(f"METHOD: {request.method}")
 
    if request.method == 'POST':
        username = request.POST.get('employee_id').strip()
        password = request.POST.get('password').strip()
        print(f"USERNAME: {username}")
        print(f"PASSWORD: {password}")
 
        # custom password validations
        errors = []
 
        if len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
 
        if not any(i.isupper() for i in password):
            errors.append('Password must contain at least one uppercase letter.')
 
        if not any(i.islower() for i in password):
            errors.append('Password must contain at least one lowercase letter.')
 
        if not any(i.isdigit() for i in password):
            errors.append('Password must contain at least one number.')
 
        if not any(i in '!@#$%&*-_' for i in password):
            errors.append('Password must contain at least one special character: ! @ # $ % & * - _')
 
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'analytics/login.html')


 #if custom validation passes/ authetication() checks the submitted credential
 #against the database 
        user = authenticate(request, username=username, password=password)
        print(f"USER: {user}")

        # if authetication passes a session is estbalished and directed to trend dashboard 
        #if none error appears on the login page
        if user is not None:
            login(request, user)
            return redirect('trend_dashboard')
        else:
            messages.error(request, 'Invalid Employee ID or password.')
 
    return render(request, 'analytics/login.html')
 
 
#  Password Reset View 
# placeholder view — no business logic
# renders a page directing users to contact the system administrator
def password_reset_view(request):
    return render(request, 'analytics/password_reset.html')
 
 
#  Logout View 
# terminates the user session using Django's built in logout() function
# redirects to login page after session is cleared
def logout_view(request):
    print("LOGOUT CALLED")
    logout(request)
    return redirect('login')
 
 
#  Trend Dashboard View 
# queries nine database models and constructs six Plotly charts in a single request
# protected by @login_required - unauthenticated users redirected to login page
# accessible to both store manager and store worker
@login_required(login_url='login')
def trend_dashboard(request):
 
    #  KPI cards 
    # retrieves the most recently created TrendResult record
    trend_result = TrendResult.objects.first()
 
    # sales over time data
    # retrieves pre-aggregated sales data for daily, weekly and monthly charts
    # ordered chronologically to ensure correct chart display order 
    daily_sales = list(DailySalesTrend.objects.all().order_by('date').values())
    weekly_sales = list(WeeklySalesTrend.objects.all().order_by('week').values())
    monthly_sales = list(MonthlySalesTrend.objects.all().order_by('month').values())
 
    # converts to pandas dataframe 
    # required as plotly needs a dataframe to build chart
    daily_df = pd.DataFrame(daily_sales)
    
    #contruct the daily sales line using plotly express
    # hover tooltips enabled by default - user can hover over data points
    fig_daily = px.line(
        daily_df, x='date', y='sales',
        title='Daily Sales Trend',
        labels={'date': 'Date', 'sales': 'Sales (£)'},
        color_discrete_sequence=['#008C8C']
    )
    # update the the visual appearance of chart to match system colour palette 
    fig_daily.update_layout(
        paper_bgcolor='#FFFFFF', # outer background 
        plot_bgcolor='#F5F5F5', # inner chart colour
        font_color='#555555', 
        title_font_color='#333333', # chart title text colour 
        xaxis=dict(gridcolor='#E0E0E0', #horizontal grid lines
                   linecolor='#E0E0E0'), #x axis border line colour 
        yaxis=dict(
            gridcolor='#E0E0E0', #vertical grid lines colour
            linecolor='#E0E0E0'), #y axis border lines colour
    )
    #converts plotly chart to a Html scripts 
    daily_chart = to_html(fig_daily, full_html=False)
 
    # weekly sales chart
    weekly_df = pd.DataFrame(weekly_sales)
    fig_weekly = px.line(
        weekly_df, x='week', y='sales',
        title='Weekly Sales Trend',
        labels={'week': 'Week', 'sales': 'Sales (£)'},
        color_discrete_sequence=['#008C8C']
    )
    #styling the chart
    fig_weekly.update_layout(
        paper_bgcolor='#FFFFFF', plot_bgcolor='#F5F5F5',
        font_color='#555555', title_font_color='#333333',
        xaxis=dict(gridcolor='#E0E0E0', linecolor='#E0E0E0'),
        yaxis=dict(gridcolor='#E0E0E0', linecolor='#E0E0E0'),
    )
    weekly_chart = to_html(fig_weekly, full_html=False)
 
    # monthly sales chart 
    monthly_df = pd.DataFrame(monthly_sales)
    fig_monthly = px.line(
        monthly_df, x='month', y='sales',
        title='Monthly Sales Trend',
        labels={'month': 'Month', 'sales': 'Sales (£)'},
        color_discrete_sequence=['#008C8C']
    )
    fig_monthly.update_layout(
        paper_bgcolor='#FFFFFF', plot_bgcolor='#F5F5F5',
        font_color='#555555', title_font_color='#333333',
        xaxis=dict(gridcolor='#E0E0E0', linecolor='#E0E0E0'),
        yaxis=dict(gridcolor='#E0E0E0', linecolor='#E0E0E0'),
    )
    monthly_chart = to_html(fig_monthly, full_html=False)
 
    #product line ranking chart
    product_ranking = list(
        ProductMonthlyTrend.objects.values('product_line').annotate(
            total_sales=Sum('sales')
        ).order_by('total_sales')
    )
    ranking_df = pd.DataFrame(product_ranking)
    fig_ranking = px.bar(
        ranking_df, x='total_sales', y='product_line',
        orientation='h',   # horizontal orienation
        title='Product Line Ranking',
        labels={'total_sales': 'Total Sales (£)', 'product_line': ''},
        color_discrete_sequence=['#008C8C']
    )
    fig_ranking.update_layout(
        paper_bgcolor='#FFFFFF', plot_bgcolor='#F5F5F5',
        font_color='#555555', title_font_color='#333333',
        xaxis=dict(gridcolor='#E0E0E0', linecolor='#E0E0E0'),
        yaxis=dict(gridcolor='#E0E0E0', linecolor='#E0E0E0'),
    )
    ranking_chart = to_html(fig_ranking, full_html=False)
 
    # category trend status
    trend_status = list(
        ProductLineTrendStatus.objects.all().order_by('product_line').values()
    )
 
    # product lines for monthly category trend filter (no duplicates) 
    product_lines = list(set(ProductMonthlyTrend.objects.values_list(
        'product_line', flat=True
    )))
    product_lines.sort()
 
    # get selected product line (default to first in list) 
    selected_product_line = request.GET.get('product_line', product_lines[0])
 
    #  monthly category trend dual panel chart (filtered by product line) 
    
    monthly_category = pd.DataFrame(
    ProductMonthlyTrend.objects.filter(
        product_line=selected_product_line
    ).order_by('month').values()
)
    
    #create dual panel subplot
    #row 1 = monthly sales line chart
    #row 2 = monthly growth rate bar chart
    fig_dual = make_subplots(
    rows=2, cols=1,

    # dynamic titles for each panel using the selected productline
    subplot_titles=(
        f'Monthly Sales — {selected_product_line}',
        f'Monthly Growth Rate (%) — {selected_product_line}'
    ),
    vertical_spacing=0.25
)
    fig_dual.add_trace(
    go.Scatter(
        x=monthly_category['month'],
        y=monthly_category['sales'],
        name='Sales (£)',
        line=dict(color='#008C8C', width=2),
        mode='lines+markers',
        marker=dict(size=8),
    ),
    row=1, col=1
)
# add bar chart for the monthly growth rate in panel 2
    fig_dual.add_trace(
    go.Bar(
        x=monthly_category['month'],  #shows month number
        y=monthly_category['monthly_growth'], #growth percentage
        name='Growth %',
        marker_color=['#008C8C' if v and v >= 0 else '#E05C4B'
                      for v in monthly_category['monthly_growth']],
        showlegend=True,  

        #show the growth percentage value as label for each chart 
        text=[f'{v:.1f}%' if v else '' for v in monthly_category['monthly_growth']],
        textposition='outside',  #position label above the bar
        textfont=dict(color='#333333', size=12),
    ),
    row=2, col=1
)
    #update x axis for both panels 

    fig_dual.update_xaxes(
    tickmode='array',
    tickvals=[1, 2, 3],
    ticktext=['Month 1', 'Month 2', 'Month 3'],
    gridcolor='#E0E0E0',
    linecolor='#E0E0E0',
)

#update the y axis for both panels 
    fig_dual.update_yaxes(
    gridcolor='#E0E0E0',
    linecolor='#E0E0E0',
)

# update overall chart layout to match the system palette
    fig_dual.update_layout(
    paper_bgcolor='#FFFFFF',
    plot_bgcolor='#F5F5F5',
    font_color='#555555',
    title_font_color='#333333',
    height=550,
    legend=dict(font=dict(color='#555555')),
)
    dual_chart = to_html(fig_dual, full_html=False)
 
    #busy day analysis chart
    # retrieves total sales per day of week from WeekdaySalesTrend
    # pd.Categorical enforces Monday to Sunday ordering
    # rather than default alphabetical ordering
    
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_sales = list(WeekdaySalesTrend.objects.all().values())
    weekday_df = pd.DataFrame(weekday_sales)
    weekday_df['day_of_week'] = pd.Categorical(
        weekday_df['day_of_week'], categories=day_order, ordered=True
    )
    weekday_df = weekday_df.sort_values('day_of_week')
    fig_busy = px.bar(
        weekday_df, x='day_of_week', y='sales',
        title='Busy Day Analysis',
        labels={'day_of_week': 'Day', 'sales': 'Sales (£)'},
        color_discrete_sequence=['#008C8C']
    )
    fig_busy.update_layout(
        paper_bgcolor='#FFFFFF', plot_bgcolor='#F5F5F5',
        font_color='#555555', title_font_color='#333333',
        xaxis=dict(gridcolor='#E0E0E0', linecolor='#E0E0E0'),
        yaxis=dict(gridcolor='#E0E0E0', linecolor='#E0E0E0'),
    )
    busy_chart = to_html(fig_busy, full_html=False)



 # context dictionary #####
 #packages all prepared data into the context dictionary
    # passed to the template via render() for injection into HTML placeholders
    # three categories of data:
    # 1 — Plotly chart HTML strings generated by to_html()
    # 2 — KPI and query results retrieved from database models

    context = {
        #kpi cards 
        'trend_result': trend_result,

        # Plotly chart HTML strings — rendered in template using |safe filter
        'daily_chart': daily_chart,
        'weekly_chart': weekly_chart,
        'monthly_chart': monthly_chart,
        'ranking_chart': ranking_chart,
        'trend_status': trend_status,
        'dual_chart': dual_chart,
        'busy_chart': busy_chart,

        #dropdown filter - list of product line
        'product_lines': product_lines,
        'selected_product_line': selected_product_line,
        #used to hide forecasting tab in navgation if user is not manager 
        'is_manager': request.user.groups.filter(name='Store Manager').exists(),
    }
 
    return render(request, 'analytics/trend_dashboard.html', context)
 
 
# Forecast Dashboard View 
# restricted to store manager only 
# @login_required ensures unauthenticated users redirected to login page
@login_required(login_url='login')
def forecast_dashboard(request):

    # checks whether authenticated user belongs to Store Manager group
    # queries auth_user_groups table via ORM
    # store worker redirected to trend dashboard with error message
    # prevents unauthorised access even via direct URL manipulation
    if not request.user.groups.filter(name='Store Manager').exists():
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('trend_dashboard')
 
    #  KPI cards 
    forecast_summary = ForecastSummary.objects.first()
    forecast_results = list(ForecastResult.objects.all().order_by('product_line').values())
    forecast_df = pd.DataFrame(forecast_results)
 
    #  total forecasted units KPI 
    total_forecast_units = round(forecast_df['forecast_quantity'].sum(), 1)
 
    # restock needed calculation 
    # calculates restock quantity for low stock product lines only
    # restock needed = forecast quantity minus available stock
    # None returned for normal and overstock product lines -displayed as dash in table

    restock_list = []
    for _, row in forecast_df.iterrows():
        if row['stock_status'] == 'lowstock':
            restock_list.append(round(row['forecast_quantity'] - row['available_stock'], 1))
        else:
            restock_list.append(None)
    forecast_df['restock_needed'] = restock_list
    forecast_results = forecast_df.to_dict('records')
 
    #7 day forecast bar chart 
    fig_forecast = px.bar(
        forecast_df,
        x='forecast_quantity',
        y='product_line',
        orientation='h',
        title='7 Day Forecast by Product Line',
        labels={'forecast_quantity': 'Forecast Quantity', 'product_line': ''},
        color_discrete_sequence=['#008C8C']
    )
    fig_forecast.update_layout(
        paper_bgcolor='#FFFFFF', plot_bgcolor='#F5F5F5',
        font_color='#555555', title_font_color='#333333',
        xaxis=dict(gridcolor='#E0E0E0', linecolor='#E0E0E0'),
        yaxis=dict(gridcolor='#E0E0E0', linecolor='#E0E0E0'),
    )
    forecast_chart = to_html(fig_forecast, full_html=False)
 
    # inventory vs forecast grouped bar chart 
    fig_combo = go.Figure()
    fig_combo.add_trace(go.Bar(
        name='Forecast Quantity',
        x=forecast_df['product_line'],
        y=forecast_df['forecast_quantity'],
        marker_color='#008C8C'
    ))
    fig_combo.add_trace(go.Bar(
        name='Available Stock',
        x=forecast_df['product_line'],
        y=forecast_df['available_stock'],
        marker_color='#F2C94C'
    ))
    fig_combo.update_layout(
        barmode='group',
        title='Inventory vs Forecast',
        paper_bgcolor='#FFFFFF', plot_bgcolor='#F5F5F5',
        font_color='#555555', title_font_color='#333333',
        legend=dict(font=dict(color='#555555')),
        xaxis_title='Product Line',
        yaxis_title='Quantity',
        xaxis=dict(gridcolor='#E0E0E0', linecolor='#E0E0E0'),
        yaxis=dict(gridcolor='#E0E0E0', linecolor='#E0E0E0'),
    )
    combo_chart = to_html(fig_combo, full_html=False)
 

  # Context Dictionary#
    # packages all prepared data into the context dictionary
    # passed to the forecast dashboard template via render()
    context = {

# KPI card data - low stock, overstock and normal stock counts
        'forecast_summary': forecast_summary,
        'forecast_results': forecast_results,
        'forecast_chart': forecast_chart,
        'combo_chart': combo_chart,
         # total forecast units KPI - calculated at request time
        'total_forecast_units': total_forecast_units,
        # used to conditionally show Forecasting tab in navigation
        'is_manager': request.user.groups.filter(name='Store Manager').exists(),
    }
 
    return render(request, 'analytics/forecast_dashboard.html', context)
 


 # View Level Calculations#
# the following two calculations are performed at request time in the view
# rather than being pre-computed in the ETL pipeline
# both were added as final additions during frontend development
# after the ETL pipeline and database schema had been finalised
# restock_needed — presentation calculation added when building the restock table
# total_forecast_units — additional KPI added after ForecastSummary was created