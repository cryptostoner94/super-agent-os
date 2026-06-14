/** @type {import('next').NextConfig} */
module.exports = {
  reactStrictMode: true,
  async rewrites() {
    const api = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    return [
      { source: '/api/backend/:path*', destination: `${api}/:path*` },
    ]
  },
}
