function asPositiveInteger(value, fallback = 1) {
  const parsed = Number.parseInt(value, 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

function resolveQuestionIndex(questions, currentQuestion) {
  if (!Array.isArray(questions) || questions.length === 0) return -1

  const currentId = String(asPositiveInteger(currentQuestion))
  const matchingIndex = questions.findIndex(
    (question) => String(question?.id) === currentId,
  )

  if (matchingIndex >= 0) return matchingIndex

  const ordinalIndex = asPositiveInteger(currentQuestion) - 1
  return Math.min(ordinalIndex, questions.length - 1)
}

function questionTimeLimit(question) {
  return asPositiveInteger(question?.time_limit_seconds)
}

function countdownStep(secondsRemaining) {
  return Math.max(Number(secondsRemaining) - 1, 0)
}

function buildInterviewAnswerFormData({ audioBlob, metrics, question }) {
  const formData = new FormData()

  formData.append('audio', audioBlob, 'answer.webm')
  formData.append('question_id', String(question.id))
  formData.append('duration_seconds', String(metrics.durationSeconds))
  formData.append('speaking_seconds', String(metrics.speakingSeconds))
  formData.append('silence_seconds', String(metrics.silenceSeconds))
  formData.append('silence_ratio', String(metrics.silenceRatio))
  formData.append('long_pause_count', String(metrics.longPauseCount))
  formData.append('longest_pause_seconds', String(metrics.longestPauseSeconds))

  return formData
}

export {
  buildInterviewAnswerFormData,
  countdownStep,
  questionTimeLimit,
  resolveQuestionIndex,
}
