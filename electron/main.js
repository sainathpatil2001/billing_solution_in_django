const { app, BrowserWindow, Menu, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const isDev = process.env.NODE_ENV === 'development';

let mainWindow;
let djangoProcess;

// Keep a global reference of the window object
function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      webSecurity: true
    },
    icon: path.join(__dirname, '../assets/icon.png'),
    titleBarStyle: 'default',
    show: false // Don't show until ready
  });

  // Load the Django app
  const startUrl = 'http://localhost:8000';

  // Try to load the URL with retry logic
  const loadWithRetry = (retries = 5) => {
    mainWindow.loadURL(startUrl).then(() => {
      mainWindow.show();

      // Open DevTools in development
      if (isDev) {
        mainWindow.webContents.openDevTools();
      }
    }).catch(err => {
      console.error('Failed to load URL (attempt ' + (6 - retries) + '):', err);

      if (retries > 0) {
        // Retry after 2 seconds
        setTimeout(() => {
          loadWithRetry(retries - 1);
        }, 2000);
      } else {
        dialog.showErrorBox('Connection Error', 'Failed to connect to Django server. Please make sure the server is running on http://localhost:8000');
      }
    });
  };

  loadWithRetry();

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Create application menu
  createMenu();
}

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'New Bill',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            mainWindow.loadURL('http://localhost:8000/billing/');
          }
        },
        {
          label: 'Search Bills',
          accelerator: 'CmdOrCtrl+F',
          click: () => {
            mainWindow.loadURL('http://localhost:8000/billing/bills/');
          }
        },
        {
          label: 'Inventory',
          accelerator: 'CmdOrCtrl+I',
          click: () => {
            mainWindow.loadURL('http://localhost:8000/inventory_management/');
          }
        },
        { type: 'separator' },
        {
          label: 'Business Settings',
          click: () => {
            mainWindow.loadURL('http://localhost:8000/billing/business-settings/');
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectall' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Window',
      submenu: [
        { role: 'minimize' },
        { role: 'close' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About Billing System',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About Billing System',
              message: 'Billing System Desktop Application',
              detail: 'Version 1.0.0\nA comprehensive billing and inventory management system.'
            });
          }
        },
        { type: 'separator' },
        {
          label: 'License & Activation',
          click: () => {
            mainWindow.loadURL('http://localhost:8000/billing/business-settings/');
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

function startDjangoServer() {
  return new Promise((resolve, reject) => {
    console.log('Starting Django server...');

    // Use the Python executable from the system
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';

    djangoProcess = spawn(pythonCmd, ['manage.py', 'runserver', '8000'], {
      cwd: path.join(__dirname, '..'),
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let serverReady = false;

    djangoProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log('Django:', output);

      // Check if server is ready - look for the specific Django startup message
      if (output.includes('Starting development server at http://127.0.0.1:8000/') ||
        output.includes('Starting development server at http://localhost:8000/') ||
        output.includes('Quit the server with CTRL-BREAK')) {
        if (!serverReady) {
          serverReady = true;
          console.log('Django server is ready!');
          setTimeout(() => resolve(), 1000); // Wait 1 second for server to be fully ready
        }
      }
    });

    djangoProcess.stderr.on('data', (data) => {
      const error = data.toString();
      console.error('Django Error:', error);

      // Some Django messages go to stderr but are not errors
      if (error.includes('Watching for file changes') ||
        error.includes('Starting development server')) {
        // These are normal Django messages, not errors
        return;
      }
    });

    djangoProcess.on('error', (err) => {
      console.error('Failed to start Django server:', err);
      reject(err);
    });

    djangoProcess.on('close', (code) => {
      console.log(`Django server exited with code ${code}`);
    });

    // Timeout after 15 seconds (reduced from 30)
    setTimeout(() => {
      if (!serverReady) {
        reject(new Error('Django server startup timeout'));
      }
    }, 15000);
  });
}

// App event handlers
// App event handlers
app.whenReady().then(async () => {
  try {
    // Start Django server in background and WAIT for it
    await startDjangoServer();
    createWindow();

  } catch (error) {
    console.error('Failed to start application:', error);
    dialog.showErrorBox('Startup Error', 'Failed to start the Django server.\n\nError: ' + error.message + '\n\nPlease ensure Python is installed and added to PATH.');
    app.quit();
  }
});

app.on('window-all-closed', () => {
  // Kill Django process
  if (djangoProcess) {
    djangoProcess.kill();
  }

  // On macOS, keep app running even when all windows are closed
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On macOS, re-create window when dock icon is clicked
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', () => {
  // Kill Django process before quitting
  if (djangoProcess) {
    djangoProcess.kill();
  }
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
    shell.openExternal(navigationUrl);
  });
});

