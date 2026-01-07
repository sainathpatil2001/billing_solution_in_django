# Billing System Desktop Application

This is a desktop version of the Django-based billing system, packaged using Electron.

## Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- Django dependencies installed

## Installation

1. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Development

### Running in Development Mode

```bash
npm run dev
```

This will:
- Start the Django development server on port 8000
- Launch the Electron app
- Open developer tools for debugging

### Running Django Server Only

```bash
npm run django
```

### Running Electron Only (Django must be running)

```bash
npm start
```

## Building for Production

### Build for Current Platform

```bash
npm run build
```

### Build for Specific Platforms

```bash
# Windows
npm run build-win

# macOS
npm run build-mac

# Linux
npm run build-linux
```

## Project Structure

```
billing_solution_in_django/
├── electron/
│   └── main.js              # Electron main process
├── bill_maker/              # Django project settings
├── genrate_bill/            # Billing app
├── inventory/               # Inventory app
├── package.json             # Node.js dependencies
├── requirements.txt         # Python dependencies
├── electron-builder.json    # Build configuration
└── README-ELECTRON.md       # This file
```

## Features

- **Native Desktop App**: Runs as a standalone desktop application
- **Auto-start Django**: Automatically starts the Django server
- **Native Menus**: Desktop-style application menus
- **Keyboard Shortcuts**: Common shortcuts for better UX
- **Cross-platform**: Works on Windows, macOS, and Linux

## Keyboard Shortcuts

- `Ctrl+N` (Cmd+N on Mac): New Bill
- `Ctrl+F` (Cmd+F on Mac): Search Bills
- `Ctrl+I` (Cmd+I on Mac): Inventory Management
- `Ctrl+Q` (Cmd+Q on Mac): Quit Application
- `F11`: Toggle Fullscreen
- `Ctrl+R` (Cmd+R on Mac): Reload

## Troubleshooting

### Django Server Won't Start

1. Check if Python is installed and in PATH
2. Verify Django dependencies are installed: `pip install -r requirements.txt`
3. Check if port 8000 is available

### Electron App Won't Load

1. Make sure Django server is running on http://localhost:8000
2. Check browser console for errors
3. Try running Django server manually first

### Build Issues

1. Make sure all dependencies are installed
2. Check that all required files are present
3. Verify Python and Node.js versions are compatible

## Distribution

The built applications will be in the `dist/` folder:

- **Windows**: `.exe` installer
- **macOS**: `.dmg` disk image
- **Linux**: `.AppImage` portable application

## Customization

### Changing App Icon

Replace the icon files in the `assets/` folder:
- `icon.ico` (Windows)
- `icon.icns` (macOS)
- `icon.png` (Linux)

### Modifying App Settings

Edit `electron/main.js` to change:
- Window size and properties
- Menu items
- Keyboard shortcuts
- Startup behavior

## Support

For issues related to:
- **Django**: Check Django documentation
- **Electron**: Check Electron documentation
- **This Project**: Create an issue in the project repository

