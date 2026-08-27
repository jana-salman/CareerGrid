import { apiRequest, encodeApiPathSegment } from './api.js'

function submitInterviewAnswer(interviewId, answerFormData) {
  return apiRequest(
    `/api/interview/${encodeApiPathSegment(interviewId)}/answer`,
    {
      method: 'POST',
      body: answerFormData,
    },
  )
}

export { submitInterviewAnswer }
