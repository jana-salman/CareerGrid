function finalReportPath(attemptId) {
  return `/simulation/attempts/${encodeURIComponent(attemptId)}/report`
}

function createFinalReportMessage({ attemptId, evaluation, taskMessage }) {
  return {
    attachments: [{
      id: `report-${taskMessage.id}`,
      name: 'Open Task Review Report',
      reportPath: finalReportPath(attemptId),
      size: 'Generated review',
      threadId: taskMessage.id,
      type: 'evaluation-report',
    }],
    body: evaluation?.review_message || "I've completed my review and attached the feedback report.",
    id: `review-${taskMessage.id}`,
    role: taskMessage.role || 'Advisor',
    sender: taskMessage.sender,
    type: 'evaluation-review',
  }
}

function ensureFinalReportMessage(message, options) {
  if (!message?.task || message.replies?.some((reply) => reply.type === 'evaluation-review')) return message
  return { ...message, replies: [...(message.replies || []), createFinalReportMessage({ ...options, taskMessage: message })] }
}

export { createFinalReportMessage, ensureFinalReportMessage, finalReportPath }
