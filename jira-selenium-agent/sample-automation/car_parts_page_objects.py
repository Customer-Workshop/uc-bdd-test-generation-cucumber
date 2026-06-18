"""Car Parts Salesforce Lightning Web Component Page Objects.

Complete POM for a Car Parts management application in Salesforce
with Lightning Web Components, including all dropdown fields and values.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dropdown field definitions with all picklist values
# ---------------------------------------------------------------------------

@dataclass
class DropdownField:
    """Represents a Salesforce picklist/dropdown field with all its values."""
    field_name: str
    api_name: str
    label: str
    values: list[str] = field(default_factory=list)
    default_value: str = ""
    is_required: bool = False
    dependent_on: str = ""


# All dropdown fields for Car Parts object
PART_CATEGORY = DropdownField(
    field_name="Part_Category__c",
    api_name="Part_Category__c",
    label="Part Category",
    values=[
        "Engine Components",
        "Transmission & Drivetrain",
        "Braking System",
        "Suspension & Steering",
        "Electrical & Lighting",
        "Exhaust System",
        "Body & Exterior",
        "Interior & Comfort",
        "Cooling System",
        "Fuel System",
        "HVAC & Climate Control",
        "Wheels & Tires",
    ],
    default_value="Engine Components",
    is_required=True,
)

PART_SUB_CATEGORY = DropdownField(
    field_name="Part_Sub_Category__c",
    api_name="Part_Sub_Category__c",
    label="Part Sub-Category",
    values=[
        # Engine Components sub-categories
        "Cylinder Head", "Piston", "Crankshaft", "Camshaft", "Valve",
        "Gasket Set", "Timing Belt", "Oil Pump", "Engine Block", "Turbocharger",
        # Transmission sub-categories
        "Gearbox", "Clutch Kit", "Drive Shaft", "CV Joint", "Differential",
        "Flywheel", "Transfer Case", "Torque Converter",
        # Braking sub-categories
        "Brake Pad", "Brake Disc", "Brake Caliper", "Brake Line",
        "Master Cylinder", "ABS Module", "Brake Drum", "Brake Shoe",
        # Suspension sub-categories
        "Shock Absorber", "Strut Assembly", "Control Arm", "Ball Joint",
        "Tie Rod", "Sway Bar", "Steering Rack", "Power Steering Pump",
        # Electrical sub-categories
        "Alternator", "Starter Motor", "Battery", "Ignition Coil",
        "Spark Plug", "Headlight", "Tail Light", "Wiring Harness",
    ],
    default_value="",
    is_required=True,
    dependent_on="Part_Category__c",
)

MANUFACTURER = DropdownField(
    field_name="Manufacturer__c",
    api_name="Manufacturer__c",
    label="Manufacturer",
    values=[
        "Bosch", "Denso", "Continental", "Delphi", "Valeo",
        "ZF Friedrichshafen", "Aisin", "Magna International",
        "BorgWarner", "Mahle", "NGK", "ACDelco", "Brembo",
        "Monroe", "KYB", "Gates", "Hella", "Moog",
        "Dayco", "TRW", "Sachs", "SKF", "NTN",
    ],
    default_value="Bosch",
    is_required=True,
)

CONDITION = DropdownField(
    field_name="Condition__c",
    api_name="Condition__c",
    label="Condition",
    values=["New", "Refurbished", "Used - Grade A", "Used - Grade B", "Used - Grade C", "Salvage"],
    default_value="New",
    is_required=True,
)

AVAILABILITY_STATUS = DropdownField(
    field_name="Availability_Status__c",
    api_name="Availability_Status__c",
    label="Availability Status",
    values=[
        "In Stock",
        "Low Stock",
        "Out of Stock",
        "Back Ordered",
        "Discontinued",
        "Pre-Order",
        "Made to Order",
    ],
    default_value="In Stock",
    is_required=False,
)

VEHICLE_MAKE = DropdownField(
    field_name="Vehicle_Make__c",
    api_name="Vehicle_Make__c",
    label="Vehicle Make",
    values=[
        "Toyota", "Honda", "Ford", "Chevrolet", "BMW",
        "Mercedes-Benz", "Audi", "Volkswagen", "Hyundai", "Kia",
        "Nissan", "Mazda", "Subaru", "Volvo", "Jeep",
        "Ram", "GMC", "Lexus", "Porsche", "Tesla",
        "Universal / Multi-Fit",
    ],
    default_value="",
    is_required=False,
)

VEHICLE_MODEL_YEAR_RANGE = DropdownField(
    field_name="Model_Year_Range__c",
    api_name="Model_Year_Range__c",
    label="Model Year Range",
    values=[
        "2020-2026", "2015-2019", "2010-2014", "2005-2009",
        "2000-2004", "1995-1999", "1990-1994", "Pre-1990",
        "All Years",
    ],
    default_value="All Years",
    is_required=False,
)

WAREHOUSE_LOCATION = DropdownField(
    field_name="Warehouse_Location__c",
    api_name="Warehouse_Location__c",
    label="Warehouse Location",
    values=[
        "Warehouse A - North",
        "Warehouse B - South",
        "Warehouse C - East",
        "Warehouse D - West",
        "Warehouse E - Central",
        "Distributor Hub",
        "Transit / In Shipment",
    ],
    default_value="Warehouse A - North",
    is_required=False,
)

QUALITY_GRADE = DropdownField(
    field_name="Quality_Grade__c",
    api_name="Quality_Grade__c",
    label="Quality Grade",
    values=["OEM", "OES", "Aftermarket Premium", "Aftermarket Standard", "Economy"],
    default_value="OEM",
    is_required=False,
)

SHIPPING_CLASS = DropdownField(
    field_name="Shipping_Class__c",
    api_name="Shipping_Class__c",
    label="Shipping Class",
    values=[
        "Standard Ground",
        "Express 2-Day",
        "Overnight",
        "Freight / LTL",
        "Oversized",
        "Hazmat",
        "White Glove",
    ],
    default_value="Standard Ground",
    is_required=False,
)

WARRANTY_TYPE = DropdownField(
    field_name="Warranty_Type__c",
    api_name="Warranty_Type__c",
    label="Warranty Type",
    values=[
        "No Warranty",
        "30-Day Limited",
        "90-Day Limited",
        "1-Year Limited",
        "2-Year Limited",
        "Lifetime Limited",
        "Manufacturer Warranty",
    ],
    default_value="1-Year Limited",
    is_required=False,
)

CURRENCY_CODE = DropdownField(
    field_name="Currency_Code__c",
    api_name="Currency_Code__c",
    label="Currency",
    values=["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "INR"],
    default_value="USD",
    is_required=False,
)

# Registry of all dropdown fields
ALL_DROPDOWN_FIELDS = [
    PART_CATEGORY, PART_SUB_CATEGORY, MANUFACTURER, CONDITION,
    AVAILABILITY_STATUS, VEHICLE_MAKE, VEHICLE_MODEL_YEAR_RANGE,
    WAREHOUSE_LOCATION, QUALITY_GRADE, SHIPPING_CLASS, WARRANTY_TYPE,
    CURRENCY_CODE,
]


# ---------------------------------------------------------------------------
# Car Parts LWC Page Objects
# ---------------------------------------------------------------------------

class CarPartsBasePage:
    """Base page for Car Parts Salesforce Lightning application."""

    def __init__(self, driver: WebDriver, base_url: str = ""):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 20)

    def wait_for_lightning(self, timeout: int = 30):
        """Wait for Salesforce Lightning framework to be ready."""
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script(
                "return document.readyState === 'complete'"
                " && (typeof $A === 'undefined' || $A.get('e.force:navigateToURL') !== undefined)"
            )
        )
        self._wait_spinners_gone()

    def _wait_spinners_gone(self, timeout: int = 15):
        """Wait for all loading spinners to disappear."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((
                    By.CSS_SELECTOR,
                    "lightning-spinner, div.slds-spinner_container, .slds-spinner"
                ))
            )
        except Exception:
            pass

    def find_element(self, by: str, value: str, timeout: int = 10) -> WebElement:
        """Find element with explicit wait."""
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def find_elements(self, by: str, value: str) -> list[WebElement]:
        """Find all matching elements."""
        return self.driver.find_elements(by, value)

    def click_element(self, by: str, value: str):
        """Click an element with wait."""
        element = self.wait.until(EC.element_to_be_clickable((by, value)))
        element.click()

    def type_text(self, by: str, value: str, text: str):
        """Clear and type text into an element."""
        element = self.find_element(by, value)
        element.clear()
        element.send_keys(text)

    def take_screenshot(self, name: str) -> str:
        """Take a screenshot and return the path."""
        path = f"screenshots/car-parts-{name}-{int(time.time())}.png"
        self.driver.save_screenshot(path)
        return path

    def get_lwc_shadow_element(self, host_css: str, inner_css: str) -> WebElement:
        """Traverse LWC Shadow DOM to find inner element."""
        return self.driver.execute_script(
            "const host = document.querySelector(arguments[0]);"
            "if (!host || !host.shadowRoot) return null;"
            "return host.shadowRoot.querySelector(arguments[1]);",
            host_css, inner_css,
        )

    def get_nested_shadow_element(self, selectors: list[str]) -> WebElement:
        """Traverse multiple levels of Shadow DOM.

        Args:
            selectors: List of CSS selectors, each piercing one shadow root.
        """
        script = "let el = document;"
        for i, sel in enumerate(selectors):
            if i < len(selectors) - 1:
                script += f"el = el.querySelector('{sel}');"
                script += "if (!el) return null; el = el.shadowRoot; if (!el) return null;"
            else:
                script += f"el = el.querySelector('{sel}');"
        script += "return el;"
        return self.driver.execute_script(script)


