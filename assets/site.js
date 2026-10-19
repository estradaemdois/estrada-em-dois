// Estrada em Dois — interações leves (sem bibliotecas)
(function () {
  // Menu do celular
  var botao = document.querySelector('.abrir-menu');
  var menu = document.getElementById('menu');
  if (botao && menu) {
    botao.addEventListener('click', function () {
      var aberto = menu.classList.toggle('aberto');
      botao.setAttribute('aria-expanded', aberto ? 'true' : 'false');
    });
  }

  // Foto que não carregou: some e deixa o fundo de montanhas no lugar
  document.querySelectorAll('.foto img, .hero > img').forEach(function (img) {
    function esconder() { img.style.visibility = 'hidden'; }
    if (img.complete && img.naturalWidth === 0) esconder();
    img.addEventListener('error', esconder);
  });

  // Copiar cupom
  document.querySelectorAll('[data-copiar]').forEach(function (b) {
    b.addEventListener('click', function () {
      var texto = b.getAttribute('data-copiar');
      var feito = function () { var o = b.textContent; b.textContent = 'Copiado!'; setTimeout(function () { b.textContent = o; }, 1800); };
      if (navigator.clipboard) navigator.clipboard.writeText(texto).then(feito, feito); else feito();
    });
  });

  // Vídeos do YouTube: só carregam ao clicar (site mais rápido)
  document.querySelectorAll('.video-player[data-id]').forEach(function (b) {
    b.addEventListener('click', function () {
      var f = document.createElement('iframe');
      f.src = 'https://www.youtube-nocookie.com/embed/' + b.getAttribute('data-id') + '?autoplay=1&rel=0';
      f.title = b.getAttribute('aria-label') || 'Vídeo do Estrada em Dois';
      f.allow = 'accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture';
      f.allowFullscreen = true;
      b.replaceWith(f);
      f.parentNode && f.parentNode.classList.add('video-player');
    });
  });

  // Filtro do blog
  var filtros = document.querySelectorAll('.filtros button');
  filtros.forEach(function (f) {
    f.addEventListener('click', function () {
      var cat = f.getAttribute('data-cat');
      filtros.forEach(function (x) { x.setAttribute('aria-pressed', x === f ? 'true' : 'false'); });
      document.querySelectorAll('[data-cats]').forEach(function (c) {
        c.hidden = !(cat === 'todos' || c.getAttribute('data-cats').indexOf(cat) > -1);
      });
    });
  });

  // Newsletter: se ainda não houver serviço de e-mail configurado no "action", abre o e-mail
  document.querySelectorAll('form.form-news').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (form.getAttribute('action')) return; // serviço configurado: envio normal
      e.preventDefault();
      var nome = form.querySelector('[name=nome]').value;
      var email = form.querySelector('[name=email]').value;
      location.href = 'mailto:estradaemdois@gmail.com?subject=' + encodeURIComponent('Quero receber os roteiros') +
        '&body=' + encodeURIComponent('Nome: ' + nome + '\nE-mail: ' + email);
    });
  });

  // Ano no rodapé
  var ano = document.getElementById('ano');
  if (ano) ano.textContent = new Date().getFullYear();
})();
