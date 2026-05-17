// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import Header from './Header'

vi.mock('./AuthProvider', () => ({
  useAuth: () => ({ user: { full_name: 'Admin' }, logout: vi.fn() }),
}))

describe('Header', () => {
  it('renders PLAYBOOK branding', () => {
    render(<Header />)
    expect(screen.getByText('PLAYBOOK')).toBeDefined()
  })
})
