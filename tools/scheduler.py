from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

us_eastern_tz = timezone('US/Eastern')
scheduler = BackgroundScheduler(time_zone=us_eastern_tz)