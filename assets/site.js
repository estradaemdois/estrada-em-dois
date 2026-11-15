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
// ---- layout novo (nov/2026) ----
(function () {
  var PAGINAS = [{"u": "mal-de-altitude-atacama.html", "t": "Mal de altitude no Atacama: como evitar e o que fazer", "d": "O que a gente sentiu a 4.300 m e no Cerro Toco, a ordem certa dos passeios, sinais de alerta, onde tem atendimento e se o seguro viagem cobre.", "i": "assets/cerro-toco-descanso.webp", "g": "Guia prático", "c": "guias chile atacama altitude soroche seguro"}, {"u": "viajar-sem-seguro-viagem.html", "t": "Viajar sem seguro viagem: e se passar mal?", "d": "Quem paga o hospital, o que muda na Argentina, por que o seguro comprado depois de ficar doente não cobre e o que fazer se você já está viajando sem seguro.", "i": "assets/argentina-atacama.webp", "g": "Guia prático", "c": "guias argentina chile"}, {"u": "cerro-toco.html", "t": "Cerro Toco: como foi tentar subir a pé um vulcão de 5.604 m no Atacama", "d": "Cerro Toco, perto de San Pedro de Atacama: nosso carro 4x2 não subiu, seguimos a pé e voltamos a uns 400 m do cume. Altitude, frio, AllTrails e dicas.", "i": "assets/cerro-toco-vista.webp", "g": "Chile", "c": "chile"}, {"u": "geysers-del-tatio.html", "t": "Gêiseres del Tatio: como é o passeio mais frio do Atacama", "d": "Gêiseres del Tatio: saída de madrugada, -14°C no dia em que fomos e gêiseres a mais de 4.300 m. O que levar e como se preparar.", "i": "assets/el-tatio-campo.webp", "g": "Chile", "c": "chile"}, {"u": "seguro-viagem-argentina-chile.html", "t": "Seguro viagem para Argentina, Chile e Uruguai: é obrigatório e qual a cobertura mínima?", "d": "O que cada país exige, qual seguro a Argentina aceita, quanto de cobertura médica contratar, se o seguro do cartão vale e como usar o cupom ESTRADAEMDOIS.", "i": "assets/argentina-atacama.webp", "g": "Guia prático", "c": "guias argentina chile"}, {"u": "foz-do-iguacu-em-1-dia.html", "t": "Foz do Iguaçu em 1 dia: dá para ver Cataratas e Itaipu?", "d": "Dá, sim. Horários, ingressos e o que saber para encaixar os dois passeios no mesmo dia.", "i": "assets/brasil-cataratas.webp", "g": "Brasil", "c": "brasil"}, {"u": "morro-do-fogao-itirapina.html", "t": "Morro do Fogão (Itirapina): como chegar, camping de graça e pôr do sol", "d": "Como chegar saindo de Rio Preto, pedágios, estrutura e as regras para acampar no alto do morro.", "i": "assets/morro-do-fogao.webp", "g": "Brasil", "c": "brasil"}, {"u": "documentos-argentina-de-carro.html", "t": "Argentina de carro: documentos, Carta Verde e itens obrigatórios", "d": "Documentos para entrar na Argentina de carro: RG ou passaporte, CNH, CRLV, como tirar a Carta Verde, seguro viagem e itens obrigatórios no carro.", "i": "assets/argentina-atacama.webp", "g": "Guia prático", "c": "guias argentina"}, {"u": "argentina-atacama-de-carro.html", "t": "Da Argentina ao Atacama de carro: nosso roteiro", "d": "Roteiro parada por parada pelo norte argentino até San Pedro de Atacama.", "i": "assets/salta-norte-argentino.webp", "g": "Roteiro", "c": "argentina chile"}, {"u": "valle-de-la-luna.html", "t": "Valle de la Luna: a paisagem de outro planeta no Atacama", "d": "Dunas, paredões e formações que parecem de outro planeta: fotos, vídeo e o essencial para visitar em San Pedro de Atacama.", "i": "assets/valle-de-la-luna-card-extraido.webp", "g": "Chile", "c": "chile"}, {"u": "argentina.html", "t": "Norte da Argentina de carro: Salta, Purmamarca e Salinas Grandes", "d": "Nossa viagem pelo norte argentino: Salta, Cafayate, Purmamarca, Salinas Grandes e a estrada até o Atacama, com documentos e dicas de fronteira.", "i": "assets/salta-norte-argentino.webp", "g": "Destino", "c": "argentina salta jujuy"}, {"u": "blog.html", "t": "Blog de viagem de carro", "d": "Guias práticos e roteiros de viagem de carro pela Argentina, Chile e Brasil: documentos de fronteira, seguro viagem, Atacama, Foz do Iguaçu e mais.", "i": "assets/hero-casal.webp", "g": "Blog", "c": "posts"}, {"u": "brasil.html", "t": "Viagens pelo Brasil: Foz do Iguaçu, interior de SP e Goiás", "d": "Nossas viagens pelo Brasil com preços e horários: Cataratas do Iguaçu, Itaipu, Serra Negra, Morro do Fogão, Águas de São Pedro e Lagoa Santa.", "i": "assets/brasil-cataratas.webp", "g": "Destino", "c": "brasil foz itirapina"}, {"u": "chile.html", "t": "Chile e Deserto do Atacama: o que fazer", "d": "Nossa viagem pelo Chile: San Pedro de Atacama, Valle de la Luna, Geysers del Tatio e dicas para quem chega de carro pela Argentina.", "i": "assets/deserto-atacama.webp", "g": "Destino", "c": "chile atacama"}, {"u": "midia-kit.html", "t": "Parcerias e mídia kit", "d": "Anuncie para quem viaja de carro: vídeos no YouTube, Reels, TikTok, guias no site e produção de conteúdo com drone para pousadas, passeios, destinos e marcas de viagem.", "i": "assets/hero-casal.webp", "g": "Parcerias", "c": "parceria midia kit marca pousada"}, {"u": "sobre.html", "t": "Sobre nós: Andressa e Guilherme", "d": "Somos a Andressa e o Guilherme, um casal de São José do Rio Preto (SP) que viaja de carro pelo Brasil, Argentina e Chile e conta tudo no YouTube e aqui no site.", "i": "assets/hero-casal.webp", "g": "Sobre nós", "c": "andressa guilherme"}, {"u": "quicktrip/", "t": "Para onde ir no fim de semana", "d": "O QuickTrip monta o fim de semana saindo de Rio Preto e região: destino, passeios e combustível.", "i": "assets/brasil-lagoa-santa.webp", "g": "Ferramenta", "c": "fim de semana quicktrip"}];
  var $ = function (s, el) { return (el || document).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || document).querySelectorAll(s)); };
  var norm = function (s) { return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };

  // Menu do celular
  var gaveta = $('#nv-gaveta');
  var botaoMenu = $('[data-abrir-gaveta]');
  function fecharGaveta() { if (!gaveta) return; gaveta.classList.remove('nv-aberta'); document.body.style.overflow = ''; if (botaoMenu) botaoMenu.setAttribute('aria-expanded', 'false'); }
  if (gaveta && botaoMenu) {
    botaoMenu.addEventListener('click', function () { gaveta.classList.add('nv-aberta'); document.body.style.overflow = 'hidden'; botaoMenu.setAttribute('aria-expanded', 'true'); });
    $$('[data-fechar-gaveta]').forEach(function (b) { b.addEventListener('click', fecharGaveta); });
  }

  // Busca no site
  var modal = $('#nv-busca'), campo = $('#nv-busca-input'), res = $('#nv-busca-res');
  function buscar(q) {
    var n = norm(q.trim());
    var lista = n ? PAGINAS.filter(function (p) { return norm(p.t + ' ' + p.d + ' ' + p.c + ' ' + p.g).indexOf(n) > -1; }) : PAGINAS.slice(0, 6);
    res.innerHTML = lista.length ? lista.map(function (p) {
      return '<a href="/' + esc(p.u) + '">' + (p.i ? '<img src="/' + esc(p.i) + '" alt="" width="64" height="44" loading="lazy">' : '') + '<div><strong>' + esc(p.t) + '</strong><small>' + esc(p.g) + ' · ' + esc(p.d) + '</small></div></a>';
    }).join('') : '<p style="padding:10px;margin:0">Nada encontrado. Tente "Atacama", "seguro" ou "Foz".</p>';
  }
  function abrirBusca(q) {
    if (!modal) return;
    fecharGaveta();
    modal.classList.add('nv-aberta');
    campo.value = q || '';
    buscar(campo.value);
    setTimeout(function () { campo.focus(); }, 30);
  }
  function fecharBusca() { if (modal) modal.classList.remove('nv-aberta'); }
  if (modal) {
    $$('[data-abrir-busca]').forEach(function (b) { b.addEventListener('click', function () { abrirBusca(); }); });
    $$('[data-buscar]').forEach(function (a) { a.addEventListener('click', function (e) { e.preventDefault(); abrirBusca(a.getAttribute('data-buscar')); }); });
    campo.addEventListener('input', function () { buscar(campo.value); });
    campo.addEventListener('keydown', function (e) { if (e.key === 'Enter') { var p = $('a', res); if (p) location.href = p.getAttribute('href'); } });
    $$('[data-fechar-busca]').forEach(function (b) { b.addEventListener('click', fecharBusca); });
    modal.addEventListener('click', function (e) { if (e.target === modal) fecharBusca(); });
  }
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { fecharBusca(); fecharGaveta(); } });

  // Blog: busca e filtros
  var grade = $('#nv-blog-grade');
  if (grade) {
    var buscaBlog = $('#nv-blog-busca'), destaque = $('#nv-blog-destaque'), cat = '';
    var cards = $$('[data-cats]', grade);
    var filtrar = function () {
      var q = norm(buscaBlog.value.trim()), total = 0;
      var passa = function (el) { return (!cat || el.getAttribute('data-cats').indexOf(cat) > -1) && (!q || norm(el.textContent + ' ' + el.getAttribute('data-cats')).indexOf(q) > -1); };
      cards.forEach(function (c) { var ok = passa(c); c.hidden = !ok; if (ok) total++; });
      var destOk = passa(destaque);
      destaque.hidden = !destOk;
      if (destOk) total++;
      $('#nv-blog-contagem').textContent = total + (total === 1 ? ' post' : ' posts');
      $('#nv-blog-vazio').style.display = total ? 'none' : 'block';
    };
    buscaBlog.addEventListener('input', filtrar);
    var chips = $$('#nv-blog-filtros button');
    chips.forEach(function (b) { b.addEventListener('click', function () { cat = b.getAttribute('data-cat'); chips.forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); }); filtrar(); }); });
    $('#nv-blog-limpar').addEventListener('click', function () { cat = ''; buscaBlog.value = ''; chips.forEach(function (x, i) { x.setAttribute('aria-pressed', i === 0 ? 'true' : 'false'); }); filtrar(); });
  }

  // Artigos: barra de leitura e índice que acompanha a rolagem
  var texto = $('.artigo .texto');
  var indiceLat = $('.artigo .lateral .caixa ol');
  if (texto && indiceLat) {
    var barra = document.createElement('div');
    barra.className = 'nv-progresso';
    document.body.appendChild(barra);
    var movel = document.createElement('details');
    movel.className = 'nv-indice-movel';
    movel.innerHTML = '<summary>Neste post <span></span></summary>' + indiceLat.outerHTML;
    texto.insertBefore(movel, texto.firstChild);
    var titulos = $$('h2[id]', texto);
    var links = $$('a[href^="#"]', indiceLat).concat($$('a[href^="#"]', movel));
    $$('a', movel).forEach(function (a) { a.addEventListener('click', function () { movel.open = false; }); });
    var aoRolar = function () {
      var r = texto.getBoundingClientRect();
      var p = Math.min(1, Math.max(0, -r.top / Math.max(1, r.height - innerHeight)));
      barra.style.width = (p * 100) + '%';
      var atual = null;
      titulos.forEach(function (h) { if (h.getBoundingClientRect().top < 140) atual = h; });
      links.forEach(function (a) { a.classList.toggle('nv-ativo', !!atual && a.getAttribute('href') === '#' + atual.id); });
      $('summary span', movel).textContent = atual ? atual.textContent : '';
    };
    addEventListener('scroll', aoRolar, { passive: true });
    aoRolar();
  }

})();
