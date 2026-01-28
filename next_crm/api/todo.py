import frappe
from frappe import _

from next_crm.ncrm.doctype.crm_notification.crm_notification import notify_user


def _validate_task_reference(reference_doctype: str, reference_name: str):
    if reference_doctype not in ("Lead", "Opportunity"):
        frappe.throw(_("Invalid reference_doctype"), frappe.ValidationError)

    if not reference_name:
        frappe.throw(_("reference_name is required"), frappe.ValidationError)

    if not frappe.db.exists(reference_doctype, reference_name):
        frappe.throw(_("Document not found"), frappe.DoesNotExistError)

    # Creating a follow-up should require write access to the referenced doc.
    if not frappe.has_permission(reference_doctype, "write", reference_name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    if not frappe.has_permission("ToDo", "create"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)


@frappe.whitelist()
def create_task(
    reference_doctype,
    reference_name,
    title=None,
    description=None,
    allocated_to=None,
    date=None,
    priority="Medium",
    status="Open",
):
    """Create a follow-up ToDo linked to a Lead or Opportunity."""

    _validate_task_reference(reference_doctype, reference_name)

    title = (title or "").strip()
    description = (description or "").strip()

    if not title and not description:
        frappe.throw(
            _("ToDo must have either a title or a description."),
            frappe.ValidationError,
        )

    todo = frappe.get_doc(
        {
            "doctype": "ToDo",
            "reference_type": reference_doctype,
            "reference_name": reference_name,
            "custom_title": title,
            "description": description,
            "allocated_to": allocated_to or frappe.session.user,
            "assigned_by": frappe.session.user,
            "date": date,
            "priority": priority or "Medium",
            "status": status or "Open",
        }
    )
    todo.insert()
    return todo


def notify_assigned_user(doc, is_cancelled=False):
    _doc = frappe.get_doc(doc.reference_type, doc.reference_name)
    owner = frappe.get_cached_value("User", frappe.session.user, "full_name")
    notification_text = get_notification_text(owner, doc, _doc, is_cancelled)

    message = (
        _("Your assignment on {0} {1} has been removed by {2}").format(
            doc.reference_type, doc.reference_name, owner
        )
        if is_cancelled
        else _("{0} assigned a {1} {2} to you").format(
            owner, doc.reference_type, doc.reference_name
        )
    )

    redirect_to_doctype, redirect_to_name = get_redirect_to_doc(doc)

    notify_user(
        {
            "owner": frappe.session.user,
            "assigned_to": doc.allocated_to,
            "notification_type": "Assignment",
            "message": message,
            "notification_text": notification_text,
            "reference_type": doc.reference_type,
            "reference_name": doc.reference_name,
            "redirect_to_doctype": redirect_to_doctype,
            "redirect_to_docname": redirect_to_name,
        }
    )


def get_notification_text(owner, doc, reference_doc, is_cancelled=False):
    name = doc.reference_name
    doctype = doc.reference_type
    doc_doctype = doc.doctype

    if doctype.startswith("CRM "):
        doctype = doctype[4:].lower()

    if doctype in ["Lead", "Opportunity"] and (
        doc.allocated_to not in reference_doc._assign if reference_doc._assign else True
    ):
        name = (
            reference_doc.title or name
            if doctype == "Lead"
            else reference_doc.title or reference_doc.customer or name
        )

        if is_cancelled:
            return f"""
				<div class="mb-2 leading-5 text-ink-gray-5">
					<span>{
                _("Your assignment on {0} {1} has been removed by {2}").format(
                    doctype,
                    f'<span class="font-medium text-ink-gray-9">{name}</span>',
                    f'<span class="font-medium text-ink-gray-9">{owner}</span>',
                )
            }</span>
				</div>
			"""

        return f"""
			<div class="mb-2 leading-5 text-ink-gray-5">
				<span class="font-medium text-ink-gray-9">{owner}</span>
				<span>{
            _("assigned a {0} {1} to you").format(doctype, f'<span class="font-medium text-ink-gray-9">{name}</span>')
        }</span>
			</div>
		"""

    if doc_doctype == "ToDo":
        if is_cancelled:
            return f"""
				<div class="mb-2 leading-5 text-ink-gray-5">
					<span>{
                _("Your assignment on ToDo {0} has been removed by {1}").format(
                    f'<span class="font-medium text-ink-gray-9">{reference_doc.title or reference_doc.name}</span>',
                    f'<span class="font-medium text-ink-gray-9">{owner}</span>',
                )
            }</span>
				</div>
			"""
        return f"""
			<div class="mb-2 leading-5 text-ink-gray-5">
				<span class="font-medium text-ink-gray-9">{owner}</span>
				<span>{
            _("assigned a new ToDo in {0} {1} to you").format(
                doctype, f'<span class="font-medium text-ink-gray-9">{reference_doc.title or reference_doc.name}</span>'
            )
        }</span>
			</div>
		"""


def get_redirect_to_doc(doc):
    if doc.reference_type == "ToDo":
        reference_doc = frappe.get_doc(doc.reference_type, doc.reference_name)
        return reference_doc.reference_type, reference_doc.reference_name

    return doc.reference_type, doc.reference_name
