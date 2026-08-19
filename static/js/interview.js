(() => {
    const config = window.CAREERGRID_INTERVIEW;

    const questions = config.questions || [];
    const interviewId = config.interviewId;

    let questionIndex = 0;

    let mediaRecorder = null;
    let mediaStream = null;
    let audioChunks = [];

    let timerInterval = null;
    let secondsRemaining = 0;

    let recordingStartedAt = null;
    let isRecording = false;

    let audioContext = null;
    let analyser = null;
    let microphoneSource = null;
    let analysisFrame = null;

    let silenceStartedAt = null;
    let totalSilenceMs = 0;
    let longPauseCount = 0;
    let longestPauseMs = 0;

    const SILENCE_THRESHOLD = 0.025;
    const LONG_PAUSE_MS = 1500;

    const questionText =
        document.getElementById("questionText");

    const questionCategory =
        document.getElementById("questionCategory");

    const questionProgress =
        document.getElementById("questionProgress");

    const difficultyLabel =
        document.getElementById("difficultyLabel");

    const progressBar =
        document.getElementById("progressBar");

    const timerValue =
        document.getElementById("timerValue");

    const microphoneButton =
        document.getElementById("microphoneButton");

    const finishButton =
        document.getElementById("finishAnswerButton");

    const recordingTitle =
        document.getElementById("recordingTitle");

    const recordingStatus =
        document.getElementById("recordingStatus");

    const visualizer =
        document.getElementById("audioVisualizer");

    const processingOverlay =
        document.getElementById("processingOverlay");


    function currentQuestion() {
        return questions[questionIndex];
    }


    function renderQuestion() {
        const question = currentQuestion();

        if (!question) {
            return;
        }

        questionText.textContent =
            question.question;

        questionCategory.textContent =
            question.category || "Interview";

        difficultyLabel.textContent =
            `${question.difficulty} difficulty`;

        questionProgress.textContent =
            `Question ${questionIndex + 1} of ${questions.length}`;

        const progress =
            ((questionIndex + 1) / questions.length) * 100;

        progressBar.style.width =
            `${progress}%`;

        secondsRemaining =
            question.time_limit_seconds;

        timerValue.textContent =
            secondsRemaining;

        recordingTitle.textContent =
            "Ready to answer?";

        recordingStatus.textContent =
            "Press the microphone when you're ready.";

        finishButton.disabled = true;
    }


    async function requestMicrophone() {
        if (mediaStream) {
            return mediaStream;
        }

        mediaStream =
            await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    channelCount: 1
                }
            });

        return mediaStream;
    }


    function resetSpeechMetrics() {
        silenceStartedAt = null;
        totalSilenceMs = 0;
        longPauseCount = 0;
        longestPauseMs = 0;
    }


    function startAudioAnalysis(stream) {
        stopAudioAnalysis();

        audioContext =
            new (
                window.AudioContext ||
                window.webkitAudioContext
            )();

        analyser =
            audioContext.createAnalyser();

        analyser.fftSize = 2048;

        analyser.smoothingTimeConstant =
            0.75;

        microphoneSource =
            audioContext.createMediaStreamSource(
                stream
            );

        microphoneSource.connect(
            analyser
        );

        const samples =
            new Float32Array(
                analyser.fftSize
            );

        const monitor = () => {
            if (!isRecording) {
                return;
            }

            analyser.getFloatTimeDomainData(
                samples
            );

            let sumSquares = 0;

            for (
                let index = 0;
                index < samples.length;
                index += 1
            ) {
                sumSquares +=
                    samples[index] *
                    samples[index];
            }

            const rms =
                Math.sqrt(
                    sumSquares /
                    samples.length
                );

            const now =
                performance.now();

            const silent =
                rms < SILENCE_THRESHOLD;

            if (silent) {
                if (silenceStartedAt === null) {
                    silenceStartedAt = now;
                }
            } else {
                if (silenceStartedAt !== null) {
                    const pauseDuration =
                        now - silenceStartedAt;

                    totalSilenceMs +=
                        pauseDuration;

                    longestPauseMs =
                        Math.max(
                            longestPauseMs,
                            pauseDuration
                        );

                    if (
                        pauseDuration >=
                        LONG_PAUSE_MS
                    ) {
                        longPauseCount += 1;
                    }

                    silenceStartedAt = null;
                }
            }

            analysisFrame =
                requestAnimationFrame(
                    monitor
                );
        };

        monitor();
    }


    function stopAudioAnalysis() {
        if (analysisFrame) {
            cancelAnimationFrame(
                analysisFrame
            );

            analysisFrame = null;
        }

        if (
            silenceStartedAt !== null
            &&
            recordingStartedAt !== null
        ) {
            const now =
                performance.now();

            const pauseDuration =
                now - silenceStartedAt;

            totalSilenceMs +=
                pauseDuration;

            longestPauseMs =
                Math.max(
                    longestPauseMs,
                    pauseDuration
                );

            if (
                pauseDuration >=
                LONG_PAUSE_MS
            ) {
                longPauseCount += 1;
            }

            silenceStartedAt = null;
        }

        if (microphoneSource) {
            try {
                microphoneSource.disconnect();
            } catch (_) {}

            microphoneSource = null;
        }

        if (audioContext) {
            try {
                audioContext.close();
            } catch (_) {}

            audioContext = null;
        }

        analyser = null;
    }


    function startTimer() {
        clearInterval(
            timerInterval
        );

        timerInterval =
            setInterval(
                () => {
                    secondsRemaining -= 1;

                    timerValue.textContent =
                        Math.max(
                            secondsRemaining,
                            0
                        );

                    if (
                        secondsRemaining <= 0
                    ) {
                        clearInterval(
                            timerInterval
                        );

                        stopRecording();
                    }
                },
                1000
            );
    }


    async function startRecording() {
        try {
            const stream =
                await requestMicrophone();

            audioChunks = [];

            resetSpeechMetrics();

            mediaRecorder =
                new MediaRecorder(
                    stream
                );

            mediaRecorder.addEventListener(
                "dataavailable",
                event => {
                    if (
                        event.data &&
                        event.data.size > 0
                    ) {
                        audioChunks.push(
                            event.data
                        );
                    }
                }
            );

            mediaRecorder.addEventListener(
                "stop",
                submitRecording,
                {
                    once: true
                }
            );

            recordingStartedAt =
                performance.now();

            isRecording = true;

            mediaRecorder.start(
                250
            );

            startAudioAnalysis(
                stream
            );

            microphoneButton.classList.add(
                "recording"
            );

            visualizer.classList.add(
                "active"
            );

            recordingTitle.textContent =
                "Recording your answer";

            recordingStatus.textContent =
                "Speak naturally and answer the interviewer.";

            finishButton.disabled =
                false;

            startTimer();

        } catch (error) {
            console.error(
                error
            );

            recordingTitle.textContent =
                "Microphone unavailable";

            recordingStatus.textContent =
                "Please allow microphone access and try again.";
        }
    }


    function stopRecording() {
        if (
            !isRecording ||
            !mediaRecorder
        ) {
            return;
        }

        isRecording = false;

        clearInterval(
            timerInterval
        );

        stopAudioAnalysis();

        microphoneButton.classList.remove(
            "recording"
        );

        visualizer.classList.remove(
            "active"
        );

        finishButton.disabled =
            true;

        recordingTitle.textContent =
            "Processing answer";

        recordingStatus.textContent =
            "CareerGrid is analyzing your response.";

        if (
            mediaRecorder.state !==
            "inactive"
        ) {
            mediaRecorder.stop();
        }
    }


    async function submitRecording() {
        processingOverlay.classList.remove(
            "hidden"
        );

        const finishedAt =
            performance.now();

        const durationSeconds =
            Math.max(
                1,
                (
                    finishedAt -
                    recordingStartedAt
                ) / 1000
            );

        const silenceSeconds =
            totalSilenceMs / 1000;

        const speakingSeconds =
            Math.max(
                0,
                durationSeconds -
                silenceSeconds
            );

        const silenceRatio =
            durationSeconds > 0
                ? silenceSeconds /
                  durationSeconds
                : 0;

        const audioBlob =
            new Blob(
                audioChunks,
                {
                    type:
                        mediaRecorder.mimeType ||
                        "audio/webm"
                }
            );

        const question =
            currentQuestion();

        const formData =
            new FormData();

        formData.append(
            "audio",
            audioBlob,
            "answer.webm"
        );

        formData.append(
            "question_id",
            String(
                question.id
            )
        );

        formData.append(
            "duration_seconds",
            String(
                durationSeconds
            )
        );

        formData.append(
            "speaking_seconds",
            String(
                speakingSeconds
            )
        );

        formData.append(
            "silence_seconds",
            String(
                silenceSeconds
            )
        );

        formData.append(
            "silence_ratio",
            String(
                silenceRatio
            )
        );

        formData.append(
            "long_pause_count",
            String(
                longPauseCount
            )
        );

        formData.append(
            "longest_pause_seconds",
            String(
                longestPauseMs / 1000
            )
        );

        try {
            const response = await fetch(
                `/api/interview/${interviewId}/answer`,
                {
                    method: "POST",
                    body: formData
                }
            );

            const responseText = await response.text();

            let result = {};

            try {
                result = responseText
                    ? JSON.parse(responseText)
                    : {};
            } catch (parseError) {
                console.error(
                    "CareerGrid backend returned non-JSON:",
                    responseText
                );

                throw new Error(
                    `Backend error (${response.status}). Check the Flask terminal.`
                );
            }

            if (!response.ok) {
                throw new Error(
                    result.error ||
                    `Answer evaluation failed (${response.status}).`
                );
            }

            if (result.completed) {
                window.location.href =
                    result.review_url;

                return;
            }

            questionIndex += 1;

            processingOverlay.classList.add(
                "hidden"
            );

            renderQuestion();

        } catch (error) {
            console.error(
                error
            );

            processingOverlay.classList.add(
                "hidden"
            );

            recordingTitle.textContent =
            "We couldn't process that answer.";

            recordingStatus.textContent =
            error.message || "Press the microphone to try again.";
        }
    }


    microphoneButton.addEventListener(
        "click",
        () => {
            if (isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
        }
    );


    finishButton.addEventListener(
        "click",
        stopRecording
    );


    renderQuestion();
})();