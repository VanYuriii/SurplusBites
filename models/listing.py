import datetime
from typing import Optional

class FoodListing:
    """
    Represents a listing of available food for donation.
    Demonstrates Encapsulation.
    """
    def __init__(self, listing_id: str, donor_id: str, items: dict, pickup_window: str, expires_at: Optional[datetime.datetime] = None):
        self._listing_id = listing_id
        self._donor_id = donor_id
        self._items = items
        self._status = "Available"
        self._pickup_window = pickup_window
        self._expires_at = expires_at

    @property
    def listing_id(self) -> str:
        return self._listing_id

    @property
    def donor_id(self) -> str:
        return self._donor_id
        
    @property
    def status(self) -> str:
        return self._status

    @property
    def expires_at(self) -> Optional[datetime.datetime]:
        return self._expires_at

    @property
    def is_expired(self) -> bool:
        if self._expires_at:
            return datetime.datetime.now() > self._expires_at
        return False

    def update_status(self, new_status: str) -> None:
        """Updates the status of the listing."""
        valid_statuses = ["Available", "Pending Confirmation", "Claimed", "Picked Up"]
        if new_status in valid_statuses:
            self._status = new_status
            print(f"Listing {self._listing_id} status updated to: {self._status}")
        else:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")

    def display_details(self) -> str:
        """Returns a formatted string representation of the listing details."""
        details_str = (f"Listing ID: {self._listing_id}\n"
                       f"Donor ID: {self._donor_id}\n"
                       f"Items: {self._items}\n"
                       f"Status: {self._status}\n"
                       f"Pickup Window: {self._pickup_window}")
        return details_str
