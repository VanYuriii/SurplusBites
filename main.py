#!/usr/local/bin/python3.14
import customtkinter as ctk
from tkinter import messagebox
import json
import re

from services.platform_manager import PlatformManager
from models.user import Donor, Recipient

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class RatingDialog(ctk.CTkToplevel):
    def __init__(self, master, ratee_id, listing_id, platform_manager, current_user_id, callback=None):
        super().__init__(master)
        self.title("Rate User")
        self.geometry("300x200")
        self.resizable(False, False)
        
        # Center the dialog
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - 150
        y = master.winfo_y() + (master.winfo_height() // 2) - 100
        self.geometry(f"+{x}+{y}")
        self.transient(master)
        self.grab_set()
        
        self.platform_manager = platform_manager
        self.current_user_id = current_user_id
        self.ratee_id = ratee_id
        self.listing_id = listing_id
        self.callback = callback
        
        ctk.CTkLabel(self, text=f"Rate {ratee_id}", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))
        
        self.rating_var = ctk.StringVar(value="5")
        self.rating_segmented = ctk.CTkSegmentedButton(
            self, values=["1", "2", "3", "4", "5"],
            variable=self.rating_var,
            width=200
        )
        self.rating_segmented.pack(pady=10)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        ctk.CTkButton(btn_frame, text="Cancel", width=80, fg_color="gray", command=self.destroy).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Submit", width=80, command=self._submit).pack(side="left", padx=10)
        
    def _submit(self):
        score = int(self.rating_var.get())
        self.platform_manager.add_rating(self.current_user_id, self.ratee_id, self.listing_id, score)
        messagebox.showinfo("Success", f"Rated {self.ratee_id} with {score} stars!")
        if self.callback:
            self.callback()
        self.destroy()

class WelcomeFrame(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master=master, corner_radius=0)
        self.controller = controller
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Central card for redesign
        card = ctk.CTkFrame(self, fg_color=("gray95", "gray20"), corner_radius=20)
        card.grid(row=0, column=0, padx=40, pady=40, sticky="nsew")
        card.grid_rowconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=0)
        card.grid_rowconfigure(2, weight=0)
        card.grid_rowconfigure(3, weight=0)
        card.grid_rowconfigure(4, weight=1)
        card.grid_columnconfigure(0, weight=1)
        
        # Logo / Title
        ctk.CTkLabel(card, text="SurplusBite", font=ctk.CTkFont(size=48, weight="bold"), text_color="#2ecc71").grid(row=1, column=0, pady=(0, 10))
        ctk.CTkLabel(card, text="Community Food Rescue Platform", font=ctk.CTkFont(size=18), text_color="gray").grid(row=2, column=0, pady=(0, 40))
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=3, column=0)
        
        ctk.CTkButton(btn_frame, text="Login", width=160, height=45, font=ctk.CTkFont(size=16, weight="bold"),
                      command=lambda: controller.switch_frame(LoginFrame)).pack(side="left", padx=15)
        ctk.CTkButton(btn_frame, text="Register", width=160, height=45, font=ctk.CTkFont(size=16, weight="bold"),
                      fg_color="transparent", border_width=2, text_color=("gray10", "gray90"),
                      command=lambda: controller.switch_frame(RegistrationFrame)).pack(side="left", padx=15)

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master=master, corner_radius=0)
        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        form = ctk.CTkFrame(self, corner_radius=15, fg_color=("gray95", "gray20"))
        form.grid(row=1, column=0, padx=20, pady=20, ipadx=20, ipady=20)
        
        ctk.CTkLabel(form, text="Login", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(10, 20))
        
        self.user_id_entry = ctk.CTkEntry(form, placeholder_text="User ID", width=250, height=40)
        self.user_id_entry.pack(pady=10)
        self.password_entry = ctk.CTkEntry(form, placeholder_text="Password", show="*", width=250, height=40)
        self.password_entry.pack(pady=10)
        
        ctk.CTkButton(form, text="Submit", width=250, height=40, font=ctk.CTkFont(weight="bold"), command=self._login).pack(pady=(20, 10))
        ctk.CTkButton(form, text="Back", width=250, height=40, fg_color="transparent", border_width=2, text_color=("gray10", "gray90"),
                      command=lambda: controller.switch_frame(WelcomeFrame)).pack()

    def _login(self):
        user_id = self.user_id_entry.get().strip()
        pwd = self.password_entry.get().strip()
        
        user = self.controller.platform_manager.authenticate(user_id, pwd)
        if user:
            self.controller.current_user = user
            if isinstance(user, Donor):
                self.controller.switch_frame(DonorDashboard)
            else:
                self.controller.switch_frame(RecipientDashboard)
        else:
            messagebox.showerror("Login Failed", "Invalid credentials.")

