import "./index1.css";

// Import all images so Vite can find them
import csImg from "./imgs/cs2-bg.png";
import mcImg from "./imgs/mc-bg.png";
import arkImg from "./imgs/ark-bg.png";
import armaImg from "./imgs/arma3-bg.png";
import kf2Img from "./imgs/kf2-bg.png";
import rustImg from "./imgs/rust-bg.png";
import terrariaImg from "./imgs/terraria-bg.png";
import valheimImg from "./imgs/valheim-bg.png";

function GameMenu({ onCreate }) {
  return (
    <>
      <header className="main-header">
        <h1 className="logo-text">Arcade Cabinet</h1>
      </header>

      <section className="grid-container">
        <article className="game-card">
          <div className="image-wrapper">
            <img src={csImg} alt="CS2" draggable="false" />
            <div className="overlay-buttons">
              <button
                className="btn create-btn"
                onClick={() => onCreate("cs2")}
              >
                Create
              </button>
              <button className="btn join-btn" onClick={() => onCreate("cs2")}>
                Join
              </button>
            </div>
          </div>
          <div className="card-content">
            <h3>CS2</h3>
            <p>
              Status: <em>Available</em>
            </p>
          </div>
        </article>

        <article className="game-card">
          <div className="image-wrapper">
            <img src={mcImg} alt="Minecraft" draggable="false" />
            <div className="overlay-buttons">
              <button
                className="btn create-btn"
                onClick={() => onCreate("minecraft")}
              >
                Create
              </button>
              <button
                className="btn join-btn"
                onClick={() => onCreate("minecraft")}
              >
                Join
              </button>
            </div>
          </div>
          <div className="card-content">
            <h3>Minecraft</h3>
            <p>
              Status: <em>Available</em>
            </p>
          </div>
        </article>

        <article className="game-card coming-soon">
          <div className="image-wrapper">
            <img src={arkImg} alt="Ark" draggable="false" />
          </div>
          <div className="card-content">
            <h3>Ark: Survival Evolved</h3>
            <p>
              Status: <em>Coming Soon</em>
            </p>
          </div>
        </article>

        <article className="game-card coming-soon">
          <div className="image-wrapper">
            <img src={armaImg} alt="Arma 3" draggable="false" />
          </div>
          <div className="card-content">
            <h3>Arma 3</h3>
            <p>
              Status: <em>Coming Soon</em>
            </p>
          </div>
        </article>

        <article className="game-card coming-soon">
          <div className="image-wrapper">
            <img src={kf2Img} alt="Killing Floor 2" draggable="false" />
          </div>
          <div className="card-content">
            <h3>Killing Floor 2</h3>
            <p>
              Status: <em>Coming Soon</em>
            </p>
          </div>
        </article>

        <article className="game-card coming-soon">
          <div className="image-wrapper">
            <img src={rustImg} alt="Rust" draggable="false" />
          </div>
          <div className="card-content">
            <h3>Rust</h3>
            <p>
              Status: <em>Coming Soon</em>
            </p>
          </div>
        </article>

        <article className="game-card coming-soon">
          <div className="image-wrapper">
            <img src={terrariaImg} alt="Terraria" draggable="false" />
          </div>
          <div className="card-content">
            <h3>Terraria</h3>
            <p>
              Status: <em>Coming Soon</em>
            </p>
          </div>
        </article>

        <article className="game-card coming-soon">
          <div className="image-wrapper">
            <img src={valheimImg} alt="Valheim" draggable="false" />
          </div>
          <div className="card-content">
            <h3>Valheim</h3>
            <p>
              Status: <em>Coming Soon</em>
            </p>
          </div>
        </article>
      </section>
    </>
  );
}

export default GameMenu;
