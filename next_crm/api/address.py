import frappe
from frappe import _


@frappe.whitelist()
def get_address(name):
    Address = frappe.qb.DocType("Address")

    query = frappe.qb.from_(Address).select("*").where(Address.name == name).limit(1)

    address = query.run(as_dict=True)
    if not len(address):
        frappe.throw(_("Address not found"), frappe.DoesNotExistError)
    address = address.pop()

    address["doctype"] = "Address"
    return address


@frappe.whitelist()
def get_linked_address(link_doctype, link_name):
    filters = [
        ["Dynamic Link", "link_doctype", "=", link_doctype],
        ["Dynamic Link", "link_name", "=", link_name],
    ]

    if not "Lead" == link_doctype and not "Opportunity" == link_doctype:
        addresses = frappe.get_list(
            "Address",
            filters,
            pluck="name",
        )
        return addresses

    addresses = frappe.get_list(
        "Address",
        fields=[
            "address_line1",
            "phone",
            "title",
            "name",
            "is_primary_address",
            "is_shipping_address",
        ],
        filters=filters,
        distinct=True,
    )
    return addresses


@frappe.whitelist()
def get_linked_docs(address, link_doctype):
    address_doc = frappe.get_doc("Address", address)

    names = []
    for link in address_doc.links:
        if link.link_doctype == link_doctype:
            names.append(link.link_name)

    return names


@frappe.whitelist()
def link_address_to_doc(address, doctype, docname):
    if not frappe.has_permission(doctype, "write", docname):
        frappe.throw(_("Not allowed to link address"), frappe.PermissionError)

    address_doc = frappe.get_doc("Address", address)

    address_doc.append("links", {"link_doctype": doctype, "link_name": docname})

    address_doc.save()

    return address_doc.name


@frappe.whitelist()
def set_billing_shipping(address_name, is_billing):
    address = frappe.get_doc("Address", address_name)
    if is_billing:
        address.is_primary_address = True
    else:
        address.is_shipping_address = True

    address.save()
    return True


@frappe.whitelist()
def remove_address(link_doctype, link_name, address):
    if not frappe.has_permission(link_doctype, "write", link_name):
        frappe.throw(_("Not allowed to remove address"), frappe.PermissionError)

    address_doc = frappe.get_doc("Address", address)
    address_doc.links = [d for d in address_doc.links if d.link_name != link_name]
    address_doc.save()
    return True


def migrate_lead_addresses_to_opportunity(lead_name, opportunity_name):
    addresses = frappe.get_all(
        "Address",
        filters=[
            ["Dynamic Link", "link_doctype", "=", "Lead"],
            ["Dynamic Link", "link_name", "=", lead_name],
        ],
        pluck="name",
    )
    if not addresses:
        return

    for address in addresses:
        address_doc = frappe.get_doc("Address", address)
        address_doc.append(
            "links",
            {
                "link_doctype": "Opportunity",
                "link_name": opportunity_name,
            },
        )
        address_doc.save()

    return True
