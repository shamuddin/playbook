// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { apiFetch } from '../utils/api'
import DashboardPage from './DashboardPage'

vi.mock('../utils/api')

vi.mock('../hooks/useWebSocket', () => ({
  useWebSocket: () => ({ connected: false, messages: [], send: vi.fn() }),
}))

vi.mock('../utils/config', () => ({
  getApiBase: () => 'http://localhost:8000/api/v1',
  getRefreshInterval: () => 0,
}))

describe('DashboardPage', () => {
  it('renders Dashboard heading and overview stats', async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        data: {
          overview: {
            total_incidents: 42,
            open_incidents: 5,
            resolved_incidents: 37,
            critical_alerts: 2,
          },
          incidents: {
            by_severity: { critical: 2, high: 8, medium: 15, low: 17 },
            by_status: { open: 5, resolved: 37 },
            trend: { direction: 'decreasing', change_percent: 12 },
          },
          agents: {
            total: 8,
            online: 6,
            degraded: 1,
            offline: 1,
            avg_health_score: 92,
          },
          judge_layer: {
            total_decisions: 150,
            bypasses_detected: 3,
            avg_latency_ms: 12.5,
            allow_rate: 0.85,
            deny_rate: 0.1,
          },
          playbooks: {
            total: 10,
            active: 7,
            success_rate: 0.95,
          },
        },
      }),
    } as Response)

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Dashboard/i })).toBeDefined()
    })

    expect(screen.getByText('Total Incidents')).toBeDefined()
    expect(screen.getByText('Critical Alerts')).toBeDefined()
    expect(screen.getByText('Agent Health')).toBeDefined()
    expect(screen.getByText('Judge Decisions')).toBeDefined()
  })
})
