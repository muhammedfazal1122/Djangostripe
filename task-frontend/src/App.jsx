import { useState } from "react";
import Login from "./components/Login";
import TaskManager from "./components/TaskManager";
import AuthForm from "./components/AuthForm";

function App() {
  const [token, setToken] = useState(localStorage.getItem("access_token"));

  return (
    <div className="App">
      {token ? <TaskManager token={token} /> : <AuthForm setToken={setToken} />}
    </div>
  );
}

export default App;
