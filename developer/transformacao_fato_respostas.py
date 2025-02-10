from leitura_arquivo_drive import *
from transformacao_autoavaliacao import GoogleDriveManager,DataExtractor
import pandas as pd


#para transformar o arquivo autoavaliacao da pasta trusted no formato modelo_fato_respostas
auth = GoogleAuthenticator()
drive_manager = GoogleDriveManager(auth.drive_service)
folder_id = drive_manager.Id_camada['trusted'] #obter o id da pasta trusted
relatorio = 'autoavaliacao.xlsx'  # Defina o relatório desejado
file_id = drive_manager.get_file_id(relatorio,folder_id) obter o id do arquivo relatorio
autoavaliacao = drive_manager.get_file_data(file_id) #baixar o arquivo para a memória local
autoavaliacao = autoavaliacao.drop_duplicates() #para remover o cabeçalho caso ele se repita
#o processo de transformação
#coluna com a descrição do tipo de pergunta
tipo_perguntas = ['Quantitativa de 0 a 10','Quantitativa de 0 a 10','Quantitativa de 0 a 10','Quantitativa de 0 a 10',
                  'Quantitativa de 0 a 10','Quantitativa de 0 a 10','Quantitativa de 0 a 10,','Quantitativa de 0 a 10',
                  'sim/nao','Quantitativa de 0 a 10','Quantitativa de 0 a 10','Quantitativa de 0 a 10',
                  'Quantitativa de 0 a 10','Quantitativa de 0 a 10','Quantitativa de 0 a 10','Quantitativa de 0 a 10',
                  'Descritiva, texto de opinião']
#coluna com o tipo de dados das respostas
tipo_repostas = ['int','int','int','int','int','int','int','int','boolean','int','int','int','int','int','int','int',
                 'str']
perguntas = autoavaliacao.keys().tolist()[5:22]
#Cada entrevistado, que representa uma linha, que terá que ser transposta separadamente, transformado em dataframe e depois
#os dataframes serão concatenados verticalmente
all_df = []
for i_entrevistado in range(autoavaliacao.shape[0]):
    row = autoavaliacao.iloc[i_entrevistado].T
    row = row.apply(lambda x: int(x) if pd.notna(x) and isinstance(x, (np.float64, float)) else x) #transformar todos os campos float para integer
    fato_resposta = {'timestamp': row[0],
                             'dsEmailRespondente': row.iloc[1], #campo do email
                              'dsNomeRespondente': row.iloc[2], #campo do entrevistado    
                              'dsQualFuncaoDesempenha':row.iloc[3], #campo da função
                              'dsEquipeParticipante':row.iloc[4], #campo da equipe
                              'nmCadernoPergunta': 'Autoavaliação Pipoca Ágil (respostas)', #modificar para cada formulário
                              'dsTituloPergunta': perguntas, #lista com as perguntas
                              'dsTipoPergunta':tipo_perguntas, #lista com o tipo das perguntas
                              'dsResposta':row.iloc[5:22], #lista com as respotas
                              'dsDataType':tipo_repostas} #lista com os tipos das respostas
    df_fato_resposta = pd.DataFrame(fato_resposta).reset_index(drop=True) #criar um dataframe do dicionário fato_reposta
    all_df.append(df_fato_resposta) #unir todos os dataframes en uma lista
#para transformar as listas em um dataframe só
df_new = pd.concat(all_df)

#obter o arquivo fato_respostas que está na pasta refined
folder_id_refined = drive_manager.Id_camada['refined'] #verificar o id da pasta
relatorio_refined = 'modelo_fato_respostas.xlsx'  # Defina o relatório desejado
file_id_refined = drive_manager.get_file_id(relatorio_refined,folder_id_refined) #obter o id do arquivo
fato_resposta = drive_manager.get_file_data(file_id_refined) #baixar o arquivo na memória local
#adicionar as novas respostas à planilha fato_respostas
df_upload = pd.concat([fato_resposta,df_new])
#Substituir o arquivo fato_respostas na camada trusted 
drive_manager.save_data_to_layer(df_upload,datetime.today(),relatorio_refined)
