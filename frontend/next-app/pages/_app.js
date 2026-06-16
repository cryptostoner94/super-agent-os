import '../styles/globals.css'
import Layout from '../components/Layout'

export default function App({ Component, pageProps }) {
  const NoLayout = Component.noLayout
  if (NoLayout) return <Component {...pageProps} />
  return (
    <Layout>
      <Component {...pageProps} />
    </Layout>
  )
}
