import './index1.css'
import mcImg from './imgs/mc-bg.png'
import csImg from './imgs/cs2-bg.png'

function GameMenu({ onCreate }) {
  return (
    <>
      <header className="main-header">
        <h1 className="logo-text">Arcade Cabinet</h1>
        
      </header>

      <section className="grid-container">

        <article className="game-card">
          <div className="image-wrapper">
            <img src={csImg} alt="CS2" />

            <div className="overlay-buttons">
              <button
                className="btn create-btn"
                onClick={() => onCreate('cs2')}
              >
                Create
              </button>

              <button
                className="btn join-btn"
                onClick={() => onCreate('cs2')}
              >
                Join
              </button>
            </div>
          </div>

          <div className="card-content">
            <h3>CS2</h3>
            <p>Status: <em>Available</em></p>
          </div>
        </article>

        <article className="game-card">
          <div className="image-wrapper">
            <img src={mcImg} alt="Minecraft" />

            <div className="overlay-buttons">
              <button
                className="btn create-btn"
                onClick={() => onCreate('minecraft')}
              >
                Create
              </button>

              <button
                className="btn join-btn"
                onClick={() => onCreate('minecraft')}
              >
                Join
              </button>
            </div>
          </div>

          <div className="card-content">
            <h3>Minecraft</h3>
            <p>Status: <em>Available</em></p>
          </div>
        </article>
        <article class="game-card coming-soon">
        <div class="image-wrapper">
          <img src="./imgs/valheim-bg.png" alt="Valheim" draggable="false" />
        </div>
        <div class="card-content">
          <h3>Valheim</h3>
          <p>Status: <em>Coming Soon</em></p>
        </div>
      </article>
        

      </section>
    </>
  )
}

export default GameMenu
