import json

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.desk.form.load import get_docinfo


@frappe.whitelist()
def get_activities(name):
    if frappe.db.exists("Opportunity", name):
        return get_opportunity_activities(name)
    elif frappe.db.exists("Lead", name):
        return get_lead_activities(name)
    else:
        frappe.throw(_("Document not found"), frappe.DoesNotExistError)


def get_opportunity_activities(name):
    get_docinfo("", "Opportunity", name)
    docinfo = frappe.response["docinfo"]
    opportunity_meta = frappe.get_meta("Opportunity")
    opportunity_fields = {
        field.fieldname: {"label": field.label, "options": field.options}
        for field in opportunity_meta.fields
    }
    avoid_fields = [
        "party_name",
        "lead",
        "response_by",
        "sla_creation",
        "sla",
        "first_response_time",
        "first_responded_on",
    ]

    doc = frappe.db.get_values(
        "Opportunity", name, ["creation", "owner", "opportunity_from", "party_name"]
    )[0]
    opportunity_from = doc[2]

    activities = []
    calls = []
    todos = []
    events = []
    attachments = []
    creation_text = "created this opportunity"

    if opportunity_from == "Lead":
        lead = doc[3]
        activities, calls, _notes, todos, events, attachments, _opportunities = (
            get_lead_activities(lead, False, True)
        )

        creation_text = "converted the lead to this opportunity"

    activities.append(
        {
            "activity_type": "creation",
            "creation": doc[0],
            "owner": doc[1],
            "data": creation_text,
            "is_lead": False,
        }
    )

    docinfo.versions.reverse()

    for version in docinfo.versions:
        data = json.loads(version.data)
        if not data.get("changed"):
            continue

        if change := data.get("changed")[0]:
            field = opportunity_fields.get(change[0], None)

            if (
                not field
                or change[0] in avoid_fields
                or (not change[1] and not change[2])
            ):
                continue

            field_label = field.get("label") or change[0]
            field_option = field.get("options") or None

            activity_type = "changed"
            data = {
                "field": change[0],
                "field_label": field_label,
                "old_value": change[1],
                "value": change[2],
            }

            if not change[1] and change[2]:
                activity_type = "added"
                data = {
                    "field": change[0],
                    "field_label": field_label,
                    "value": change[2],
                }
            elif change[1] and not change[2]:
                activity_type = "removed"
                data = {
                    "field": change[0],
                    "field_label": field_label,
                    "value": change[1],
                }

        activity = {
            "activity_type": activity_type,
            "creation": version.creation,
            "owner": version.owner,
            "data": data,
            "is_lead": False,
            "options": field_option,
        }
        activities.append(activity)

    for comment in docinfo.comments:
        activity = {
            "name": comment.name,
            "activity_type": "comment",
            "creation": comment.creation,
            "owner": comment.owner,
            "content": comment.content,
            "attachments": get_attachments("Comment", comment.name),
            "is_lead": False,
        }
        activities.append(activity)

    for info_log in docinfo.info_logs:
        activity = {
            "name": info_log.name,
            "activity_type": "comment",
            "creation": info_log.creation,
            "owner": info_log.owner,
            "content": info_log.content,
            "attachments": get_attachments("Comment", info_log.name),
            "is_lead": False,
        }
        activities.append(activity)

    for communication in docinfo.communications + docinfo.automated_messages:
        activity = {
            "activity_type": "communication",
            "communication_type": communication.communication_type,
            "creation": communication.creation,
            "data": {
                "subject": communication.subject,
                "content": communication.content,
                "sender_full_name": communication.sender_full_name,
                "sender": communication.sender,
                "recipients": communication.recipients,
                "cc": communication.cc,
                "bcc": communication.bcc,
                "attachments": get_attachments("Communication", communication.name),
                "read_by_recipient": communication.read_by_recipient,
                "delivery_status": communication.delivery_status,
            },
            "is_lead": False,
        }
        activities.append(activity)

    if "frappe_gmail_thread" in frappe.get_installed_apps():
        from frappe_gmail_thread.api.activity import get_linked_gmail_threads

        threads = get_linked_gmail_threads("Opportunity", name)

        for thread in threads:
            activity = {
                "activity_type": "communication",
                "communication_type": "Email",
                "creation": thread["template_data"]["doc"]["creation"],
                "data": {
                    "subject": thread["template_data"]["doc"]["subject"],
                    "content": thread["template_data"]["doc"]["content"],
                    "sender_full_name": thread["template_data"]["doc"][
                        "sender_full_name"
                    ],
                    "sender": thread["template_data"]["doc"]["sender"],
                    "recipients": thread["template_data"]["doc"]["recipients"],
                    "cc": thread["template_data"]["doc"]["cc"],
                    "bcc": thread["template_data"]["doc"]["bcc"],
                    "attachments": thread["template_data"]["doc"]["attachments"],
                    "read_by_recipient": thread["template_data"]["doc"][
                        "read_by_recipient"
                    ],
                    "delivery_status": thread["template_data"]["doc"][
                        "delivery_status"
                    ],
                },
                "is_lead": False,
            }
            activities.append(activity)

    for attachment_log in docinfo.attachment_logs:
        activity = {
            "name": attachment_log.name,
            "activity_type": "attachment_log",
            "creation": attachment_log.creation,
            "owner": attachment_log.owner,
            "data": parse_attachment_log(
                attachment_log.content, attachment_log.comment_type
            ),
            "is_lead": False,
        }
        activities.append(activity)

    calls = calls + get_linked_calls(name)
    notes = get_linked_notes(name)["root_notes"]
    todos = todos + get_linked_todos(name)
    events = events + get_linked_events(name)
    attachments = attachments + get_attachments("Opportunity", name)

    activities.sort(key=lambda x: x["creation"], reverse=True)
    activities = handle_multiple_versions(activities)
    notes.sort(key=lambda x: x["added_on"], reverse=True)

    return activities, calls, notes, todos, events, attachments, []


