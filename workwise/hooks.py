# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "Workwise"
app_title = "Workwise"
app_publisher = "HDI Systech"
app_description = "Workwise HRIS"
app_icon = "octicon octicon-book"
app_color = "#589494"
app_email = "krefin.fagara@gmail.com"
app_license = "GNU General Public License"
app_version = "1.0.58"

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
# web_include_js = "/assets/workwise/js/workwise.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

calendars = ["Payroll Settings"]

# Website user home page (by function)
# get_website_user_home_page = "workwise.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "workwise.install.before_install"
# after_install = "workwise.install.after_install"

# Desk Notifications
# ------------------
notification_config = "workwise.notifications.notifications.get_notification_config"
# notification_config = "workwise.notification.notifications.get_notification_config"

# See frappe.core.notifications.get_notification_config

# notification_config = "workwise.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"workwise.tasks.all"
# 	],
# 	"daily": [
# 		"workwise.tasks.daily"
# 	],
# 	"hourly": [
# 		"workwise.tasks.hourly"
# 	],
# 	"weekly": [
# 		"workwise.tasks.weekly"
# 	]
# 	"monthly": [
# 		"workwise.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "workwise.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "workwise.event.get_events"
# }

