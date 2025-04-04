import { useEffect, useState } from "react";
import { getTasks, createTask, deleteTask, getMetering } from "./api";

export default function TaskManager({ token }) {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [metering, setMetering] = useState(null);

  const fetchData = async () => {
    const data = await getTasks(token);
    setTasks(data);
    const meteringData = await getMetering(token);
    setMetering(meteringData);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    await createTask(token, { title, description });
    setTitle("");
    setDescription("");
    fetchData();
  };

  const handleDelete = async (id) => {
    await deleteTask(token, id);
    fetchData();
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div>
      <h2>Task Manager</h2>

      <form onSubmit={handleCreate}>
        <input
          type="text"
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
        <input
          type="text"
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
        />
        <button type="submit">Create Task</button>
      </form>

      <h3>Tasks</h3>
      <ul>
        {tasks.map((task) => (
          <li key={task.id}>
            <strong>{task.title}</strong>: {task.description}
            <button onClick={() => handleDelete(task.id)}>Delete</button>
          </li>
        ))}
      </ul>

      {metering && (
        <div>
          <h4>API Metering</h4>
          <p>Total: {metering.total_calls} / {metering.total_limit}</p>
          <p>Daily: {metering.daily_calls} / {metering.daily_limit}</p>
        </div>
      )}
    </div>
  );
}
