import React, { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ActionIcon, Button, Stack, TextInput, Title } from '@mantine/core'
import { IconCapture } from '@tabler/icons-react'
import { Link } from 'react-router-dom'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'

const Capture = () => {
  const queryClient = useQueryClient()

  const form = useForm({
    mode: 'uncontrolled',
    initialValues: {
      todo: ''
    }
  })

  const addTodo = async (todo: string) => {
    const mutate = await window.electron.ipcRenderer.invoke('add-todo', todo)
    return mutate
  }

  const test = async () => {
    const todos = await window.electron.ipcRenderer.invoke('get-todos')
    return todos
  }

  const mutation = useMutation({
    mutationFn: addTodo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] })
      notifications.show({
        title: 'Success',
        message: 'Hey there, your todo got added!'
      })
    },
    onError: () => {
      notifications.show({
        title: 'Error',
        message: 'Hey there, there was an error adding your todo!'
      })
    }
  })

  const todos = useQuery({ queryKey: ['todos'], queryFn: test })

  if (todos.isLoading) return <div>Loading...</div>
  if (todos.isError) return <div>Error: {todos.error}</div>

  return (
    <Stack gap="xl">
      <Title size="xl">Capture</Title>
      <ActionIcon variant="filled" size="xl" radius="xl" aria-label="Settings">
        <IconCapture style={{ width: '70%', height: '70%' }} stroke={1.5} />
      </ActionIcon>
      <Button variant="outline" component={Link} to="/">
        back to Home
      </Button>
      <form
        onSubmit={form.onSubmit((values) => {
          mutation.mutate(values.todo)
        })}
      >
        <TextInput
          withAsterisk
          label="Todo"
          key={form.key('todo')}
          {...form.getInputProps('todo')}
        />

        <Button loading={mutation.isPending} type="submit">
          Submit
        </Button>
      </form>
      {todos && todos.data && todos.data.map((todo) => <div key={todo.id}>{todo.todo}</div>)}
    </Stack>
  )
}

export default Capture
