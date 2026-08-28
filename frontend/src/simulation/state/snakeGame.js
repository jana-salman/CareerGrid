const GRID_SIZE = 20

const moves = {
  down: { x: 0, y: 1 },
  left: { x: -1, y: 0 },
  right: { x: 1, y: 0 },
  up: { x: 0, y: -1 },
}

function placeFood(snake, random = Math.random) {
  const empty = []
  for (let y = 0; y < GRID_SIZE; y += 1) {
    for (let x = 0; x < GRID_SIZE; x += 1) {
      if (!snake.some((part) => part.x === x && part.y === y)) empty.push({ x, y })
    }
  }
  return empty[Math.floor(random() * empty.length)] || null
}

function resetSnakeGame(highScore = 0, startNow = false, random = Math.random) {
  const snake = [{ x: 8, y: 10 }, { x: 7, y: 10 }, { x: 6, y: 10 }]
  const direction = { x: 1, y: 0 }
  return {
    direction,
    food: placeFood(snake, random),
    gameOver: false,
    highScore: Number(highScore) || 0,
    paused: false,
    queued: direction,
    running: startNow,
    score: 0,
    snake,
  }
}

function queueSnakeMove(game, next) {
  const value = moves[next]
  if (!value || (value.x === -game.direction.x && value.y === -game.direction.y)) return game
  return {
    ...game,
    queued: value,
    running: game.gameOver ? game.running : true,
  }
}

function startSnakeGame(game) {
  return !game.running && !game.gameOver ? { ...game, paused: false, running: true } : game
}

function pauseSnakeGame(game) {
  return game.running ? { ...game, paused: true } : game
}

function resumeSnakeGame(game) {
  return game.running && game.paused ? { ...game, paused: false } : game
}

function tickSnakeGame(game, random = Math.random) {
  if (!game.running || game.paused || game.gameOver) return game
  const direction = game.queued
  const head = {
    x: game.snake[0].x + direction.x,
    y: game.snake[0].y + direction.y,
  }
  const collision = head.x < 0 || head.y < 0 || head.x >= GRID_SIZE || head.y >= GRID_SIZE
    || game.snake.some((part) => part.x === head.x && part.y === head.y)
  if (collision) return { ...game, direction, gameOver: true, running: false }

  const snake = [head, ...game.snake]
  if (game.food && head.x === game.food.x && head.y === game.food.y) {
    const score = game.score + 1
    return {
      ...game,
      direction,
      food: placeFood(snake, random),
      highScore: Math.max(score, game.highScore),
      score,
      snake,
    }
  }
  snake.pop()
  return { ...game, direction, snake }
}

function snakeTickDelay(score) { return Math.max(65, 150 - Number(score || 0) * 4) }

export {
  GRID_SIZE,
  pauseSnakeGame,
  placeFood,
  queueSnakeMove,
  resetSnakeGame,
  resumeSnakeGame,
  snakeTickDelay,
  startSnakeGame,
  tickSnakeGame,
}
