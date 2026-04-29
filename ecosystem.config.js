module.exports = {
  apps: [
    {
      name: 'parser-service',
      script: 'scripts/start-parser.js',
      cwd: 'D:/pengpengRAG',
      watch: false,
      windowsHide: true,
      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'qa-service',
      script: 'scripts/start-qa.js',
      cwd: 'D:/pengpengRAG',
      watch: false,
      windowsHide: true,
      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'frontend',
      script: 'scripts/start-frontend.js',
      cwd: 'D:/pengpengRAG',
      watch: false,
      windowsHide: true
    }
  ]
}
