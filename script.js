// Mensajes romÃ¡nticos para mostrar cuando intenten abrir antes de tiempo
const mensajesRomanticos = [
  "No desesperes chiquita 🌸",
  "Ya casi mi amor 💕",
  "Espera un poquitito más princesa 👑",
  "No sabes cuánto te amo mi niña ❤️",
  "Vale la pena la espera, te lo prometo 🥺",
  "Poquito más mi vida 🌹",
  "Pronto pronto, corazón 💖",
];

let mensajeActualIndex = 0;
let mensajeInterval = null;

function mostrarMensajeEspera() {
  // Si ya existe el modal, solo hacerlo visible
  let modal = document.getElementById('modal-espera');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'modal-espera';
    modal.innerHTML = `
      <div class="modal-contenido">
        <div class="modal-icono">💌</div>
        <p id="mensaje-romantico">${mensajesRomanticos[0]}</p>
        <div class="modal-timer-mini" id="modal-timer"></div>
        <button onclick="cerrarModal()">Oki mi amor 🩷</button>
      </div>
    `;
    document.body.appendChild(modal);
  }

  modal.classList.add('visible');

  // Rotar mensajes cada 2.5s
  mensajeActualIndex = 0;
  document.getElementById('mensaje-romantico').textContent = mensajesRomanticos[0];

  if (mensajeInterval) clearInterval(mensajeInterval);
  mensajeInterval = setInterval(() => {
    mensajeActualIndex = (mensajeActualIndex + 1) % mensajesRomanticos.length;
    const el = document.getElementById('mensaje-romantico');
    if (el) {
      el.style.opacity = '0';
      el.style.transform = 'translateY(8px)';
      setTimeout(() => {
        el.textContent = mensajesRomanticos[mensajeActualIndex];
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';
      }, 300);
    }
  }, 2500);
}

function cerrarModal() {
  const modal = document.getElementById('modal-espera');
  if (modal) modal.classList.remove('visible');
  if (mensajeInterval) {
    clearInterval(mensajeInterval);
    mensajeInterval = null;
  }
}

// â”€â”€â”€ Temporizador fijo: 3 de abril 2025 a las 00:00:00 hora MÃ©xico (UTC-6) â”€â”€â”€
// Nota: ajusta el aÃ±o si es necesario.
function obtenerFechaObjetivo() {
  // Objetivo: 3 de abril 2026 a las 00:00:00 hora MÃ©xico Ciudad (CDT = UTC-5 en verano)
  // 3 abril 2026 00:00 CDT  â†’  3 abril 2026 05:00 UTC
  return new Date('2026-04-03T00:00:00-06:00');
}

const countDownDate = obtenerFechaObjetivo().getTime();

function intentarAbrirCarta() {
  const ahora = new Date().getTime();

  if (ahora >= countDownDate) {
    // Â¡Ya llegÃ³ la hora! Descargar la carta
    const xhr = new XMLHttpRequest();
    xhr.open('GET', 'carta.pdf', true);
    xhr.responseType = 'blob';
    xhr.onload = function () {
      if (xhr.status === 200) {
        const blob = xhr.response;
        const link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = 'cartita.pdf';
        link.click();
        window.URL.revokeObjectURL(link.href);
      } else {
        console.error('No se pudo descargar el archivo.');
      }
    };
    xhr.send();
  } else {
    // AÃºn no es hora ðŸ’•
    mostrarMensajeEspera();
  }
}

document.querySelector('.heart').addEventListener('click', intentarAbrirCarta);

// â”€â”€â”€ Countdown display â”€â”€â”€
function actualizarCountdown() {
  var now = new Date().getTime();
  var distance = countDownDate - now;

  if (distance <= 0) {
    clearInterval(x);
    document.getElementById("countdown").innerHTML =
      `<span class="carta-lista">Â¡Tu cartita estÃ¡ lista! Toca el corazÃ³n ðŸ’Œ</span>`;
    // Cerrar modal si estaba abierto
    cerrarModal();
    return;
  }

  var days = Math.floor(distance / (1000 * 60 * 60 * 24));
  var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
  var seconds = Math.floor((distance % (1000 * 60)) / 1000);

  let texto = '';
  if (days > 0) texto += `${days}d `;
  texto += `${String(hours).padStart(2,'0')}h ${String(minutes).padStart(2,'0')}m ${String(seconds).padStart(2,'0')}s`;

  document.getElementById("countdown").innerHTML =
    `<span class="countdown-label">Tu carta llega en:</span><br><span class="countdown-tiempo">${texto}</span>`;

  // Actualizar tambiÃ©n el mini-timer del modal si estÃ¡ abierto
  const miniTimer = document.getElementById('modal-timer');
  if (miniTimer) {
    miniTimer.textContent = texto;
  }

}

actualizarCountdown();
var x = setInterval(actualizarCountdown, 1000);
