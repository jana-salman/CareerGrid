import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

const root = new URL('../', import.meta.url)
const read = (path) => readFile(new URL(path, root), 'utf8')

const contracts = {
  browser: [
    'browser-layout', 'browser-tab-strip', 'browser-page-tab', 'browser-toolbar',
    'browser-navigation', 'browser-address-form', 'browser-viewport',
    'browser-page', 'browser-devtools', 'browser-devtools-content',
  ],
  files: [
    'files-layout', 'files-sidebar', 'files-toolbar', 'files-content',
    'files-list-heading', 'files-row', 'files-preview', 'files-text-preview',
  ],
  github: [
    'github-toolbar', 'github-repository-picker', 'github-content',
    'github-repository-page', 'github-repository-header', 'github-tabs',
    'github-layout', 'github-section', 'github-pr-form', 'github-pr-detail',
  ],
  mail: [
    'mail-layout', 'mail-sidebar', 'mail-folder', 'mail-list-column',
    'mail-list-item', 'mail-list-topline', 'mail-list-subject',
    'mail-reading-pane', 'mail-message-view', 'mail-thread-message',
    'mail-thread-message-header', 'mail-thread-body', 'mail-composer',
    'mail-composer-footer',
  ],
  terminal: [
    'terminal-tab-bar', 'terminal-screen',
    'terminal-command-block', 'terminal-command-line', 'terminal-output',
    'terminal-command-bar',
  ],
  vscode: [
    'vscode-layout', 'vscode-activity-bar', 'vscode-sidebar',
    'vscode-file-tree', 'vscode-tree-row', 'vscode-tree-label',
    'vscode-tabs', 'vscode-tab', 'vscode-editor', 'vscode-code-wrapper',
    'vscode-line-numbers', 'vscode-code-editor', 'vscode-status-bar',
  ],
}

const componentFiles = {
  browser: 'BrowserApp.jsx',
  files: 'FilesApp.jsx',
  github: 'GitHubApp.jsx',
  mail: 'MailApp.jsx',
  terminal: 'TerminalApp.jsx',
  vscode: 'VSCodeApp.jsx',
}

test('React simulation applications retain the class contracts styled by legacy CSS', async () => {
  for (const [application, classNames] of Object.entries(contracts)) {
    const componentName = componentFiles[application].replace('.jsx', '')
    const [component, stylesheet] = await Promise.all([
      read(`src/simulation/apps/${componentFiles[application]}`),
      read(`../static/css/simulation/${application}.css`),
    ])
    for (const className of classNames) {
      assert.ok(component.includes(className), `${componentName}App must render .${className}`)
      assert.ok(stylesheet.includes(`.${className}`), `${application}.css must style .${className}`)
    }
  }
})

test('desktop windows use the legacy application and header class names', async () => {
  const desktop = await read('src/simulation/SimulationDesktop.jsx')
  for (const className of [
    'mail-window', 'files-window', 'vscode-window', 'browser-window',
    'terminal-app-window', 'github-app-window', 'guide-window',
    'mail-window-header', 'files-window-header', 'vscode-window-header',
    'terminal-app-header', 'github-app-header', 'workspace-clock', 'role-card',
  ]) assert.ok(desktop.includes(className), `desktop must retain .${className}`)
})

test('Vite proxies every Flask-served static stylesheet used by the React shell', async () => {
  const [index, viteConfig] = await Promise.all([
    read('index.html'),
    read('vite.config.js'),
  ])
  assert.match(viteConfig, /['"]\/static['"]\s*:/)
  for (const stylesheet of [
    'desktop', 'frontend_workplace', 'mail', 'files', 'vscode',
    'terminal', 'browser', 'github', 'snake',
  ]) assert.ok(index.includes(`/static/css/simulation/${stylesheet}.css`))
})

test('Mail keeps the ID selectors required for search and reply sizing', async () => {
  const mail = await read('src/simulation/apps/MailApp.jsx')
  assert.match(mail, /id="mail-search"/)
  assert.match(mail, /id="mail-reply-text"/)
})