def get_lead_activities(name, get_events=True, exclude_crm_note_attachments=False):
    get_docinfo("", "Lead", name)
    docinfo = frappe.response["docinfo"]
    lead_meta = frappe.get_meta("Lead")
    lead_fields = {
        field.fieldname: {"label": field.label, "options": field.options}
        for field in lead_meta.fields
    }
    avoid_fields = [
        "converted",
        "response_by",
        "sla_creation",
        "sla",
        "first_response_time",
        "first_responded_on",
    ]

    doc = frappe.db.get_values("Lead", name, ["creation", "owner"])[0]
    activities = [
        {
            "activity_type": "creation",
            "creation": doc[0],
            "owner": doc[1],
            "data": "created this lead",
            "is_lead": True,
        }
    ]

    docinfo.versions.reverse()

    for version in docinfo.versions:
        data = json.loads(version.data)
        if not data.get("changed"):
            continue

        if change := data.get("changed")[0]:
            field = lead_fields.get(change[0], None)

            if (
                not field
                or change[0] in avoid_fields
                or (not change[1] and not change[2])
            ):
                continue

            field_label = field.get("label") or change[0]
            field_option = field.get("options") or None

            activity_type = "changed"
            data = {
                "field": change[0],
                "field_label": field_label,
                "old_value": change[1],
                "value": change[2],
            }

            if not change[1] and change[2]:
                activity_type = "added"
                data = {
                    "field": change[0],
                    "field_label": field_label,
                    "value": change[2],
                }
            elif change[1] and not change[2]:
                activity_type = "removed"
                data = {
                    "field": change[0],
                    "field_label": field_label,
                    "value": change[1],
                }

        activity = {
            "activity_type": activity_type,
            "creation": version.creation,
            "owner": version.owner,
            "data": data,
            "is_lead": True,
            "options": field_option,
        }
        activities.append(activity)

    for comment in docinfo.comments:
        activity = {
            "name": comment.name,
            "activity_type": "comment",
            "creation": comment.creation,
            "owner": comment.owner,
            "content": comment.content,
            "attachments": get_attachments("Comment", comment.name),
            "is_lead": True,
        }
        activities.append(activity)

    for communication in docinfo.communications + docinfo.automated_messages:
        if communication.get("communication_medium") == "Event" and not get_events:
            continue
        activity = {
            "activity_type": "communication",
            "communication_type": communication.communication_type,
            "creation": communication.creation,
            "data": {
                "subject": communication.subject,
                "content": communication.content,
                "sender_full_name": communication.sender_full_name,
                "sender": communication.sender,
                "recipients": communication.recipients,
                "cc": communication.cc,
                "bcc": communication.bcc,
                "attachments": get_attachments("Communication", communication.name),
                "read_by_recipient": communication.read_by_recipient,
                "delivery_status": communication.delivery_status,
            },
            "is_lead": True,
        }
        activities.append(activity)

    if "frappe_gmail_thread" in frappe.get_installed_apps():
        from frappe_gmail_thread.api.activity import get_linked_gmail_threads

        threads = get_linked_gmail_threads("Lead", name)

        for thread in threads:
            activity = {
                "activity_type": "communication",
                "communication_type": "Email",
                "creation": thread["template_data"]["doc"]["creation"],
                "data": {
                    "subject": thread["template_data"]["doc"]["subject"],
                    "content": thread["template_data"]["doc"]["content"],
                    "sender_full_name": thread["template_data"]["doc"][
                        "sender_full_name"
                    ],
                    "sender": thread["template_data"]["doc"]["sender"],
                    "recipients": thread["template_data"]["doc"]["recipients"],
                    "cc": thread["template_data"]["doc"]["cc"],
                    "bcc": thread["template_data"]["doc"]["bcc"],
                    "attachments": thread["template_data"]["doc"]["attachments"],
                    "read_by_recipient": thread["template_data"]["doc"][
                        "read_by_recipient"
                    ],
                    "delivery_status": thread["template_data"]["doc"][
                        "delivery_status"
                    ],
                },
                "is_lead": True,
            }
            activities.append(activity)

    for attachment_log in docinfo.attachment_logs:
        activity = {
            "name": attachment_log.name,
            "activity_type": "attachment_log",
            "creation": attachment_log.creation,
            "owner": attachment_log.owner,
            "data": parse_attachment_log(
                attachment_log.content, attachment_log.comment_type
            ),
            "is_lead": True,
        }
        activities.append(activity)

    calls = get_linked_calls(name)
    linked_notes = get_linked_notes(name)
    notes = linked_notes["root_notes"]
    todos = get_linked_todos(name)
    events = get_linked_events(name)
    attachments = get_attachments("Lead", name)
    opportunities = get_linked_opportunities("Lead", name)

    if exclude_crm_note_attachments:
        filenames_to_exclude = linked_notes["attached_file_names"]
        attachments = [a for a in attachments if a.name not in filenames_to_exclude]

    activities.sort(key=lambda x: x["creation"], reverse=True)
    activities = handle_multiple_versions(activities)
    notes.sort(key=lambda x: x["added_on"], reverse=True)

    return activities, calls, notes, todos, events, attachments, opportunities


