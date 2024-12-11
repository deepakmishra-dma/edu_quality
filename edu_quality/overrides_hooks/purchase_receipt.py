from datetime import datetime
import pytz
import frappe


def before_save(self, method=None):
    old_doc = self.get_doc_before_save()
    if old_doc and old_doc.workflow_state != "Received" and self.workflow_state == "Received":
        utc_now = datetime.now(pytz.UTC)
        ist_now = utc_now.astimezone(pytz.timezone("Asia/Kolkata")).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        self.custom_receiving_date = ist_now
