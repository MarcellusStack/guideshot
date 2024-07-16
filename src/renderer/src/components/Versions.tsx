import { Button, Select, Stack, Title, Text } from '@mantine/core'
import { useField } from '@mantine/form'
import supabase from '../../../../utils/supabase'
import { useEffect, useState } from 'react'
import { decode } from 'base64-arraybuffer'
import { v4 as uuidv4 } from 'uuid'

function Versions(): JSX.Element {
  const [isCapturing, setIsCapturing] = useState(false)
  const [screenshots, setScreenshots] = useState([])
  const [sources, setSources] = useState([])
  const [error, setError] = useState('')

  const field = useField({
    initialValue: '',
    validate: (value) => (value.trim().length === 0 ? 'Please select a shortcut' : null)
  })

  const field2 = useField({
    initialValue: '',
    validate: (value) => (value.trim().length === 0 ? 'Please select a device' : null)
  })

  const startCapture = async () => {
    field.validate()
    field2.validate()

    if (field.getValue() === '' || field2.getValue() === '') {
      return
    }
    setIsCapturing(true)
    window.electron.ipcRenderer.send('start-capture', {
      shortcut: field.getValue(),
      receivedSourceId: field2?.getValue()
    })
  }

  const stopCapture = () => {
    setIsCapturing(false)
    window.electron.ipcRenderer.send('stop-capture', { screenshots })
  }

  const signIn = () => {
    window.electron.ipcRenderer.send('sign-in')
  }

  const getSession = () => {
    window.electron.ipcRenderer.send('get-session')
  }

  const setSession = () => {
    window.electron.ipcRenderer.send('set-session')
  }

  const getStore = () => {
    window.electron.ipcRenderer.send('get-store')
  }

  const signOut = () => {
    window.electron.ipcRenderer.send('sign-out')
  }

  useEffect(() => {
    const handleScreenshot = async (event, base64Image: string): Promise<void> => {
      console.log('Uploading Image')
      setScreenshots((prevScreenshots) => [...prevScreenshots, base64Image])
    }

    window.electron.ipcRenderer.on('screenshot-captured', handleScreenshot)

    return () => {
      window.electron.ipcRenderer.removeAllListeners('screenshot-captured')
    }
  }, [])

  useEffect(() => {
    window.electron.ipcRenderer.send('get-sources', { types: ['window', 'screen'] })

    window.electron.ipcRenderer.on('got-sources', (event, sources) => {
      setSources(sources) // Now you can use this list to populate a select dropdown
    })

    return () => {
      window.electron.ipcRenderer.removeAllListeners('got-sources')
    }
  }, [])

  return (
    <Stack>
      <Title>Test </Title>
      <Select label="Select Shortcut" {...field2.getInputProps()} data={sources} />
      <Select
        label="Select Shortcut"
        {...field.getInputProps()}
        data={[
          { value: 'Space', label: 'Space' },
          { value: 'S', label: 'S' },
          { value: 'Ctrl+S', label: 'Ctrl+S' }
        ]}
      />
      <Text>{screenshots.length} Screenshots</Text>
      <Button onClick={startCapture} disabled={isCapturing}>
        Start Capture
      </Button>
      <Button onClick={stopCapture} disabled={!isCapturing}>
        Stop Capture
      </Button>
      <Button onClick={signIn}>Sign In</Button>
      <Button onClick={getSession}>Get Session</Button>
      <Button onClick={setSession}>Set Session</Button>
      <Button onClick={getStore}>Get Store</Button>
      <Button onClick={signOut}>Sign Out</Button>
      <Text>{error}</Text>
    </Stack>
  )
}

export default Versions
