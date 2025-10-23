
CONTEXTO GERAL

* faça um novo script em src/ sem dependências de outros py do projeto, irá conectar diretamente no SLSKD apenas para processar as musicas em playlists/ (dentro do docker)
* use a lib nativa do slskd
* não use outro scripts como referencia, ele precisa rodar sozinho, apenas use o .env para as informações de acesso
* liste todos os arquivos .txt que estão na pasta playlists/ (docker app/data/playlists, local data/playlists)
* Leia um arquivo de cada vez, a busca será a cada linha do arquivo
	* a linha virá no formato ARTISTA - ALBUM - MUSICA
		exemplo: Soundgarden - A-Sides - Black Hole Sun
* Após acabar a leitura de um arquivo, inicie do proximo, ao chegar no final de todos arquivos, finalize o processo
* Adicione no cron do docker para rodar o processo a cada 1hr
* crie uma solução para identificar se o processo já está rodando e não ter processos duplicados
* crie uma base com SQLite para guardar os dados das musicas baixadas e musicas com falhas (ver 3 - Dados para guardar no SQLite)

PASSOS DE DESENVOLVIMENTO

1 - Pré download - BUSCA DE FAIXAS
	1.1 - Busca deve ser SEMPRE faixa a faixa, nunca album ou artista, um download por vez
	1.2 - baixe APENAS a versão em .flac
	1.3 - IGNORE versões que tenha remix no título após a pesquisa
	1.4 - O primeiro padrão de pesquisa deve ser:  ARTISTA - ALBUM - MUSICA  \*.flac
		Caso não encontre, a segunda busca deve ser
		ARTISTA - MUSICA \*.flac
		Caso não encontre, a terceira busca deve ser
		MUSICA \*.flac
		Não faça mais que esses padrões de busca
		1.4.1 - Após listar os resultados, siga essa prioridade para escolher qual arquivo baixar
			- Procure primeiro a versão com "bitDepth": 24, e "sampleRate": 96000
			- Caso não ache nenhuma neste formato, em segundo "bitDepth": 16, e "sampleRate": 44100,
			-  Se não achar nenhuma das duas combinações 
				- pode ser qualquer uma com "bitDepth": 24
				- e se não achar qualquer uma com "bitDepth": 16, 
				- caso falha, informe que musica não encontrada, guarde os dados no SQLite como NOT_FOUND (ver tópico 3 - Dados para guardar no SQLite)
			- caso sucesso, siga para o próximo passo item 1.5
	1.5 - Ao encontrar a musica, antes de enviar para download
		1.5.1 - Verifique se a música está na base SQLite de musicas já baixadas (ver passo 3)
			1.5.1.2 - Se a musica não estiver na base, siga para o passo 1.5.2
			1.5.1.3 - Se a musica já estiver na base, aborte o processo e siga para a próxima musica do arquivo
		1.5.2 - Liste a fila de downloads atual
		1.5.3 - Verifique se o usuário da musica escolhida para download está na listagem (ver CONTRATO DE DADOS RETORNO DA FILA DE DOWNLOAD para extração dos dados)
			1.5.3.1 - Se o usuário existir, verifique se a musica está na lista através do filename (ver CONTRATO DE DADOS RETORNO DA FILA DE DOWNLOAD para extração dos dados)
				1.5.3.2.1 - se a música existir, prossiga para o fluxo de verificação de status (passo 2)
				1.5.3.2.2 - se a música não existir, envie a música para fila de download e siga para o passo 4 
			1.5.3.4 - Se o usuário não existir, envie a música para a fila de download e siga para o passo 4
		

