__version__ = "2.0.0-dev"
__title__ = "Next CRM"

import erpnext.crm.doctype.lead.lead as lead_doc
import erpnext.crm.utils as erp_utils
import frappe
from erpnext.crm.doctype.lead.lead import _set_missing_values
from frappe.desk.doctype.event import event as frappe_event
from frappe.model.mapper import get_mapped_doc


def monkey_patch():
    erp_utils.link_open_tasks = link_open_tasks
    erp_utils.link_open_events = link_open_events
    lead_doc.make_opportunity = make_opportunity
    frappe_event.Event.set_participants_email = lambda self: None


def link_open_tasks(ref_doctype, ref_docname, doc):
    todos = erp_utils.get_open_todos(ref_doctype, ref_docname)

    for todo in todos:
        todo_doc = frappe.get_doc("ToDo", todo.name)
        todo_doc.reference_type = doc.doctype
        todo_doc.reference_name = doc.name
        todo_doc.save(ignore_permissions=True)


def link_open_events(ref_doctype, ref_docname, doc):
    events = erp_utils.get_open_events(ref_doctype, ref_docname)
    for event in events:
        event_doc = frappe.get_doc("Event", event.name)
        event_doc.add_participant(doc.doctype, doc.name)
        event_doc.save(ignore_permissions=True)


@frappe.whitelist()
def make_opportunity(source_name, target_doc=None):
    def set_missing_values(source, target):
        _set_missing_values(source, target)

    target_doc = get_mapped_doc(
        "Lead",
        source_name,
        {
            "Lead": {
                "doctype": "Opportunity",
                "field_map": {
                    "campaign_name": "campaign",
                    "doctype": "opportunity_from",
                    "name": "party_name",
                    "lead_name": "contact_display",
                    "company_name": "customer_name",
                    "email_id": "contact_email",
                    "mobile_no": "contact_mobile",
                    "lead_owner": "opportunity_owner",
                },
            }
        },
        target_doc,
        set_missing_values,
    )
    return target_doc


# try:
#     monkey_patch()
# except Exception:
#     pass
