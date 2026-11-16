import {
  branchSyncStatus,
  diffSnapshots,
  findPullRequestByUrl,
  pushedCommit,
  validatePullRequest,
} from './repositoryModel.js'

function copy(value) { return JSON.parse(JSON.stringify(value)) }

const SUBMISSION_ACKNOWLEDGEMENT = 'Thanks, I will treat this pull request as your final submission and begin the review.'
const MAIN_SUBMISSION_ACKNOWLEDGEMENT = 'Thanks, I will treat the work pushed to main as your final submission and begin the review.'
const PULL_REQUEST_CONFIRMATION = 'Just to confirm, is this the pull request you want me to review as your final submission?'

// One shared explanation used by Mail, the task brief, GitHub, and the terminal.
const SUBMISSION_OPTIONS = {
  pullRequest: [
    'Create a branch: git switch -c feature/<short-name>',
    'Edit and save files, then git add . and git commit -m "..."',
    'git push, then open a pull request in GitHub',
    'Reply to the task email with a short summary and the pull request link',
  ],
  main: [
    'Edit and save files while on main',
    'git add . and git commit -m "..."',
    'git push (this pushes main)',
    'Reply to the task email saying your work is ready on main, with a short summary',
  ],
}

const SUBMISSION_HELP = [
  'You can submit in either of two ways:',
  '',
  'Option A - pull request (recommended team practice):',
  ...SUBMISSION_OPTIONS.pullRequest.map((step, index) => `  ${index + 1}. ${step}`),
  '',
  'Option B - directly on main (no pull request link needed):',
  ...SUBMISSION_OPTIONS.main.map((step, index) => `  ${index + 1}. ${step}`),
  '',
  'Only committed and pushed work is reviewed. I will ask you to confirm before the final review starts.',
].join('\n')

function extractSimulatedPullRequestUrls(body) {
  const matches = String(body || '').match(/https:\/\/github\.com\/careergrid-sim\/[^\r\n]*?\/pull\/\d+(?=$|[\s)\],.!?;:])/gi) || []
  return [...new Set(matches.map((url) => url.replace(/[)\],.!?;:]+$/, '')))]
}

