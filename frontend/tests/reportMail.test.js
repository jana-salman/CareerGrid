import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

import {
  createFinalReportMessage,
  ensureFinalReportMessage,
  finalReportPath,
} from '../src/simulation/state/reportMail.js'

const taskMessage = {
  body: 'Complete the workplace task.',
  id: 'task-report',
  role: 'Senior Engineer',
  sender: 'Maya Chen',
  subject: 'Production issue',
  task: true,
}

test('successful evaluation creates the legacy report Mail message and saved-report action', () => {
  const report = createFinalReportMessage({
    attemptId: 'attempt/report 1',
    evaluation: { review_message: 'Your completed review is attached.' },
    taskMessage,
  })

  assert.equal(report.sender, 'Maya Chen')
  assert.equal(report.role, 'Senior Engineer')
  assert.equal(report.type, 'evaluation-review')
  assert.equal(report.body, 'Your completed review is attached.')
  assert.deepEqual(report.attachments, [{
    id: 'report-task-report',
    name: 'Open Task Review Report',
    reportPath: '/simulation/attempts/attempt%2Freport%201/report',
    size: 'Generated review',
    threadId: 'task-report',
    type: 'evaluation-report',
  }])
})

test('reopening a completed workspace restores one report message without reevaluation', () => {
  const first = ensureFinalReportMessage(taskMessage, {
    attemptId: 'attempt-42',
    evaluation: { overall_score: 88 },
  })
  const reopened = ensureFinalReportMessage(first, {
    attemptId: 'attempt-42',
    evaluation: { overall_score: 88 },
  })

  assert.equal(first.replies.length, 1)
  assert.equal(reopened, first)
  assert.equal(reopened.replies.filter((reply) => reply.type === 'evaluation-review').length, 1)
})

test('the Final Report action targets the existing React report route', () => {
  assert.equal(finalReportPath('attempt-42'), '/simulation/attempts/attempt-42/report')
})

test('Mail evaluation remains in the workspace and navigation belongs only to the report action', async () => {
  const mail = await readFile(new URL('../src/simulation/apps/MailApp.jsx', import.meta.url), 'utf8')
  const evaluationBlock = mail.slice(mail.indexOf('const runEvaluation'), mail.indexOf('const send'))

  assert.doesNotMatch(evaluationBlock, /navigate\(/)
  assert.match(mail, /createFinalReportMessage/)
  assert.match(mail, /onOpenReport/)
  assert.match(mail, /navigate\(path\)/)
  assert.match(mail, /onOpenReport\(attachment\.reportPath\)/)
  assert.match(mail, /!replies\.some\(\(reply\) => reply\.type === 'evaluation-review'\)/)
})
