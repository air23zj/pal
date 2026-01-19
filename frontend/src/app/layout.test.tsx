import { render } from '@testing-library/react'
import RootLayout from './layout'

// Mock next/font/google
jest.mock('next/font/google', () => ({
  Inter: () => ({ className: 'inter-font' }),
}))

describe('RootLayout', () => {
  it('renders the layout with children', () => {
    const { getByText } = render(
      <RootLayout>
        <div>Test Child</div>
      </RootLayout>
    )

    expect(getByText('Test Child')).toBeInTheDocument()
  })

  it('has internal font class name on body', () => {
    const { container } = render(
      <RootLayout>
        <div />
      </RootLayout>
    )

    const body = container.querySelector('body')
    expect(body).toHaveClass('inter-font')
  })

  it('renders correct lang attribute', () => {
    const { container } = render(
      <RootLayout>
        <div />
      </RootLayout>
    )

    const html = container.querySelector('html')
    expect(html).toHaveAttribute('lang', 'en')
  })
})
