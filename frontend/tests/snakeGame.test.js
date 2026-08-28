import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

import {
  pauseSnakeGame,
  placeFood,
  queueSnakeMove,
  resetSnakeGame,
  resumeSnakeGame,
  startSnakeGame,
  tickSnakeGame,
} from '../src/simulation/state/snakeGame.js'

test('Snake starts in the legacy position and moves on its timed tick', () => {
  let game = resetSnakeGame(4, false, () => 0)
  assert.deepEqual(game.snake, [{ x: 8, y: 10 }, { x: 7, y: 10 }, { x: 6, y: 10 }])
  assert.equal(game.running, false)
  assert.equal(game.highScore, 4)

  game = startSnakeGame(game)
  game = tickSnakeGame(game, () => 0)
  assert.deepEqual(game.snake, [{ x: 9, y: 10 }, { x: 8, y: 10 }, { x: 7, y: 10 }])
})

test('Snake accepts arrow-direction changes, rejects reversal, and supports pause and resume', () => {
  let game = startSnakeGame(resetSnakeGame())
  assert.equal(queueSnakeMove(game, 'left'), game)
  game = queueSnakeMove(game, 'up')
  game = tickSnakeGame(game)
  assert.deepEqual(game.snake[0], { x: 8, y: 9 })

  game = pauseSnakeGame(game)
  assert.equal(game.paused, true)
  assert.equal(tickSnakeGame(game), game)
  game = resumeSnakeGame(game)
  assert.equal(game.paused, false)
})

test('eating food grows the snake and updates score and high score', () => {
  let game = startSnakeGame(resetSnakeGame(0, false, () => 0))
  game = { ...game, food: { x: 9, y: 10 } }
  game = tickSnakeGame(game, () => 0)

  assert.equal(game.snake.length, 4)
  assert.equal(game.score, 1)
  assert.equal(game.highScore, 1)
  assert.ok(game.food)
  assert.equal(game.snake.some((part) => part.x === game.food.x && part.y === game.food.y), false)
})

test('wall and self collisions stop the game with game-over state', () => {
  const wall = tickSnakeGame({
    ...startSnakeGame(resetSnakeGame()),
    direction: { x: 1, y: 0 },
    queued: { x: 1, y: 0 },
    snake: [{ x: 19, y: 4 }, { x: 18, y: 4 }, { x: 17, y: 4 }],
  })
  assert.equal(wall.running, false)
  assert.equal(wall.gameOver, true)

  const self = tickSnakeGame({
    ...startSnakeGame(resetSnakeGame()),
    direction: { x: 0, y: 1 },
    queued: { x: -1, y: 0 },
    snake: [{ x: 2, y: 2 }, { x: 2, y: 3 }, { x: 1, y: 3 }, { x: 1, y: 2 }],
  })
  assert.equal(self.gameOver, true)
})

test('food placement only selects unoccupied grid cells', () => {
  const snake = [{ x: 0, y: 0 }, { x: 1, y: 0 }]
  assert.deepEqual(placeFood(snake, () => 0), { x: 2, y: 0 })
})

test('Browser retains the legacy Snake canvas, controls, and active-window integration', async () => {
  const [browser, desktop] = await Promise.all([
    readFile(new URL('../src/simulation/apps/BrowserApp.jsx', import.meta.url), 'utf8'),
    readFile(new URL('../src/simulation/SimulationDesktop.jsx', import.meta.url), 'utf8'),
  ])
  for (const contract of ['snake-heading', 'snake-scores', 'snake-canvas-wrap', 'snake-overlay', 'snake-actions', 'snake-direction-pad']) {
    assert.ok(browser.includes(contract))
  }
  assert.match(browser, /ArrowUp/)
  assert.match(browser, /SNAKE_HIGH_SCORE_KEY/)
  assert.match(desktop, /<BrowserApp active=\{active\}/)
})
