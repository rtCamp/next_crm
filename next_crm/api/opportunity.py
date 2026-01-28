import frappe
from frappe import _

from next_crm.api.doc import get_assigned_users, get_fields_meta
from next_crm.ncrm.doctype.crm_form_script.crm_form_script import get_form_script


@frappe.whitelist()
def get_opportunity(name):
    opportunity = frappe.get_doc("Opportunity", name, for_update=False).as_dict()

    opportunity["doctype"] = "Opportunity"
    opportunity["fields_meta"] = get_fields_meta("Opportunity")
    opportunity["_form_script"] = get_form_script("Opportunity")
    opportunity["_assign"] = get_assigned_users("Opportunity", opportunity.name)
    hide_comments_tab = frappe.db.get_single_value("NCRM Settings", "hide_comments_tab")
    opportunity["hide_comments_tab"] = hide_comments_tab
    return opportunity


@frappe.whitelist()
def declare_enquiry_lost_api(
    name, lost_reasons_list, competitors, detailed_reason=None
):
    opportunity = frappe.get_doc("Opportunity", name)
    opportunity.declare_enquiry_lost(
        lost_reasons_list=lost_reasons_list,
        competitors=competitors,
        detailed_reason=detailed_reason,
    )
    return _("Opportunity updated successfully")


def create_checklist(docname, field=None, value=None):
    if not field and not value:
        return

    title = _("Checklist for {0}").format(value)

    existing_todo = frappe.get_all(
        "ToDo",
        filters={
            "reference_type": "Opportunity",
            "reference_name": docname,
            "custom_title": title,
            "status": "Open",
        },
        fields=["name"],
        limit=1,
        ignore_permissions=True,
    )
    if existing_todo:
        return

    parenttype = "CRM Deal Status" if field == "status" else "Sales Stage"
    checklist_items = frappe.get_all(
        "Opportunity Status Checklist",
        filters={"parent": value, "parenttype": parenttype},
        fields=["checklist_item"],
        pluck="checklist_item",
        ignore_permissions=True,
    )

    if not checklist_items:
        return

    content = (
        '<div class="ql-editor read-mode"><ol>'
        + "".join(
            [
                f'<li data-list="unchecked"><span class="ql-ui" contenteditable="false"></span>{item}</li>'
                for item in checklist_items
            ]
        )
        + "</ol></div>"
    )

    opportunity_owner = (
        frappe.db.get_value("Opportunity", docname, "opportunity_owner")
        or frappe.session.user
    )

    todo = frappe.get_doc(
        {
            "doctype": "ToDo",
            "custom_title": title,
            "description": content,
            "reference_type": "Opportunity",
            "reference_name": docname,
            "allocated_to": opportunity_owner,
        },
        ignore_permissions=True,
    )

    todo.insert(ignore_permissions=True)
    return todo.name


def _validate_reference(reference_doctype: str, reference_name: str):
    if reference_doctype not in ("Lead", "Opportunity"):
        frappe.throw(_("Invalid reference_doctype"), frappe.ValidationError)

    if not reference_name:
        frappe.throw(_("reference_name is required"), frappe.ValidationError)

    if not frappe.db.exists(reference_doctype, reference_name):
        frappe.throw(_("Document not found"), frappe.DoesNotExistError)

    if not frappe.has_permission(reference_doctype, "write", reference_name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)


def _validate_deal_inputs(reference_doctype: str, deal_stage=None, status=None):
    if deal_stage is not None:
        if reference_doctype == "Opportunity" and not frappe.db.exists(
            "Sales Stage", deal_stage
        ):
            frappe.throw(_("Invalid deal_stage"), frappe.ValidationError)

    if status is not None:
        status_doctype = (
            "CRM Deal Status"
            if reference_doctype == "Opportunity"
            else "CRM Lead Status"
        )
        if not frappe.db.exists(status_doctype, status):
            frappe.throw(_("Invalid status"), frappe.ValidationError)


@frappe.whitelist()
def update_deal(reference_doctype, reference_name, deal_stage=None, status=None):
    _validate_reference(reference_doctype, reference_name)
    _validate_deal_inputs(reference_doctype, deal_stage=deal_stage, status=status)

    updates = {}

    if status is not None:
        updates["status"] = status

    if deal_stage is not None and reference_doctype == "Opportunity":
        updates["sales_stage"] = deal_stage

    if updates:
        frappe.db.set_value(
            reference_doctype, reference_name, updates, update_modified=True
        )

    return frappe.get_doc(reference_doctype, reference_name)
