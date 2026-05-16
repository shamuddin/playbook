// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { apiFetch } from '../utils/api'
import JudgePage from './JudgePage'

vi.mock('../utils/api')

vi.mock('../utils/config', () => ({
  getApiBase: () => 'http://localhost:8000/api/v1',
}))

describe('JudgePage', () => {
  it('renders Judge Layer heading', async () => {
    vi.mocked(apiFetch).mockImplementation((url: string) => {
      if (url.includes('/judge/stats')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            total_decisions: 200,
            verdict_distribution: { ALLOW: 150, DENY: 30, QUARANTINE: 15, ESCALATE: 5 },
            avg_latency_ms: 10.5,
            p95_latency_ms: 25.0,
            bypass_attempts_blocked: 12,
          }),
        } as Response)
      }
      if (url.includes('/judge/bypass-patterns')) {
        return Promise.resolve({ ok: true, json: async () => [] } as Response)
      }
      if (url.includes('/judge/bypass-attempts')) {
        return Promise.resolve({ ok: true, json: async () => [] } as Response)
      }
      return Promise.resolve({ ok: false, json: async () => null } as Response)
    })

    render(<JudgePage />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Judge Layer/i })).toBeDefined()
    })
  })
})