class CarPartsLoginPage(CarPartsBasePage):
    """Salesforce login page for Car Parts application."""

    def login(self, username: str, password: str):
        """Perform Salesforce login."""
        self.driver.get(self.base_url)
        self.type_text(By.ID, "username", username)
        self.type_text(By.ID, "password", password)
        self.click_element(By.ID, "Login")
        self.wait_for_lightning()
        logger.info("Logged in to Salesforce successfully")

    def is_logged_in(self) -> bool:
        """Check if user is logged in to Salesforce."""
        try:
            self.find_element(By.CSS_SELECTOR, "one-app-nav-bar, nav[role='navigation']", timeout=10)
            return True
        except Exception:
            return False


class CarPartsNavigationPage(CarPartsBasePage):
    """Navigation page for Car Parts within Salesforce."""

    def navigate_to_car_parts(self):
        """Navigate to Car Parts object list view."""
        self.driver.get(f"{self.base_url}/lightning/o/Car_Part__c/list")
        self.wait_for_lightning()
        logger.info("Navigated to Car Parts list view")

    def navigate_to_car_part_record(self, record_id: str):
        """Navigate to a specific Car Part record."""
        self.driver.get(f"{self.base_url}/lightning/r/Car_Part__c/{record_id}/view")
        self.wait_for_lightning()

    def open_app_launcher(self, app_name: str = "Car Parts"):
        """Open app through App Launcher."""
        self.click_element(By.CSS_SELECTOR, "button.slds-icon-waffle_container, div.appLauncher")
        time.sleep(1)
        search = self.find_element(By.CSS_SELECTOR, "input.slds-input[type='search'], one-app-launcher-search-bar input")
        search.send_keys(app_name)
        time.sleep(1)
        self.click_element(By.XPATH, f"//one-app-launcher-menu-item//span[contains(text(), '{app_name}')]")
        self.wait_for_lightning()
        logger.info("Opened Car Parts app via launcher")

    def click_tab(self, tab_name: str):
        """Click a navigation tab."""
        self.click_element(By.XPATH, f"//one-app-nav-bar-item-root//a[@title='{tab_name}']")
        self.wait_for_lightning()

    def global_search(self, search_term: str):
        """Search for a car part using global search."""
        search_input = self.find_element(
            By.CSS_SELECTOR, "input.slds-input[type='search'], lightning-input.search-input input"
        )
        search_input.clear()
        search_input.send_keys(search_term)
        search_input.send_keys(Keys.ENTER)
        self.wait_for_lightning()
        logger.info("Global search: %s", search_term)


