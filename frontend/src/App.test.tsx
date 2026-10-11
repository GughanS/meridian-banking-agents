import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders Meridian Banking', () => {
    render(<App />)
    expect(screen.getByText('Meridian Banking')).toBeDefined()
  })
})