class RegistrationFrame(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master=master, corner_radius=0)
        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Centered non-scrollable card
        form = ctk.CTkFrame(self, corner_radius=16, fg_color=("gray95", "gray20"))
        form.grid(row=1, column=0, padx=20, pady=20, ipadx=25, ipady=20)
        
        ctk.CTkLabel(form, text="Create an Account", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=(5, 4))
        ctk.CTkLabel(form, text="Join SurplusBite Food Rescue", font=ctk.CTkFont(size=13), text_color="gray").pack(pady=(0, 15))
        
        self.role_var = ctk.StringVar(value="Donor")
        self.role_segmented = ctk.CTkSegmentedButton(
            form, values=["Donor", "Recipient"], variable=self.role_var, width=320, height=34,
            command=self._on_role_change
        )
        self.role_segmented.pack(pady=(0, 15))
        
        # 2-column layout for input fields to eliminate vertical overflow and scrolling
        grid_frame = ctk.CTkFrame(form, fg_color="transparent")
        grid_frame.pack(fill="x", padx=10, pady=5)
        
        # Column 0: User ID, Name, Address
        ctk.CTkLabel(grid_frame, text="User ID", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=10, pady=(2, 2))
        self.id_entry = ctk.CTkEntry(grid_frame, placeholder_text="e.g. green_bakery", width=250, height=36)
        self.id_entry.grid(row=1, column=0, padx=10, pady=(0, 10))
        
        ctk.CTkLabel(grid_frame, text="Organization / Full Name", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(row=2, column=0, sticky="w", padx=10, pady=(2, 2))
        self.name_entry = ctk.CTkEntry(grid_frame, placeholder_text="e.g. Green Bakery", width=250, height=36)
        self.name_entry.grid(row=3, column=0, padx=10, pady=(0, 10))
        
        ctk.CTkLabel(grid_frame, text="Address", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(row=4, column=0, sticky="w", padx=10, pady=(2, 2))
        self.address_entry = ctk.CTkEntry(grid_frame, placeholder_text="e.g. 123 Main Street", width=250, height=36)
        self.address_entry.grid(row=5, column=0, padx=10, pady=(0, 10))

        # Column 1: Password, Contact, Specific ID
        ctk.CTkLabel(grid_frame, text="Password", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(row=0, column=1, sticky="w", padx=10, pady=(2, 2))
        self.pw_entry = ctk.CTkEntry(grid_frame, placeholder_text="••••••••", show="*", width=250, height=36)
        self.pw_entry.grid(row=1, column=1, padx=10, pady=(0, 10))
        
        ctk.CTkLabel(grid_frame, text="Contact Email/Phone", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(row=2, column=1, sticky="w", padx=10, pady=(2, 2))
        self.contact_entry = ctk.CTkEntry(grid_frame, placeholder_text="contact@example.com", width=250, height=36)
        self.contact_entry.grid(row=3, column=1, padx=10, pady=(0, 10))
        
        self.specific_label = ctk.CTkLabel(grid_frame, text="Tax ID (Donor)", font=ctk.CTkFont(size=12, weight="bold"), anchor="w")
        self.specific_label.grid(row=4, column=1, sticky="w", padx=10, pady=(2, 2))
        self.specific_entry = ctk.CTkEntry(grid_frame, placeholder_text="e.g. TAX-12345", width=250, height=36)
        self.specific_entry.grid(row=5, column=1, padx=10, pady=(0, 10))
        
        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(pady=(15, 5))
        
        ctk.CTkButton(btn_frame, text="Submit", width=140, height=38, font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color="#2ecc71", hover_color="#27ae60",
                      command=self._handle_register).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Back", width=140, height=38, font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color="transparent", border_width=2, text_color=("gray10", "gray90"),
                      command=lambda: controller.switch_frame(WelcomeFrame)).pack(side="left", padx=8)

    def _on_role_change(self, value):
        if value == "Donor":
            self.specific_label.configure(text="Tax ID (Donor)")
            self.specific_entry.configure(placeholder_text="e.g. TAX-12345")
        else:
            self.specific_label.configure(text="Charity No (Recipient)")
            self.specific_entry.configure(placeholder_text="e.g. CH-98765")

    def _handle_register(self):
        try:
            role = self.role_var.get()
            user_id = self.id_entry.get().strip()
            pwd = self.pw_entry.get().strip()
            name = self.name_entry.get().strip()
            contact = self.contact_entry.get().strip()
            address = self.address_entry.get().strip()
            specific = self.specific_entry.get().strip()
            
            if not all([user_id, pwd, name, contact, address, specific]):
                messagebox.showwarning("Missing Fields", "All fields are required.")
                return
                
            self.controller.platform_manager.register_user(role, user_id, pwd, name, contact, address, specific)
            messagebox.showinfo("Success", "Registration complete! You can now log in.")
            self.controller.switch_frame(LoginFrame)
        except Exception as e:
            messagebox.showerror("Error", str(e))

class DashboardBase(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master=master, corner_radius=0)
        self.controller = controller
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=1) # Main Content
        
        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=("gray85", "gray17"))
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) # Spacer
        
        # Branding
        ctk.CTkLabel(self.sidebar_frame, text="SurplusBite", font=ctk.CTkFont(size=24, weight="bold"), text_color="#2ecc71").grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # User Info
        self.user = self.controller.current_user
        ctk.CTkLabel(self.sidebar_frame, text=f"Hello, {self.user.name}", font=ctk.CTkFont(size=14)).grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # Main Content Container
        self.main_content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_content_frame.grid_rowconfigure(1, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        
        # Header (Title) in Main Content
        self.content_header = ctk.CTkLabel(self.main_content_frame, text="", font=ctk.CTkFont(size=28, weight="bold"))
        self.content_header.grid(row=0, column=0, sticky="w", pady=(0, 20))
        
        # The frame that holds the actual content of the selected tab
        self.view_container = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.view_container.grid(row=1, column=0, sticky="nsew")
        self.view_container.grid_rowconfigure(0, weight=1)
        self.view_container.grid_columnconfigure(0, weight=1)
        
        # Views dictionary to store different screens
        self.views = {}
        self.current_view = None
        self.sidebar_buttons = []
        
        self.setup_sidebar()
        self.setup_views()
        
        # Bottom of sidebar (Rating & Logout)
        avg_rating = self.user.get_average_rating(self.controller.platform_manager)
        ctk.CTkLabel(self.sidebar_frame, text=f"Rating: {avg_rating}", font=ctk.CTkFont(size=13, weight="bold")).grid(row=6, column=0, padx=20, pady=(10, 5))
        ctk.CTkButton(self.sidebar_frame, text="Logout", fg_color="#d9534f", hover_color="#c9302c",
                      command=self._logout).grid(row=7, column=0, padx=20, pady=(10, 20))

    def setup_sidebar(self):
        pass
        
    def setup_views(self):
        pass

    def add_sidebar_button(self, text, view_name, row):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, fg_color="transparent", text_color=("gray10", "gray90"),
                            hover_color=("gray70", "gray30"), anchor="w",
                            command=lambda: self.show_view(view_name))
        btn.grid(row=row, column=0, padx=20, pady=5, sticky="ew")
        self.sidebar_buttons.append((view_name, btn))

    def show_view(self, view_name):
        if self.current_view is not None:
            self.views[self.current_view].grid_forget()
            
        self.views[view_name].grid(row=0, column=0, sticky="nsew")
        self.current_view = view_name
        self.content_header.configure(text=view_name)
        
        for name, btn in self.sidebar_buttons:
            if name == view_name:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")
                
        self.refresh_data()

    def refresh_data(self):
        pass

    def _logout(self):
        self.controller.current_user.logout()
        self.controller.current_user = None
        self.controller.switch_frame(WelcomeFrame)

    # --- UI Helpers for modern design ---
    def create_status_badge(self, parent, status):
        color = "#2ecc71" if status in ["Available", "Claimed"] else "#f39c12"
        badge = ctk.CTkFrame(parent, fg_color=color, corner_radius=15, height=24)
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=status, font=ctk.CTkFont(size=12, weight="bold"), text_color="white").pack(expand=True, padx=10, pady=2)
        return badge

    def create_pagination_bar(self, parent, current_page, total_items, per_page, on_page_change):
        if total_items <= per_page:
            return
        total_pages = max(1, (total_items + per_page - 1) // per_page)
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", pady=(10, 5))
        
        prev_btn = ctk.CTkButton(
            bar, text="◀ Prev", width=75, height=28,
            state="normal" if current_page > 0 else "disabled",
            fg_color=("gray75", "gray30") if current_page > 0 else ("gray85", "gray20"),
            command=lambda: on_page_change(current_page - 1)
        )
        prev_btn.pack(side="left", padx=5)
        
        ctk.CTkLabel(
            bar, text=f"Page {current_page + 1} of {total_pages} ({total_items} items)",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).pack(side="left", expand=True)
        
        next_btn = ctk.CTkButton(
            bar, text="Next ▶", width=75, height=28,
            state="normal" if current_page < total_pages - 1 else "disabled",
            fg_color=("gray75", "gray30") if current_page < total_pages - 1 else ("gray85", "gray20"),
            command=lambda: on_page_change(current_page + 1)
        )
        next_btn.pack(side="right", padx=5)


class DonorDashboard(DashboardBase):
    def __init__(self, master, controller):
        self.items_dict = {}
        self.active_page = 0
        self.past_page = 0
        self.community_page = 0
        super().__init__(master, controller)
        self.show_view("Dashboard")

    def setup_sidebar(self):
        self.add_sidebar_button("Dashboard", "Dashboard", 2)
        self.add_sidebar_button("Create Listing", "Create Listing", 3)
        self.add_sidebar_button("Community Listings", "Community Listings", 4)

    def setup_views(self):
        # 1. Dashboard View (My Listings + Past Listings + Metrics)
        view_dash = ctk.CTkFrame(self.view_container, fg_color="transparent")
        view_dash.grid_rowconfigure(1, weight=1)
        view_dash.grid_columnconfigure(0, weight=1)
        view_dash.grid_columnconfigure(1, weight=1)
        
        # Top Metrics
        metrics_frame = ctk.CTkFrame(view_dash, fg_color="transparent")
        metrics_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        metrics_frame.grid_columnconfigure(0, weight=1)
        
        self.metric_card = ctk.CTkFrame(metrics_frame, fg_color=("gray90", "gray20"), corner_radius=12)
        self.metric_card.grid(row=0, column=0, sticky="ew")
        
        self.metric_value = ctk.CTkLabel(self.metric_card, text="0", font=ctk.CTkFont(size=48, weight="bold"))
        self.metric_value.pack(pady=(20, 0))
        ctk.CTkLabel(self.metric_card, text="Total Items Donated", font=ctk.CTkFont(size=16), text_color="gray").pack(pady=(0, 20))
        
        # Splits: Active Listings and Past Listings
        left_col = ctk.CTkFrame(view_dash, fg_color="transparent")
        left_col.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_col.grid_rowconfigure(1, weight=1)
        left_col.grid_columnconfigure(0, weight=1)
        
        right_col = ctk.CTkFrame(view_dash, fg_color="transparent")
        right_col.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        right_col.grid_rowconfigure(1, weight=1)
        right_col.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(left_col, text="Active Listings", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.active_scroll = ctk.CTkFrame(left_col, fg_color="transparent")
        self.active_scroll.grid(row=1, column=0, sticky="nsew")
        
        ctk.CTkLabel(right_col, text="Past Listings", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.past_scroll = ctk.CTkFrame(right_col, fg_color="transparent")
        self.past_scroll.grid(row=1, column=0, sticky="nsew")
        
        self.views["Dashboard"] = view_dash

        # 2. Create Listing View
        view_create = ctk.CTkFrame(self.view_container, fg_color="transparent")
        view_create.grid_rowconfigure(1, weight=1)
        view_create.grid_columnconfigure(0, weight=1)
        
        card_create = ctk.CTkFrame(view_create, fg_color=("gray95", "gray25"), corner_radius=12)
        card_create.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        input_row = ctk.CTkFrame(card_create, fg_color="transparent")
        input_row.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(input_row, text="Item Name:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))
        self.item_name_entry = ctk.CTkEntry(input_row, width=150)
        self.item_name_entry.pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(input_row, text="Qty:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))
        self.quantity_entry = ctk.CTkEntry(input_row, width=70)
        self.quantity_entry.pack(side="left", padx=(0, 20))
        
        ctk.CTkButton(input_row, text="Add Item", width=100, command=self._add_item).pack(side="left")
        
        self.cart_scroll = ctk.CTkFrame(card_create, fg_color="transparent")
        self.cart_scroll.pack(fill="x", padx=20, pady=(0, 10))
        
        bottom_row = ctk.CTkFrame(card_create, fg_color="transparent")
        bottom_row.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(bottom_row, text="Pickup Time:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))
        self.window_var = ctk.StringVar(value="8AM - 10AM")
        ctk.CTkComboBox(bottom_row, values=["8AM - 10AM", "10AM - 12PM", "12PM - 2PM", "2PM - 4PM", "4PM - 6PM"], 
                        variable=self.window_var, width=130).pack(side="left", padx=(0, 20))
                        
        ctk.CTkButton(bottom_row, text="Submit Listing", fg_color="#5cb85c", hover_color="#4cae4c",
                      command=self._submit_listing).pack(side="right")
                      
        self.views["Create Listing"] = view_create
        self._update_cart()
        
        # 3. Community Listings View
        view_community = ctk.CTkFrame(self.view_container, fg_color="transparent")
        view_community.grid_rowconfigure(0, weight=1)
        view_community.grid_columnconfigure(0, weight=1)
        self.community_scroll = ctk.CTkFrame(view_community, fg_color="transparent")
        self.community_scroll.grid(row=0, column=0, sticky="nsew")
        self.views["Community Listings"] = view_community

    def _add_item(self):
        name = self.item_name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing Item", "Please enter an item name.")
            return
            
        qty_str = self.quantity_entry.get().strip()
        try:
            qty = int(qty_str)
            if qty < 1 or qty > 30:
                messagebox.showwarning("Invalid Quantity", "Quantity must be between 1 and 30.")
                return
        except ValueError:
            messagebox.showwarning("Invalid Quantity", "Please enter a valid number for quantity.")
            return
            
        if name in self.items_dict:
            self.items_dict[name] += qty
        else:
            self.items_dict[name] = qty
            
        self.item_name_entry.delete(0, "end")
        self.quantity_entry.delete(0, "end")
        self._update_cart()
        
    def _remove_item(self, item_name):
        if item_name in self.items_dict:
            del self.items_dict[item_name]
            self._update_cart()

    def _update_cart(self):
        for widget in self.cart_scroll.winfo_children():
            widget.destroy()
            
        if not self.items_dict:
            ctk.CTkLabel(self.cart_scroll, text="No items added yet.", text_color="gray").pack(pady=20)
            return
            
        for item_name, qty in self.items_dict.items():
            row = ctk.CTkFrame(self.cart_scroll, fg_color=("gray85", "gray30"), corner_radius=6)
            row.pack(fill="x", pady=4, padx=5)
            ctk.CTkLabel(row, text=f"{item_name}", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(row, text=f"Qty: {qty}").pack(side="left", padx=10, pady=5)
            ctk.CTkButton(row, text="✖", width=30, fg_color="#d9534f", hover_color="#c9302c",
                          command=lambda n=item_name: self._remove_item(n)).pack(side="right", padx=10)

    def _submit_listing(self):
        if not self.items_dict:
            messagebox.showwarning("Empty", "Cannot submit an empty listing.")
            return
            
        window = self.window_var.get()
        try:
            self.controller.current_user.create_listing(self.controller.platform_manager, self.items_dict.copy(), window)
            messagebox.showinfo("Success", "Listing created successfully!")
            self.items_dict.clear()
            self._update_cart()
            self.window_var.set("8AM - 10AM")
            self.show_view("Dashboard")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def create_listing_card(self, parent, listing_data, is_community=False):
        card = ctk.CTkFrame(parent, fg_color=("gray95", "gray22"), corner_radius=12)
        card.pack(fill="x", pady=10, padx=10)
        
        # Header Row
        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=15, pady=(15, 10))
        
        title = f"Listing {listing_data.listing_id}"
        if is_community:
            title += f"  |  Donor: {listing_data.donor_id}"
            
        ctk.CTkLabel(header_row, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        st = getattr(listing_data, '_status', 'Available')
        badge = self.create_status_badge(header_row, st)
        badge.pack(side="right")
        
        # Body Row
        body_row = ctk.CTkFrame(card, fg_color="transparent")
        body_row.pack(fill="x", padx=15, pady=(0, 15))
        
        items_str = ", ".join(f"{k} (x{v})" for k, v in listing_data._items.items())
        ctk.CTkLabel(body_row, text=f"Items: {items_str}", justify="left", wraplength=350).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(body_row, text=f"Pickup Window: {listing_data._pickup_window}", text_color="gray").pack(anchor="w")

        # Action Buttons
        if not is_community:
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=(0, 15))
            
            if st == "Pending Confirmation":
                ctk.CTkButton(btn_frame, text="Confirm", width=90, height=30, fg_color="#5cb85c", hover_color="#4cae4c",
                              command=lambda l=listing_data.listing_id: self._confirm_listing(l)).pack(side="right", padx=(10, 0))
                ctk.CTkButton(btn_frame, text="Reject", width=90, height=30, fg_color="#f0ad4e", hover_color="#ec971f",
                              command=lambda l=listing_data.listing_id: self._reject_listing(l)).pack(side="right", padx=(10, 0))
            
            if st != "Claimed":
                ctk.CTkButton(btn_frame, text="Delete", width=90, height=30, fg_color="#d9534f", hover_color="#c9302c",
                              command=lambda l=listing_data.listing_id: self._delete_listing(l)).pack(side="right", padx=(10, 0))
            
            if st == "Claimed":
                recipient_id = self.controller.platform_manager.get_listing_recipient(listing_data.listing_id)
                if recipient_id and not self.controller.platform_manager.has_user_rated_listing(self.controller.current_user.user_id, listing_data.listing_id):
                    ctk.CTkButton(btn_frame, text="Rate Recipient", width=120, height=30, fg_color="#f39c12", hover_color="#e67e22",
                                  command=lambda r=recipient_id, l=listing_data.listing_id: self._rate_user(r, l)).pack(side="left")

    def _rate_user(self, ratee_id, listing_id):
        RatingDialog(self, ratee_id, listing_id, self.controller.platform_manager, self.controller.current_user.user_id, callback=self.refresh_data)

    def _confirm_listing(self, listing_id):
        try:
            self.controller.current_user.confirm_listing(self.controller.platform_manager, listing_id)
            messagebox.showinfo("Confirmed", f"Listing {listing_id} confirmed!")
            self.refresh_data()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _reject_listing(self, listing_id):
        try:
            self.controller.current_user.reject_listing(self.controller.platform_manager, listing_id)
            messagebox.showinfo("Rejected", f"Listing {listing_id} rejected and returned to available.")
            self.refresh_data()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete_listing(self, listing_id):
        if messagebox.askyesno("Delete Listing", f"Are you sure you want to delete listing {listing_id}?"):
            try:
                self.controller.current_user.delete_listing(self.controller.platform_manager, listing_id)
                messagebox.showinfo("Deleted", f"Listing {listing_id} deleted successfully.")
                self.refresh_data()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def refresh_data(self):
        if self.current_view == "Dashboard":
            for widget in self.active_scroll.winfo_children():
                widget.destroy()
            for widget in self.past_scroll.winfo_children():
                widget.destroy()
                
            current_user_id = self.controller.current_user.user_id
            my_listings = self.controller.platform_manager.get_donor_listings(current_user_id)
            
            active_listings = [l for l in my_listings if getattr(l, '_status', 'Available') != "Claimed"]
            past_listings = [l for l in my_listings if getattr(l, '_status', 'Available') == "Claimed"]
            
            # Calculate Total Donated Items
            total_items = 0
            for l in past_listings:
                for qty in l._items.values():
                    total_items += qty
            self.metric_value.configure(text=str(total_items))
            
            PER_PAGE = 2
            tot_act = len(active_listings)
            tot_act_pages = max(1, (tot_act + PER_PAGE - 1) // PER_PAGE)
            if self.active_page >= tot_act_pages:
                self.active_page = tot_act_pages - 1
                
            if not active_listings:
                ctk.CTkLabel(self.active_scroll, text="No active listings.", text_color="gray").pack(pady=30)
            else:
                start = self.active_page * PER_PAGE
                for l in active_listings[start:start + PER_PAGE]:
                    self.create_listing_card(self.active_scroll, l, is_community=False)
                self.create_pagination_bar(self.active_scroll, self.active_page, tot_act, PER_PAGE, self._change_active_page)

            tot_past = len(past_listings)
            tot_past_pages = max(1, (tot_past + PER_PAGE - 1) // PER_PAGE)
            if self.past_page >= tot_past_pages:
                self.past_page = tot_past_pages - 1

            if not past_listings:
                ctk.CTkLabel(self.past_scroll, text="No past listings.", text_color="gray").pack(pady=30)
            else:
                start = self.past_page * PER_PAGE
                for l in past_listings[start:start + PER_PAGE]:
                    self.create_listing_card(self.past_scroll, l, is_community=False)
                self.create_pagination_bar(self.past_scroll, self.past_page, tot_past, PER_PAGE, self._change_past_page)
                    
        elif self.current_view == "Community Listings":
            for widget in self.community_scroll.winfo_children():
                widget.destroy()
            current_user_id = self.controller.current_user.user_id
            available_listings = self.controller.platform_manager.get_available_listings()
            community_listings = [l for l in available_listings if l.donor_id != current_user_id]
            
            PER_PAGE = 3
            tot_comm = len(community_listings)
            tot_comm_pages = max(1, (tot_comm + PER_PAGE - 1) // PER_PAGE)
            if self.community_page >= tot_comm_pages:
                self.community_page = tot_comm_pages - 1

            if not community_listings:
                ctk.CTkLabel(self.community_scroll, text="No active community listings.", text_color="gray").pack(pady=30)
            else:
                start = self.community_page * PER_PAGE
                for l in community_listings[start:start + PER_PAGE]:
                    self.create_listing_card(self.community_scroll, l, is_community=True)
                self.create_pagination_bar(self.community_scroll, self.community_page, tot_comm, PER_PAGE, self._change_community_page)

    def _change_active_page(self, page):
        self.active_page = page
        self.refresh_data()

    def _change_past_page(self, page):
        self.past_page = page
        self.refresh_data()

    def _change_community_page(self, page):
        self.community_page = page
        self.refresh_data()


class RecipientDashboard(DashboardBase):
    def __init__(self, master, controller):
        self.avail_page = 0
        self.claims_page = 0
        self.past_claims_page = 0
        super().__init__(master, controller)
        self.show_view("Available Listings")

    def setup_sidebar(self):
        self.add_sidebar_button("Available Listings", "Available Listings", 2)
        self.add_sidebar_button("My Claims", "My Claims", 3)
        self.add_sidebar_button("Past Claims", "Past Claims", 4)

    def setup_views(self):
        # 1. Available Listings View
        view_avail = ctk.CTkFrame(self.view_container, fg_color="transparent")
        view_avail.grid_rowconfigure(0, weight=1)
        view_avail.grid_columnconfigure(0, weight=1)
        self.avail_scroll = ctk.CTkFrame(view_avail, fg_color="transparent")
        self.avail_scroll.grid(row=0, column=0, sticky="nsew")
        self.views["Available Listings"] = view_avail
        
        # 2. My Claims View
        view_claims = ctk.CTkFrame(self.view_container, fg_color="transparent")
        view_claims.grid_rowconfigure(0, weight=1)
        view_claims.grid_columnconfigure(0, weight=1)
        self.claims_scroll = ctk.CTkFrame(view_claims, fg_color="transparent")
        self.claims_scroll.grid(row=0, column=0, sticky="nsew")
        self.views["My Claims"] = view_claims
        
        # 3. Past Claims View
        view_past = ctk.CTkFrame(self.view_container, fg_color="transparent")
        view_past.grid_rowconfigure(0, weight=1)
        view_past.grid_columnconfigure(0, weight=1)
        self.past_claims_scroll = ctk.CTkFrame(view_past, fg_color="transparent")
        self.past_claims_scroll.grid(row=0, column=0, sticky="nsew")
        self.views["Past Claims"] = view_past

    def create_claim_card(self, parent, listing_data, is_available=False):
        card = ctk.CTkFrame(parent, fg_color=("gray95", "gray22"), corner_radius=12)
        card.pack(fill="x", pady=6, padx=10)
        
        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=15, pady=(12, 6))
        
        ctk.CTkLabel(header_row, text=f"Listing {listing_data.listing_id}  |  Donor: {listing_data.donor_id}", 
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        
        st = getattr(listing_data, '_status', 'Available' if is_available else 'Pending Confirmation')
        badge = self.create_status_badge(header_row, st)
        badge.pack(side="right")
        
        body_row = ctk.CTkFrame(card, fg_color="transparent")
        body_row.pack(fill="x", padx=15, pady=(0, 10))
        
        items_str = ", ".join(f"{k} (x{v})" for k, v in listing_data._items.items())
        ctk.CTkLabel(body_row, text=f"Items: {items_str}", justify="left", wraplength=500).pack(anchor="w", pady=(0, 3))
        ctk.CTkLabel(body_row, text=f"Pickup Window: {listing_data._pickup_window}", text_color="gray").pack(anchor="w")

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        if is_available:
            ctk.CTkButton(btn_frame, text="✔ Claim Listing", width=130, height=32, fg_color="#3498db", hover_color="#2980b9",
                          font=ctk.CTkFont(weight="bold"),
                          command=lambda l=listing_data.listing_id: self._claim(l)).pack(side="right")
        else:
            if st != "Claimed":
                ctk.CTkButton(btn_frame, text="✖ Cancel Claim", width=130, height=32, fg_color="#e74c3c", hover_color="#c0392b",
                              font=ctk.CTkFont(weight="bold"),
                              command=lambda l=listing_data.listing_id: self._cancel_claim(l)).pack(side="right")
            elif st == "Claimed":
                if not self.controller.platform_manager.has_user_rated_listing(self.controller.current_user.user_id, listing_data.listing_id):
                    ctk.CTkButton(btn_frame, text="Rate Donor", width=110, height=32, fg_color="#f39c12", hover_color="#e67e22",
                                  font=ctk.CTkFont(weight="bold"),
                                  command=lambda d=listing_data.donor_id, l=listing_data.listing_id: self._rate_user(d, l)).pack(side="left")

    def _rate_user(self, ratee_id, listing_id):
        RatingDialog(self, ratee_id, listing_id, self.controller.platform_manager, self.controller.current_user.user_id, callback=self.refresh_data)

    def refresh_data(self):
        PER_PAGE = 3
        if self.current_view == "Available Listings":
            for widget in self.avail_scroll.winfo_children():
                widget.destroy()
            avail_listings = self.controller.platform_manager.get_available_listings()
            tot = len(avail_listings)
            tot_pages = max(1, (tot + PER_PAGE - 1) // PER_PAGE)
            if self.avail_page >= tot_pages:
                self.avail_page = tot_pages - 1

            if not avail_listings:
                ctk.CTkLabel(self.avail_scroll, text="No listings available right now.", text_color="gray").pack(pady=30)
            else:
                start = self.avail_page * PER_PAGE
                for l in avail_listings[start:start + PER_PAGE]:
                    self.create_claim_card(self.avail_scroll, l, is_available=True)
                self.create_pagination_bar(self.avail_scroll, self.avail_page, tot, PER_PAGE, self._change_avail_page)
                    
        elif self.current_view in ["My Claims", "Past Claims"]:
            for widget in self.claims_scroll.winfo_children():
                widget.destroy()
            for widget in self.past_claims_scroll.winfo_children():
                widget.destroy()
                
            current_user_id = self.controller.current_user.user_id
            my_claims = self.controller.platform_manager.get_recipient_claims(current_user_id)

            active_claims = [l for l in my_claims if getattr(l, '_status', 'Pending Confirmation') != "Claimed"]
            past_claims = [l for l in my_claims if getattr(l, '_status', 'Pending Confirmation') == "Claimed"]

            # Active claims
            tot_act = len(active_claims)
            tot_act_pages = max(1, (tot_act + PER_PAGE - 1) // PER_PAGE)
            if self.claims_page >= tot_act_pages:
                self.claims_page = tot_act_pages - 1

            if not active_claims:
                ctk.CTkLabel(self.claims_scroll, text="You haven't claimed any listings yet.", text_color="gray").pack(pady=30)
            else:
                start = self.claims_page * PER_PAGE
                for l in active_claims[start:start + PER_PAGE]:
                    self.create_claim_card(self.claims_scroll, l, is_available=False)
                self.create_pagination_bar(self.claims_scroll, self.claims_page, tot_act, PER_PAGE, self._change_claims_page)

            # Past claims
            tot_past = len(past_claims)
            tot_past_pages = max(1, (tot_past + PER_PAGE - 1) // PER_PAGE)
            if self.past_claims_page >= tot_past_pages:
                self.past_claims_page = tot_past_pages - 1

            if not past_claims:
                ctk.CTkLabel(self.past_claims_scroll, text="You have no past claims.", text_color="gray").pack(pady=30)
            else:
                start = self.past_claims_page * PER_PAGE
                for l in past_claims[start:start + PER_PAGE]:
                    self.create_claim_card(self.past_claims_scroll, l, is_available=False)
                self.create_pagination_bar(self.past_claims_scroll, self.past_claims_page, tot_past, PER_PAGE, self._change_past_claims_page)

    def _change_avail_page(self, page):
        self.avail_page = page
        self.refresh_data()

    def _change_claims_page(self, page):
        self.claims_page = page
        self.refresh_data()

    def _change_past_claims_page(self, page):
        self.past_claims_page = page
        self.refresh_data()

    def _claim(self, listing_id):
        try:
            self.controller.current_user.claim_listing(self.controller.platform_manager, listing_id)
            messagebox.showinfo("Claimed", f"Listing {listing_id} claimed! Awaiting donor confirmation.")
            self.show_view("My Claims")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _cancel_claim(self, listing_id):
        if messagebox.askyesno("Cancel Claim", f"Are you sure you want to cancel your claim for listing {listing_id}?"):
            try:
                self.controller.current_user.cancel_claim(self.controller.platform_manager, listing_id)
                messagebox.showinfo("Cancelled", f"Claim for listing {listing_id} has been cancelled.")
                self.refresh_data()
            except Exception as e:
                messagebox.showerror("Error", str(e))


class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SurplusBite – Food Rescue Platform")
        self.geometry("1100x720")
        self.minsize(950, 650)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.platform_manager = PlatformManager()
        self.current_user = None
        self._current_frame = None

        self.switch_frame(WelcomeFrame)

    def switch_frame(self, frame_class):
        """Destroy the active frame and replace it with the new one."""
        if self._current_frame is not None:
            self._current_frame.destroy()
        self._current_frame = frame_class(master=self, controller=self)
        self._current_frame.grid(row=0, column=0, sticky="nsew")


if __name__ == "__main__":
    app = AppWindow()
    app.mainloop()
