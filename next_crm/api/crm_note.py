import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import (
    enqueue_create_notification,
    get_title_html,
)
from frappe.utils import now

from next_crm.ncrm.doctype.crm_notification.crm_notification import notify_user


@frappe.whitelist()
def create_note(
    doctype,
    docname,
    title=None,
    note=None,
    parent_note=None,
    attachments=None,
    added_on=None,
):
    """
    Create a new CRM Note.
    """
    if not note and not title:
        raise frappe.ValidationError("Either note or title is required.")

    added_on = added_on if added_on else now()

    new_note = frappe.get_doc(
        {
            "doctype": "CRM Note",
            "custom_title": title,
            "note": note,
            "parenttype": doctype,
            "parent": docname or "",
            "parentfield": "notes",
            "owner": frappe.session.user,
            "added_by": frappe.session.user,
            "added_on": added_on,
            "custom_parent_note": parent_note,
        }
    )
    if attachments:
        new_note.set(
            "custom_note_attachments",
            [
                {"filename": file} if isinstance(file, str) else file
                for file in attachments
            ],
        )
    new_note.insert()
    notify_mentions_ncrm(note, new_note.name, docname, doctype)
    # Doctype are fetched using 'get_cached_doc'. hence we need to clear the cache
    # to ensure the new note is reflected in the doc's child table. Without this,
    # the notes sometimes gets deleted when lead is saved during conversion.
    frappe.clear_document_cache(doctype, docname)
    return new_note


