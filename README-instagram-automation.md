# Automação do Instagram — Estrada em Dois

**Perfil do Instagram:** `@estradam2.oficial`

Este diretório reúne os arquivos da automação de conteúdo do Instagram.

## Objetivo

Preparar uma publicação por dia (imagem ou vídeo, legenda e hashtags), solicitar aprovação humana e publicar somente depois da aprovação explícita.

## Regras de publicação

- Nenhum conteúdo deve ser publicado sem aprovação explícita.
- Registrar o histórico das publicações para evitar duplicidade.
- Não armazenar tokens, senhas ou outras credenciais neste repositório.
- As credenciais devem ficar em GitHub Actions Secrets ou em um serviço seguro de configuração.

## Segredos esperados

- `INSTAGRAM_ACCESS_TOKEN` — token de acesso da API do Instagram.

## Observação

O perfil informado para esta automação é `@estradam2.oficial`. Confirme que esse é o nome de usuário exato antes de ativar qualquer publicação.
