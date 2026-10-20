const { spawn } = require('child_process')
const path = require('path')

const cwd = path.join(__dirname, '../backend/v1/file_analysis')
const python = path.join(cwd, 'venv_RAG/bin/python')

const proc = spawn(python, ['main.py'], {
  cwd,
  stdio: 'inherit'
})

proc.on('exit', (code) => {
  process.exit(code ?? 0)
})
