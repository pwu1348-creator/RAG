const { spawn } = require('child_process')
const path = require('path')

const cwd = path.join(__dirname, '../frontend')

const proc = spawn('node', ['node_modules/vite/bin/vite.js', '--port', '3000', '--host'], {
  cwd,
  stdio: 'inherit'
})

proc.on('exit', (code) => {
  process.exit(code ?? 0)
})
