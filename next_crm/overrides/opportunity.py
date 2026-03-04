# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from erpnext.crm.doctype.opportunity.opportunity import Opportunity
from frappe import _
from frappe.desk.form.assign_to import add as assign
from frappe.utils import get_datetime


class OverrideOpportunity(Opportunity):
	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Opportunity From",
				"type": "Dynamic Link",
				"key": "party_name",
				"options": "opportunity_from",
				"width": "11rem",
			},
			{
				"label": "Amount",
				"type": "Currency",
				"key": "opportunity_amount",
				"width": "9rem",
			},
			{
				"label": "Status",
				"type": "Link",
				"key": "status",
				"width": "10rem",
			},
			{
				"label": "Email",
				"type": "Data",
				"key": "contact_email",
				"width": "12rem",
			},
			{
				"label": "Mobile No",
				"type": "Data",
				"key": "contact_mobile",
				"width": "11rem",
			},
			{
				"label": "Assigned To",
				"type": "Text",
				"key": "_assign",
				"width": "10rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"customer",
			"opportunity_amount",
			"status",
			"contact_email",
			"currency",
			"contact_mobile",
			"opportunity_owner",
			"sla_status",
			"response_by",
			"first_response_time",
			"first_responded_on",
			"modified",
			"_assign",
		]
		return {"columns": columns, "rows": rows}

	@staticmethod
	def default_kanban_settings():
		return {
			"column_field": "status",
			"title_field": "customer",
			"kanban_fields": '["opportunity_amount", "contact_email", "contact_mobile", "_assign", "modified"]',
		}
