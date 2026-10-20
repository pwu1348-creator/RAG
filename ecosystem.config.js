module.exports = {
  apps: [
    {
      name: 'parser-service',
      script: 'scripts/start-parser.js',
      cwd: '/home/wsp/pengpengRAG',
      watch: false,
      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'qa-service',
      script: 'scripts/start-qa.js',
      cwd: '/home/wsp/pengpengRAG',
      watch: false,
      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'frontend',
      script: 'scripts/start-frontend.js',
      cwd: '/home/wsp/pengpengRAG',
      watch: false
    }
  ]
}
