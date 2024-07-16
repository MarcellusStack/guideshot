import './assets/main.css'
import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { createHashRouter, RouterProvider, Link } from 'react-router-dom'
import { ActionIcon, Button, MantineProvider, Stack, Title } from '@mantine/core'
import { IconCapture } from '@tabler/icons-react'
import { ModalsProvider } from '@mantine/modals'
import Versions from './components/Versions'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Capture from './components/Capture'
import { Notifications } from '@mantine/notifications'

const queryClient = new QueryClient()

const router = createHashRouter([
  {
    path: '/',
    element: (
      <Stack gap="xl">
        <Versions />
        <Title size="xl">GuideShot</Title>
        <Button component={Link} to="/capture">
          Start
        </Button>
      </Stack>
    )
  },
  {
    path: '/capture',
    element: <Capture />
  }
])

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <MantineProvider>
        <Notifications />
        <ModalsProvider>
          <RouterProvider router={router} />
        </ModalsProvider>
      </MantineProvider>
    </QueryClientProvider>
  </React.StrictMode>
)
