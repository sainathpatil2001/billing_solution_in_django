# Billing Solution in Django

A robust and efficient Billing and Inventory Management System designed for local businesses (e.g., Kirana stores, Grocery shops, Retail outlets). This web application simplifies the process of generating bills, managing inventory, tracking payments, and maintaining business records. It can be run as a standard Django web application or as a desktop application using Electron.

## Key Features

### 🧾 Billing & Invoicing
*   **Fast Bill Generation**: Create professional invoices quickly for customers.
*   **Tax Compliance**: Automated calculation of GST (CGST, SGST, IGST) based on product settings.
*   **Payment Tracking**: Support for multiple payment statuses ('Paid', 'Pending', 'Partially Paid') and modes ('Cash', 'Online').
*   **Discount Management**: Apply discounts directly to bills.
*   **Bill History**: Search, view, and manage past bills.
*   **Print Support**: Printer-friendly bill layouts.

### 📦 Inventory Management
*   **Product Tracking**: Manage products with details like Name, Category, Unit, Prices (Dealer/Selling), and MRP.
*   **Stock Monitoring**: Real-time tracking of stock levels with status indicators ("In Stock", "Low Stock", "Out of Stock").
*   **Batch & Expiry**: Track products by Batch Number, Manufacturing Date, and Expiry Date.
*   **Barcode/HSN**: Support for HSN numbers for tax regulation.
*   **Category & Unit Management**: Organize products into categories and define custom units (kg, pc, liter, etc.).

### ⚙️ Business Administration
*   **Profile Management**: Configure business details, address, phone, email, and GST number.
*   **Customization**: Upload Business Logo and Authorized Signature for bills.
*   **Payment Details**: Display UPI ID and custom Terms & Conditions on invoices.
*   **Security**: Password protection for sensitive settings.

### 💾 Data Management & Security
*   **Backup & Restore**: Built-in functionality to create ZIP backups of the database and media files, and easy restoration process.
*   **Activation System**: License key management system for controlling application access/validity duration.

### 🖥️ Desktop Experience
*   **Electron Integration**: Includes an Electron shell to run the Django app as a native-like desktop application.

## Technology Stack

*   **Backend**: Django 4.2 (Python)
*   **Frontend**: HTML5, CSS3, JavaScript
*   **Database**: SQLite (Default, scalable to PostgreSQL/MySQL)
*   **Imaging**: Pillow (for handling logos/signatures)
*   **Desktop Wrapper**: Electron JS

## Installation & Setup

### Prerequisites
*   Python 3.8 or higher installed.
*   Node.js (optional, only for Electron Desktop App).

### 1. Clone or Download the Repository
```bash
git clone <repository_url>
cd "Billing Platform webapp/billing_solution_in_django"
```

### 2. Set Up Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Migrations
Initialize the database tables:
```bash
python manage.py make migrations
python manage.py migrate
```

### 5. Run the Web Server
```bash
python manage.py runserver
```
Access the application at: `http://127.0.0.1:8000/`

## Running as Desktop App (Electron)

If you prefer a desktop application experience:

1.  Ensure **Node.js** and **npm** are installed.
2.  Navigate to the `electron` directory (or root if package.json is there).
3.  Install dependencies:
    ```bash
    npm install
    ```
4.  Start the application (this usually starts the Django server and the Electron window):
    ```bash
    npm start
    ```
    *(Refer to `README-ELECTRON.md` for specific desktop app build instructions)*

## Project Structure

*   `genrate_bill/`: Core billing logic, bill views, and business settings.
*   `inventory/`: Product, category, and unit management.
*   `bill_maker/`: Main project settings and configuration.
*   `templates/`: HTML templates for the UI.
*   `static/`: CSS, JS, and static assets.
*   `media/`: User-uploaded content (Logos, Signatures).

## License
[License Name/Type]