function normalizedAnswer(body) {
  return String(body || '').toLowerCase().replace(/[^a-z0-9\s']/g, ' ').replace(/\s+/g, ' ').trim()
}

function isAffirmativeSubmissionConfirmation(body) {
  return /^(?:yes|yep|yeah|yup|correct|affirmative|submit(?: it)?|that's (?:the one|it|final)|yes (?:this is it|that's (?:the pr|it|the one)|review (?:it|this)|final|please|submit(?: it)?))$/.test(normalizedAnswer(body))
}

function isSubmissionCancellation(body) {
  return /^(?:no|nope|cancel|cancel it|not yet|let me correct it|i need to correct it|wait|hold on)$/.test(normalizedAnswer(body))
}

const QUESTION_START = /^(?:how|what|where|when|why|which|who|should|shall|can|could|would|do|does|did|is|are|am|will|may|any idea)\b/
const NOT_READY = /\b(?:not (?:yet |quite )?(?:ready|done|finished|pushed|committed)|still (?:working|fixing|investigating|testing|need)|need to (?:finish|test|push|commit|fix)|haven'?t (?:pushed|finished|committed|tested)|have not (?:pushed|finished|committed)|will (?:push|submit|send)|going to (?:push|submit)|about to|almost (?:done|ready|finished)|in progress|working on|before i (?:submit|push))\b/
const SUBMISSION_INTENT = /\b(?:ready for (?:your |the |a )?(?:review|assessment|evaluation|final review)|ready to be (?:reviewed|assessed|evaluated)|(?:work|changes|fix|task|solution|it) (?:is|are) (?:ready|complete|done|finished)|(?:it's|its) (?:ready|done|finished)|final submission|(?:i'm|i am) (?:submitting|done)|(?:i )?(?:submit|submitting) (?:my|the|this) (?:work|changes|fix|solution|task)|please (?:review|assess|evaluate|check) (?:my|the|it)|pushed (?:it |my (?:work|changes|fix) |the (?:changes|fix|work) |everything )?(?:directly )?to (?:origin\/)?main|(?:work|changes|fix|commits?) (?:is|are) (?:on|in) (?:origin\/)?main|(?:finished|completed) the task)\b/

function sentencesOf(body) {
  return String(body || '')
    .toLowerCase()
    .split(/(?<=[.!?])\s+|\n+/)
    .map((sentence) => sentence.replace(/https?:\/\/\S+/g, '').trim())
    .filter(Boolean)
}

function isQuestionSentence(sentence) { return sentence.endsWith('?') || QUESTION_START.test(sentence) }

// Separates explicit submissions from questions and progress updates. Only an
// explicit, non-hedged statement that the work is ready counts as intent.
function classifyCompletionMessage(body) {
  const text = String(body || '')
  const lower = text.toLowerCase()
  const urls = extractSimulatedPullRequestUrls(text)
  const sentences = sentencesOf(text)
  if (urls.length) return { intent: 'pull_request', urls }
  const declarative = sentences.filter((sentence) => !isQuestionSentence(sentence))
  const explicit = declarative.some((sentence) => SUBMISSION_INTENT.test(sentence) && !NOT_READY.test(sentence))
  const mentionsMain = /\b(?:origin\/)?main\b/.test(lower)
  const mentionsPullRequest = /\bpull request\b|\bpr\b/.test(lower)
  if (explicit && !NOT_READY.test(lower)) return { intent: 'direct_submission', mentionsMain, mentionsPullRequest }
  if (sentences.length && sentences.every(isQuestionSentence)) {
    const aboutSubmitting = /\b(?:submit|submission|pull request|\bpr\b|main|push|deliver|hand in|send (?:my|the) work)\b/.test(lower)
    return { intent: aboutSubmitting ? 'submission_question' : 'question' }
  }
  if (NOT_READY.test(lower) || explicit) return { intent: 'progress' }
  return { intent: 'none' }
}

function communicationFlags(text) {
  const lower = text.toLowerCase()
  return {
    hasSummary: /found|identified|changed|updated|fixed|implemented|investigated|resolved|added|refactored/.test(lower)
      && text.replace(/https?:\/\/\S+/g, '').trim().split(/\s+/).filter(Boolean).length >= 8,
    hasVerification: /test|tested|testing|verify|verified|validation|reviewed|checked/.test(lower),
  }
}

function syncWarnings(status) {
  const warnings = []
  if (status?.uncommittedPaths?.length) warnings.push('uncommitted_changes')
  return warnings
}

function assessCompletionEmail(repository, body) {
  const text = String(body || '')
  const lower = text.toLowerCase()
  const urls = extractSimulatedPullRequestUrls(text)
  const reportedBranch = text.match(/(?:^|\n)\s*branch\s*:\s*([A-Za-z0-9._/-]+)/i)?.[1] || ''
  const pullRequest = urls.map((url) => findPullRequestByUrl(repository, url)).find(Boolean) || null
  const validatedPullRequest = validatePullRequest(repository, pullRequest)
  const looksLikeSubmission = urls.length > 0 || (Boolean(reportedBranch) && reportedBranch !== 'main' && /pull request|github|\bpr\b|pushed/.test(lower))
  const { hasSummary, hasVerification } = communicationFlags(text)
  const errors = []

  if (looksLikeSubmission && !urls.length) errors.push('missing_pull_request')
  if (urls.length && !pullRequest) errors.push('invalid_pull_request')
  if (pullRequest && !validatedPullRequest) {
    const compare = repository.branches[pullRequest.compareBranch]
    const base = repository.branches[pullRequest.baseBranch]
    if (pullRequest.status !== 'open') errors.push('pull_request_not_open')
    if (!compare) errors.push('missing_compare_branch')
    if (compare && !repository.remote.pushedBranches.includes(pullRequest.compareBranch)) errors.push('branch_not_pushed')
    if (base && compare) {
      const baseIds = new Set(base.commits.map((item) => item.id))
      if (!compare.commits.some((item) => !baseIds.has(item.id))) errors.push('no_compare_commits')
    }
  }
  if (pullRequest && reportedBranch && reportedBranch !== pullRequest.compareBranch) errors.push('branch_mismatch')
  const status = validatedPullRequest ? branchSyncStatus(repository, validatedPullRequest.compareBranch) : null
  if (status?.unpushedCommits.length) errors.push('unpushed_commits')
  return {
    errors,
    hasSummary,
    hasVerification,
    looksLikeSubmission,
    mode: 'pull_request',
    pullRequest: validatedPullRequest,
    reportedBranch,
    status,
    urls,
    validCandidate: looksLikeSubmission && Boolean(validatedPullRequest) && errors.length === 0,
    warnings: syncWarnings(status),
  }
}

// Direct-to-main: only the commit that has been pushed to main is reviewed, and
// it is compared with the immutable original project snapshot.
function assessMainSubmission(repository, body = '') {
  const { hasSummary, hasVerification } = communicationFlags(String(body || ''))
  const errors = []
  const status = branchSyncStatus(repository, repository.defaultBranch)
  const pushed = pushedCommit(repository, repository.defaultBranch)
  const baseline = repository.baseline
  let changedPaths = []
  if (!repository.workspace?.projectExtracted) errors.push('project_not_extracted')
  else if (!baseline?.snapshot) errors.push('baseline_unavailable')
  else if (!pushed) errors.push(status?.unpushedCommits.length ? 'main_not_pushed' : status?.uncommittedPaths.length ? 'uncommitted_only' : 'empty_submission')
  else {
    changedPaths = diffSnapshots(baseline.snapshot, pushed.snapshot).map((change) => change.path)
    if (status.unpushedCommits.length) errors.push('unpushed_commits')
    else if (!changedPaths.length) errors.push(status.uncommittedPaths.length ? 'uncommitted_only' : 'empty_submission')
  }
  const otherBranchesWithWork = Object.keys(repository.branches)
    .filter((name) => name !== repository.defaultBranch && repository.branches[name].commits.some((item) => item.id !== 'initial'))
  return {
    changedPaths,
    commit: pushed ? { id: pushed.id, message: pushed.message } : null,
    errors,
    hasSummary,
    hasVerification,
    mode: 'main',
    otherBranchesWithWork,
    status,
    validCandidate: errors.length === 0,
    warnings: syncWarnings(status),
  }
}

function completionGuidance(errors, context = {}) {
  if (errors.includes('missing_pull_request')) return 'Thanks for the update. Please send the pull request link once the branch is pushed and ready for review. If you worked directly on main instead, push main and tell me the work is ready on main - no link is needed.'
  if (errors.includes('invalid_pull_request')) return "I couldn't find that pull request in the current project. Please double-check the link and send it again."
  if (errors.includes('branch_mismatch')) return 'I found the pull request, but the branch name in your update does not match the branch attached to it. Could you confirm the correct branch?'
  if (errors.includes('branch_not_pushed')) return 'Push the pull request branch before submitting it for review.'
  if (errors.includes('no_compare_commits')) return 'Commit your changes on the feature branch before submitting the pull request.'
  if (errors.includes('project_not_extracted')) return 'I can not see the project yet. Download the project attachment from this email, extract it in Files, make your changes, then commit and push.'
  if (errors.includes('baseline_unavailable')) return 'This workspace was saved before CareerGrid kept a copy of the original project, so I can not compare main against it fairly. Please submit through a pull request from a feature branch instead, or start a new attempt.'
  if (errors.includes('main_not_pushed')) return 'Your commits on main have not been pushed yet, so there is nothing for me to review. Run git push in the terminal while on main, then send your message again.'
  if (errors.includes('unpushed_commits')) return `Some commits on ${context.branch || 'your branch'} have not been pushed, and I only review pushed work. Run git push, then send your message again.`
  if (errors.includes('uncommitted_only')) return 'Your edits are saved in the editor but not committed. Run git add . then git commit -m "..." and git push, then send your message again.'
  if (errors.includes('empty_submission')) {
    return context.otherBranchesWithWork?.length
      ? `main has no changes compared with the original project, but ${context.otherBranchesWithWork.join(', ')} does. Open a pull request from that branch and send me the link, or merge your work into main and push it.`
      : 'main has no changes compared with the original project yet, so there is nothing to review. Make your changes, commit them, push, and then let me know.'
  }
  return 'Please complete the simulated Git workflow before submitting.'
}

function warningText(warnings, status) {
  if (!warnings?.includes('uncommitted_changes')) return ''
  return ` Note: you also have uncommitted edits (${status.uncommittedPaths.join(', ')}). They will NOT be included. To include them, reply no, then commit and push them first.`
}

function candidatePrompt(candidate) {
  if (candidate.mode === 'main') {
    return `Just to confirm: should I review the work pushed to main (commit ${candidate.commitId}, ${candidate.changedPaths.length} file(s) changed from the original project) as your final submission? Reply yes to start the review, or no to keep working.${warningText(candidate.warnings, candidate.status)}`
  }
  return `${PULL_REQUEST_CONFIRMATION}${warningText(candidate.warnings, candidate.status)}`
}

function createSubmissionCandidate(repository, threadId, rawMessage, assessment) {
  const next = copy(repository); const key = String(threadId || 'default')
  if (next.submissions[key]) return { repository: next, error: 'This task already has a recorded submission.', existing: next.submissions[key] }
  if (!assessment?.validCandidate) return { repository: next, error: 'The completion email is not ready for submission.' }
  const mode = assessment.mode || 'pull_request'
  if (mode === 'pull_request' && !assessment.pullRequest) return { repository: next, error: 'The completion email is not ready for submission.' }
  const branch = mode === 'main' ? next.defaultBranch : assessment.pullRequest.compareBranch
  const candidate = {
    threadId: key, mode, repositoryPath: next.rootPath, branch,
    commitId: pushedCommit(next, branch)?.id || null,
    changedPaths: assessment.changedPaths || [],
    awaitingConfirmation: true, createdAt: new Date().toISOString(), rawMessages: [String(rawMessage)],
    hasSummary: assessment.hasSummary, hasVerification: assessment.hasVerification,
    warnings: assessment.warnings || [],
    status: assessment.status ? { uncommittedPaths: assessment.status.uncommittedPaths } : null,
  }
  if (mode === 'pull_request') {
    candidate.pullRequestId = Number(assessment.pullRequest.id)
    candidate.pullRequestUrl = assessment.pullRequest.url
  }
  next.submissionCandidates[key] = candidate
  return { repository: next, candidate }
}

function cancelSubmissionCandidate(repository, threadId) {
  const next = copy(repository); delete next.submissionCandidates[String(threadId || 'default')]
  return { repository: next }
}

function frozenCommits(branch, commitId) {
  const index = branch.commits.findIndex((item) => item.id === commitId)
  return branch.commits.slice(0, index + 1)
    .filter((item) => item.id !== 'initial')
    .map(({ id, message, author, createdAt }) => ({ id, message, author, createdAt }))
}

// Copies everything the evaluator needs at the moment of confirmation, so
// later edits, commits, pushes, or branch changes cannot alter the evidence.
function freezeSubmissionEvidence(repository, candidate, pullRequest) {
  const branch = repository.branches[candidate.branch]
  const pushed = pushedCommit(repository, candidate.branch)
  const baseline = repository.baseline?.snapshot ? copy(repository.baseline) : null
  const frozen = {
    branch: candidate.branch,
    commitId: pushed.id,
    commitMessage: pushed.message,
    commits: frozenCommits(branch, pushed.id),
    frozenAt: new Date().toISOString(),
    mode: candidate.mode,
    pushedBranches: copy(repository.remote.pushedBranches),
    snapshot: copy(pushed.snapshot),
    baseline,
  }
  if (pullRequest) {
    const baseBranch = repository.branches[pullRequest.baseBranch]
    const basePushed = pushedCommit(repository, pullRequest.baseBranch)
    frozen.pullRequest = copy(pullRequest)
    frozen.baseBranch = pullRequest.baseBranch
    // Kept only as a fallback comparison for legacy workspaces without a baseline.
    frozen.baseSnapshot = copy((basePushed || baseBranch.commits.at(-1)).snapshot)
  }
  return frozen
}

function confirmSubmission(repository, threadId, confirmationMessage, messageId = '') {
  const next = copy(repository); const key = String(threadId || 'default'); const existing = next.submissions[key]
  if (existing) return { repository: next, error: 'This task already has a recorded submission.', existing }
  const candidate = next.submissionCandidates[key]
  if (!candidate || !isAffirmativeSubmissionConfirmation(confirmationMessage)) return { repository: next, error: 'Explicit confirmation is required.' }
  const mode = candidate.mode || 'pull_request'
  let pullRequest = null
  if (mode === 'pull_request') {
    pullRequest = next.pullRequests.find((item) => item.id === candidate.pullRequestId && item.url === candidate.pullRequestUrl)
    if (!validatePullRequest(next, pullRequest)) return { repository: next, error: 'The pull request is no longer valid.' }
  } else {
    const assessment = assessMainSubmission(next)
    if (!assessment.validCandidate) {
      delete next.submissionCandidates[key]
      return { repository: next, error: completionGuidance(assessment.errors, assessment) }
    }
  }
  const pushed = pushedCommit(next, candidate.branch)
  if (!pushed) return { repository: next, error: 'Push your work before confirming the submission.' }
  if (candidate.commitId && pushed.id !== candidate.commitId) {
    delete next.submissionCandidates[key]
    return { repository: next, error: 'Your pushed work changed after you shared it. Please send your submission message again so I review the right version.' }
  }
  const submission = {
    status: 'submitted', submittedAt: new Date().toISOString(), messageId: String(messageId), threadId: key,
    mode,
    rawMessage: candidate.rawMessages.join('\n\n'), rawMessages: [...candidate.rawMessages, String(confirmationMessage)],
    confirmationMessage: String(confirmationMessage), repositoryPath: candidate.repositoryPath, branch: candidate.branch,
    commitId: pushed.id,
    extracted: { hasSummary: candidate.hasSummary, hasVerification: candidate.hasVerification },
    frozen: freezeSubmissionEvidence(next, { ...candidate, mode }, pullRequest),
  }
  if (pullRequest) {
    submission.pullRequestId = candidate.pullRequestId
    submission.pullRequestUrl = candidate.pullRequestUrl
  }
  next.submissions[key] = submission; delete next.submissionCandidates[key]
  return { repository: next, submission }
}

// Read-only summary used by the task brief, GitHub, and Mail status banners.
function submissionState(repository, threadId) {
  const key = String(threadId || 'default')
  const evaluation = repository.evaluations?.[key]
  if (evaluation?.status === 'completed') return { stage: 'evaluated', label: 'Feedback ready' }
  if (evaluation?.status === 'pending') return { stage: 'evaluating', label: 'Evaluation in progress' }
  if (evaluation?.status === 'failed') return { stage: 'evaluation_failed', label: 'Evaluation failed - reply retry in Mail', message: evaluation.message }
  if (repository.submissions?.[key]) return { stage: 'submitted', label: 'Submitted' }
  if (repository.submissionCandidates?.[key]) return { stage: 'awaiting_confirmation', label: 'Waiting for your confirmation in Mail' }
  return { stage: 'not_submitted', label: 'Not submitted yet' }
}

async function processCompletionReply({ body, evaluate, messageId = '', repository, threadId }) {
  const key = String(threadId || 'default')
  const candidate = repository.submissionCandidates[key]
  const existing = repository.submissions[key]

  if (existing) {
    const evaluation = repository.evaluations[key]
    if (evaluation?.status === 'completed') {
      return { advisorReply: 'This task has already been submitted and evaluated.', evaluationTriggered: false, repository }
    }
    if (evaluation?.status === 'pending') {
      return { advisorReply: 'Your evaluation is already in progress.', evaluationTriggered: false, repository }
    }
    if (/\bretry\b/i.test(body) && evaluate) {
      const evaluated = await evaluate(repository, existing)
      return { ...evaluated, evaluationTriggered: true, submission: existing }
    }
    return { advisorReply: 'This task is recorded. Reply retry to run the evaluation again.', evaluationTriggered: false, repository }
  }

  if (candidate && isSubmissionCancellation(body)) {
    const cancelled = cancelSubmissionCandidate(repository, key)
    return {
      advisorReply: 'No problem. The pending submission was cancelled so you can correct it.',
      evaluationTriggered: false,
      repository: cancelled.repository,
    }
  }

  if (candidate && isAffirmativeSubmissionConfirmation(body)) {
    const confirmed = confirmSubmission(repository, key, body, messageId)
    if (confirmed.error) return { advisorReply: confirmed.error, evaluationTriggered: false, repository: confirmed.repository }
    const acknowledgement = confirmed.submission.mode === 'main' ? MAIN_SUBMISSION_ACKNOWLEDGEMENT : SUBMISSION_ACKNOWLEDGEMENT
    if (!evaluate) {
      return {
        advisorReply: acknowledgement,
        evaluationTriggered: false,
        repository: confirmed.repository,
        submission: confirmed.submission,
      }
    }
    const evaluated = await evaluate(confirmed.repository, confirmed.submission)
    return {
      ...evaluated,
      advisorReply: evaluated.failed ? evaluated.advisorReply : acknowledgement,
      evaluationTriggered: true,
      submission: confirmed.submission,
    }
  }

  if (candidate) {
    const target = candidate.mode === 'main' ? 'the work pushed to main' : 'the pull request you shared'
    return {
      advisorReply: `I have ${target} queued for final review. Reply yes when you want me to begin, or no to keep working.`,
      evaluationTriggered: false,
      repository,
    }
  }

  const classification = classifyCompletionMessage(body)
  if (classification.intent === 'pull_request') {
    const assessment = assessCompletionEmail(repository, body)
    if (assessment.validCandidate) {
      const created = createSubmissionCandidate(repository, key, body, assessment)
      return { advisorReply: candidatePrompt(created.candidate), candidate: created.candidate, evaluationTriggered: false, repository: created.repository }
    }
    return { advisorReply: completionGuidance(assessment.errors, { branch: assessment.pullRequest?.compareBranch }), assessment, evaluationTriggered: false, repository }
  }

  if (classification.intent === 'direct_submission' && (classification.mentionsMain || !classification.mentionsPullRequest)) {
    const assessment = assessMainSubmission(repository, body)
    if (assessment.validCandidate) {
      const created = createSubmissionCandidate(repository, key, body, assessment)
      return { advisorReply: candidatePrompt(created.candidate), candidate: created.candidate, evaluationTriggered: false, repository: created.repository }
    }
    return { advisorReply: completionGuidance(assessment.errors, { ...assessment, branch: repository.defaultBranch }), assessment, evaluationTriggered: false, repository }
  }

  if (classification.intent === 'submission_question') {
    return { advisorReply: SUBMISSION_HELP, evaluationTriggered: false, repository }
  }

  // Legacy: an update naming a feature branch and a PR without its link.
  const assessment = assessCompletionEmail(repository, body)
  if (assessment.looksLikeSubmission || (classification.intent === 'direct_submission' && classification.mentionsPullRequest)) {
    return { advisorReply: completionGuidance(assessment.errors.length ? assessment.errors : ['missing_pull_request']), assessment, evaluationTriggered: false, repository }
  }
  // Questions and progress updates go to the normal advisor conversation.
  return { advisorReply: '', assessment, classification, evaluationTriggered: false, repository }
}

export {
  MAIN_SUBMISSION_ACKNOWLEDGEMENT,
  PULL_REQUEST_CONFIRMATION,
  SUBMISSION_ACKNOWLEDGEMENT,
  SUBMISSION_HELP,
  SUBMISSION_OPTIONS,
  assessCompletionEmail,
  assessMainSubmission,
  cancelSubmissionCandidate,
  classifyCompletionMessage,
  completionGuidance,
  confirmSubmission,
  createSubmissionCandidate,
  extractSimulatedPullRequestUrls,
  isAffirmativeSubmissionConfirmation,
  isSubmissionCancellation,
  processCompletionReply,
  submissionState,
}
