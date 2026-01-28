import frappe
from frappe import _


def set_primary_email(doc):
    if not doc.email_ids:
        return

    if len(doc.email_ids) == 1:
        doc.email_ids[0].is_primary = 1


def set_primary_mobile_no(doc):
    if not doc.phone_nos:
        return

    if len(doc.phone_nos) == 1:
        doc.phone_nos[0].is_primary_mobile_no = 1


@frappe.whitelist()
def get_contact(name):
    Contact = frappe.qb.DocType("Contact")

    query = frappe.qb.from_(Contact).select("*").where(Contact.name == name).limit(1)

    contact = query.run(as_dict=True)
    if not len(contact):
        frappe.throw(_("Contact not found"), frappe.DoesNotExistError)
    contact = contact.pop()

    contact["doctype"] = "Contact"
    contact["email_ids"] = frappe.get_all(
        "Contact Email",
        filters={"parent": name},
        fields=["name", "email_id", "is_primary"],
    )
    contact["phone_nos"] = frappe.get_all(
        "Contact Phone",
        filters={"parent": name},
        fields=["name", "phone", "is_primary_mobile_no"],
    )
    return contact


@frappe.whitelist()
def get_contact_by_email(email: str):
    """Fetch contact details using email as the primary identifier."""
    if not email:
        frappe.throw(_("Email is required"), frappe.ValidationError)

    contacts = frappe.get_all(
        "Contact Email",
        filters={"email_id": email},
        fields=["parent", "is_primary"],
        order_by="is_primary desc",
    )

    if not contacts:
        frappe.throw(_("Contact not found"), frappe.DoesNotExistError)

    for contact in contacts:
        if not frappe.has_permission("Contact", "read", contact.parent):
            continue
        return get_contact(contact.parent)

    frappe.throw(_("Not permitted to access this contact"), frappe.PermissionError)


@frappe.whitelist()
def get_linked_opportunities(contact):
    """Get linked opportunities for a contact"""
    opportunity_names = get_linked_docs(contact, "Opportunity")

    # get opportunities data
    opportunities = []
    for opportunity_name in opportunity_names:
        opportunity = frappe.get_cached_doc(
            "Opportunity",
            opportunity_name,
            fields=[
                "name",
                "customer",
                "currency",
                "opportunity_amount",
                "status",
                "contact_email",
                "contact_mobile",
                "opportunity_owner",
                "modified",
            ],
        )
        opportunities.append(opportunity.as_dict())

    return opportunities


@frappe.whitelist()
def get_linked_customers(contact):
    """Get customer details linked to a contact."""
    customer_names = get_linked_docs(contact, "Customer")
    if not customer_names:
        return []

    customers = []
    for customer_name in customer_names:
        if not frappe.has_permission("Customer", "read", customer_name):
            continue
        customer = frappe.get_cached_value(
            "Customer",
            customer_name,
            [
                "name",
                "customer_name",
                "customer_group",
                "customer_type",
                "territory",
                "disabled",
            ],
            as_dict=True,
        )
        if customer:
            customers.append(customer)

    if customers:
        return customers

    frappe.throw(_("Not permitted to access linked customers"), frappe.PermissionError)


@frappe.whitelist()
def get_linked_leads(contact):
    """Get lead details linked to a contact."""
    lead_names = get_linked_docs(contact, "Lead")
    if not lead_names:
        return []

    leads = []
    for lead_name in lead_names:
        if not frappe.has_permission("Lead", "read", lead_name):
            continue
        lead = frappe.get_cached_value(
            "Lead",
            lead_name,
            [
                "name",
                "lead_name",
                "company_name",
                "status",
                "source",
                "territory",
                "email_id",
                "mobile_no",
            ],
            as_dict=True,
        )
        if lead:
            leads.append(lead)

    if leads:
        return leads

    frappe.throw(_("Not permitted to access linked leads"), frappe.PermissionError)


@frappe.whitelist()
def get_linked_docs(contact, link_doctype):
    contact_doc = frappe.get_doc("Contact", contact)

    names = []
    for link in contact_doc.links:
        if link.link_doctype == link_doctype:
            names.append(link.link_name)

    return names


@frappe.whitelist()
def create_new(contact, field, value):
    """Create new email or phone for a contact"""
    if not frappe.has_permission("Contact", "write", contact):
        frappe.throw("Not permitted", frappe.PermissionError)

    contact = frappe.get_doc("Contact", contact)

    if field == "email":
        contact.append("email_ids", {"email_id": value})
    elif field in ("mobile_no", "phone"):
        contact.append("phone_nos", {"phone": value})
    else:
        frappe.throw("Invalid field")

    contact.save()
    return True


