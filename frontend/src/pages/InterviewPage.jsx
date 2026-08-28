import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'

import {
  buildInterviewAnswerFormData,
  countdownStep,
  questionTimeLimit,
  resolveQuestionIndex,
} from '../interview/interviewSession.js'
import {
  getInterviewWorkspace,
  submitInterviewAnswer,
} from '../services/interviewApi.js'

const INTERVIEW_STYLESHEET = '/static/css/interview.css'
const SILENCE_THRESHOLD = 0.025
const LONG_PAUSE_MS = 1500

function formatIdentifier(value) {
  return String(value || '')
    .replaceAll('-', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function useInterviewStyles() {
  useEffect(() => {
    const existing = [...document.querySelectorAll('link[rel="stylesheet"]')].find(
      (link) => link.getAttribute('href') === INTERVIEW_STYLESHEET,
    )
    const stylesheet = existing || document.createElement('link')
    if (!existing) {
      stylesheet.rel = 'stylesheet'
      stylesheet.href = INTERVIEW_STYLESHEET
      document.head.appendChild(stylesheet)
    }

    document.body.classList.add('interview-route')

    return () => {
      document.body.classList.remove('interview-route')
      if (!existing) stylesheet.remove()
    }
  }, [])
}

function InterviewWorkspace({ workspace }) {
  const questions = workspace.questions || []
  const initialQuestionIndex = resolveQuestionIndex(
    questions,
    workspace.current_question,
  )
  const [questionIndex, setQuestionIndex] = useState(initialQuestionIndex)
  const currentQuestion = questions[questionIndex]
  const [secondsRemaining, setSecondsRemaining] = useState(
    questionTimeLimit(currentQuestion),
  )
  const [isRecording, setIsRecording] = useState(false)
  const [isStarting, setIsStarting] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [recordingTitle, setRecordingTitle] = useState('Ready to answer?')
  const [recordingStatus, setRecordingStatus] = useState(
    "Press the microphone when you're ready.",
  )

  const mountedRef = useRef(true)
  const mediaRecorderRef = useRef(null)
  const mediaStreamRef = useRef(null)
  const audioChunksRef = useRef([])
  const timerIntervalRef = useRef(null)
  const secondsRemainingRef = useRef(secondsRemaining)
  const recordingStartedAtRef = useRef(null)
  const isRecordingRef = useRef(false)
  const isStartingRef = useRef(false)
  const submissionInFlightRef = useRef(false)
  const recorderHandlersRef = useRef(null)
  const audioContextRef = useRef(null)
  const analyserRef = useRef(null)
  const microphoneSourceRef = useRef(null)
  const analysisFrameRef = useRef(null)
  const stopRecordingRef = useRef(null)
  const speechMetricsRef = useRef({
    silenceStartedAt: null,
    totalSilenceMs: 0,
    longPauseCount: 0,
    longestPauseMs: 0,
  })

  function clearTimer() {
    if (timerIntervalRef.current !== null) {
      window.clearInterval(timerIntervalRef.current)
      timerIntervalRef.current = null
    }
  }

  function resetSpeechMetrics() {
    speechMetricsRef.current = {
      silenceStartedAt: null,
      totalSilenceMs: 0,
      longPauseCount: 0,
      longestPauseMs: 0,
    }
  }

  function finishSilenceMeasurement() {
    const metrics = speechMetricsRef.current
    if (metrics.silenceStartedAt === null || recordingStartedAtRef.current === null) {
      return
    }

    const pauseDuration = performance.now() - metrics.silenceStartedAt
    metrics.totalSilenceMs += pauseDuration
    metrics.longestPauseMs = Math.max(metrics.longestPauseMs, pauseDuration)
    if (pauseDuration >= LONG_PAUSE_MS) metrics.longPauseCount += 1
    metrics.silenceStartedAt = null
  }

  function stopAudioAnalysis() {
    if (analysisFrameRef.current !== null) {
      window.cancelAnimationFrame(analysisFrameRef.current)
      analysisFrameRef.current = null
    }

    finishSilenceMeasurement()

    if (microphoneSourceRef.current) {
      try {
        microphoneSourceRef.current.disconnect()
      } catch (_) {
        // The audio graph may already have been released by the browser.
      }
      microphoneSourceRef.current = null
    }

    if (audioContextRef.current) {
      Promise.resolve(audioContextRef.current.close()).catch(() => {})
      audioContextRef.current = null
    }
    analyserRef.current = null
  }

  function startAudioAnalysis(stream) {
    stopAudioAnalysis()

    const AudioContext = window.AudioContext || window.webkitAudioContext
    if (!AudioContext) return

    const audioContext = new AudioContext()
    const analyser = audioContext.createAnalyser()
    analyser.fftSize = 2048
    analyser.smoothingTimeConstant = 0.75

    const microphoneSource = audioContext.createMediaStreamSource(stream)
    microphoneSource.connect(analyser)

    audioContextRef.current = audioContext
    analyserRef.current = analyser
    microphoneSourceRef.current = microphoneSource

    const samples = new Float32Array(analyser.fftSize)
    const monitor = () => {
      if (!isRecordingRef.current) return

      analyser.getFloatTimeDomainData(samples)
      let sumSquares = 0
      for (const sample of samples) sumSquares += sample * sample

      const rms = Math.sqrt(sumSquares / samples.length)
      const now = performance.now()
      const metrics = speechMetricsRef.current

      if (rms < SILENCE_THRESHOLD) {
        if (metrics.silenceStartedAt === null) metrics.silenceStartedAt = now
      } else if (metrics.silenceStartedAt !== null) {
        const pauseDuration = now - metrics.silenceStartedAt
        metrics.totalSilenceMs += pauseDuration
        metrics.longestPauseMs = Math.max(metrics.longestPauseMs, pauseDuration)
        if (pauseDuration >= LONG_PAUSE_MS) metrics.longPauseCount += 1
        metrics.silenceStartedAt = null
      }

      analysisFrameRef.current = window.requestAnimationFrame(monitor)
    }

    monitor()
  }

  function startTimer() {
    clearTimer()
    timerIntervalRef.current = window.setInterval(() => {
      const nextValue = countdownStep(secondsRemainingRef.current)
      secondsRemainingRef.current = nextValue
      if (mountedRef.current) setSecondsRemaining(nextValue)

      if (nextValue <= 0) {
        clearTimer()
        stopRecordingRef.current?.()
      }
    }, 1000)
  }

  async function submitRecording(recorder, answeredQuestion, answeredIndex) {
    if (submissionInFlightRef.current) return
    submissionInFlightRef.current = true

    const finishedAt = performance.now()
    const durationSeconds = Math.max(
      1,
      (finishedAt - recordingStartedAtRef.current) / 1000,
    )
    const speechMetrics = speechMetricsRef.current
    const silenceSeconds = speechMetrics.totalSilenceMs / 1000
    const speakingSeconds = Math.max(0, durationSeconds - silenceSeconds)
    const silenceRatio = durationSeconds > 0 ? silenceSeconds / durationSeconds : 0
    const audioBlob = new Blob(audioChunksRef.current, {
      type: recorder.mimeType || 'audio/webm',
    })
    audioChunksRef.current = []

    const formData = buildInterviewAnswerFormData({
      audioBlob,
      question: answeredQuestion,
      metrics: {
        durationSeconds,
        speakingSeconds,
        silenceSeconds,
        silenceRatio,
        longPauseCount: speechMetrics.longPauseCount,
        longestPauseSeconds: speechMetrics.longestPauseMs / 1000,
      },
    })

    try {
      const result = await submitInterviewAnswer(workspace.interview_id, formData)
      if (!mountedRef.current) return

      if (result.completed && result.review_url) {
        window.location.href = result.review_url
        return
      }

      const nextQuestionIndex = answeredIndex + 1
      if (nextQuestionIndex >= questions.length) {
        throw new Error('CareerGrid could not confirm the next interview question.')
      }

      submissionInFlightRef.current = false
      setIsProcessing(false)
      setQuestionIndex(nextQuestionIndex)
    } catch (error) {
      if (!mountedRef.current) return
      submissionInFlightRef.current = false
      setIsProcessing(false)
      setRecordingTitle("We couldn't process that answer.")
      setRecordingStatus(error.message || 'Press the microphone to try again.')
    }
  }

  function stopRecording() {
    const recorder = mediaRecorderRef.current
    if (!isRecordingRef.current || !recorder) return

    isRecordingRef.current = false
    setIsRecording(false)
    setIsProcessing(true)
    clearTimer()
    stopAudioAnalysis()
    setRecordingTitle('Processing answer')
    setRecordingStatus('CareerGrid is analyzing your response.')

    if (recorder.state !== 'inactive') recorder.stop()
  }
  stopRecordingRef.current = stopRecording

  async function requestMicrophone() {
    if (mediaStreamRef.current) return mediaStreamRef.current
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error('Microphone recording is not supported by this browser.')
    }

    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        channelCount: 1,
      },
    })
    mediaStreamRef.current = stream
    return stream
  }

  async function startRecording() {
    if (
      isRecordingRef.current
      || isStartingRef.current
      || isProcessing
      || submissionInFlightRef.current
      || !currentQuestion
    ) return

    isStartingRef.current = true
    setIsStarting(true)

    try {
      const stream = await requestMicrophone()
      if (!mountedRef.current) return
      if (!window.MediaRecorder) {
        throw new Error('Microphone recording is not supported by this browser.')
      }

      audioChunksRef.current = []
      resetSpeechMetrics()

      const recorder = new MediaRecorder(stream)
      mediaRecorderRef.current = recorder
      const handleDataAvailable = (event) => {
        if (event.data && event.data.size > 0) audioChunksRef.current.push(event.data)
      }
      const handleStop = () => submitRecording(recorder, currentQuestion, questionIndex)
      recorderHandlersRef.current = { handleDataAvailable, handleStop, recorder }
      recorder.addEventListener('dataavailable', handleDataAvailable)
      recorder.addEventListener('stop', handleStop, { once: true })

      recordingStartedAtRef.current = performance.now()
      recorder.start(250)
      isRecordingRef.current = true

      try {
        startAudioAnalysis(stream)
      } catch (analysisError) {
        console.error(analysisError)
      }

      setIsRecording(true)
      setRecordingTitle('Recording your answer')
      setRecordingStatus('Speak naturally and answer the interviewer.')
      startTimer()
    } catch (error) {
      console.error(error)
      isRecordingRef.current = false
      setIsRecording(false)

      const handlers = recorderHandlersRef.current
      if (handlers) {
        handlers.recorder.removeEventListener('dataavailable', handlers.handleDataAvailable)
        handlers.recorder.removeEventListener('stop', handlers.handleStop)
        recorderHandlersRef.current = null
      }
      setRecordingTitle('Microphone unavailable')
      setRecordingStatus('Please allow microphone access and try again.')
    } finally {
      isStartingRef.current = false
      if (mountedRef.current) setIsStarting(false)
    }
  }

  useEffect(() => {
    const timeLimit = questionTimeLimit(questions[questionIndex])
    secondsRemainingRef.current = timeLimit
    setSecondsRemaining(timeLimit)
    setRecordingTitle('Ready to answer?')
    setRecordingStatus("Press the microphone when you're ready.")
  }, [questionIndex, questions])

  useEffect(() => {
    mountedRef.current = true

    return () => {
      mountedRef.current = false
      clearTimer()
      isRecordingRef.current = false
      stopAudioAnalysis()

      const recorder = mediaRecorderRef.current
      const handlers = recorderHandlersRef.current
      if (handlers) {
        handlers.recorder.removeEventListener('dataavailable', handlers.handleDataAvailable)
        handlers.recorder.removeEventListener('stop', handlers.handleStop)
        recorderHandlersRef.current = null
      }
      if (recorder) {
        if (recorder.state !== 'inactive') recorder.stop()
      }

      for (const track of mediaStreamRef.current?.getTracks() || []) track.stop()
      mediaStreamRef.current = null
      audioChunksRef.current = []
    }
  }, [])

  const progress = ((questionIndex + 1) / questions.length) * 100

  return (
    <div
      id="interviewApp"
      className="interview-app"
      data-interview-id={workspace.interview_id}
    >
      <header className="interview-header">
        <div className="brand">CareerGrid</div>
        <div className="interview-meta">
          <span>{formatIdentifier(workspace.company_id)}</span>
          <span className="meta-dot" aria-hidden="true" />
          <span>{formatIdentifier(workspace.position_id)}</span>
        </div>
      </header>

      <main className="interview-stage">
        <section className="interviewer-card">
          <div className="interviewer-avatar" aria-hidden="true">
            <div className="avatar-ring"><span>CG</span></div>
          </div>
          <div className="interviewer-information">
            <span className="interviewer-label">AI INTERVIEWER</span>
            <h1>{workspace.interview_title}</h1>
            <p id="interviewerStatus">{workspace.opening_message}</p>
          </div>
        </section>

        <section className="progress-area" aria-label="Interview progress">
          <div className="progress-information">
            <span id="questionProgress">
              Question {questionIndex + 1} of {questions.length}
            </span>
            <span id="difficultyLabel">{currentQuestion.difficulty} difficulty</span>
          </div>
          <div className="progress-track">
            <div id="progressBar" className="progress-bar" style={{ width: `${progress}%` }} />
          </div>
        </section>

        <section className="question-card" aria-labelledby="questionText">
          <span id="questionCategory" className="question-category">
            {currentQuestion.category || 'Interview'}
          </span>
          <h2 id="questionText">{currentQuestion.question}</h2>
        </section>

        <section className="timer-area" aria-label="Answer time remaining">
          <div id="timerCircle" className="timer-circle">
            <span id="timerValue" className="timer-value" aria-live="polite">
              {secondsRemaining}
            </span>
            <span className="timer-label">seconds</span>
          </div>
        </section>

        <section className="microphone-area">
          <button
            id="microphoneButton"
            className={`microphone-button${isRecording ? ' recording' : ''}`}
            type="button"
            aria-label={isRecording ? 'Stop recording answer' : 'Start recording answer'}
            disabled={isStarting || isProcessing || !currentQuestion}
            onClick={isRecording ? stopRecording : startRecording}
          >
            <span className="microphone-symbol" aria-hidden="true">🎙</span>
          </button>
          <h3 id="recordingTitle">{recordingTitle}</h3>
          <p id="recordingStatus" aria-live="polite">{recordingStatus}</p>
          <div
            id="audioVisualizer"
            className={`audio-visualizer${isRecording ? ' active' : ''}`}
            aria-hidden="true"
          >
            {Array.from({ length: 8 }, (_, index) => <span key={index} />)}
          </div>
        </section>

        <section className="interview-actions">
          <button
            id="finishAnswerButton"
            className="finish-answer-button"
            type="button"
            disabled={!isRecording || isProcessing}
            onClick={stopRecording}
          >
            Finish Answer
          </button>
        </section>

        <section
          id="processingOverlay"
          className={`processing-overlay${isProcessing ? '' : ' hidden'}`}
          role="status"
          aria-live="polite"
        >
          <div className="processing-card">
            <div className="processing-spinner" aria-hidden="true" />
            <h3>Evaluating your answer</h3>
            <p>CareerGrid AI is analyzing your response and speaking delivery.</p>
          </div>
        </section>
      </main>
    </div>
  )
}

function InterviewPage() {
  const { interviewId } = useParams()
  const [workspace, setWorkspace] = useState(null)
  const [error, setError] = useState('')

  useInterviewStyles()

  useEffect(() => {
    let active = true
    getInterviewWorkspace(interviewId)
      .then((data) => {
        if (!active) return
        if (data.status === 'completed' && data.review_url) {
          window.location.replace(data.review_url)
          return
        }
        setWorkspace(data)
      })
      .catch((requestError) => active && setError(requestError.message))
    return () => { active = false }
  }, [interviewId])

  useEffect(() => {
    if (!workspace?.interview_title) return undefined
    const previousTitle = document.title
    document.title = `${workspace.interview_title} | CareerGrid`
    return () => { document.title = previousTitle }
  }, [workspace?.interview_title])

  if (error) {
    return <main className="interview-stage" role="alert"><p>{error}</p></main>
  }
  if (!workspace) {
    return <main className="interview-stage" aria-live="polite"><p>Preparing your interview...</p></main>
  }

  return <InterviewWorkspace workspace={workspace} />
}

export default InterviewPage
