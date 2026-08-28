import { apiRequest, encodeApiPathSegment } from './api.js'

function getInterviewWorkspace(interviewId) {
  return apiRequest(`/api/interview/${encodeApiPathSegment(interviewId)}`)
}

function getInterviewReview(interviewId) {
  return apiRequest(`/api/interview/${encodeApiPathSegment(interviewId)}/review`)
}

function submitInterviewAnswer(interviewId, answerFormData) {
  return apiRequest(
    `/api/interview/${encodeApiPathSegment(interviewId)}/answer`,
    {
      method: 'POST',
      body: answerFormData,
    },
  )
}

export { getInterviewReview, getInterviewWorkspace, submitInterviewAnswer }