@frappe.whitelist()
def set_as_primary(contact, field, value):
    """Set email or phone as primary for a contact"""
    if not frappe.has_permission("Contact", "write", contact):
        frappe.throw("Not permitted", frappe.PermissionError)

    contact = frappe.get_doc("Contact", contact)

    if field == "email_id":
        for email in contact.email_ids:
            if email.email_id == value:
                email.is_primary = 1
            else:
                email.is_primary = 0
    elif field in ("mobile_no", "phone"):
        name = "is_primary_mobile_no" if field == "mobile_no" else "is_primary_phone"
        for phone in contact.phone_nos:
            if phone.phone == value:
                phone.set(name, 1)
            else:
                phone.set(name, 0)
    else:
        frappe.throw("Invalid field")

    contact.save()
    return True


@frappe.whitelist()
def search_emails(txt: str):
    doctype = "Contact"
    meta = frappe.get_meta(doctype)
    filters = [["Contact", "email_id", "is", "set"]]

    if meta.get("fields", {"fieldname": "enabled", "fieldtype": "Check"}):
        filters.append([doctype, "enabled", "=", 1])
    if meta.get("fields", {"fieldname": "disabled", "fieldtype": "Check"}):
        filters.append([doctype, "disabled", "!=", 1])

    or_filters = []
    search_fields = ["full_name", "email_id", "name"]
    if txt:
        for f in search_fields:
            or_filters.append([doctype, f.strip(), "like", f"%{txt}%"])

    results = frappe.get_list(
        doctype,
        filters=filters,
        fields=search_fields,
        or_filters=or_filters,
        limit_start=0,
        limit_page_length=20,
        order_by="email_id, full_name, name",
        ignore_permissions=False,
        as_list=True,
        strict=False,
    )

    return results


@frappe.whitelist()
def get_linked_contact(link_doctype, link_name):
    contacts = frappe.get_list(
        "Contact",
        [
            ["Dynamic Link", "link_doctype", "=", link_doctype],
            ["Dynamic Link", "link_name", "=", link_name],
        ],
        distinct=True,
        pluck="name",
    )

    return contacts


@frappe.whitelist()
def link_contact_to_doc(contact, doctype, docname):
    if not frappe.has_permission(doctype, "write", docname):
        frappe.throw(_("Not allowed to link contact to doc"), frappe.PermissionError)

    contact_doc = frappe.get_doc("Contact", contact)

    contact_doc.append("links", {"link_doctype": doctype, "link_name": docname})
    contact_doc.save()

    return contact_doc.name


@frappe.whitelist()
def remove_link_from_contact(contact, doctype, docname):
    if not frappe.has_permission(doctype, "write", docname):
        frappe.throw(_("Not allowed to remove contact"), frappe.PermissionError)

    contact_doc = frappe.get_doc("Contact", contact)

    contact_doc.links = [d for d in contact_doc.links if d.link_name != docname]
    contact_doc.save()

    return contact_doc.name


@frappe.whitelist()
def get_lead_opportunity_contacts(doctype, docname):
    contacts = get_linked_contact(doctype, docname)
    linked_contacts = []
    for contact in contacts:
        contact = frappe.get_doc("Contact", contact).as_dict()

        _contact = {
            "name": contact.name,
            "image": contact.image,
            "full_name": contact.full_name,
            "email": get_primary_email(contact),
            "mobile_no": get_primary_mobile_no(contact),
            "is_primary_contact": contact.is_primary_contact,
        }
        linked_contacts.append(_contact)
    return linked_contacts


@frappe.whitelist()
def set_opportunity_primary_contact(docname, contact=None):
    linked_contacts = get_linked_contact("Opportunity", docname)
    if not linked_contacts:
        return

    opportunity_doc = frappe.get_doc("Opportunity", docname)
    if not contact and len(linked_contacts) == 1:
        opportunity_doc.contact_person = linked_contacts[0]
    elif contact:
        opportunity_doc.contact_person = contact
    opportunity_doc.save()
    return True


def get_primary_email(contact):
    for email in contact.email_ids:
        if email.is_primary:
            return email.email_id
    return contact.email_ids[0].email_id if contact.email_ids else ""


def get_primary_mobile_no(contact):
    for phone in contact.phone_nos:
        if phone.is_primary:
            return phone.phone
    return contact.phone_nos[0].phone if contact.phone_nos else ""


def migrate_lead_contacts_to_opportunity(lead_name, opportunity_name):
    contacts = frappe.get_all(
        "Contact",
        filters=[
            ["Dynamic Link", "link_doctype", "=", "Lead"],
            ["Dynamic Link", "link_name", "=", lead_name],
        ],
        pluck="name",
    )
    if not contacts:
        return

    for contact in contacts:
        contact_doc = frappe.get_doc("Contact", contact)
        contact_doc.append(
            "links",
            {
                "link_doctype": "Opportunity",
                "link_name": opportunity_name,
            },
        )
        contact_doc.save()

    return True
