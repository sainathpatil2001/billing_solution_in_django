# Bill Maker Desktop Application

A comprehensive desktop application built with Django and Electron for managing invoices, customers, and inventory with ease.

## Features

✨ **Key Features:**
- 📄 **Bill Generation**: Create professional invoices with custom templates
- 👥 **Customer Management**: Manage customer information and GST details
- 📦 **Inventory Management**: Track products, batch numbers, and expiry dates
- 💳 **Payment Tracking**: Record payment history and payment modes
- 🏢 **Business Information**: Store and manage business details, logos, and signatures
- 📊 **GST Compliance**: Built-in GST rate management (SGST, CGST, IGST)
- 💾 **Database Management**: SQLite database with migration support
- 🖥️ **Desktop App**: Native desktop experience with Electron
- 🌐 **Web Interface**: Django-based web interface
- 🔐 **Security**: Password protection for sensitive data
- 📱 **Responsive Design**: Works seamlessly across different screen sizes

## Tech Stack

### Frontend
- **Electron**: Desktop application framework
- **JavaScript**: Frontend logic
- **HTML/CSS**: User interface

### Backend
- **Django**: Python web framework
- **SQLite**: Database management
- **Python**: Backend logic

### Build Tools
- **electron-builder**: Package and build Electron apps
- **Node.js**: JavaScript runtime
- **npm**: Package manager

## Installation

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Steps

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd "Pritam Softwere"
   ```

2. **Install Python Dependencies**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

3. **Install Node Dependencies**
   ```bash
   npm install
   ```

4. **Run Django Migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create Superuser (Optional)**
   ```bash
   python manage.py createsuperuser
   ```

## Usage

### Running the Django Server
```bash
python run_django.py
# or
python manage.py runserver
```

The web interface will be available at `http://localhost:8000`

### Running the Desktop App
```bash
# Development mode
npm start

# Build the application
npm run build

# On Windows
./start-desktop-app.bat
```

### Building Installer
```bash
python build_installer.py
```

## Project Structure

```
.
├── bill_maker/                 # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── genrate_bill/               # Bill generation app
│   ├── models.py              # Bill, Customer, BillItem models
│   ├── views.py               # Bill views and logic
│   ├── urls.py                # App routes
│   └── templates/             # Bill templates
├── inventory/                  # Inventory management app
│   ├── models.py              # Product model
│   ├── views.py               # Inventory views
│   └── templates/             # Inventory templates
├── electron/                   # Electron app configuration
│   ├── main.js                # Electron main process
│   └── splash.html            # Splash screen
├── static/                     # Static files (CSS, JS)
├── media/                      # User uploads (logos, signatures)
├── db.sqlite3                  # Database
├── manage.py                   # Django management
├── requirements.txt            # Python dependencies
├── package.json                # Node dependencies
└── README.md                   # This file
```

## Database Models

### Bill
- Bill number, date, and details
- Customer information
- Payment details (amount, mode, date)
- GST calculations
- Place of supply

### Customer
- First name, last name
- Contact details
- GST number
- City, district, address

### BillItem
- Product details
- Quantity and rates
- HSN/SAC codes
- GST rates and amounts
- Batch number and expiry date

### BusinessInformation
- Company details
- Logo and signature
- Bank details
- UPI ID
- Security password
- Terms and conditions

### Product (Inventory)
- Product name and description
- MRP and cost price
- GST rate
- Batch number and expiry date
- Stock tracking

## Configuration

### Settings
Edit `bill_maker/settings.py` to configure:
- Database settings
- Static/media files location
- Email configuration
- Other Django settings

### Business Information
Store business details in Django admin:
- Access at: `http://localhost:8000/admin`
- Add your company information, logo, and signature

## API Endpoints

- `GET/POST /api/bills/` - Bill management
- `GET/POST /api/customers/` - Customer management
- `GET/POST /api/inventory/` - Inventory management
- `GET/POST /api/payment-history/` - Payment tracking

## Development

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Running Tests
```bash
python manage.py test
```

### Static Files Collection
```bash
python manage.py collectstatic
```

## Build & Deployment

### Desktop App Build
```bash
npm run build
# Creates installer in dist_electron/ folder
```

### Web Deployment
For production deployment:
1. Set `DEBUG = False` in settings.py
2. Configure allowed hosts
3. Use a production server (Gunicorn, uWSGI)
4. Set up SSL/HTTPS
5. Configure static files serving

## Common Issues

### Issue: Database locked
**Solution**: Make sure only one instance of the app is running

### Issue: Port 8000 already in use
**Solution**: Change port in run_django.py or use:
```bash
python manage.py runserver 8001
```

### Issue: Missing static files
**Solution**: Run `python manage.py collectstatic`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact & Support

For issues, questions, or suggestions, please open an issue on GitHub or contact the development team.

## Changelog

### Version 1.0.0
- Initial release
- Bill generation and management
- Customer management
- Inventory tracking
- Payment history
- GST compliance
- Desktop app with Electron

---

**Last Updated**: May 2026

**Status**: Active Development

**Maintainer**: Pritam Software
