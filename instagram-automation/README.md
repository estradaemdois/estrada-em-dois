# Automação do Instagram · Estrada em Dois

Todo dia de manhã, a automação prepara uma sugestão de post para o **@estradaemdois.oficial** e pede a sua aprovação. **Nada é publicado sem o seu `/aprovar`.**

## Como funciona

1. Às 8h (horário de São Paulo), o GitHub escolhe o próximo post do banco, prepara a foto no formato do Instagram e abre uma **issue** (uma página de aprovação) na aba **Issues** do repositório.
2. Você recebe a notificação do GitHub (e-mail ou app do GitHub no celular).
3. Na issue aparecem a prévia da foto, a legenda e as hashtags.
4. Você responde com um comentário:
   - `/aprovar` publica no Instagram e responde com o link do post
   - `/rejeitar` descarta (o post volta para o fim da fila)
   - `/outra` descarta e já prepara outra sugestão
5. Quer ajustar o texto? Edite a issue (menu ··· › Editar) antes de comentar `/aprovar`.

Só a dona do repositório consegue aprovar. Comentários de outras pessoas são ignorados.
Enquanto houver uma sugestão esperando, não é criada outra.

## De onde vêm os posts

Do arquivo `conteudo/banco-de-posts.json`. Cada post usa uma foto que já está no site e informações dos guias publicados (o campo `fonte` mostra a página). São 14 posts para começar. Quando acabarem, a automação avisa com uma issue.

## Histórico

`historico/historico.json` guarda cada sugestão: aguardando, publicada (com link), rejeitada ou com erro. Um post publicado nunca é sugerido de novo.

## Pausar ou desligar

- **Pausa rápida:** Settings › Secrets and variables › Actions › aba Variables › criar `INSTAGRAM_PAUSADO` com valor `sim`. Para voltar, troque para `nao`.
- **Desligar de vez:** aba Actions › "Instagram · 1. Preparar sugestão do dia" › botão ··· › Disable workflow.
- **Modo de teste:** variável `INSTAGRAM_MODO_TESTE` = `sim` faz o `/aprovar` conferir tudo sem enviar nada ao Instagram.

## Verificar a conexão

Aba Actions › "Instagram · 3. Verificar conexão" › Run workflow. O resultado mostra o tipo de token, a conta acessada e se está tudo certo. Não publica nada. Também roda sozinho toda segunda-feira e abre um aviso se o token parar de funcionar.

## Renovar o token

Tokens da Meta expiram (os de longa duração costumam valer cerca de 60 dias). Quando a verificação avisar, gere um novo token no painel da Meta e substitua o valor do segredo `INSTAGRAM_ACCESS_TOKEN` em Settings › Secrets and variables › Actions. Nunca cole o token em issues, arquivos ou no chat.

## Custos

Tudo gratuito: GitHub Actions em repositório público e a API oficial da Meta. As legendas vêm do banco de posts, sem serviço pago de IA.