def get_attachments(doctype, name):
    return (
        frappe.db.get_all(
            "File",
            filters={"attached_to_doctype": doctype, "attached_to_name": name},
            fields=[
                "name",
                "file_name",
                "file_type",
                "file_url",
                "file_size",
                "is_private",
                "creation",
                "owner",
            ],
        )
        or []
    )


def handle_multiple_versions(versions):
    activities = []
    grouped_versions = []
    old_version = None
    for version in versions:
        is_version = version["activity_type"] in ["changed", "added", "removed"]
        if not is_version:
            activities.append(version)
        if not old_version:
            old_version = version
            if is_version:
                grouped_versions.append(version)
            continue
        if (
            is_version
            and old_version.get("owner")
            and version["owner"] == old_version["owner"]
        ):
            grouped_versions.append(version)
        else:
            if grouped_versions:
                activities.append(parse_grouped_versions(grouped_versions))
            grouped_versions = []
            if is_version:
                grouped_versions.append(version)
        old_version = version
        if version == versions[-1] and grouped_versions:
            activities.append(parse_grouped_versions(grouped_versions))

    return activities


def parse_grouped_versions(versions):
    version = versions[0]
    if len(versions) == 1:
        return version
    other_versions = versions[1:]
    version["other_versions"] = other_versions
    return version


def get_linked_calls(name):
    calls = frappe.db.get_all(
        "CRM Call Log",
        filters={"reference_docname": name},
        fields=[
            "name",
            "caller",
            "receiver",
            "from",
            "to",
            "duration",
            "start_time",
            "end_time",
            "status",
            "type",
            "recording_url",
            "creation",
            "note",
        ],
    )
    return calls or []


def get_linked_notes(name):
    notes = frappe.db.get_all(
        "CRM Note",
        filters={"parent": name},
        fields=[
            "name",
            "custom_title",
            "note",
            "owner",
            "added_on",
            "custom_parent_note",
        ],
        order_by="added_on desc",
    )

    if not notes:
        return {"root_notes": [], "attached_file_names": []}

    note_map = {
        str(note["name"]).strip(): {**note, "noteReplies": [], "attachments": []}
        for note in notes
    }

    note_names = [note["name"] for note in notes]
    attachments = frappe.get_all(
        "NCRM Attachments",
        filters={"parent": ["in", note_names], "parenttype": "CRM Note"},
        fields=["parent", "filename"],
    )
    attached_file_names = []

    for attachment in attachments:
        attached_file_names.append(attachment["filename"])
        parent = attachment["parent"]
        if parent in note_map:
            note_map[parent]["attachments"].append(attachment)

    root_notes = []

    for note in notes:
        note_id = str(note["name"]).strip()
        parent_note_id = str(note.get("custom_parent_note") or "").strip()

        if parent_note_id and parent_note_id in note_map:
            note_map[parent_note_id]["noteReplies"].insert(0, note_map[note_id])
        else:
            root_notes.append(note_map[note_id])

    return {"root_notes": root_notes, "attached_file_names": attached_file_names}


