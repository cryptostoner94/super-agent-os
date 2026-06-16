/** @type {import('next').NextConfig} */
const _rawApi = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const TRUSTED_API = /^https?:\/\/[\w.:-]+$/.test(_rawApi) ? _rawApi : 'http://localhost:8000'

module.exports = {
  reactStrictMode: true,
  async rewrites() {
    return [
      { source: '/api/backend/:path*', destination: `${TRUSTED_API}/:path*` },
    ]
  },
}
