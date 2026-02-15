import frappe


def delete_attachments_from_crm_notes(doctype, docname):
    """
    Removes all files attached in custom_note_attachments from CRM Notes
    linked to the given parent document (e.g., Opportunity or Lead),
    and deletes the corresponding File documents.

    Args:
        doctype (str): The parent doctype (e.g., "Opportunity")
        docname (str): The name of the parent doc (e.g., "OPTY-0001")
    """
    # Use direct SQL query to get all attachment filenames and their references
    # This replaces the N+1 pattern of loading each note document
    attachment_data = frappe.db.sql(
        """
        SELECT nca.name as attachment_id, nca.filename
        FROM `tabNCRM Attachments` nca
        INNER JOIN `tabCRM Note` cn ON cn.name = nca.parent
        WHERE cn.parenttype = %s
        AND cn.parent = %s
        AND nca.filename IS NOT NULL
    """,
        (doctype, docname),
        as_dict=True,
    )

    if not attachment_data:
        return

    # Collect unique filenames for deletion
    file_names_to_delete = {row["filename"] for row in attachment_data}

    # Delete all attachment references directly from child table
    attachment_ids = [row["attachment_id"] for row in attachment_data]
    if attachment_ids:
        frappe.db.delete("NCRM Attachments", {"name": ("in", attachment_ids)})

    # Delete the actual file documents
    for file_name in file_names_to_delete:
        try:
            frappe.delete_doc("File", file_name)
        except frappe.LinkExistsError:
            frappe.log_error(
                f"File {file_name} still linked to another document",
                "File Deletion Warning",
            )
        except Exception as e:
            frappe.log_error(
                f"Failed to delete file {file_name}: {e}", "File Deletion Error"
            )
