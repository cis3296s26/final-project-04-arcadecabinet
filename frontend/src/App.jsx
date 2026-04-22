import { useState } from "react";
import GameMenu from "./GameMenu";
import Dashboard from "./Dashboard";

function App() {
  const [page, setPage] = useState("menu");
  const [game, setGame] = useState(null);

  const handleCreate = (gameName) => {
    setGame(gameName);
    setPage("dashboard");
  };

  return (
    <>
      {page === "menu" && <GameMenu onCreate={handleCreate} />}

      {page === "dashboard" && <Dashboard game={game} />}
    </>
  );
}

export default App;
