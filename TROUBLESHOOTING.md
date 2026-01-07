# Desktop App Troubleshooting Guide

## Common Issues and Solutions

### 1. Django Server Won't Start

**Error**: `Failed to start Django server` or `Django server startup timeout`

**Solutions**:
1. **Check Python Installation**:
   ```bash
   python --version
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Check Port 8000**:
   - Make sure port 8000 is not being used by another application
   - Try running Django manually: `python manage.py runserver 8000`

4. **Database Issues**:
   ```bash
   python manage.py migrate
   ```

### 2. Electron App Won't Load

**Error**: `Failed to connect to Django server`

**Solutions**:
1. **Manual Start Method**:
   - Open two command prompts
   - In first: `python manage.py runserver 8000`
   - In second: `npm start`

2. **Use Batch File**:
   - Double-click `start-desktop-app.bat`

3. **Use PowerShell Script**:
   - Right-click `start-desktop-app.ps1` → "Run with PowerShell"

### 3. Node.js/npm Issues

**Error**: `npm is not recognized`

**Solutions**:
1. **Install Node.js**: Download from https://nodejs.org/
2. **Restart Command Prompt** after installation
3. **Check Installation**:
   ```bash
   node --version
   npm --version
   ```

### 4. Build Issues

**Error**: `electron-builder` fails

**Solutions**:
1. **Install Build Dependencies**:
   ```bash
   npm install
   ```

2. **Check Python Path**:
   - Make sure Python is in your system PATH

3. **Try Manual Build**:
   ```bash
   npm run build-win
   ```

## Alternative Startup Methods

### Method 1: Manual Two-Step Process
```bash
# Terminal 1: Start Django
python manage.py runserver 8000

# Terminal 2: Start Electron (after Django is running)
npm start
```

### Method 2: Use Batch File
```bash
# Double-click the batch file
start-desktop-app.bat
```

### Method 3: Use PowerShell Script
```bash
# Right-click and "Run with PowerShell"
start-desktop-app.ps1
```

### Method 4: Development Mode
```bash
# This should work with the improved code
npm run dev
```

## Testing Django Server

Test if Django is working:
```bash
# Start Django
python manage.py runserver 8000

# In another terminal, test connection
curl http://localhost:8000
```

You should see HTML content if Django is working.

## Testing Electron

Test if Electron is working:
```bash
# Make sure Django is running first
npm start
```

## Getting Help

1. **Check Console Output**: Look for error messages in the terminal
2. **Check Browser**: Try opening http://localhost:8000 in your browser
3. **Check Dependencies**: Make sure all packages are installed
4. **Restart**: Sometimes a simple restart helps

## System Requirements

- **Python**: 3.8 or higher
- **Node.js**: 16 or higher
- **Windows**: 10 or higher
- **Memory**: At least 4GB RAM
- **Disk Space**: At least 1GB free space
