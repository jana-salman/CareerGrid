import {
  findPullRequestByUrl,
  validatePullRequest,
} from './repositoryModel.js'

function copy(value) { return JSON.parse(JSON.stringify(value)) }

const SUBMISSION_ACKNOWLEDGEMENT = 'Thanks, I will treat this pull request as your final submission and begin the review.'

function extractSimulatedPullRequestUrls(body) {
  const matches = String(body || '').match(/https:\/\/github\.com\/careergrid-sim\/[^\r\n]*?\/pull\/\d+(?=$|[\s)\],.!?;:])/gi) || []
  return [...new Set(matches.map((url) => url.replace(/[)\],.!?;:]+$/, '')))]
}

function isAffirmativeSubmissionConfirmation(body) {
  const answer = String(body || '').toLowerCase().replace(/[^a-z0-9\s']/g, ' ').replace(/\s+/g, ' ').trim()
  return /^(?:yes|yep|yeah|yup|correct|affirmative|submit(?: it)?|that's (?:the one|it|final)|yes (?:this is it|that's (?:the pr|it|the one)|review (?:it|this)|final))$/.test(answer)
}

function isSubmissionCancellation(body) {
  const answer = String(body || '').toLowerCase().replace(/[^a-z0-9\s']/g, ' ').replace(/\s+/g, ' ').trim()
  return /^(?:no|nope|cancel|cancel it|not yet|let me correct it|i need to correct it)$/.test(answer)
}

function assessCompletionEmail(repository, body) {
  const text = String(body || '')
  const lower = text.toLowerCase()
  const urls = extractSimulatedPullRequestUrls(text)
  const reportedBranch = text.match(/(?:^|\n)\s*branch\s*:\s*([A-Za-z0-9._/-]+)/i)?.[1] || ''
  const pullRequest = urls.map((url) => findPullRequestByUrl(repository, url)).find(Boolean) || null
  const validatedPullRequest = validatePullRequest(repository, pullRequest)
  const looksLikeSubmission = urls.length > 0 || (Boolean(reportedBranch) && /pull request|github|\bpr\b|pushed/.test(lower))
  const hasSummary = /found|identified|changed|updated|fixed|implemented|investigated|resolved/.test(lower)
    && text.replace(/https?:\/\/\S+/g, '').trim().split(/\s+/).filter(Boolean).length >= 8
  const hasVerification = /test|tested|testing|verify|verified|validation|reviewed|checked/.test(lower)
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
  return {
    errors,
    hasSummary,
    hasVerification,
    looksLikeSubmission,
    pullRequest: validatedPullRequest,
    reportedBranch,
    urls,
    validCandidate: looksLikeSubmission && Boolean(validatedPullRequest) && errors.length === 0,
  }
}

function completionGuidance(errors) {
  if (errors.includes('missing_pull_request')) return 'Thanks for the update. Please send the pull request link once the branch is pushed and ready for review.'
  if (errors.includes('invalid_pull_request')) return "I couldn't find that pull request in the current project. Please double-check the link and send it again."
  if (errors.includes('branch_mismatch')) return 'I found the pull request, but the branch name in your update does not match the branch attached to it. Could you confirm the correct branch?'
  if (errors.includes('branch_not_pushed')) return 'Push the pull request branch before submitting it for review.'
  if (errors.includes('no_compare_commits')) return 'Commit your changes on the feature branch before submitting the pull request.'
  return 'Please complete the simulated Git and pull request workflow before submitting.'
}

function createSubmissionCandidate(repository, threadId, rawMessage, assessment) {
  const next = copy(repository); const key = String(threadId || 'default')
  if (next.submissions[key]) return { repository: next, error: 'This task already has a recorded submission.', existing: next.submissions[key] }
  if (!assessment?.validCandidate || !assessment.pullRequest) return { repository: next, error: 'The completion email is not ready for submission.' }
  const candidate = {
    threadId: key, repositoryPath: next.rootPath, branch: assessment.pullRequest.compareBranch,
    pullRequestId: Number(assessment.pullRequest.id), pullRequestUrl: assessment.pullRequest.url,
    awaitingConfirmation: true, createdAt: new Date().toISOString(), rawMessages: [String(rawMessage)],
    hasSummary: assessment.hasSummary, hasVerification: assessment.hasVerification,
  }
  next.submissionCandidates[key] = candidate
  return { repository: next, candidate }
}

function cancelSubmissionCandidate(repository, threadId) {
  const next = copy(repository); delete next.submissionCandidates[String(threadId || 'default')]
  return { repository: next }
}

function confirmSubmission(repository, threadId, confirmationMessage, messageId = '') {
  const next = copy(repository); const key = String(threadId || 'default'); const existing = next.submissions[key]
  if (existing) return { repository: next, error: 'This task already has a recorded submission.', existing }
  const candidate = next.submissionCandidates[key]
  if (!candidate || !isAffirmativeSubmissionConfirmation(confirmationMessage)) return { repository: next, error: 'Explicit confirmation is required.' }
  const pullRequest = next.pullRequests.find((item) => item.id === candidate.pullRequestId && item.url === candidate.pullRequestUrl)
  if (!validatePullRequest(next, pullRequest)) return { repository: next, error: 'The pull request is no longer valid.' }
  const submission = {
    status: 'submitted', submittedAt: new Date().toISOString(), messageId: String(messageId), threadId: key,
    rawMessage: candidate.rawMessages.join('\n\n'), rawMessages: [...candidate.rawMessages, String(confirmationMessage)],
    confirmationMessage: String(confirmationMessage), repositoryPath: candidate.repositoryPath, branch: candidate.branch,
    pullRequestId: candidate.pullRequestId, pullRequestUrl: candidate.pullRequestUrl,
    extracted: { hasSummary: candidate.hasSummary, hasVerification: candidate.hasVerification },
  }
  next.submissions[key] = submission; delete next.submissionCandidates[key]
  return { repository: next, submission }
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
    if (!evaluate) {
      return {
        advisorReply: SUBMISSION_ACKNOWLEDGEMENT,
        evaluationTriggered: false,
        repository: confirmed.repository,
        submission: confirmed.submission,
      }
    }
    const evaluated = await evaluate(confirmed.repository, confirmed.submission)
    return {
      ...evaluated,
      advisorReply: evaluated.failed
        ? evaluated.advisorReply
        : SUBMISSION_ACKNOWLEDGEMENT,
      evaluationTriggered: true,
      submission: confirmed.submission,
    }
  }

  if (candidate) {
    return {
      advisorReply: 'I have the pull request you shared queued for final review. Reply yes when you want me to begin.',
      evaluationTriggered: false,
      repository,
    }
  }

  const assessment = assessCompletionEmail(repository, body)
  if (assessment.validCandidate) {
    const created = createSubmissionCandidate(repository, key, body, assessment)
    return {
      advisorReply: 'Just to confirm, is this the pull request you want me to review as your final submission?',
      candidate: created.candidate,
      evaluationTriggered: false,
      repository: created.repository,
    }
  }
  return {
    advisorReply: assessment.looksLikeSubmission ? completionGuidance(assessment.errors) : '',
    assessment,
    evaluationTriggered: false,
    repository,
  }
}

export {
  SUBMISSION_ACKNOWLEDGEMENT,
  assessCompletionEmail,
  cancelSubmissionCandidate,
  completionGuidance,
  confirmSubmission,
  createSubmissionCandidate,
  extractSimulatedPullRequestUrls,
  isAffirmativeSubmissionConfirmation,
  isSubmissionCancellation,
  processCompletionReply,
}
