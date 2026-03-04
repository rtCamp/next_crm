# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from crm.fcrm.doctype.crm_service_level_agreement.utils import get_sla
from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import (
	add_status_change_log,
)
from erpnext.crm.doctype.lead.lead import Lead
from frappe import _
from frappe.desk.form.assign_to import add as assign
from frappe.utils import has_gravatar, validate_email_address


class Lead(Lead):
	def before_validate(self):
		# self.set_sla()
		super()

	def validate(self):
		super()
		if not self.is_new():
			curr_owner = frappe.db.get_value(self.doctype, self.name, "lead_owner")
			if self.lead_owner and self.lead_owner != curr_owner:
				self.share_with_agent(self.lead_owner)
				self.assign_agent(self.lead_owner)
		# if self.has_value_changed("status"):
		# 	add_status_change_log(self)

	def after_insert(self):
		if self.lead_owner:
			self.assign_agent(self.lead_owner)
		super()

	def before_save(self):
		# self.apply_sla()
		super()

	def validate_email(self):
		if self.email:
			if not self.flags.ignore_email_validation:
				validate_email_address(self.email, throw=True)

			if self.email == self.lead_owner:
				frappe.throw(_("Lead Owner cannot be same as the Lead Email Address"))

			if self.is_new() or not self.image:
				self.image = has_gravatar(self.email)

	def assign_agent(self, agent):
		if not agent:
			return

		assignees = self.get_assigned_users()
		if assignees:
			for assignee in assignees:
				if agent == assignee:
					# the agent is already set as an assignee
					return

		assign({"assign_to": [agent], "doctype": "Lead", "name": self.name})

	def share_with_agent(self, agent):
		if not agent:
			return

		docshares = frappe.get_all(
			"DocShare",
			filters={"share_name": self.name, "share_doctype": self.doctype},
			fields=["name", "user"],
		)

		shared_with = [d.user for d in docshares] + [agent]

		for user in shared_with:
			if user == agent and not frappe.db.exists(
				"DocShare",
				{"user": agent, "share_name": self.name, "share_doctype": self.doctype},
			):
				frappe.share.add_docshare(
					self.doctype,
					self.name,
					agent,
					write=1,
					flags={"ignore_share_permission": True},
				)
			elif user != agent:
				frappe.delete_doc("DocShare", self.name, ignore_permissions=True)

	def create_contact(self, existing_contact=None, throw=False):
		if not self.lead_name:
			self.set_full_name()
			self.set_lead_name()

		existing_contact = existing_contact or self.contact_exists(throw)
		if existing_contact:
			self.update_lead_contact(existing_contact)
			return existing_contact

		contact = frappe.new_doc("Contact")
		contact.update(
			{
				"first_name": self.first_name or self.lead_name,
				"last_name": self.last_name,
				"salutation": self.salutation,
				"gender": self.gender,
				"designation": self.job_title,
				"company_name": self.customer,
				"image": self.image or "",
			}
		)

		if self.email_id:
			contact.append("email_ids", {"email_id": self.email_id, "is_primary": 1})

		if self.phone:
			contact.append("phone_nos", {"phone": self.phone, "is_primary_phone": 1})

		if self.mobile_no:
			contact.append("phone_nos", {"phone": self.mobile_no, "is_primary_mobile_no": 1})

		contact.insert()
		contact.reload()  # load changes by hooks on contact

		return contact.name

	def update_lead_contact(self, contact):
		contact = frappe.get_cached_doc("Contact", contact)
		frappe.db.set_value(
			"Lead",
			self.name,
			{
				"salutation": contact.salutation,
				"first_name": contact.first_name,
				"last_name": contact.last_name,
				"email_id": contact.email_id,
				"mobile_no": contact.mobile_no,
			},
		)

	def create_customer(self):
		if not self.company_name:
			return

		existing_customer = frappe.db.exists("Customer", {"customer_name": self.company_name})
		if existing_customer:
			return existing_customer

		customer = frappe.new_doc("Customer")
		customer.update(
			{
				"customer_name": self.company_name,
				"customer_type": "company",
				"website": self.website,
				"territory": self.territory,
				"industry": self.industry,
			}
		)
		customer.insert()
		return customer.name

	def contact_exists(self, throw=True):
		email_exist = frappe.db.exists("Contact Email", {"email_id": self.email_id})
		phone_exist = frappe.db.exists("Contact Phone", {"phone": self.phone})
		mobile_exist = frappe.db.exists("Contact Phone", {"phone": self.mobile_no})

		doctype = "Contact Email" if email_exist else "Contact Phone"
		name = email_exist or phone_exist or mobile_exist

		if name:
			text = "Email" if email_exist else "Phone" if phone_exist else "Mobile No"
			data = self.email_id if email_exist else self.phone if phone_exist else self.mobile_no

			value = f"{text}: {data}"

			contact = frappe.db.get_value(doctype, name, "parent")

			if throw:
				frappe.throw(
					_("Contact already exists with {0}").format(value),
					title=_("Contact Already Exists"),
				)
			return contact

		return False

	def create_opportunity(self, contact, customer):
		from erpnext.crm.doctype.lead.lead import make_opportunity

		from next_crm.api.address import migrate_lead_addresses_to_opportunity
		from next_crm.api.contact import (
			link_contact_to_doc,
			migrate_lead_contacts_to_opportunity,
			set_opportunity_primary_contact,
		)

		opportunity = make_opportunity(self.name)

		opportunity.update({"customer": customer})

		# if self.first_responded_on:
		# 	opportunity.update(
		# 		{
		# 			"sla_creation": self.sla_creation,
		# 			"response_by": self.response_by,
		# 			"sla_status": self.sla_status,
		# 			"communication_status": self.communication_status,
		# 			"first_response_time": self.first_response_time,
		# 			"first_responded_on": self.first_responded_on,
		# 		}
		# 	)

		opportunity.insert()
		link_contact_to_doc(contact, "Opportunity", opportunity.name)
		migrate_lead_addresses_to_opportunity(self.name, opportunity.name)
		migrate_lead_contacts_to_opportunity(self.name, opportunity.name)
		set_opportunity_primary_contact(opportunity.name)
		return opportunity.name

	def set_sla(self):
		"""
		Find an SLA to apply to the lead.
		"""
		if self.sla:
			return

		sla = get_sla(self)
		if not sla:
			self.first_responded_on = None
			self.first_response_time = None
			return
		self.sla = sla.name

	def apply_sla(self):
		"""
		Apply SLA if set.
		"""
		if not self.sla:
			return
		sla = frappe.get_last_doc("CRM Service Level Agreement", {"name": self.sla})
		if sla:
			sla.apply(self)

	def convert_to_opportunity(self):
		return convert_to_opportunity(lead=self.name, doc=self)

	def on_trash(self):
		frappe.db.set_value("Issue", {"lead": self.name}, "lead", None)
		frappe.db.delete("Prospect Lead", filters={"lead": self.name})
		frappe.db.delete(
			"Dynamic Link",
			filters={
				"link_name": self.name,
				"parenttype": ["in", ["Contact", "Address"]],
			},
		)
		delete_linked_event(self.name)
		frappe.db.delete("CRM Notification", {"reference_name": self.name})
		if "frappe_gmail_thread" in frappe.get_installed_apps():
			unlink_gmail_thread(self.name)

	@staticmethod
	def get_non_filterable_fields():
		return ["custom_converted"]

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Name",
				"type": "Data",
				"key": "lead_name",
				"width": "12rem",
			},
			{
				"label": "Customer",
				"type": "Link",
				"key": "company_name",
				"options": "Customer",
				"width": "10rem",
			},
			{
				"label": "Status",
				"type": "Select",
				"key": "status",
				"width": "8rem",
			},
			{
				"label": "Email",
				"type": "Data",
				"key": "email_id",
				"width": "12rem",
			},
			{
				"label": "Mobile No",
				"type": "Data",
				"key": "mobile_no",
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
			"lead_name",
			"customer",
			"status",
			"email_id",
			"mobile_no",
			"lead_owner",
			"first_name",
			"sla_status",
			"response_by",
			"first_response_time",
			"first_responded_on",
			"modified",
			"_assign",
			"image",
		]
		return {"columns": columns, "rows": rows}

	@staticmethod
	def default_kanban_settings():
		return {
			"column_field": "status",
			"title_field": "lead_name",
			"kanban_fields": '["customer", "email_id", "mobile_no", "_assign", "modified"]',
		}


