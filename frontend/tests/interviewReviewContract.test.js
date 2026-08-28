import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

const root = new URL('../', import.meta.url)
const read = (path) => readFile(new URL(path, root), 'utf8')

test('React owns the Interview Review route and uses the shared API service', async () => {
  const [router, page] = await Promise.all([
    read('src/router.jsx'),
    read('src/pages/InterviewReviewPage.jsx'),
  ])

  assert.match(router, /import InterviewReviewPage from '.\/pages\/InterviewReviewPage\.jsx'/)
  assert.match(
    router,
    /path="\/interview\/:interviewId\/review" element=\{<InterviewReviewPage \/>\}/,
  )
  assert.match(router, /'\/interview\/:interviewId\/review',/)
  assert.match(page, /getInterviewReview\(interviewId\)/)
  assert.doesNotMatch(page, /fetch\(/)
})

test('Interview Review preserves the complete legacy rendering contract', async () => {
  const page = await read('src/pages/InterviewReviewPage.jsx')

  for (const className of [
    'interview-app',
    'interview-header',
    'interview-meta',
    'interview-stage',
    'question-card',
    'final-score',
    'review-grid',
    'review-card',
    'review-wide',
    'question-review-list',
    'answer-review-card',
    'answer-review-top',
    'answer-score',
    'speech-stats',
    'answer-transcript',
    'answer-feedback',
    'interview-actions',
    'finish-answer-button',
  ]) assert.ok(page.includes(className), `Interview Review must retain ${className}`)

  for (const copy of [
    'INTERVIEW COMPLETE',
    'Your interview performance',
    'Strengths',
    'Improve',
    'Speaking performance',
    'Answer quality',
    'QUESTION ANALYSIS',
    'Your answers',
    'What you said',
    'CareerGrid feedback',
    'Recommended next steps',
    'Explore More Careers',
  ]) assert.ok(page.includes(copy), `Interview Review must retain ${copy}`)

  for (const field of [
    'overall_score',
    'summary',
    'strengths',
    'areas_for_improvement',
    'communication_feedback',
    'content_feedback',
    'question_results',
    'category',
    'score',
    'transcript',
    'feedback',
    'word_count',
    'words_per_minute',
    'filler_count',
    'long_pause_count',
    'next_steps',
  ]) assert.ok(page.includes(field), `Interview Review must render ${field}`)
})

test('Interview Review preserves incomplete and unavailable redirect behavior', async () => {
  const page = await read('src/pages/InterviewReviewPage.jsx')

  assert.match(page, /data\.status !== 'completed' && data\.redirect_url/)
  assert.match(page, /window\.location\.replace\(data\.redirect_url\)/)
  assert.match(page, /href=\{review\.explore_url\}/)
})

test('Interview Review and interview controls preserve keyboard accessibility', async () => {
  const [page, interviewPage, css] = await Promise.all([
    read('src/pages/InterviewReviewPage.jsx'),
    read('src/pages/InterviewPage.jsx'),
    read('../static/css/interview.css'),
  ])

  assert.match(page, /role="alert"/)
  assert.match(page, /aria-busy="true" aria-live="polite"/)
  assert.match(page, /aria-labelledby="interviewReviewHeading"/)
  assert.match(page, /aria-label=\{`Overall interview score:/)
  assert.match(page, /aria-label=\{`Question score:/)
  assert.match(page, /<a[\s\S]*?className="finish-answer-button"/)
  assert.match(interviewPage, /<button[\s\S]*?id="microphoneButton"/)
  assert.match(interviewPage, /<button[\s\S]*?id="finishAnswerButton"/)
  assert.match(css, /\.microphone-button:focus-visible,[\s\S]*?\.finish-answer-button:focus-visible/)
})

test('workplace report routes through Flask eligibility to React interview and review', async () => {
  const [workplaceReport, interview, router] = await Promise.all([
    read('src/pages/WorkplaceReportPage.jsx'),
    read('src/pages/InterviewPage.jsx'),
    read('src/router.jsx'),
  ])

  assert.match(workplaceReport, /report\.interview_unlocked &&/)
  assert.match(
    workplaceReport,
    /action=\{`\/simulation\/attempts\/\$\{encodeURIComponent\(attemptId\)\}\/interview\/start`\}/,
  )
  assert.match(workplaceReport, /method="post"/)
  assert.match(interview, /result\.completed && result\.review_url/)
  assert.match(interview, /window\.location\.href = result\.review_url/)
  assert.match(router, /path="\/interview\/:interviewId\/review"/)
})
