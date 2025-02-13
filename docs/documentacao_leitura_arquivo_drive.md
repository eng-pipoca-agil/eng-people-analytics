Documentação do Projeto
Visão Geral
Este projeto tem como objetivo automatizar a extração de dados do Google Sheets e armazená-los em diferentes camadas de processamento no Google Drive. Ele utiliza as bibliotecas gspread, googleapiclient, pandas e logging para acessar, manipular e armazenar os dados de forma eficiente.
Tecnologias Utilizadas
•	Python 3.11
•	Google Sheets API
•	Google Drive API
•	Bibliotecas: gspread, googleapiclient, pandas, logging, os, datetime
Estrutura do Projeto
O projeto está dividido nas seguintes classes e funções:
1. GoogleAuthenticator
Gerencia a autenticação para o Google Sheets e Google Drive.
Métodos:
•	authenticate(): Realiza a autenticação e cria os clientes para interagir com as APIs do Google Sheets e Google Drive.
2. GoogleSheetsManager
Gerencia as operações com o Google Sheets.
Métodos:
•	get_sheet(relatorio): Obtém a planilha correspondente ao relatório solicitado.
•	get_data(sheet): Obtém todos os dados da planilha e os retorna como uma lista de listas.
3. GoogleDriveManager
Gerencia as operações de upload e download de arquivos no Google Drive.
Métodos:
•	get_file_id(file_name, folder_id): Busca um arquivo no Google Drive pelo nome e retorna seu ID.
•	download_existing_file(file_id, file_name): Faz o download de um arquivo existente no Google Drive.
•	save_data_to_layer(data, camada, relatorio): Salva os dados na camada especificada do Google Drive, incluindo a timestamp de processamento.
4. Processamento dos Relatórios
Existem três funções para processar os dados e armazená-los nas diferentes camadas:
•	processar_camadas_raw(sheets_manager, drive_manager, relatorio): Processa os dados do relatório e os armazena na camada RAW.
•	processar_camadas_refined(sheets_manager, drive_manager, relatorio): Processa os dados e os armazena na camada REFINED.
•	processar_camadas_trusted(sheets_manager, drive_manager, relatorio): Processa os dados e os armazena na camada TRUSTED.
5. Logging
A função setup_logging() é utilizada para configurar o sistema de logs, permitindo o registro de informações e erros.
Execução do Projeto
O script principal segue a seguinte lógica:
1.	Configura o logging.
2.	Autentica no Google Sheets e Google Drive.
3.	Inicializa os gerenciadores de Google Sheets e Google Drive.
4.	Define o relatório a ser processado.
5.	Processa e armazena os dados nas camadas RAW e TRUSTED.
Para executar o projeto, basta rodar o script principal:
python script.py
Possíveis Melhorias
•	Adicionar suporte para processamento automatizado de todos os relatórios sem necessidade de definir manualmente.
•	Criar uma interface web para gerenciamento e execução das operações.
•	Implementar testes unitários para verificar a integridade do código.
•	Melhorar a segurança do projeto utilizando armazenamento seguro das credenciais.
Conclusão
Este projeto fornece uma solução automatizada e escalável para extrair e armazenar dados do Google Sheets no Google Drive, permitindo análise e processamento eficiente. Com futuras melhorias, pode se tornar ainda mais robusto e flexível para diferentes cenários empresariais.
