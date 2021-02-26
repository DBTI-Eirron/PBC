
import frappe

def execute():
	update_period_on_weekly_set()

def update_period_on_weekly_set():
	print("update_period_on_weekly_set . . .")
	frappe.db.sql(""" UPDATE `tabPayroll Period` PP 
		INNER JOIN `tabWeekly Set`WS ON PP.weekly_set = WS.`name`
		SET
		WS.period_group = PP.period_group
		WHERE PP.schedule = "Weekly" AND (PP.period_group IS NOT NULL OR PP.period_group != "") AND (PP.weekly_set IS NOT NULL OR PP.weekly_set != "") """)
	frappe.db.commit()
