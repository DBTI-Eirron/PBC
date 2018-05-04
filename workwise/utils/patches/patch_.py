from __future__ import unicode_literals

from __future__ import unicode_literals
import frappe, datetime
from frappe import _
from frappe.utils import cint, flt, getdate, cstr, nowdate
from frappe.model.document import Document
from workwise.time_keeping.timekeeping_utils import datetimediff_hrs, sub_date, timediff_hrs

def run_patch():
	#get list of old ob
	ob_list = frappe.db.sql(""" SELECT `name`, from_time, to_time FROM `tabOfficial Business Application` WHERE (from_time is null or from_time != "00:00:00.000000") """, as_dict=1)
	for d in ob_list:
		entries = [];
		dates = [];

		ob = frappe.get_doc("Employee", self.employee)
		ob.update({
			"rate_type": self.current_rate_type,
			"rate": self.current_rate,
			"min_take_home": self.current_minimum_take_home,
			"is_attendance_base": self.current_attendance_base,
		})
	
		start = datetime.datetime.strptime(ob.from_date, '%Y-%m-%d')
		end = datetime.datetime.strptime(ob.to_date, '%Y-%m-%d')
		step = datetime.timedelta(days=1)
			
		while start <= end:
			dates.append(start.date());
			start += step

		for i in dates:
			info = {
				"target_date": i,
				"from_time": ob.from_time,
				"to_time": ob.to_time,
				"is_holiday": self.chk_holiday(i),
				"is_halfday": 0,
				"is_excluded": 0
			}

			entries.append(info);
			for d in sorted(list(entries), key=lambda k: k['target_date']):
				pr.append("official_business_application_table", d)



