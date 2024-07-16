import {
  app,
  shell,
  BrowserWindow,
  ipcMain,
  globalShortcut,
  desktopCapturer,
  screen
} from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'
import supabase from '../../utils/supabase'
import sharp from 'sharp'
import { decode } from 'base64-arraybuffer'
import { v4 as uuidv4 } from 'uuid'
const Store = (...args) => import('electron-store').then(({ default: Store }) => new Store(...args))
let mainWindow: BrowserWindow

function createWindow(): void {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 900,
    height: 670,
    show: false,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      webSecurity: false
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // HMR for renderer base on electron-vite cli.
  // Load the remote URL for development or the local html file for production.
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

async function takeScreenshot(receivedSourceId: string) {
  const mousePosition = screen.getCursorScreenPoint() // Capture mouse position

  desktopCapturer
    .getSources({ types: ['window', 'screen'], thumbnailSize: { width: 1920, height: 1080 } })
    .then(async (sources) => {
      for (const source of sources) {
        if (source.id !== receivedSourceId) {
          return
        }
        // Capture the screen
        try {
          const image = source.thumbnail.toPNG()
          console.log('Screenshot taken at')

          // Create a circle overlay as SVG
          const circleOverlay = `<svg width="1920" height="1080">
  <circle cx="${mousePosition.x}" cy="${mousePosition.y}" r="35" fill="rgba(255, 0, 0, 0.2)" stroke="red" stroke-width="3"/>
</svg>`

          // Use sharp to overlay the circle on the screenshot
          const buffer = await sharp(image)
            .composite([{ input: Buffer.from(circleOverlay), top: 0, left: 0 }])
            .toBuffer()

          // Correctly convert buffer to base64 string and then decode to ArrayBuffer
          const base64Image = buffer.toString('base64')
          /* const decodedImage = decode(base64Image) */

          /*  const { data, error } = await supabase.storage
            .from('steps')
            .upload(`step_${uuidv4()}.png`, decodedImage, {
              contentType: 'image/png'
            })
          if (error) {
            console.error('Error uploading file: ', error)
          } */

          /* const newTodo = await supabase
            .from('todos')
            .insert({ todo: 'test', image: data?.fullPath })
          if (error) {
            console.error('Error getting todos: ', error)
            throw new Error('Error getting todos')
          } */

          mainWindow.webContents.send('screenshot-captured', base64Image)
        } catch (e) {
          console.error('Failed to save screenshot', e)
        }
      }
    })
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  // Set app user model id for windows
  electronApp.setAppUserModelId('com.electron')

  // Default open or close DevTools by F12 in development
  // and ignore CommandOrControl + R in production.
  // see https://github.com/alex8088/electron-toolkit/tree/master/packages/utils
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  app.commandLine.appendSwitch('disable-web-security')

  createWindow()

  app.commandLine.appendSwitch('disable-web-security')

  ipcMain.on('start-capture', (event, { shortcut, receivedSourceId }) => {
    globalShortcut.unregisterAll() // Unregister all shortcuts to avoid conflicts
    mainWindow.minimize() // Minimize the main window before taking the screenshot
    globalShortcut.register(shortcut, () => takeScreenshot(receivedSourceId))
  })

  ipcMain.on('stop-capture', async (event, { screenshots }) => {
    const uploadedImagePaths = []

    for (const base64Image of screenshots) {
      const decodedImage = decode(base64Image) // Ensure 'decode' correctly decodes your base64 image

      // Upload each screenshot
      const { data, error } = await supabase.storage
        .from('steps')
        .upload(`step_${uuidv4()}.png`, decodedImage, {
          contentType: 'image/png'
        })

      if (error) {
        console.error('Error uploading file: ', error)
        return // Stop execution and log error
      }

      // Add the path of the uploaded image to the array
      if (data?.path) {
        uploadedImagePaths.push(data.path)
      }
    }

    // After all screenshots are uploaded, insert their paths into the 'todos' table
    const todosInsertData = uploadedImagePaths.map((path) => ({
      todo: 'test', // Assuming 'test' is a placeholder, replace or modify as needed
      image: path
    }))

    const { error: insertError } = await supabase.from('todos').insert(todosInsertData)

    if (insertError) {
      console.error('Error inserting todos: ', insertError)
    }
    globalShortcut.unregisterAll() // Unregister the shortcut when capture is stopped
  })

  ipcMain.on('sign-in', async () => {
    const store = await Store()
    const { data, error } = await supabase.auth.signInWithPassword({
      email: 'marcellusstack@gmail.com',
      password: 'AMOSVs1357"ma'
    })
    if (error) {
      console.error('Error signing in: ', error)
      return
    }

    store.set('access_token', data.session.access_token)
    store.set('refresh_token', data.session.refresh_token)

    console.log('Signed in: ', data)
  })

  ipcMain.on('sign-out', async () => {
    const store = await Store()
    const { error } = await supabase.auth.signOut()
    if (error) {
      console.error('Error signing in: ', error)
      return
    }
    store.set('access_token', null)
    store.set('refresh_token', null)
  })

  ipcMain.on('get-session', async () => {
    const { data, error } = await supabase.auth.getSession()

    if (error) {
      console.error('Error signing in: ', error)
    }
    console.log('Get Session: ', data)
  })

  ipcMain.on('set-session', async () => {
    const store = await Store()
    const access_token = store.get('access_token') as string
    const refresh_token = store.get('refresh_token') as string
    const { data, error } = await supabase.auth.setSession({
      access_token,
      refresh_token
    })

    if (error) {
      console.error('Error signing in: ', error)
      return
    }
    store.set('access_token', data.session.access_token)
    store.set('refresh_token', data.session.refresh_token)
    console.log('Signed in: ', data)
  })

  ipcMain.on('get-store', async () => {
    const store = await Store()
    const access_token = store.get('access_token') as string
    const refresh_token = store.get('refresh_token') as string
    console.log('Access Token: ', access_token, 'Refresh Token: ', refresh_token)
  })

  ipcMain.on('get-sources', async (event, options) => {
    const sources = await desktopCapturer.getSources(options)
    const transformedSources = sources.map((source) => ({ value: source.id, label: source.name }))
    mainWindow.webContents.send('got-sources', transformedSources)
  })

  ipcMain.handle('get-todos', async () => {
    const { data, error } = await supabase.from('todos').select('*')
    if (error) {
      console.error('Error getting todos: ', error)
      throw new Error('Error getting todos')
    }
    console.log(data)
    return data
  })

  ipcMain.handle('add-todo', async (event, todo) => {
    console.log(todo)
    const { data, error } = await supabase.from('todos').insert({ todo: todo })
    if (error) {
      console.error('Error getting todos: ', error)
      throw new Error('Error getting todos')
    }

    return data
  })

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })

  // Listening to 'mouse-click' event triggered by renderer process
})

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  globalShortcut.unregisterAll()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// In this file you can include the rest of your app"s specific main process
// code. You can also put them in separate files and require them here.
