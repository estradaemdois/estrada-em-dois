# QuickTrip

Página do Estrada em Dois que lista destinos de viagem curta num raio de até 200 km da cidade escolhida. Mostra pontos turísticos, ideias de hospedagem, eventos, estimativa de combustível e link para traçar a rota no Google Maps. Tem um botão que sorteia um destino dentro do raio e filtros por duração e interesse. O mapa é real (Leaflet + OpenStreetMap). O visual usa o tema escuro em azul-petróleo do site e um tema claro em creme, conforme a preferência do aparelho.

Endereço: `https://estradaemdois.com.br/quicktrip/`

```
quicktrip/
  index.html                 página publicada, gerada por _ferramentas/build.py
  dados/destinos.json        origens, destinos e parceiros (edite aqui para ampliar a base)
  dados/eventos.json         gerado por _ferramentas/scripts/atualizar_eventos.py
  dados/avaliacoes.json      gerado por _ferramentas/scripts/atualizar_avaliacoes.py
  _ferramentas/              não é publicado pelo GitHub Pages (pasta começa com "_")
    src/pagina.html          modelo da página (CSS, HTML e JS)
    build.py                 gera quicktrip/index.html
    scripts/                 atualizadores de eventos e avaliações
```

Não edite `quicktrip/index.html` à mão. Mude `_ferramentas/src/pagina.html` e rode o build, senão a próxima geração apaga a alteração.

## Rodar e ver no seu computador

```bash
python3 quicktrip/_ferramentas/build.py     # gera quicktrip/index.html
python3 -m http.server 8000                 # na raiz do repositório
# abra http://localhost:8000/quicktrip/
```

Abrir o `index.html` direto do disco não funciona, porque o navegador bloqueia a leitura dos JSON, e a marca e o ícone usam caminhos a partir da raiz do site. Use o servidor local acima.

## Monte seu fim de semana (assistente)

A página abre com um assistente em 8 etapas, uma por vez. Cada etapa obrigatória só libera o botão "Continuar" depois de respondida:

1. Saída (cidade de origem), 2. Tempo (bate-volta, 1 noite, 2 noites ou mais), 3. Companhia, 4. Clima (os interesses de `tags`, ou "Tanto faz"),
5. Transporte e consumo/preço do litro (opcional; "Pular" usa valores de exemplo), 6. Seu destino, 7. Custos, 8. Onde ficar (última etapa, com hospedagem).

A ferramenta escolhe o destino e os lugares do roteiro: pontua os destinos dentro do tempo escolhido por interesses e companhia, e sorteia entre os melhores. "Escolher outro destino" passa para o próximo da lista. "Me surpreenda" (etapa 1) preenche o resto e vai direto ao resultado. A lista completa com mapa continua disponível em "Prefiro ver todos os destinos".

- Roteiro: bate-volta usa até 3 lugares, 1 noite até 5 em 2 dias, 2 noites ou mais distribui todos em 3 dias. Os lugares vêm de `pontos`, na ordem do arquivo (coloque os principais primeiro).
- Se nenhum destino cabe no tempo ou nos interesses, o assistente avisa e escolhe o mais próximo, sem beco sem saída.
- Transporte: carro e moto calculam combustível; "Ônibus ou outro" pede o valor da passagem.
- Favoritos ficam só no navegador (localStorage). O link `?origem=sjrp&destino=olimpia` abre direto na etapa do destino.
- Os climas disponíveis vêm das `tags` dos destinos. Para oferecer "Serra e frio" ou "Romance", adicione destinos com essas tags.

## Gasto da viagem (combustível e pedágios)

Cada destino tem o botão "Calcular gasto da viagem". Ele pede o valor dos pedágios de um sentido e o número de pessoas, e mostra combustível, pedágios, total e valor por pessoa (ida e volta).

Os pedágios dependem da rota, então a página não inventa valores: o campo vem vazio, com link para a rota do Google Maps, que mostra os pedágios do trajeto. Para pré-preencher trechos que você conferiu, preencha `config.pedagios` em `quicktrip/dados/destinos.json`, com a chave `origem>destino` e o valor de um sentido para carro de passeio:

```json
"pedagios": { "sjrp>olimpia": 12.5 }
```

## Parceiros de hospedagem e comissão

Cada destino tem dois espaços marcados como "Publicidade". Enquanto não houver parceiro, aparecem vagas de exemplo. Para ocupar uma vaga, adicione `parceiros` ao destino em `quicktrip/dados/destinos.json`:

```json
"parceiros": [
  { "nome": "Pousada Fulana", "tipo": "Pousada · 2 km do centro", "descricao": "Café da manhã incluso.", "url": "https://link-de-afiliado..." }
]
```

Quando houver ao menos um parceiro com URL válida, ele substitui as vagas de exemplo. O link sai com `rel="sponsored"`.

O botão "Ver hospedagens" abre uma busca no Booking.com. Para ganhar comissão, cadastre-se no programa de afiliados deles e preencha `config.booking_aid` em `destinos.json` com o seu identificador. O botão passa a indicar "(afiliado)".

Mantenha os avisos de publicidade e de afiliado que já estão na página. Conteúdo pago ou com comissão precisa ser identificado como tal.

## Eventos em tempo (quase) real

O script pede ao Claude, com busca na web, os eventos dos próximos 60 dias em cada cidade. Um evento só entra se a URL dele apareceu nos resultados da busca daquela cidade. Mesmo assim, confira antes de divulgar.

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sua_chave
python3 quicktrip/_ferramentas/scripts/atualizar_eventos.py
python3 quicktrip/_ferramentas/scripts/atualizar_eventos.py --cidades olimpia,barretos --dias 90
```

O script grava `quicktrip/dados/eventos.json`. Faça commit e push do arquivo para o GitHub Pages publicar. A página esconde sozinha os eventos que já passaram.

## Avaliações do Google Maps

O script consulta a Places API (New) e grava nota e número de avaliações de cada ponto turístico.

```bash
export GOOGLE_MAPS_API_KEY=sua_chave
python3 quicktrip/_ferramentas/scripts/atualizar_avaliacoes.py
```

- Ative a Places API (New) no Google Cloud e restrinja a chave. A API é cobrada por requisição.
- Os termos do Google limitam por quanto tempo certos dados podem ficar guardados. Rode o script periodicamente (a cada poucas semanas) e confira os termos atuais.
- A página mostra a nota com link para o lugar no Google Maps, onde ficam os comentários. Os textos das avaliações não são copiados.
- Sem o JSON de avaliações, a página mostra o link "ver avaliações" para cada ponto.

Nunca coloque as chaves em arquivos do repositório. Elas ficam só no ambiente de quem roda os scripts.

## Ampliar a base

Edite `quicktrip/dados/destinos.json`. Cada destino tem `id`, `nome`, `lat`, `lon`, `tags`, `pontos` (nomes que serão usados para buscar avaliações), `ficar`, `tipo` e `nota`. Para novas cidades de saída, edite `origens`. Depois rode o build.

## Pontos de atenção

- O servidor público de mapas do OpenStreetMap é para uso leve. Com muito tráfego, use um provedor de tiles (MapTiler, Stadia Maps etc.).
- Pedágios ainda não entram na conta. A Routes API do Google tem suporte a pedágio, mas a cobertura no Brasil deve ser testada com rotas reais.
