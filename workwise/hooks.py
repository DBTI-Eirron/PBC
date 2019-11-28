# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "Workwise"
app_title = "Payroll Timekeeping Core"
app_publisher = "OSI"
app_description = "HRIS Developed by Opensoft Solutions Inc."
app_icon = "octicon octicon-book"
app_color = "#589494"
app_email = "krefin.fagara@gmail.com"
app_license = ""
app_version = "1.0.64"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/workwise/css/workwise.css"
app_include_js = "/assets/js/workwise.min.js"
website_context = {
	"favicon": 	"/assets/workwise/images/favicon.png",
	"splash_image": "/assets/workwise/images/favicon.png"
}
# include js, css files in header of web template
web_include_css = "/assets/workwise/css/web_workwise.css"
calendars = ["Payroll Settings"]

notification_config = "workwise.notifications.notifications.get_notification_config"

scheduler_events = {
	"monthly": [
		"workwise.time_keeping.timekeeping_task.leave_balance_monthly",
	],
	#"cron": {
    #    "0/10 * * * *": [
    #        "workwise.time_keeping.timekeeping_task.employee_movement_effectivity"
    #	],
    #}
}