@frappe.whitelist()
def convert_to_opportunity(
	lead, opportunity=None, existing_contact=None, existing_organization=None, doc=None
):
	if not (doc and doc.flags.get("ignore_permissions")) and not frappe.has_permission("Lead", "write", lead):
		frappe.throw(_("Not allowed to convert Lead to Opportunity"), frappe.PermissionError)

	lead = frappe.get_cached_doc("Lead", lead)
	if frappe.db.exists("CRM Lead Status", "Qualified"):
		lead.status = "Qualified"
	lead.custom_converted = 1
	# if lead.sla and frappe.db.exists("CRM Communication Status", "Replied"):
	# 	lead.communication_status = "Replied"
	lead.save()
	contact = lead.create_contact(existing_contact, False)
	if not existing_organization:
		existing_organization = lead.create_customer()
	opportunity = lead.create_opportunity(contact, existing_organization)

	frappe.enqueue(
		"next_crm.api.crm_note.copy_crm_notes_to_opportunity",
		job_name=f"Copy CRM Notes from {lead} to {opportunity}",
		queue="short",
		enqueue_after_commit=True,
		lead=lead.name,
		opportunity=opportunity,
	)
	return opportunity


def delete_linked_event(docname):
	event_part = frappe.qb.DocType("Event Participants")
	event_participants_query = (
		frappe.qb.from_(event_part)
		.where(event_part.reference_doctype == "Lead")
		.where(event_part.reference_docname == docname)
		.select(event_part.parent)
	)

	event = frappe.qb.DocType("Event")
	event_delete_query = (
		frappe.qb.from_(event).where(event.name.isin(event_participants_query)).delete().get_sql()
	)

	event_participants_delete_query = (
		frappe.qb.from_(event_part).where(event_part.parent.isin(event_participants_query)).delete().get_sql()
	)

	frappe.db.sql(event_delete_query)
	frappe.db.sql(event_participants_delete_query)


def unlink_gmail_thread(docname):
	gmail_thread = frappe.qb.DocType("Gmail Thread")

	query = (
		frappe.qb.update(gmail_thread)
		.set(gmail_thread.reference_doctype, None)
		.set(gmail_thread.reference_name, None)
		.set(gmail_thread.status, "Open")
		.where(gmail_thread.reference_doctype == "Lead")
		.where(gmail_thread.reference_name == docname)
		.get_sql()
	)

	frappe.db.sql(query)
