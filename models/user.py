from abc import ABC, abstractmethod
from typing import Any

class User(ABC):
    """
    Abstract Base Class representing a platform user.
    Demonstrates Encapsulation and Abstraction.
    """
    def __init__(self, user_id: str, name: str, contact_info: str, address: str, latitude: float = 0.0, longitude: float = 0.0):
        self._user_id = user_id
        self._name = name
        self._contact_info = contact_info
        self._address = address
        self._latitude = latitude
        self._longitude = longitude

    @property
    def latitude(self) -> float:
        return self._latitude

    @property
    def longitude(self) -> float:
        return self._longitude

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def name(self) -> str:
        return self._name

    def login(self) -> bool:
        """Simulates logging in."""
        print(f"User {self._name} logged in.")
        return True

    def logout(self) -> bool:
        """Simulates logging out."""
        print(f"User {self._name} logged out.")
        return True

    @abstractmethod
    def get_dashboard(self) -> str:
        """Abstract method to get user-specific dashboard."""
        pass

    def get_average_rating(self, platform_manager: Any) -> str:
        return platform_manager.get_average_rating(self.user_id)

class Donor(User):
    """
    Represents a food donor on the platform.
    Demonstrates Inheritance and Polymorphism.
    """
    def __init__(self, user_id: str, name: str, contact_info: str, address: str, business_type: str, tax_id: str, latitude: float = 0.0, longitude: float = 0.0):
        super().__init__(user_id, name, contact_info, address, latitude, longitude)
        self._business_type = business_type
        self._tax_id = tax_id

    def create_listing(self, platform_manager: Any, items: dict, pickup_window: str) -> None:
        """Creates a new food listing by interacting with the PlatformManager."""
        platform_manager.add_listing(self.user_id, items, pickup_window)

    def confirm_listing(self, platform_manager: Any, listing_id: str) -> None:
        platform_manager.confirm_listing(listing_id)

    def reject_listing(self, platform_manager: Any, listing_id: str) -> None:
        platform_manager.reject_listing(listing_id)

    def delete_listing(self, platform_manager: Any, listing_id: str) -> None:
        """Deletes a listing created by the donor."""
        platform_manager.delete_listing(listing_id)

    def view_impact_metrics(self) -> str:
        """Returns the impact metrics of the donor."""
        return f"Donor {self.name} impact metrics: 500 meals donated."

    def get_dashboard(self) -> str:
        """Implementation of the abstract get_dashboard method."""
        return f"Donor Dashboard for {self.name} (Type: {self._business_type})"

class Recipient(User):
    """
    Represents a charitable organization receiving food.
    Demonstrates Inheritance and Polymorphism.
    """
    def __init__(self, user_id: str, name: str, contact_info: str, address: str, charity_registration_number: str, capacity: str, latitude: float = 0.0, longitude: float = 0.0):
        super().__init__(user_id, name, contact_info, address, latitude, longitude)
        self._charity_registration_number = charity_registration_number
        self._capacity = capacity

    def update(self, listing: Any) -> None:
        """Observer update method."""
        print(f"Recipient {self.name} notified of new listing {listing.listing_id}!")

    def claim_listing(self, platform_manager: Any, listing_id: str) -> bool:
        """Claims a food listing by interacting with the PlatformManager."""
        return platform_manager.claim_listing(listing_id, self.user_id)

    def cancel_claim(self, platform_manager: Any, listing_id: str) -> None:
        """Cancels a previously claimed listing."""
        platform_manager.cancel_claim(listing_id)

    def assign_driver(self, driver_name: str) -> str:
        """Assigns a driver for pickup."""
        return f"Driver {driver_name} assigned for pickup by {self.name}."

    def get_dashboard(self) -> str:
        """Implementation of the abstract get_dashboard method."""
        return f"Recipient Dashboard for {self.name} (Capacity: {self._capacity})"

class VolunteerDriver(User):
    """
    Represents a volunteer driver who delivers rescued food.
    """
    def __init__(self, user_id: str, name: str, contact_info: str, address: str, vehicle_type: str, max_load_capacity: float, latitude: float = 0.0, longitude: float = 0.0):
        super().__init__(user_id, name, contact_info, address, latitude, longitude)
        self._vehicle_type = vehicle_type
        self._max_load_capacity = max_load_capacity

    @property
    def vehicle_type(self) -> str:
        return self._vehicle_type

    @property
    def max_load_capacity(self) -> float:
        return self._max_load_capacity

    def get_dashboard(self) -> str:
        return f"Driver Dashboard for {self.name} (Vehicle: {self._vehicle_type})"

