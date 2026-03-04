from frappe.core.doctype.report.report import Report


class OverrideReport(Report):

    @staticmethod
    def default_list_data():
        columns = [
            {
                "label": "Report Name",
                "type": "Data",
                "key": "report_name",
                "width": "22rem",
            },
            {
                "label": "Doctype",
                "type": "Link",
                "key": "ref_doctype",
                "width": "11rem",
            },
            {
                "label": "Last Modified",
                "type": "Datetime",
                "key": "modified",
                "width": "8rem",
            },
        ]
        rows = [
            "report_name",
            "ref_doctype",
            "modified",
        ]
        return {"columns": columns, "rows": rows}