2 - Fluxo de verificação de status
	2.1 - Se a musica existir, verifique o status em "state" (ver CONTRATO DE DADOS RETORNO DA FILA DE DOWNLOAD para extração dos dados)
		Os status podem ser
			SUCESSO: "state": "Completed, Succeeded",
			ERRO: "state": "Completed, Errored",
			ERRO: "state": "Completed, Canceled",
			EM PROGRESSO: "state": "InProgress",
			AGUARDANDO: "state": "Queued, Remotely",
		2.1.1 - Se a musica estiver no status SUCESSO, não enviar para a fila de download e registrar no passo 3 como SUCESSO
		2.1.2- Se a musica estiver no status EM PROGRESSO ou AGUARDANDO, siga para o passo 4
		2.1.3 - Se a musica estiver no status ERRO, registre no passo 3 como ERRO

3 - Dados para guardar no SQLite
	Deve-se criar uma tabela para musica com status SUCESSO
	Campos para salvar baseados na api do slskd
		id - UUID gerado se não houver ID do SLSKD
		username - ou vazio se não houver do SLSKD
		filename - ou vazio se não houver do SLSKD
		fileLine - string que é a linha do arquivo que começou a busca
		requestedAt - data/hora que foi feita a requisição do SLSKD - se não houver, usar a hora atual do registro
		

4 - Acompanhamento de fila de download
	- Após o arquivo ser enviado para a fila de download, acompanhar o download do arquivo a cada 10 segundos para ver o status do mesmo
	Os status podem ser
			SUCESSO: "state": "Completed, Succeeded",
			ERRO: "state": "Completed, Errored",
			ERRO: "state": "Completed, Canceled",
			EM PROGRESSO: "state": "InProgress",
			AGUARDANDO: "state": "Queued, Remotely",
   - Em caso de SUCESSO
	   - registrar no passo 3 como SUCESSO
	   - remover o download da fila de download
	   - remover a linha do arquivo txt
	   - concluir o processo e passar para a proxima busca
   - Em caso de ERROR
	   - remover download da fila de download
	   - concluir o processo e passar para a proxima busca
   - Em caso de AGUARDANDO
	   - remover download da fila de download
	   - concluir o processo e passar para a proxima busca
   - Em caso de EM PROGRESSO
	   - aguardar mais 10 segundos e verificar novamente
	   - aguarde por 5 minutos verificando de 10 em 10 segundos o status novamente para reclassificação
	   - caso não mude o status depois de 5 minutos
		   - entenda que o status é SUCESSO e faça o mesmo tratamento do SUCESSO
	
	