class CarPartsListPage(CarPartsBasePage):
    """Car Parts list view page."""

    def get_list_rows(self) -> list[WebElement]:
        """Get all rows in the list view."""
        self.wait_for_lightning()
        return self.find_elements(
            By.CSS_SELECTOR,
            "table.slds-table tbody tr, lightning-datatable tbody tr, "
            "force-list-view-manager-grid table tbody tr"
        )

    def get_row_count(self) -> int:
        """Get total number of rows displayed."""
        return len(self.get_list_rows())

    def click_new_button(self):
        """Click the New button to create a new Car Part."""
        self.click_element(
            By.CSS_SELECTOR,
            "a[title='New'], lightning-button[title='New'] button, "
            "div.slds-page-header__control button[name='New']"
        )
        self.wait_for_lightning()
        logger.info("Clicked New Car Part button")

    def select_list_view(self, view_name: str):
        """Select a specific list view."""
        self.click_element(
            By.CSS_SELECTOR,
            "button.slds-button[title='Select a List View'], "
            "lightning-button-icon-stateful[title='Select a List View']"
        )
        time.sleep(0.5)
        self.click_element(
            By.XPATH, f"//li//a//span[text()='{view_name}']"
        )
        self.wait_for_lightning()

    def search_list(self, search_term: str):
        """Search within the list view."""
        search = self.find_element(
            By.CSS_SELECTOR,
            "input[name='Car_Part__c-search-input'], "
            "lightning-input.list-search-input input"
        )
        search.clear()
        search.send_keys(search_term)
        time.sleep(1)
        self.wait_for_lightning()

    def click_row(self, row_index: int = 0):
        """Click on a specific row to open the record."""
        rows = self.get_list_rows()
        if rows and row_index < len(rows):
            link = rows[row_index].find_element(By.CSS_SELECTOR, "a[data-refid='recordId']")
            link.click()
            self.wait_for_lightning()

    def sort_by_column(self, column_name: str):
        """Sort list by clicking a column header."""
        self.click_element(
            By.XPATH,
            f"//th[contains(@aria-label, '{column_name}')]//a | "
            f"//span[text()='{column_name}']/ancestor::th//a"
        )
        self.wait_for_lightning()