def _validate_crm_note(
    reference_doctype, reference_name, parent_note=None, attachments=None
):
    if reference_doctype not in ("Lead", "Opportunity"):
        frappe.throw(_("Invalid reference_doctype"), frappe.ValidationError)

    if not reference_name:
        frappe.throw(_("reference_name is required"), frappe.ValidationError)

    if not frappe.db.exists(reference_doctype, reference_name):
        frappe.throw(_("Document not found"), frappe.DoesNotExistError)

        # Creating a note should require write access to the referenced doc.
    if not frappe.has_permission(reference_doctype, "write", reference_name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    if not frappe.has_permission("CRM Note", "create"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    if parent_note and not frappe.db.exists("CRM Note", parent_note):
        frappe.throw(_("Parent note not found"), frappe.DoesNotExistError)

    if attachments is not None:
        if not isinstance(attachments, (list, tuple)):
            frappe.throw(_("attachments must be a list"), frappe.ValidationError)

        for file in attachments:
            if isinstance(file, str):
                continue
            if isinstance(file, dict) and file.get("filename"):
                continue
            frappe.throw(_("Invalid attachment format"), frappe.ValidationError)


@frappe.whitelist()
def log_note(
    reference_doctype,
    reference_name,
    note=None,
    title=None,
    attachments=None,
    added_on=None,
    parent_note=None,
):
    """Log a CRM Note linked to a Lead or Opportunity."""

    _validate_crm_note(reference_doctype, reference_name, parent_note, attachments)

    return create_note(
        doctype=reference_doctype,
        docname=reference_name,
        title=title,
        note=note,
        parent_note=parent_note,
        attachments=attachments,
        added_on=added_on,
    )


@frappe.whitelist()
def update_note(doctype, docname, note_name, note=None, attachments=None):
    """
    Update a CRM Note.
    """
    if not note.get("custom_title") and not note.get("note"):
        raise frappe.ValidationError("Either note or title is required.")

    note_doc = frappe.get_doc("CRM Note", note_name)

    note_doc.custom_title = note.get("custom_title")
    note_doc.note = note.get("note")
    if note.get("added_on"):
        note_doc.added_on = note.get("added_on")

    if attachments:
        existing_filenames = {row.filename for row in note_doc.custom_note_attachments}

        for file in attachments:
            if isinstance(file, str):
                filename = file
                attachment_row = {"filename": filename}
            elif isinstance(file, dict):
                filename = file.get("filename")
                attachment_row = file
            else:
                continue

            if filename and filename not in existing_filenames:
                note_doc.append("custom_note_attachments", attachment_row)

    note_doc.save()

    notify_mentions_ncrm(note.get("note"), note_name, docname, doctype)

    return note_doc


def notify_mentions_ncrm(note, note_name, docname, doctype):
    from frappe.desk.notifications import extract_mentions

    mentions = set(extract_mentions(note))

    if not mentions:
        return

    for mention in mentions:
        owner = frappe.get_cached_value("User", frappe.session.user, "full_name")
        title = frappe.db.get_value(doctype, {"name": docname}, "title")
        name = title or docname or None
        notification_text = f"""
        <div class="mb-2 leading-5 text-ink-gray-5">
            <span class="font-medium text-ink-gray-9">{owner}</span>
            <span>{_("mentioned you in a Note in {0}").format(doctype)}</span>
            <span class="font-medium text-ink-gray-9">{name}</span>
        </div>
        """
        notify_user(
            {
                "owner": frappe.session.user,
                "assigned_to": mention,
                "notification_type": "Mention",
                "message": note,
                "notification_text": notification_text,
                "reference_doctype": "CRM Note",
                "reference_docname": note_name,
                "redirect_to_doctype": doctype,
                "redirect_to_docname": docname,
            }
        )

    email_notification_message = _(
        """[Next CRM] {0} mentioned you in a Note in {1} {2}"""
    ).format(frappe.bold(owner), frappe.bold(doctype), get_title_html(title))

    recipients = [
        frappe.db.get_value(
            "User",
            {
                "enabled": 1,
                "name": name,
                "user_type": "System User",
                "allowed_in_mentions": 1,
            },
            "email",
        )
        for name in mentions
    ]

    notification_doc = {
        "type": "Mention",
        "document_type": doctype,
        "document_name": docname,
        "subject": email_notification_message,
        "from_user": frappe.session.user,
        "email_content": note,
    }

    enqueue_create_notification(recipients, notification_doc)


@frappe.whitelist()
def delete_note(note_name):
    """
    Delete CRM Note.
    """
    note = frappe.get_doc("CRM Note", note_name)
    if not note:
        raise frappe.ValidationError(_("Note not found."))

    filenames_to_delete = [row.filename for row in note.custom_note_attachments]

    parent_note = note.custom_parent_note
    if not parent_note:
        child_notes = frappe.get_all(
            "CRM Note",
            filters={"custom_parent_note": note_name},
            fields=["name"],
            pluck="name",
        )
        for child_note in child_notes:
            child_note_doc = frappe.get_doc("CRM Note", child_note)
            child_filenames = [
                row.filename for row in child_note_doc.custom_note_attachments
            ]
            filenames_to_delete.extend(child_filenames)
            frappe.db.delete("CRM Notification", {"notification_type_doc": child_note})
            frappe.delete_doc("CRM Note", child_note)

    frappe.db.delete("CRM Notification", {"notification_type_doc": note_name})
    note.delete()
    for filename in filenames_to_delete:
        try:
            frappe.delete_doc("File", filename)
        except frappe.DoesNotExistError:
            pass

    return True


def copy_crm_notes_to_opportunity(lead, opportunity):
    notes = frappe.get_all(
        "CRM Note",
        fields="*",
        filters={
            "parent": lead,
            "parenttype": "Lead",
            "custom_parent_note": ["in", ["", None]],
        },
        order_by="creation asc",
    )

    for note in notes:
        new_parent_note = frappe.new_doc("CRM Note")
        new_parent_note.custom_title = note.custom_title or ""
        new_parent_note.note = note.note or ""
        new_parent_note.parenttype = "Opportunity"
        new_parent_note.parent = opportunity
        new_parent_note.parentfield = "notes"
        new_parent_note.added_by = note.added_by
        new_parent_note.added_on = note.added_on or now()

        new_parent_note.insert()
        attachments = frappe.get_all(
            "NCRM Attachments",
            filters={"parent": note.name, "parenttype": "CRM Note"},
            fields=["filename"],
        )
        for row in attachments:
            new_file_name = duplicate_file(
                row.filename,
                new_attached_to_doctype="Opportunity",
                new_attached_to_name=opportunity,
            )
            if new_file_name:
                new_parent_note.append(
                    "custom_note_attachments",
                    {
                        "filename": new_file_name,
                    },
                )

        if attachments:
            new_parent_note.save()

        frappe.db.set_value(
            "CRM Note",
            new_parent_note.name,
            {
                "owner": note.owner,
            },
        )

        child_notes = frappe.get_all(
            "CRM Note",
            filters={"custom_parent_note": note.name},
            fields="*",
        )

        for child_note in child_notes:
            new_child_note = frappe.new_doc("CRM Note")
            new_child_note.custom_title = child_note.custom_title or ""
            new_child_note.note = child_note.note or ""
            new_child_note.parenttype = "Opportunity"
            new_child_note.parent = opportunity
            new_child_note.parentfield = "notes"
            new_child_note.added_by = child_note.added_by
            new_child_note.added_on = child_note.added_on or now()
            new_child_note.custom_parent_note = new_parent_note.name

            new_child_note.insert()
            child_attachments = frappe.get_all(
                "NCRM Attachments",
                filters={"parent": child_note.name, "parenttype": "CRM Note"},
                fields=["filename"],
            )

            for row in child_attachments:
                new_file_name = duplicate_file(
                    row.filename,
                    new_attached_to_doctype="Opportunity",
                    new_attached_to_name=opportunity,
                )
                if new_file_name:
                    new_child_note.append(
                        "custom_note_attachments",
                        {
                            "filename": new_file_name,
                        },
                    )

            if child_attachments:
                new_child_note.save()

            frappe.db.set_value(
                "CRM Note",
                new_child_note.name,
                {
                    "owner": child_note.owner,
                },
            )
    frappe.db.commit()


def duplicate_file(
    original_file_name, new_attached_to_doctype=None, new_attached_to_name=None
):
    """
    Create a duplicate of a file with new attachment references.
    Returns the name of the new file document.
    """
    try:
        original_file = frappe.get_doc("File", original_file_name)
        new_file = frappe.new_doc("File")

        new_file.file_name = original_file.file_name or ""
        new_file.attached_to_doctype = new_attached_to_doctype
        new_file.attached_to_name = new_attached_to_name
        new_file.is_private = original_file.is_private or 0
        new_file.folder = original_file.folder or "Home"

        original_file_url = original_file.file_url
        if original_file_url:
            try:
                file_content = original_file.get_content()
                if file_content:
                    new_file.content = file_content
                    new_file.file_size = len(file_content)
                else:
                    new_file.file_size = original_file.file_size or 0
            except Exception:
                new_file.file_size = original_file.file_size or 0
        else:
            new_file.file_size = original_file.file_size or 0

        new_file.flags.ignore_permissions = True
        new_file.insert()

        if hasattr(new_file, "save_file") and original_file_url:
            try:
                file_content = original_file.get_content()
                if file_content:
                    new_file.save_file(file_content, original_file.file_name or "")
            except Exception:
                pass

        return new_file.name

    except Exception as e:
        frappe.log_error(
            f"Error duplicating file {original_file_name}: {str(e)}",
            "File Duplication Error",
        )
        return None


@frappe.whitelist()
def delete_note_attachments(file_name, note_name=None):
    """
    Deletes a file from the 'NCRM Attachments' child table of a CRM Note
    and deletes the file from the File doctype.
    """
    if not file_name:
        raise frappe.ValidationError("File name is required.")

    if note_name:
        note_doc = frappe.get_doc("CRM Note", note_name)
        removed = False

        new_attachments = []
        for row in note_doc.custom_note_attachments:
            if row.filename == file_name:
                removed = True
                continue
            new_attachments.append(row)

        if not removed:
            frappe.throw("Attachment not found in CRM Note.")

        note_doc.set("custom_note_attachments", new_attachments)
        note_doc.save()

    try:
        frappe.delete_doc("File", file_name)
    except frappe.DoesNotExistError:
        pass

    return {"status": "success", "message": "Attachment deleted successfully."}
