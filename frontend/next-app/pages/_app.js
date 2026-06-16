import '../styles/globals.css'
import Layout from '../components/Layout'
import { ThemeContext } from '../lib/theme'
import { useState, useEffect } from 'react'

export default function App({ Component, pageProps }) {
  const [theme, setTheme] = useState('dark')

  useEffect(() => {
    const saved = localStorage.getItem('theme') || 'dark'
    setTheme(saved)
    document.documentElement.setAttribute('data-theme', saved)
  }, [])

  function toggleTheme() {
    const next = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    localStorage.setItem('theme', next)
    document.documentElement.setAttribute('data-theme', next)
  }

  const NoLayout = Component.noLayout
  const content = NoLayout
    ? <Component {...pageProps} />
    : <Layout><Component {...pageProps} /></Layout>

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {content}
    </ThemeContext.Provider>
  )
}