class CarPartsFormPage(CarPartsBasePage):
    """Car Parts record create/edit form page (Lightning Record Form).

    Handles all text fields, dropdown/picklist fields, lookup fields,
    and dependent picklists in the Car Parts LWC form.
    """

    def set_text_field(self, label: str, value: str):
        """Set a text/number/currency field by its label."""
        xpath = (
            f"//lightning-input[.//label[contains(text(), '{label}')]]//input"
            f" | //lightning-textarea[.//label[contains(text(), '{label}')]]//textarea"
            f" | //force-record-layout-item[.//span[contains(text(), '{label}')]]//input"
            f" | //records-record-layout-item[.//span[contains(text(), '{label}')]]//input"
        )
        element = self.find_element(By.XPATH, xpath)
        element.clear()
        element.send_keys(value)
        logger.info("Set text field '%s' = '%s'", label, value)

    def select_picklist(self, label: str, value: str):
        """Select a value from a Lightning combobox/picklist dropdown.

        Handles both standard picklists and Lightning combobox components.

        Args:
            label: The field label text.
            value: The picklist value to select.
        """
        # Click the combobox to open dropdown
        combobox_xpath = (
            f"//lightning-combobox[.//label[contains(text(), '{label}')]]//button"
            f" | //lightning-picklist[.//label[contains(text(), '{label}')]]//button"
            f" | //force-record-layout-item[.//span[contains(text(), '{label}')]]//a[contains(@class, 'select')]"
            f" | //records-record-layout-item[.//span[contains(text(), '{label}')]]//button"
        )
        self.click_element(By.XPATH, combobox_xpath)
        time.sleep(0.5)

        # Select the value from dropdown options
        option_xpath = (
            f"//lightning-base-combobox-item[.//span[contains(text(), '{value}')]]"
            f" | //li[contains(@class, 'slds-listbox__item')]//span[text()='{value}']"
        )
        self.click_element(By.XPATH, option_xpath)
        logger.info("Selected picklist '%s' = '%s'", label, value)

    def select_picklist_and_verify(self, dropdown_field: DropdownField, value: str) -> bool:
        """Select a picklist value and verify it was set correctly.

        Args:
            dropdown_field: The DropdownField definition.
            value: The value to select.

        Returns:
            True if value was selected and verified.
        """
        self.select_picklist(dropdown_field.label, value)
        time.sleep(0.3)
        selected = self.get_selected_picklist_value(dropdown_field.label)
        if selected == value:
            logger.info("Verified picklist '%s' = '%s'", dropdown_field.label, value)
            return True
        logger.warning(
            "Picklist verification failed for '%s': expected '%s', got '%s'",
            dropdown_field.label, value, selected
        )
        return False

    def get_selected_picklist_value(self, label: str) -> str:
        """Get the currently selected value of a picklist field."""
        xpath = (
            f"//lightning-combobox[.//label[contains(text(), '{label}')]]//button//span"
            f" | //lightning-picklist[.//label[contains(text(), '{label}')]]//button//span"
        )
        try:
            element = self.find_element(By.XPATH, xpath)
            return element.text
        except Exception:
            return ""

    def get_picklist_options(self, label: str) -> list[str]:
        """Get all available options for a picklist field.

        Opens the dropdown and reads all option values.

        Args:
            label: The field label text.

        Returns:
            List of option values.
        """
        # Open the dropdown
        combobox_xpath = (
            f"//lightning-combobox[.//label[contains(text(), '{label}')]]//button"
            f" | //lightning-picklist[.//label[contains(text(), '{label}')]]//button"
        )
        self.click_element(By.XPATH, combobox_xpath)
        time.sleep(0.5)

        # Read all options
        options = self.find_elements(
            By.CSS_SELECTOR,
            "lightning-base-combobox-item span.slds-truncate, "
            "li.slds-listbox__item span.slds-truncate"
        )
        values = [opt.text for opt in options if opt.text.strip()]

        # Close dropdown by pressing Escape
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.3)

        logger.info("Picklist '%s' options: %s", label, values)
        return values

    def traverse_all_dropdown_fields(self) -> dict[str, list[str]]:
        """Open each dropdown field and read all its available values.

        Returns:
            Dict of field_label -> list of option values.
        """
        results = {}
        for dropdown in ALL_DROPDOWN_FIELDS:
            try:
                options = self.get_picklist_options(dropdown.label)
                results[dropdown.label] = options
                logger.info(
                    "Traversed dropdown '%s': %d options", dropdown.label, len(options)
                )
            except Exception as e:
                logger.warning("Could not traverse dropdown '%s': %s", dropdown.label, e)
                results[dropdown.label] = dropdown.values
        return results

    def set_lookup_field(self, label: str, search_term: str):
        """Set a lookup/reference field by searching and selecting.

        Args:
            label: The lookup field label.
            search_term: Text to search in the lookup.
        """
        lookup_xpath = (
            f"//lightning-lookup[.//label[contains(text(), '{label}')]]//input"
            f" | //lightning-grouped-combobox[.//label[contains(text(), '{label}')]]//input"
            f" | //force-lookup[.//label[contains(text(), '{label}')]]//input"
        )
        element = self.find_element(By.XPATH, lookup_xpath)
        element.clear()
        element.send_keys(search_term)
        time.sleep(1)

        # Select first result
        result_xpath = (
            "//lightning-base-combobox-item[contains(@class, 'slds-media')]"
            " | //li[contains(@class, 'lookup__item')]"
        )
        self.click_element(By.XPATH, result_xpath)
        logger.info("Set lookup field '%s' = '%s'", label, search_term)

    def set_date_field(self, label: str, date_value: str):
        """Set a date field."""
        xpath = (
            f"//lightning-datepicker[.//label[contains(text(), '{label}')]]//input"
            f" | //lightning-input[.//label[contains(text(), '{label}')]][contains(@class, 'date')]//input"
        )
        element = self.find_element(By.XPATH, xpath)
        element.clear()
        element.send_keys(date_value)
        element.send_keys(Keys.TAB)
        logger.info("Set date field '%s' = '%s'", label, date_value)

    def set_checkbox(self, label: str, checked: bool = True):
        """Set a checkbox field."""
        xpath = f"//lightning-input[.//span[contains(text(), '{label}')]]//input[@type='checkbox']"
        element = self.find_element(By.XPATH, xpath)
        if element.is_selected() != checked:
            element.click()
        logger.info("Set checkbox '%s' = %s", label, checked)

    def fill_car_part_form(
        self,
        part_name: str,
        part_number: str,
        category: str,
        sub_category: str,
        manufacturer: str,
        condition: str,
        price: str,
        quantity: str,
        vehicle_make: str = "",
        year_range: str = "",
        availability: str = "In Stock",
        warehouse: str = "Warehouse A - North",
        quality_grade: str = "OEM",
        shipping_class: str = "Standard Ground",
        warranty: str = "1-Year Limited",
        description: str = "",
    ):
        """Fill the complete Car Part creation form.

        Args:
            part_name: Name of the car part.
            part_number: Part number / SKU.
            category: Part category picklist value.
            sub_category: Part sub-category (dependent on category).
            manufacturer: Manufacturer picklist value.
            condition: Condition picklist value.
            price: Unit price.
            quantity: Stock quantity.
            vehicle_make: Compatible vehicle make.
            year_range: Model year range.
            availability: Availability status.
            warehouse: Warehouse location.
            quality_grade: Quality grade.
            shipping_class: Shipping class.
            warranty: Warranty type.
            description: Part description text.
        """
        logger.info("Filling Car Part form: %s (%s)", part_name, part_number)

        # Text fields
        self.set_text_field("Part Name", part_name)
        self.set_text_field("Part Number", part_number)

        # Required picklist fields
        self.select_picklist("Part Category", category)
        time.sleep(0.5)  # Wait for dependent picklist to refresh
        self.select_picklist("Part Sub-Category", sub_category)
        self.select_picklist("Manufacturer", manufacturer)
        self.select_picklist("Condition", condition)

        # Numeric fields
        self.set_text_field("Unit Price", price)
        self.set_text_field("Stock Quantity", quantity)

        # Optional picklist fields
        if vehicle_make:
            self.select_picklist("Vehicle Make", vehicle_make)
        if year_range:
            self.select_picklist("Model Year Range", year_range)
        if availability:
            self.select_picklist("Availability Status", availability)
        if warehouse:
            self.select_picklist("Warehouse Location", warehouse)
        if quality_grade:
            self.select_picklist("Quality Grade", quality_grade)
        if shipping_class:
            self.select_picklist("Shipping Class", shipping_class)
        if warranty:
            self.select_picklist("Warranty Type", warranty)

        # Description
        if description:
            self.set_text_field("Description", description)

        logger.info("Car Part form filled: %s", part_name)

    def save_record(self):
        """Click the Save button to create/update the record."""
        self.click_element(
            By.CSS_SELECTOR,
            "button[name='SaveEdit'], "
            "lightning-button[data-aura-class='uiButton'] button[title='Save'], "
            "button.slds-button_brand[title='Save']"
        )
        self.wait_for_lightning()
        logger.info("Record saved")

    def cancel(self):
        """Click Cancel button."""
        self.click_element(
            By.CSS_SELECTOR,
            "button[name='CancelEdit'], button[title='Cancel']"
        )
        self.wait_for_lightning()

    def get_validation_errors(self) -> list[str]:
        """Get any validation error messages shown on the form."""
        errors = self.find_elements(
            By.CSS_SELECTOR,
            "div.slds-form-element__help, "
            "lightning-helptext .slds-form-element__help, "
            "ul.errorsList li"
        )
        return [e.text for e in errors if e.text.strip()]


