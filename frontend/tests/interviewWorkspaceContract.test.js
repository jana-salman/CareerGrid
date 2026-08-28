import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

const root = new URL('../', import.meta.url)
const read = (path) => readFile(new URL(path, root), 'utf8')

test('React owns the active interview route instead of the foundation placeholder', async () => {
  const router = await read('src/router.jsx')

  assert.match(router, /import InterviewPage from '.\/pages\/InterviewPage\.jsx'/)
  assert.match(router, /path="\/interview\/:interviewId" element=\{<InterviewPage \/>\}/)
  assert.match(router, /'\/interview\/:interviewId',/)
})

test('Interview workspace preserves the legacy visual DOM with a React controller', async () => {
  const page = await read('src/pages/InterviewPage.jsx')

  for (const contract of [
    'interviewApp',
    'interview-header',
    'interviewer-card',
    'questionProgress',
    'progressBar',
    'questionText',
    'timerValue',
    'microphoneButton',
    'audioVisualizer',
    'finishAnswerButton',
    'processingOverlay',
  ]) assert.ok(page.includes(contract), `Interview must retain ${contract}`)

  assert.match(page, /getInterviewWorkspace\(interviewId\)/)
  assert.match(page, /submitInterviewAnswer\(workspace\.interview_id, formData\)/)
  assert.match(page, /resolveQuestionIndex\([\s\S]*?workspace\.current_question/)
  assert.match(page, /\/static\/css\/interview\.css/)
  assert.doesNotMatch(page, /\/static\/js\/interview\.js/)
  assert.doesNotMatch(page, /window\.CAREERGRID_INTERVIEW/)
  assert.doesNotMatch(page, /fetch\(/)
})

test('React preserves timer expiry, microphone, multipart submission, and completion flow', async () => {
  const page = await read('src/pages/InterviewPage.jsx')

  assert.match(page, /navigator\.mediaDevices\.getUserMedia/)
  assert.match(page, /new MediaRecorder\(stream\)/)
  assert.match(page, /nextValue <= 0[\s\S]*?stopRecordingRef\.current/)
  assert.match(page, /submissionInFlightRef\.current/)
  assert.match(page, /result\.completed && result\.review_url/)
  assert.match(page, /window\.location\.href = result\.review_url/)
  assert.match(page, /audioChunksRef\.current = \[\]/)
})

test('Interview controls include non-visual accessibility semantics', async () => {
  const page = await read('src/pages/InterviewPage.jsx')

  assert.match(page, /'Start recording answer'/)
  assert.match(page, /id="timerValue"[\s\S]*?aria-live="polite"/)
  assert.match(page, /id="recordingStatus" aria-live="polite"/)
  assert.match(page, /id="processingOverlay"[\s\S]*?role="status"/)
})
