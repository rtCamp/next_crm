# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document


class CRMFieldsLayout(Document):
    pass


@frappe.whitelist()
def get_fields_layout(doctype: str, type: str):
    sections = []
    if frappe.db.exists("CRM Fields Layout", {"dt": doctype, "type": type}):
        layout = frappe.get_doc("CRM Fields Layout", {"dt": doctype, "type": type})
    else:
        return []

    if layout.layout:
        sections = json.loads(layout.layout)

    allowed_fields = []
    for section in sections:
        if not section.get("fields"):
            continue
        allowed_fields.extend(section.get("fields"))

    fields = frappe.get_meta(doctype).fields
    fields = [field for field in fields if field.fieldname in allowed_fields]

    for section in sections:
        for field in section.get("fields") if section.get("fields") else []:
            field = next((f for f in fields if f.fieldname == field), None)
            if field:
                options = field.options
                if field.fieldtype == "Select" and options:
                    if isinstance(options, str):
                        select_options = options.split("\n")
                    elif isinstance(options, (list, tuple)):
                        select_options = list(options)
                    else:
                        select_options = [options]

                    options = [
                        {"label": _(option), "value": option}
                        for option in select_options
                    ]
                    options.insert(0, {"label": "", "value": ""})

                field = {
                    "label": _(field.label),
                    "name": field.fieldname,
                    "type": field.fieldtype,
                    "options": options,
                    "mandatory": field.reqd,
                    "placeholder": field.get("placeholder"),
                    "filters": field.get("link_filters"),
                }
                section["fields"][section.get("fields").index(field["name"])] = field

    return sections or []


@frappe.whitelist()
def save_fields_layout(doctype: str, type: str, layout: str):
    if frappe.db.exists("CRM Fields Layout", {"dt": doctype, "type": type}):
        doc = frappe.get_doc("CRM Fields Layout", {"dt": doctype, "type": type})
    else:
        doc = frappe.new_doc("CRM Fields Layout")

    doc.update(
        {
            "dt": doctype,
            "type": type,
            "layout": layout,
        }
    )
    doc.save(ignore_permissions=True)

    return doc.layout
