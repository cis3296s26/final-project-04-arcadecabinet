import { useEffect, useState } from 'react'
import GameMenu from './GameMenu'
import ServerStarter from './ServerStarter'

function App() {
  const [page, setPage] = useState('menu')
  const [game, setGame] = useState(null)

  useEffect(() => {
    const body = document.body
    body.classList.remove('theme-menu', 'theme-starter')
    body.classList.add(page === 'menu' ? 'theme-menu' : 'theme-starter')

    return () => {
      body.classList.remove('theme-menu', 'theme-starter')
    }
  }, [page])

  const handleCreate = (gameName) => {
    setGame(gameName)
    setPage('starter')
  }

  const handleBack = () => {
    setPage('menu')
  }

  return (
    <>
      {page === 'menu' && <GameMenu onCreate={handleCreate} />}
      {page === 'starter' && <ServerStarter game={game} onBack={handleBack} />}
    </>
  )
}

export default App
