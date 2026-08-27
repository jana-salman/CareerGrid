function TaskPanel({ attempt, progress }) {
  const scenario = attempt.public_scenario || {}
  const task = scenario.task || {}
  const totalSteps = scenario.frontend_tasks?.length || 5
  const currentStep = Number(progress?.current_step || 1)
  const complete = progress?.status === 'completed' || Boolean(progress?.evaluation)
  const title = task.subject || task.title || 'Workplace task'
  const instructions = task.instructions || task.description || 'Open the workspace tools to investigate the task.'

  return <aside className="frontend-task-panel" aria-label="Current simulation task">
    <small>WORKPLACE SIMULATION · TASK {Math.min(currentStep, totalSteps)} OF {totalSteps}</small>
    <h2>{complete ? 'Simulation complete' : title}</h2>
    <p>{complete ? progress.evaluation?.summary || 'Your report is ready.' : instructions}</p>
    <div className="frontend-task-progress" aria-label={`Progress: step ${currentStep} of ${totalSteps}`}>
      {Array.from({ length: totalSteps }, (_, index) => <span className={index + 1 <= currentStep ? 'done' : ''} key={index} />)}
    </div>
    {scenario.frontend_tasks?.[currentStep - 1]?.objective && <p>{scenario.frontend_tasks[currentStep - 1].objective}</p>}
    <p className="frontend-task-success">Use the workspace apps to complete this step. Submission remains in the existing workflow.</p>
  </aside>
}

export default TaskPanel
