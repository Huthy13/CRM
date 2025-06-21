class Address:
    def __init__(self, address_id=None, street="", city="", state="", zip_code="", country=""):
        self.address_id = address_id
        self.street = street
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.country = country

    def __str__(self):
        return (f"Address ID: {self.address_id}\n"
                f"Street: {self.street}\n"
                f"City: {self.city}\n"
                f"State: {self.state}\n"
                f"ZIP Code: {self.zip_code}\n"
                f"Country: {self.country}")

    def to_dict(self):
        """Returns the address as a dictionary."""
        return {
            "address_id": self.address_id,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country
        }

class Account:
    def __init__(self, account_id=None, name="", phone="", billing_address_id=None, shipping_address_id=None, website="", description=""):
        
        self.account_id = account_id
        self.name = name
        self.phone = phone
        self.billing_address_id = billing_address_id
        self.shipping_address_id = shipping_address_id
        self.website = website
        self.description = description

    def __str__(self):
        return (f"Data from the string method!!! Account ID: {self.account_id}\n"
                f"Name: {self.name}\n"
                f"Phone: {self.phone}\n"
                f"Billing Address ID: {self.billing_address_id}\n"
                f"Shipping Address ID: {self.shipping_address_id}\n"
                f"Website: {self.website}\n"
                f"Description: {self.description}")

    def to_dict(self):
        """Returns the account as a dictionary."""
        return {
            "account_id": self.account_id,
            "name": self.name,
            "phone": self.phone,
            "billing_address_id": self.billing_address_id,
            "shipping_address_id": self.shipping_address_id,
            "same_as_billing": self.is_billing_same_as_shipping(),
            "website": self.website,
            "description": self.description
        }
    
    def is_billing_same_as_shipping(self):
        """Checks if billing and shipping address IDs are the same."""
        if self.billing_address_id is None and self.shipping_address_id is None:
            return False

        return self.billing_address_id == self.shipping_address_id


class Contact:
    def __init__(self, contact_id=None, name="", phone="", email="", account_id=None, role=""):
        self.contact_id = contact_id
        self.name = name
        self.phone = phone
        self.email = email
        self.account_id = account_id
        self.role = role

    def __str__(self):
        return (f"Contact ID: {self.contact_id}\n"
                f"Name: {self.name}\n"
                f"Phone: {self.phone}\n"
                f"Email: {self.email}\n"
                f"Account ID: {self.account_id}\n"
                f"Role: {self.role}")

    def to_dict(self):
        """Returns the contact as a dictionary."""
        return {
            "contact_id": self.contact_id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "account_id": self.account_id,
            "role": self.role
        }