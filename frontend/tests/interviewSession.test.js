import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  buildInterviewAnswerFormData,
  countdownStep,
  questionTimeLimit,
  resolveQuestionIndex,
} from '../src/interview/interviewSession.js'

const questions = [
  { id: 1, time_limit_seconds: 45 },
  { id: 2, time_limit_seconds: 60 },
  { id: 3, time_limit_seconds: 75 },
]

test('interview progression resumes at the server-owned current question', () => {
  assert.equal(resolveQuestionIndex(questions, 1), 0)
  assert.equal(resolveQuestionIndex(questions, 2), 1)
  assert.equal(resolveQuestionIndex(questions, '3'), 2)
  assert.equal(resolveQuestionIndex(questions, 'invalid'), 0)
})

test('interview timer uses the backend limit and expires at zero', () => {
  assert.equal(questionTimeLimit(questions[1]), 60)
  assert.equal(countdownStep(2), 1)
  assert.equal(countdownStep(1), 0)
  assert.equal(countdownStep(0), 0)
})

test('answer submission preserves the multipart audio and speech metric contract', async () => {
  const audioBlob = new Blob(['recording'], { type: 'audio/webm' })
  const formData = buildInterviewAnswerFormData({
    audioBlob,
    question: questions[1],
    metrics: {
      durationSeconds: 12.5,
      speakingSeconds: 10,
      silenceSeconds: 2.5,
      silenceRatio: 0.2,
      longPauseCount: 1,
      longestPauseSeconds: 1.75,
    },
  })

  assert.equal(formData.get('question_id'), '2')
  assert.equal(formData.get('duration_seconds'), '12.5')
  assert.equal(formData.get('speaking_seconds'), '10')
  assert.equal(formData.get('silence_seconds'), '2.5')
  assert.equal(formData.get('silence_ratio'), '0.2')
  assert.equal(formData.get('long_pause_count'), '1')
  assert.equal(formData.get('longest_pause_seconds'), '1.75')
  assert.equal(await formData.get('audio').text(), 'recording')
})
