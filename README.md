# Montador de Pedido Futebol

Aplicativo desktop local para Windows feito em Python + CustomTkinter. Ele ajuda o operador a configurar times, camisas, letras, números, logos e camisas completas pela interface, sem editar código.

## Como instalar o Python

1. Acesse https://www.python.org/downloads/windows/
2. Baixe a versão mais recente do Python 3.
3. Na instalação, marque a opção **Add python.exe to PATH**.
4. Conclua a instalação.

Para conferir:

```bat
python --version
```

## Como instalar dependências

Abra o Prompt de Comando ou PowerShell dentro da pasta do projeto e rode:

```bat
python -m pip install -r requirements.txt
```

## Como executar o app

```bat
python app.py
```

Na primeira abertura, o aplicativo não mostra o painel principal. Ele abre o **Assistente de Configuração Inicial**, porque o arquivo `config/catalogo.json` começa em branco e com `"configured": false`.

## Primeira configuração

O assistente pede:

1. Nome do primeiro time.
2. Nome da primeira camisa/modelo.
3. O que essa camisa possui: letras, fila completa de letras, número costas, número frente, logos e camisa completa.
4. As pastas dos arquivos marcados.
5. A pasta de saída padrão.
6. Um teste simples mostrando quantos `.tif` e `.tiff` foram encontrados.

Depois de concluir, o painel principal é liberado.

## Adicionar novo time ou nova camisa

No painel principal, clique em **Configurações**.

- Use **+ Novo Time** para cadastrar um time.
- Use **+ Nova Camisa** para cadastrar uma camisa/modelo.
- Marque **Sim** nas opções que a camisa possui.
- Para cada opção marcada, selecione a pasta correspondente.
- Clique em **Testar pastas** para conferir os arquivos.
- Clique em **Salvar Configuração**.

O painel de produção mostra somente as categorias disponíveis para a camisa selecionada. Se a camisa não tiver número frente, por exemplo, **Número Frente** não aparece no painel.

## Como organizar as pastas

Crie uma pasta para cada camisa/modelo. Exemplo:

```text
GALO 2026
  CAMISA BRANCA
    Letras
    Números Costas
    Números Frente
    Logos
    Camisa Completa
```

Você só precisa criar as pastas dos itens que a camisa realmente possui.

## Como nomear letras

Use nomes simples:

```text
A.tif
B.tif
C.tif
```

Também são aceitos nomes minúsculos, como `a.tif`.

## Como nomear números das costas

O número deve aparecer no começo do nome:

```text
0.tif
1.tif
2.tif
10.tif
```

## Como nomear números da frente

Use o número no começo e, se possível, a palavra `FRENTE`:

```text
0 FRENTE.tif
1 FRENTE.tif
2 FRENTE.tif
```

## Logos e camisa completa

Logos, patrocinadores e arquivos de camisa completa podem ter qualquer nome, desde que estejam em `.tif` ou `.tiff`.

## Como montar um pedido

1. Informe cliente, pedido nº, observação e pasta de saída.
2. Selecione time e camisa.
3. Adicione itens individuais ou grupos separados por vírgula.
4. Use ações rápidas para camisa completa, fila de letras ou logos quando existirem na configuração.
5. Clique em **Validar arquivos**.
6. Clique em **Gerar pasta de produção**.

### Fila Completa de Letras

Quando a camisa tiver **Fila Completa de Letras**, essa categoria aparece também no campo **Categoria** e no painel **Adicionar grupo**. Assim você pode escolher letras específicas, como `A, B, C`, e informar a quantidade de cada.

A ação rápida **Fila Completa de Letras** continua disponível e copia todos os arquivos da pasta quando você precisar de uma fila completa de todas as letras.

## Pasta gerada

O app cria uma pasta no padrão:

```text
PEDIDO_{numero_pedido}_{cliente}_{data}
```

Dentro dela, os arquivos são copiados para subpastas como:

```text
arquivos de produção todos juntos na pasta principal
99_CONFERENCIA
```

Os arquivos de produção ficam juntos para facilitar selecionar tudo e arrastar para outro programa. Quando itens de times diferentes têm nomes iguais, o aplicativo usa um prefixo com time, camisa e categoria para evitar sobrescrever arquivos.

Na pasta `99_CONFERENCIA`, o app gera:

- `resumo_do_pedido.txt`
- `carrinho.json`
- `arquivos_faltando.txt`

O aplicativo nunca apaga nem move os arquivos originais. Ele apenas copia.

## Carrinho com vários times

Cada item do carrinho guarda o time e a camisa selecionados no momento em que foi adicionado.

Exemplo:

- `Cruzeiro / Camisa Azul / Número Costas / 0`
- `Atlético Mineiro / Camisa Branca / Número Costas / 0`

Mesmo sendo o item `0`, eles ficam em linhas separadas porque pertencem a times/camisas diferentes.

## Salvar e carregar pedidos

Use **Salvar** para guardar um pedido em andamento. Os arquivos ficam em:

```text
data/pedidos_salvos
```

Use **Pedidos Salvos** para carregar um pedido.

## Importar pedido do site

Use **Importar Pedido** e escolha o arquivo `.json` do pedido. O carrinho aparece preenchido, pronto para **Validar arquivos** e **Gerar pasta de produção**. Se o carrinho já tiver itens, o app pergunta se pode substituir o pedido atual.

- Itens que não existem no catálogo local entram no carrinho e aparecem em um aviso; na geração caem no `arquivos_faltando.txt`.
- Arquivo com formato errado ou versão desconhecida mostra uma mensagem e não altera o pedido atual.
- O formato do arquivo está em `contracts/order.schema.json` (exemplo em `contracts/order.example.json`).

## Ano e camisa ativa

Em **Configurações**, cada camisa tem os campos **Ano** (opcional) e **Ativa (aparece no site)**. O ano aparece no menu como `Home 1 · 2026`, então camisas de mesmo nome em anos diferentes ficam separadas. Camisas inativas continuam aparecendo no Montador, para produzir pedidos antigos.

## Backup da configuração

Em **Configurações**, clique em **Fazer backup**. O backup será salvo em:

```text
config/backups
```

Use **Restaurar backup** para voltar uma configuração anterior.

## Gerar o executável

Depois de instalar as dependências, rode:

```bat
build_exe.bat
```

O executável será criado em:

```text
dist\Montador de Pedido Futebol.exe
```

O executável usa o ícone em `assets/icon.ico`. As imagens do app ficam em `assets/icon.png` e `assets/logo_cabecalho.png`.

## Desenvolvimento

```bat
python -m pip install -r requirements-dev.txt
python -m pytest
```

Estrutura e convenções do código estão em `CLAUDE.md`. O catálogo real (`config/catalogo.json`) e os pedidos
salvos ficam só na máquina e não são versionados; use `config/catalogo.example.json` como referência de formato.
