import React from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { DashboardPage } from '@/pages/DashboardPage'
import { TopologyPage } from '@/pages/TopologyPage'
import { DevicesPage } from '@/pages/DevicesPage'
import { AlertsPage } from '@/pages/AlertsPage'
import { CopilotPage } from '@/pages/CopilotPage'
import { SettingsPage } from '@/pages/SettingsPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'topology',
        element: <TopologyPage />,
      },
      {
        path: 'devices',
        element: <DevicesPage />,
      },
      {
        path: 'alerts',
        element: <AlertsPage />,
      },
      {
        path: 'copilot',
        element: <CopilotPage />,
      },
      {
        path: 'settings',
        element: <SettingsPage />,
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
])
