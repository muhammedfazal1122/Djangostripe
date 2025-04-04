import { useState } from "react";
import AuthForm from "./components/AuthForm";

function App() {
  const [token, setToken] = useState(localStorage.getItem("access_token"));

  return (
    <div>
      {token ? (
        <h1 className="text-3xl font-bold text-center mt-10">Welcome!</h1>
      ) : (
        <AuthForm setToken={setToken} />
      )}
    </div>
  );
}

export default App;
