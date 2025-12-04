"""
Background worker thread for processing quote creation
Updated to use enhanced data validation
"""
import time
from PyQt5.QtCore import QThread, pyqtSignal

from data_processing import read_csv
from api_client import (
    create_quote,
    create_line_item_group,
    create_line_items_batch,
    create_line_item_single
)


class WorkerThread(QThread):
    """Background thread for creating quotes without blocking the UI"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, csv_path: str, contact_id: str, note: str):
        super().__init__()
        self.csv_path = csv_path
        self.contact_id = contact_id
        self.note = note

    def run(self):
        """Execute the quote creation workflow"""
        try:
            # Ensure signals are working
            self.log_signal.emit("=" * 50)
            self.log_signal.emit("Quote Creation Started")
            self.log_signal.emit("=" * 50 + "\n")

            # 1) Read and validate CSV/XLSX with enhanced processing
            self.log_signal.emit("Reading and validating file...")
            consolidated = read_csv(
                self.csv_path,
                vendor="auto",
                log_callback=self.log_signal.emit
            )

            if not consolidated:
                self.finished_signal.emit(False, "No valid items found in file.")
                return

            # Show what was consolidated
            self.log_signal.emit("Final consolidated items:")
            for item in consolidated:
                size_summary = ", ".join([f"{s['size']}({s['quantity']})" for s in item['sizes']])
                desc = item.get('description', 'No description')
                self.log_signal.emit(f"  → {item['item_num']} - {item['color']}: {size_summary}")
                if desc and desc != 'No description':
                    self.log_signal.emit(f"    ({desc})")
            self.log_signal.emit("")

            # 2) Create quote
            self.log_signal.emit("Creating quote...")
            quote = create_quote(self.contact_id, self.note)
            self.log_signal.emit(f"✓ Quote created: ID={quote['id']}")
            if quote.get('url'):
                self.log_signal.emit(f"  URL: {quote['url']}")
            self.log_signal.emit(f"  Due: {quote.get('customerDueAt')}\n")

            # 3) Create line item group
            self.log_signal.emit("Creating line item group...")
            group = create_line_item_group(quote["id"])
            self.log_signal.emit(f"✓ Line item group created: ID={group.get('id')}\n")

            # 4) Create line items: prefer batch, fallback to single
            self.log_signal.emit("Creating line items...")
            try:
                created = create_line_items_batch(group["id"], consolidated)
                self.log_signal.emit(f"✓ Batch created {len(created)} line items:")
                for c in created:
                    self.log_signal.emit(f"  • {c.get('itemNumber')} - qty={c.get('items')} - {c.get('color')}")
            except Exception as batch_exc:
                self.log_signal.emit(f"⚠ Batch create failed, using single-item creates...")
                self.log_signal.emit(f"  Error: {str(batch_exc)[:100]}...\n")

                created_single = []
                for idx, it in enumerate(consolidated):
                    try:
                        if idx > 0:
                            time.sleep(1)

                        c = create_line_item_single(group["id"], it, position=idx + 1)
                        created_single.append(c)
                        self.log_signal.emit(f"  ✓ {c.get('itemNumber')} - qty={c.get('items')} - {c.get('color')}")
                    except Exception as e:
                        self.log_signal.emit(f"  ✗ ERROR: {it['item_num']}: {str(e)[:100]}")
                        if "429" in str(e) or "rate" in str(e).lower():
                            self.log_signal.emit("  ⏳ Rate limited, waiting 5 seconds...")
                            time.sleep(5)
                            try:
                                c = create_line_item_single(group["id"], it, position=idx + 1)
                                created_single.append(c)
                                self.log_signal.emit(f"  ✓ Retry succeeded: {c.get('itemNumber')}")
                            except Exception as retry_e:
                                self.log_signal.emit(f"  ✗ Retry failed: {str(retry_e)[:100]}")

                self.log_signal.emit(f"\n✓ Created {len(created_single)} items total.")

            self.log_signal.emit("\n" + "=" * 50)
            self.log_signal.emit("✓ FINISHED SUCCESSFULLY!")
            self.log_signal.emit("=" * 50)
            self.finished_signal.emit(True, f"Quote created successfully!\nQuote ID: {quote['id']}")

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.log_signal.emit(f"\n✗ FAILED: {error_msg}")
            self.finished_signal.emit(False, error_msg)