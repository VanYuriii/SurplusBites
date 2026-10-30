from datetime import datetime
from typing import Optional

class DonationTransaction:
    """
    Represents a completed donation transaction.
    """
    def __init__(self, transaction_id: str, listing_id: str, recipient_id: str, driver_id: Optional[str] = None):
        self._transaction_id = transaction_id
        self._listing_id = listing_id
        self._recipient_id = recipient_id
        self._driver_id = driver_id
        self._timestamp = datetime.now()
        self._is_completed = False

    @property
    def driver_id(self) -> Optional[str]:
        return self._driver_id

    def assign_driver(self, driver_id: str) -> None:
        """Assigns a volunteer driver to the transaction."""
        self._driver_id = driver_id
        print(f"Driver {driver_id} assigned to transaction {self._transaction_id}.")

    def generate_tax_receipt(self) -> str:
        """Generates a tax receipt for the transaction."""
        formatted_time = self._timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return (f"--- TAX RECEIPT ---\n"
                f"Transaction ID: {self._transaction_id}\n"
                f"Date: {formatted_time}\n"
                f"Listing ID: {self._listing_id}\n"
                f"Recipient ID: {self._recipient_id}\n"
                f"-------------------")

    def complete_handover(self) -> None:
        """Marks the transaction and handover as complete."""
        self._is_completed = True
        print(f"Handover completed for transaction {self._transaction_id}.")
