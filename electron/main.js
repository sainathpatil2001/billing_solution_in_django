const { app, BrowserWindow, Menu, shell, dialog, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

const isDev = !app.isPackaged;

let mainWindow;
let splashWindow;
let djangoProcess;

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 600,
    height: 400,
    frame: false,
    transparent: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false // Allowed for internal splash screen
    },
    icon: path.join(__dirname, '../assets/icon.png'),
    alwaysOnTop: true
  });

  splashWindow.loadFile(path.join(__dirname, 'splash.html'));

  splashWindow.on('closed', () => {
    splashWindow = null;
  });
}

function createWindow() {
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
    show: false
  });

  const startUrl = 'http://localhost:8000';

  const loadWithRetry = (retries = 5) => {
    mainWindow.loadURL(startUrl).then(() => {
      // Server is definitely up, show main window
      if (splashWindow) {
        splashWindow.close();
      }
      mainWindow.show();

      if (isDev) {
        mainWindow.webContents.openDevTools();
      }
    }).catch(err => {
      console.error('Failed to load URL (attempt ' + (6 - retries) + '):', err);
      if (retries > 0) {
        setTimeout(() => loadWithRetry(retries - 1), 2000);
      } else {
        dialog.showErrorBox('Connection Error', 'Failed to connect to Django server.');
      }
    });
  };

  loadWithRetry();

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

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
          click: () => { mainWindow.loadURL('http://localhost:8000/billing/'); }
        },
        {
          label: 'Search Bills',
          accelerator: 'CmdOrCtrl+F',
          click: () => { mainWindow.loadURL('http://localhost:8000/billing/bills/'); }
        },
        {
          label: 'Inventory',
          accelerator: 'CmdOrCtrl+I',
          click: () => { mainWindow.loadURL('http://localhost:8000/inventory_management/'); }
        },
        { type: 'separator' },
        {
          label: 'Business Settings',
          click: () => { mainWindow.loadURL('http://localhost:8000/billing/business-settings/'); }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => { app.quit(); }
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' }, { role: 'redo' }, { type: 'separator' },
        { role: 'cut' }, { role: 'copy' }, { role: 'paste' }, { role: 'selectall' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' }, { role: 'forceReload' }, { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Window',
      submenu: [{ role: 'minimize' }, { role: 'close' }]
    }
  ];
  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

function startDjangoServer() {
  return new Promise((resolve, reject) => {
    const log = (msg) => {
      console.log(msg);
      if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.webContents.send('log-message', msg);
      }
    };

    const logError = (msg) => {
      console.error(msg);
      if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.webContents.send('log-error', msg);
      }
    };

    log('Starting Django server process...');

    let spawnCmd;
    let spawnArgs = [];
    let cwdOption = undefined;

    if (isDev) {
      spawnCmd = process.platform === 'win32' ? 'python' : 'python3';
      spawnArgs = ['manage.py', 'runserver', '8000'];
      cwdOption = path.join(__dirname, '..');
      log('Mode: Development');
    } else {
      const resourcesPath = process.resourcesPath;
      if (process.platform === 'win32') {
        spawnCmd = path.join(resourcesPath, 'django_app', 'django_app.exe');
      } else {
        spawnCmd = path.join(resourcesPath, 'django_app', 'django_app');
      }
      log('Mode: Production');
      log(`Executable: ${spawnCmd}`);

      if (!fs.existsSync(spawnCmd)) {
        reject(new Error(`Executable not found at: ${spawnCmd}`));
        return;
      }
    }

    try {
      djangoProcess = spawn(spawnCmd, spawnArgs, {
        cwd: cwdOption,
        stdio: ['ignore', 'pipe', 'pipe'], // Ignore stdin to prevent hanging
        env: { ...process.env, PYTHONUNBUFFERED: '1', DJANGO_SETTINGS_MODULE: 'bill_maker.settings' }
      });
    } catch (e) {
      logError(`Failed to spawn process: ${e.message}`);
      reject(e);
      return;
    }

    let serverReady = false;

    djangoProcess.stdout.on('data', (data) => {
      const output = data.toString();
      log(output.trim());

      if (output.includes('Starting development server') ||
        output.includes('Quit the server with CTRL-BREAK')) {
        if (!serverReady) {
          serverReady = true;
          log('Server is ready signal received.');
          if (splashWindow && !splashWindow.isDestroyed()) {
            splashWindow.webContents.send('server-ready');
          }
          setTimeout(resolve, 2000); // Give it a moment to actually bind
        }
      }
    });

    djangoProcess.stderr.on('data', (data) => {
      const error = data.toString();
      // Filter out non-error standard logs if needed, but showing everything is safer for debugging
      logError(error.trim());
    });

    djangoProcess.on('error', (err) => {
      logError(`Process error: ${err.message}`);
      reject(err);
    });

    djangoProcess.on('close', (code) => {
      log(`Django server exited with code ${code}`);
      if (!serverReady) {
        reject(new Error(`Server exited prematurely with code ${code}`));
      }
    });
  });
}

app.whenReady().then(async () => {
  createSplashWindow();

  try {
    await startDjangoServer();
    createWindow();
  } catch (error) {
    console.error('Failed to start:', error);
    // Keep splash open to show error, or show dialog
    // We decide to show dialog, but the splash logs are visible behind it
    dialog.showMessageBox(splashWindow || mainWindow, {
      type: 'error',
      title: 'Startup Error',
      message: 'Failed to start the Django server.',
      detail: error.message
    });
    // Do not quit immediately so user can read logs
  }
});

app.on('window-all-closed', () => {
  if (djangoProcess) djangoProcess.kill();
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  if (djangoProcess) djangoProcess.kill();
});