CONTRATO DE DADOS RETORNO DA FILA DE DOWNLOAD
```
[{
		"username": "sta-hi",
		"directories": [{
			"directory": "Headphones\\AC_DC\\1979 - Highway to Hell",
			"fileCount": 3,
			"files": [{
					"id": "82191e73-1564-4bf4-a918-f42212746680",
					"username": "sta-hi",
					"direction": "Download",
					"filename": "Headphones\\AC_DC\\1979 - Highway to Hell\\01 Highway To Hell.flac",
					"size": 26245910,
					"startOffset": 0,
					"state": "Completed, Succeeded",
					"stateDescription": "Completed, Succeeded",
					"requestedAt": "2025-10-23T14:08:05.5333317",
					"enqueuedAt": "2025-10-23T14:08:05.7938313",
					"startedAt": "2025-10-23T14:08:06.3237885Z",
					"endedAt": "2025-10-23T14:08:10.9321676Z",
					"bytesTransferred": 26245910,
					"averageSpeed": 5695258.447813028,
					"bytesRemaining": 0,
					"elapsedTime": "00:00:04.6083791",
					"percentComplete": 100,
					"remainingTime": "00:00:00"
				},
				{
					"id": "8321c3ce-4d5c-414a-bfb6-4aa0b5518ac6",
					"username": "sta-hi",
					"direction": "Download",
					"filename": "Headphones\\AC_DC\\1979 - Highway to Hell\\01 Highway To Hell.flac",
					"size": 26245910,
					"startOffset": 0,
					"state": "Completed, Errored",
					"stateDescription": "Completed, Errored",
					"requestedAt": "2025-10-23T14:08:05.5333426",
					"endedAt": "2025-10-23T14:08:05.6979108Z",
					"bytesTransferred": 0,
					"averageSpeed": 0,
					"exception": "An active or queued download of Headphones\\AC_DC\\1979 - Highway to Hell\\01 Highway To Hell.flac from sta-hi is already in progress",
					"bytesRemaining": 26245910,
					"percentComplete": 0
				},
				{
					"id": "a3fa5372-2db0-4621-bf3d-04bfce38ed01",
					"username": "sta-hi",
					"direction": "Download",
					"filename": "Headphones\\AC_DC\\1979 - Highway to Hell\\01 Highway To Hell.flac",
					"size": 26245910,
					"startOffset": 0,
					"state": "Completed, Errored",
					"stateDescription": "Completed, Errored",
					"requestedAt": "2025-10-23T14:08:05.7054988",
					"endedAt": "2025-10-23T14:08:05.713698Z",
					"bytesTransferred": 0,
					"averageSpeed": 0,
					"exception": "An active or queued download of Headphones\\AC_DC\\1979 - Highway to Hell\\01 Highway To Hell.flac from sta-hi is already in progress",
					"bytesRemaining": 26245910,
					"percentComplete": 0
				}
			]
		}]
	},
	{
		"username": "HojackBorseman",
		"directories": [{
			"directory": "!SHARE\\AC DC\\Highway to Hell (1979)",
			"fileCount": 5,
			"files": [{
					"id": "9abe7731-47ec-45c4-bc25-85b36a684ee8",
					"username": "HojackBorseman",
					"direction": "Download",
					"filename": "!SHARE\\AC DC\\Highway to Hell (1979)\\Highway to Hell.flac.flac",
					"size": 27578628,
					"startOffset": 0,
					"state": "Completed, Errored",
					"stateDescription": "Completed, Errored",
					"requestedAt": "2025-10-23T14:39:30.6374175",
					"endedAt": "2025-10-23T14:39:30.801848Z",
					"bytesTransferred": 0,
					"averageSpeed": 0,
					"exception": "An active or queued download of !SHARE\\AC DC\\Highway to Hell (1979)\\Highway to Hell.flac.flac from HojackBorseman is already in progress",
					"bytesRemaining": 27578628,
					"percentComplete": 0
				},
				{
					"id": "571553ee-b4df-4790-a7a9-da2fa917dbff",
					"username": "HojackBorseman",
					"direction": "Download",
					"filename": "!SHARE\\AC DC\\Highway to Hell (1979)\\Highway to Hell.flac.flac",
					"size": 27578628,
					"startOffset": 0,
					"state": "Completed, Errored",
					"stateDescription": "Completed, Errored",
					"requestedAt": "2025-10-23T14:39:30.8151073",
					"endedAt": "2025-10-23T14:39:30.8219788Z",
					"bytesTransferred": 0,
					"averageSpeed": 0,
					"exception": "An active or queued download of !SHARE\\AC DC\\Highway to Hell (1979)\\Highway to Hell.flac.flac from HojackBorseman is already in progress",
					"bytesRemaining": 27578628,
					"percentComplete": 0
				},
				{
					"id": "2f04f5c6-2a28-4535-8ebb-e7f6f1946f70",
					"username": "HojackBorseman",
					"direction": "Download",
					"filename": "!SHARE\\AC DC\\Highway to Hell (1979)\\Highway to Hell.flac.flac",
					"size": 27578628,
					"startOffset": 0,
					"state": "Completed, Succeeded",
					"stateDescription": "Completed, Succeeded",
					"requestedAt": "2025-10-23T15:16:17.7119257",
					"enqueuedAt": "2025-10-23T15:16:18.2071578",
					"startedAt": "2025-10-23T15:16:19.2726514Z",
					"endedAt": "2025-10-23T15:16:36.8095419Z",
					"bytesTransferred": 27578628,
					"averageSpeed": 1572606.500565194,
					"bytesRemaining": 0,
					"elapsedTime": "00:00:17.5368905",
					"percentComplete": 100,
					"remainingTime": "00:00:00"
				},
				{
					"id": "3bc1da73-ff56-402b-8c79-4683c6fe91f0",
					"username": "HojackBorseman",
					"direction": "Download",
					"filename": "!SHARE\\AC DC\\Highway to Hell (1979)\\Highway to Hell.flac.flac",
					"size": 27578628,
					"startOffset": 0,
					"state": "Completed, Errored",
					"stateDescription": "Completed, Errored",
					"requestedAt": "2025-10-23T15:16:17.7119276",
					"endedAt": "2025-10-23T15:16:18.0246602Z",
					"bytesTransferred": 0,
					"averageSpeed": 0,
					"exception": "An active or queued download of !SHARE\\AC DC\\Highway to Hell (1979)\\Highway to Hell.flac.flac from HojackBorseman is already in progress",
					"bytesRemaining": 27578628,
					"percentComplete": 0
				},
				{
					"id": "ba89c812-dc89-4adf-a210-855c726cd033",
					"username": "HojackBorseman",
					"direction": "Download",
					"filename": "!SHARE\\AC DC\\Highway to Hell (1979)\\Highway to Hell.flac.flac",
					"size": 27578628,
					"startOffset": 0,
					"state": "Completed, Errored",
					"stateDescription": "Completed, Errored",
					"requestedAt": "2025-10-23T15:16:18.0359337",
					"endedAt": "2025-10-23T15:16:18.0427602Z",
					"bytesTransferred": 0,
					"averageSpeed": 0,
					"exception": "An active or queued download of !SHARE\\AC DC\\Highway to Hell (1979)\\Highway to Hell.flac.flac from HojackBorseman is already in progress",
					"bytesRemaining": 27578628,
					"percentComplete": 0
				}
			]
		}]
	},
	{
		"username": "Catman",
		"directories": [{
			"directory": "@@voppb\\AC-DC\\1979 - Highway To Hell",
			"fileCount": 1,
			"files": [{
				"id": "9de4e66b-4075-4646-a88e-8039665c5db2",
				"username": "Catman",
				"direction": "Download",
				"filename": "@@voppb\\AC-DC\\1979 - Highway To Hell\\01. Highway To Hell.flac",
				"size": 27649966,
				"startOffset": 0,
				"state": "Completed, Succeeded",
				"stateDescription": "Completed, Succeeded",
				"requestedAt": "2025-10-23T14:39:39.259775",
				"enqueuedAt": "2025-10-23T14:39:39.6071011",
				"startedAt": "2025-10-23T14:39:40.1254395Z",
				"endedAt": "2025-10-23T14:40:16.4791926Z",
				"bytesTransferred": 27649966,
				"averageSpeed": 760580.7830608829,
				"bytesRemaining": 0,
				"elapsedTime": "00:00:36.3537531",
				"percentComplete": 100,
				"remainingTime": "00:00:00"
			}]
		}]
	},
	{
		"username": "isnotsocial",
		"directories": [{
			"directory": "flac\\AC-DC\\1979 - Highway to Hell",
			"fileCount": 1,
			"files": [{
				"id": "624b9b6c-aaf9-4beb-93d4-5ae1dea5990a",
				"username": "isnotsocial",
				"direction": "Download",
				"filename": "flac\\AC-DC\\1979 - Highway to Hell\\01 - Highway to Hell.flac",
				"size": 26440248,
				"startOffset": 0,
				"state": "Completed, Succeeded",
				"stateDescription": "Completed, Succeeded",
				"requestedAt": "2025-10-23T15:16:26.6276853",
				"enqueuedAt": "2025-10-23T15:16:26.886763",
				"startedAt": "2025-10-23T15:16:27.0665276Z",
				"endedAt": "2025-10-23T15:16:32.3034167Z",
				"bytesTransferred": 26440248,
				"averageSpeed": 5048846.2702026665,
				"bytesRemaining": 0,
				"elapsedTime": "00:00:05.2368891",
				"percentComplete": 100,
				"remainingTime": "00:00:00"
			}]
		}]
	}
]
```