def get_linked_todos(name):
    meta = frappe.get_meta("ToDo")
    fields = [
        "name",
        "custom_title",
        "description",
        "allocated_to",
        "date",
        "priority",
        "status",
        "modified",
    ]
    if meta.has_field("custom_from_time"):
        fields.append("custom_from_time")
    if meta.has_field("custom_to_time"):
        fields.append("custom_to_time")
    if meta.has_field("custom_linked_event"):
        fields.append("custom_linked_event")

    todos = frappe.db.get_list(
        "ToDo",
        filters={"reference_name": name},
        fields=fields,
    )

    for todo in todos:
        if todo.get("custom_linked_event", None):
            event = frappe.db.get_value(
                "Event",
                todo["custom_linked_event"],
                ["name", "sync_with_google_calendar", "google_calendar"],
            )
            if not event:
                continue
            todo["_event"] = {
                "name": event[0],
                "sync_with_google_calendar": event[1],
                "google_calendar": event[2],
            }
            event_participants = frappe.db.get_all(
                "Event Participants",
                filters={"parent": todo["_event"]["name"]},
                fields=["reference_doctype", "reference_docname", "email"],
            )
            event_participants = [
                {
                    "reference_doctype": participant["reference_doctype"],
                    "reference_docname": participant["reference_docname"],
                    "email": participant["email"],
                }
                for participant in event_participants
            ]
            todo["_event"]["event_participants"] = event_participants
        else:
            todo["_event"] = None

    return todos or []


def get_linked_events(name):
    events = frappe.db.get_list(
        "Event",
        filters=[["Event Participants", "reference_docname", "=", name]],
        fields=[
            "name",
            "subject",
            "description",
            "_assign",
            "starts_on",
            "ends_on",
            "event_category",
            "sync_with_google_calendar",
            "google_calendar",
            "status",
            "event_type",
            "modified",
        ],
    )

    for event in events:
        event["event_participants"] = frappe.db.get_all(
            "Event Participants",
            filters={"parent": event.name},
            fields=["reference_doctype", "reference_docname", "email"],
        )

    return events or []


def get_linked_opportunities(doctype, name):
    opportunities = frappe.get_all(
        "Opportunity",
        filters={"opportunity_from": doctype, "party_name": name},
        fields=[
            "name",
            "title",
            "status",
            "opportunity_owner",
            "modified",
            "creation",
        ],
    )

    return opportunities


def parse_attachment_log(html, type):
    soup = BeautifulSoup(html, "html.parser")
    a_tag = soup.find("a")
    type = "added" if type == "Attachment" else "removed"
    if not a_tag:
        return {
            "type": type,
            "file_name": html.replace("Removed ", ""),
            "file_url": "",
            "is_private": False,
        }

    is_private = False
    if "private/files" in a_tag["href"]:
        is_private = True

    return {
        "type": type,
        "file_name": a_tag.text,
        "file_url": a_tag["href"],
        "is_private": is_private,
    }


@frappe.whitelist()
def delete_attachment(filename, doctype=None, docname=None):
    """
    Delete a file attachment by its File.name. If doctype & docname are provided,
    also remove its reference from CRM Notes' custom_note_attachments child_table.

    Args:
        filename (str): File Doc's `name` (not file_url or file_name)
        doctype (str, optional): Parent DocType like "Opportunity"
        docname (str, optional): Parent docname like "OPTY-0001"
    """
    deleted = False

    if doctype and docname:
        # Find notes that have this attachment directly
        notes_with_attachment = frappe.get_all(
            "NCRM Attachments",
            filters={"filename": filename},
            fields=["parent"],
            pluck="parent",
        )

        if notes_with_attachment:
            # Filter to notes belonging to this document
            notes_to_update = frappe.get_all(
                "CRM Note",
                filters={
                    "name": ["in", notes_with_attachment],
                    "parenttype": doctype,
                    "parent": docname,
                },
                fields=["name"],
                pluck="name",
            )

            if notes_to_update:
                # Delete all matching attachment rows in a single operation
                frappe.db.delete(
                    "NCRM Attachments",
                    {"parent": ["in", notes_to_update], "filename": filename}
                )
                deleted = True

    try:
        frappe.delete_doc("File", filename)
        deleted = True
    except frappe.DoesNotExistError:
        frappe.throw(_("File with ID '{0}' not found.").format(filename))
    except frappe.LinkExistsError:
        frappe.throw(
            _("Cannot delete file because it's still linked with another document.")
        )
    except Exception as e:
        frappe.log_error(f"Failed to delete file: {e}", "Delete Attachment Error")
        frappe.throw(_("An unexpected error occurred while deleting the file."))

    if deleted:
        return {"message": _("File deleted successfully.")}
    else:
        frappe.throw(
            _("File was not deleted. Possibly already removed or not linked correctly.")
        )
