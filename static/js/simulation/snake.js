(() => {
  "use strict";
  const GRID = 20;
  const HIGH_SCORE_KEY = "careergrid-snake-high-score";

  window.CareerGridSnake = {
    mount(container) {
      if (!container) return null;
      let snake = [],
        food = null,
        direction = { x: 1, y: 0 },
        queued = direction;
      let score = 0,
        highScore = Number(localStorage.getItem(HIGH_SCORE_KEY)) || 0;
      let timer = null,
        running = false,
        paused = false,
        active = true,
        gameOver = false;

      const root = document.createElement("section");
      root.className = "snake-game";
      const heading = document.createElement("div");
      heading.className = "snake-heading";
      const title = document.createElement("div");
      title.innerHTML = "<span>DEBUG BREAK</span><h2>Snake</h2>";
      const scores = document.createElement("div");
      scores.className = "snake-scores";
      const canvasWrap = document.createElement("div");
      canvasWrap.className = "snake-canvas-wrap";
      const canvas = document.createElement("canvas");
      canvas.width = 400;
      canvas.height = 400;
      canvas.setAttribute("aria-label", "Snake game board");
      const overlay = document.createElement("div");
      overlay.className = "snake-overlay";
      const overlayTitle = document.createElement("strong");
      overlayTitle.textContent = "Ready?";
      const overlayText = document.createElement("span");
      overlayText.textContent = "Press Start or use an arrow key.";
      overlay.append(overlayTitle, overlayText);
      canvasWrap.append(canvas, overlay);
      const controls = document.createElement("div");
      controls.className = "snake-actions";
      [
        ["Start", "start"],
        ["Pause", "pause"],
        ["Resume", "resume"],
        ["Restart", "restart"],
      ].forEach(([label, action]) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        button.dataset.snakeAction = action;
        controls.append(button);
      });
      const mobile = document.createElement("div");
      mobile.className = "snake-direction-pad";
      [
        ["↑", "up"],
        ["←", "left"],
        ["↓", "down"],
        ["→", "right"],
      ].forEach(([label, move]) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        button.dataset.snakeMove = move;
        button.setAttribute("aria-label", `Move ${move}`);
        mobile.append(button);
      });
      heading.append(title, scores);
      root.append(heading, canvasWrap, controls, mobile);
      container.replaceChildren(root);
      const context = canvas.getContext("2d");

      function updateScores() {
        scores.textContent = `Score ${score}  ·  High ${highScore}`;
      }
      function randomFood() {
        const empty = [];
        for (let y = 0; y < GRID; y += 1)
          for (let x = 0; x < GRID; x += 1) {
            if (!snake.some((part) => part.x === x && part.y === y))
              empty.push({ x, y });
          }
        return empty[Math.floor(Math.random() * empty.length)] || null;
      }
      function draw() {
        const cell = canvas.width / GRID;
        context.fillStyle = "#071126";
        context.fillRect(0, 0, canvas.width, canvas.height);
        context.strokeStyle = "rgba(104,139,210,.08)";
        context.lineWidth = 1;
        for (let i = 0; i <= GRID; i += 1) {
          context.beginPath();
          context.moveTo(i * cell, 0);
          context.lineTo(i * cell, canvas.height);
          context.stroke();
          context.beginPath();
          context.moveTo(0, i * cell);
          context.lineTo(canvas.width, i * cell);
          context.stroke();
        }
        if (food) {
          context.fillStyle = "#c65cff";
          context.shadowColor = "#c65cff";
          context.shadowBlur = 12;
          context.beginPath();
          context.arc(
            (food.x + 0.5) * cell,
            (food.y + 0.5) * cell,
            cell * 0.3,
            0,
            Math.PI * 2,
          );
          context.fill();
          context.shadowBlur = 0;
        }
        snake.forEach((part, index) => {
          context.fillStyle = index ? "#268ef5" : "#64dcff";
          context.fillRect(
            part.x * cell + 2,
            part.y * cell + 2,
            cell - 4,
            cell - 4,
          );
        });
      }
      function schedule() {
        clearTimeout(timer);
        if (running && !paused && active)
          timer = setTimeout(tick, Math.max(65, 150 - score * 4));
      }
      function tick() {
        direction = queued;
        const head = {
          x: snake[0].x + direction.x,
          y: snake[0].y + direction.y,
        };
        if (
          head.x < 0 ||
          head.y < 0 ||
          head.x >= GRID ||
          head.y >= GRID ||
          snake.some((part) => part.x === head.x && part.y === head.y)
        ) {
          running = false;
          gameOver = true;
          clearTimeout(timer);
          overlay.hidden = false;
          overlayTitle.textContent = "Game Over";
          overlayText.textContent = `Final score: ${score}. Press Restart to try again.`;
          return;
        }
        snake.unshift(head);
        if (food && head.x === food.x && head.y === food.y) {
          score += 1;
          highScore = Math.max(score, highScore);
          localStorage.setItem(HIGH_SCORE_KEY, String(highScore));
          food = randomFood();
          updateScores();
        } else snake.pop();
        draw();
        schedule();
      }
      function reset(startNow = false) {
        clearTimeout(timer);
        snake = [
          { x: 8, y: 10 },
          { x: 7, y: 10 },
          { x: 6, y: 10 },
        ];
        direction = { x: 1, y: 0 };
        queued = direction;
        score = 0;
        food = randomFood();
        paused = false;
        gameOver = false;
        running = startNow;
        overlay.hidden = startNow;
        overlayTitle.textContent = "Ready?";
        overlayText.textContent = "Press Start or use an arrow key.";
        updateScores();
        draw();
        schedule();
      }
      function move(next) {
        const moves = {
          up: { x: 0, y: -1 },
          down: { x: 0, y: 1 },
          left: { x: -1, y: 0 },
          right: { x: 1, y: 0 },
        };
        const value = moves[next];
        if (!value || (value.x === -direction.x && value.y === -direction.y))
          return;
        queued = value;
        if (!running && !gameOver) {
          running = true;
          overlay.hidden = true;
          schedule();
        }
      }
      function keydown(event) {
        if (
          !active ||
          event.target instanceof HTMLInputElement ||
          event.target instanceof HTMLTextAreaElement
        )
          return;
        const keys = {
          ArrowUp: "up",
          w: "up",
          W: "up",
          ArrowDown: "down",
          s: "down",
          S: "down",
          ArrowLeft: "left",
          a: "left",
          A: "left",
          ArrowRight: "right",
          d: "right",
          D: "right",
        };
        if (keys[event.key]) {
          event.preventDefault();
          move(keys[event.key]);
        }
      }
      controls.addEventListener("click", (event) => {
        const action = event.target.closest("button")?.dataset.snakeAction;
        if (action === "start" && !running && !gameOver) {
          running = true;
          paused = false;
          overlay.hidden = true;
          schedule();
        }
        if (action === "pause" && running) {
          paused = true;
          clearTimeout(timer);
          overlay.hidden = false;
          overlayTitle.textContent = "Paused";
          overlayText.textContent = "Select Resume when you are ready.";
        }
        if (action === "resume" && running && paused) {
          paused = false;
          overlay.hidden = true;
          schedule();
        }
        if (action === "restart") reset(true);
      });
      mobile.addEventListener("click", (event) => {
        const next = event.target.closest("button")?.dataset.snakeMove;
        if (next) move(next);
      });
      document.addEventListener("keydown", keydown);
      reset(false);
      return {
        setActive(value) {
          active = Boolean(value);
          if (!active) clearTimeout(timer);
          else schedule();
        },
        destroy() {
          clearTimeout(timer);
          document.removeEventListener("keydown", keydown);
          root.remove();
        },
      };
    },
  };
})();