class CarPartsRecordPage(CarPartsBasePage):
    """Car Parts record detail/view page."""

    def get_field_value(self, field_label: str) -> str:
        """Get a field value from the record detail."""
        xpath = (
            f"//records-record-layout-item[.//span[contains(text(), '{field_label}')]]"
            f"//lightning-formatted-text"
            f" | //force-record-layout-item[.//span[contains(text(), '{field_label}')]]"
            f"//lightning-formatted-text"
            f" | //records-record-layout-item[.//span[contains(text(), '{field_label}')]]"
            f"//lightning-formatted-number"
        )
        try:
            element = self.find_element(By.XPATH, xpath, timeout=5)
            return element.text
        except Exception:
            return ""

    def get_all_field_values(self) -> dict[str, str]:
        """Get all visible field values from the record."""
        fields = {}
        field_items = self.find_elements(
            By.CSS_SELECTOR,
            "records-record-layout-item, force-record-layout-item"
        )
        for item in field_items:
            try:
                label = item.find_element(By.CSS_SELECTOR, "span.test-id__field-label").text
                value_el = item.find_element(
                    By.CSS_SELECTOR,
                    "lightning-formatted-text, lightning-formatted-number, "
                    "lightning-formatted-url, lightning-formatted-date-time"
                )
                fields[label] = value_el.text
            except Exception:
                pass
        return fields

    def click_edit(self):
        """Click the Edit button to enter edit mode."""
        self.click_element(
            By.CSS_SELECTOR,
            "button[name='Edit'], lightning-button-icon[title='Edit']"
        )
        self.wait_for_lightning()
        logger.info("Entered edit mode")

    def click_delete(self):
        """Click the Delete action."""
        # Open actions menu
        self.click_element(
            By.CSS_SELECTOR,
            "lightning-button-menu[data-target-reveals='sfdc:StandardButton.Car_Part__c.Delete']"
            ", runtime_platform_actions-actions-ribbon lightning-button-menu"
        )
        time.sleep(0.5)
        self.click_element(By.XPATH, "//a[@title='Delete'] | //span[text()='Delete']")
        time.sleep(0.5)
        # Confirm delete
        self.click_element(
            By.XPATH,
            "//button[contains(text(), 'Delete')] | //button[@title='Delete']"
        )
        self.wait_for_lightning()
        logger.info("Record deleted")

    def get_toast_message(self) -> str:
        """Get the toast notification message."""
        try:
            toast = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((
                    By.CSS_SELECTOR, "div.toastMessage, lightning-formatted-rich-text.toastMessage"
                ))
            )
            return toast.text
        except Exception:
            return ""

    def verify_record_created(self, part_name: str) -> bool:
        """Verify that the record was created successfully."""
        toast = self.get_toast_message()
        if "was created" in toast.lower() or part_name.lower() in toast.lower():
            logger.info("Record creation confirmed via toast: %s", toast)
            return True

        # Also check page title/header
        try:
            header = self.find_element(
                By.CSS_SELECTOR,
                "lightning-formatted-text.slds-page-header__title, "
                "records-entity-label, h1.slds-page-header__title"
            )
            if part_name.lower() in header.text.lower():
                return True
        except Exception:
            pass

        return False

    def get_related_list_count(self, related_list_name: str) -> int:
        """Get count of items in a related list."""
        try:
            count_el = self.find_element(
                By.XPATH,
                f"//article[.//span[contains(text(), '{related_list_name}')]]"
                f"//span[contains(@class, 'count')]"
            )
            return int(count_el.text.strip("()"))
        except Exception:
            return 0
