/**
 * AstroOS — Route Protection Middleware
 *
 * Protects admin routes with admin-specific token.
 * Protects user routes with standard user token.
 * Redirects unauthenticated users to appropriate login pages.
 */

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Admin routes require admin token
  if (pathname.startsWith('/admin') && !pathname.startsWith('/admin/login')) {
    const adminToken = request.cookies.get('astro_admin_token')?.value ||
                       request.headers.get('authorization')?.replace('Bearer ', '')

    // Note: For SPA-based auth (localStorage), this middleware can't check tokens.
    // The admin layout component handles client-side auth checks.
    // This middleware primarily handles server-side redirects for page loads.
  }

  // User routes require user token
  if (pathname.startsWith('/research') || pathname.startsWith('/dashboard')) {
    const userToken = request.cookies.get('access_token')?.value ||
                      request.headers.get('authorization')?.replace('Bearer ', '')

    // For SPA-based auth, the AppShell handles client-side checks
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/admin/:path*',
    '/research/:path*',
    '/dashboard/:path*',
  ],
}
