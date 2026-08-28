async function copyPullRequestLink(url, options = {}) {
  const clipboard = options.clipboard ?? globalThis.navigator?.clipboard
  const prompt = options.prompt ?? globalThis.prompt
  try {
    if (!clipboard?.writeText) throw new Error('Clipboard API unavailable.')
    await clipboard.writeText(url)
    return { copied: true, url }
  } catch {
    if (typeof prompt === 'function') prompt('Copy this pull request link:', url)
    return { copied: false, usedPrompt: true, url }
  }
}

export { copyPullRequestLink }
