import { Stack, Title } from '@mantine/core'
import { useEffect, useState } from 'react'


function Screenshot(): JSX.Element {
  /* const [isCapturing, setIsCapturing] = useState(false)

  const startCapture = () => {
    setIsCapturing(true)
    ipcRenderer.send('start-capture')
  }

  const stopCapture = () => {
    setIsCapturing(false)
    ipcRenderer.send('stop-capture')
  }

  useEffect(() => {
    ipcRenderer.on('capture-status', (event, status) => {
      setIsCapturing(status)
    })

    ipcRenderer.on('screenshot-taken', (event, { screenshot, mousePos }) => {
      const img = new Image()
      img.src = `data:image/png;base64,${screenshot}`
      document.body.appendChild(img)
      console.log(`Screenshot taken at (${mousePos.x}, ${mousePos.y})`)
    })

    const handleClick = (event) => {
      if (isCapturing) {
        const mousePos = { x: event.clientX, y: event.clientY }
        ipcRenderer.send('mouse-click', mousePos)
      }
    }

    window.addEventListener('click', handleClick)

    return () => {
      ipcRenderer.removeAllListeners('capture-status')
      ipcRenderer.removeAllListeners('screenshot-taken')
      window.removeEventListener('click', handleClick)
    }
  }, [isCapturing]) */

  return (
    <Stack>
      <Title>Test</Title>
      {/* <button onClick={startCapture} disabled={isCapturing}>
        Start Capture
      </button>
      <button onClick={stopCapture} disabled={!isCapturing}>
        Stop Capture
      </button> */}
    </Stack>
  )
}

export default Screenshot
