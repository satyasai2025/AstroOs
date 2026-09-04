// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'astroos-web',
      script: 'cmd.exe',
      args: '/c npm run dev',
      cwd: './apps/web',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      env: {
        NODE_ENV: 'development',
      },
      max_memory_restart: '512M',
      error_file: './logs/web-error.log',
      out_file: './logs/web-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
    {
      name: 'astroos-api',
      script: 'cmd.exe',
      args: '/c python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8001',
      cwd: '.',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      env: {
        NODE_ENV: 'development',
      },
      max_memory_restart: '512M',
      error_file: './logs/api-error.log',
      out_file: './logs/api-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
  ],
}
