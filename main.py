import paramiko
import os
import shutil
import datetime
import smtplib
import logging
from email.mime.text import MIMEText

# Informações de acesso ao servidor SFTP
sftp_host = 'portalarquivos.bancovotorantim.com.br'
sftp_user = '_XASSESSORIA_032_PRD'
sftp_pass = 'TcUQav91RFX'

# Informações de acesso ao servidor de email
email_from = 'sistemas@novaquest.com.br'
email_to = 'sistemas@novaquest.com.br'
email_password = 'd01@03'

# Diretório de destino dos arquivos
ano_atual = str(datetime.datetime.now().year)
meses = {
    "January": "01 - JANEIRO",
    "February": "02 - FEVEREIRO",
    "March": "03 - MARÇO",
    "April": "04 - ABRIL",
    "May": "05 - MAIO",
    "June": "06 - JUNHO",
    "July": "07 - JULHO",
    "August": "08 - AGOSTO",
    "September": "09 - SETEMBRO",
    "October": "10 - OUTUBRO",
    "November": "11 - NOVEMBRO",
    "December": "12 - DEZEMBRO",
}
mes_atual = meses[datetime.datetime.now().strftime('%B')]
dia_atual = datetime.datetime.now().strftime('%d')
destination_dir = r'\\192.168.0.48\BV\Carga Cyber\Reneg\{}\{}\{}'.format(
    ano_atual, mes_atual, dia_atual)

# Conexão ao servidor SFTP
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(sftp_host, username=sftp_user, password=sftp_pass)

sftp = ssh.open_sftp()

# Navegação até a pasta Inbox
sftp.chdir('/XASSESSORIA_022/CARGA/ENVIO_A022/Download')

# Configuração do logging
logging.basicConfig(filename='access_log.txt', level=logging.INFO)

# puxando o dia para nome do arquivo

dia_arquivo = print("{}{}{}_reneg_1688")


# Loop até encontrar os arquivos
while True:
    files_to_move = []
    for filename in ['SRMTVCBNOVA1OUTPRO', 'SRMTVCBNOVA2OUTPRO', 'SRMTVCBNOVA3OUTPRO','']:
        try:
            sftp.stat(filename)
            files_to_move.append(filename)
        except FileNotFoundError:
            pass

    # Verificação da existência dos arquivos
    if files_to_move:
        logging.info('Arquivos encontrados: {}'.format(', '.join(files_to_move)))

        # Movimentação dos arquivos para o diretório de destino
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
        for filename in files_to_move:
            if os.path.exists(os.path.join(destination_dir, filename)):
                os.remove(os.path.join(destination_dir, filename))
            sftp.get(filename, os.path.join(os.getcwd(), filename))
            shutil.move(filename, destination_dir)
            sftp.remove(filename)

        # Verificação da existência dos arquivos no diretório de destino
        if all([os.path.exists(os.path.join(destination_dir, filename)) for filename in files_to_move]):
            # Encerramento da conexão SFTP
            sftp.close()
            ssh.close()

            # Renomeia e copia os arquivos para a pasta REMESSA_PSA
            remessa_dir = os.path.join(destination_dir, 'REMESSA_PSA')
            if not os.path.exists(remessa_dir):
                os.makedirs(remessa_dir)
            for filename in files_to_move:
                if filename == 'SRMTVCBNOVA1OUTPRO':
                    new_filename = '4_SRMTVCBNOVA1OUTPRO_{}{}{}.csv'.format(dia_atual, mes_atual[:2], ano_atual)
                elif filename == 'SRMTVCBNOVA2OUTPRO':
                    new_filename = '1_SRMTVCBNOVA2OUTPRO_{}{}{}.csv'.format(dia_atual, mes_atual[:2], ano_atual)
                elif filename == 'SRMTVCBNOVA3OUTPRO':
                    new_filename = '2_SRMTVCBNOVA3OUTPRO_{}{}{}.csv'.format(dia_atual, mes_atual[:2], ano_atual)
                shutil.copy2(os.path.join(destination_dir, filename), os.path.join(remessa_dir, new_filename))

            # Envio do email de confirmação
            msg = MIMEText('Os seguintes arquivos foram recebidos e movidos com sucesso: {}'.format(
                ', '.join(files_to_move)))
            msg['Subject'] = 'REMESSA PSA {}-{}-{}'.format(dia_atual, mes_atual, ano_atual)
            msg['From'] = email_from
            msg['To'] = email_to

            server = smtplib.SMTP('smtp.novaquest.com.br', 587)
            server.starttls()
            server.login(email_from, email_password)
            server.sendmail(email_from, email_to, msg.as_string())
            server.quit()