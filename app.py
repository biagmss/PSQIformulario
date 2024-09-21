from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os

app = Flask(__name__)

# Caminho para o banco de dados SQLite
DATABASE = 'database.db'

# Função para conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/historico')
def historico():
    conn = get_db_connection()
    responses = conn.execute('SELECT * FROM psqi_responses').fetchall()
    conn.close()
    
    return render_template('historico.html', responses=responses)


# Função para criar a tabela, se não existir
def create_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS psqi_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bedtime TEXT,
            sleep_latency INTEGER,
            wake_time TEXT,
            sleep_quality INTEGER
            -- Adicione outras colunas aqui, conforme necessário
        )
    ''')
    conn.commit()
    conn.close()

# Rota para exibir o formulário de perguntas (index.html)
@app.route('/')
def resultados():
    return render_template('resultados.html')

# Rota para receber os dados do formulário e salvar no SQLite
@app.route('/submit', methods=['POST'])
def submit_psqi():
    bedtime = request.form['bedtime']
    sleep_latency = request.form['sleepLatency']
    wake_time = request.form['wakeTime']
    sleep_quality = request.form['sleepQuality']
    
    # Conectar ao banco de dados e salvar os dados
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO psqi_responses (bedtime, sleep_latency, wake_time, sleep_quality)
        VALUES (?, ?, ?, ?)
    ''', (bedtime, sleep_latency, wake_time, sleep_quality))
    conn.commit()
    conn.close()

    # Redirecionar para a página de resultados com as respostas salvas
    return redirect(url_for('results'))

# Rota para exibir os resultados do PSQI (resultados.html)
@app.route('/results')
def results():
    conn = get_db_connection()
    responses = conn.execute('SELECT * FROM psqi_responses ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()

    if responses is None:
        return "Nenhuma resposta encontrada!"

    return render_template('resultados.html', responses=responses)

# Inicializar o banco de dados e rodar o app
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        create_table()
    app.run(debug=True)
    

    # Calcular a pontuação para cada resposta
def calcular_pontuacao_psqi(respostas):
    # Componente 1: Qualidade Subjetiva do Sono
    qualidade_sono = int(respostas['sleepQuality'])
    
    # Componente 2: Latência do Sono
    latencia_sono = int(respostas['sleepLatency'])
    if latencia_sono <= 15:
        comp2 = 0
    elif 16 <= latencia_sono <= 30:
        comp2 = 1
    elif 31 <= latencia_sono <= 60:
        comp2 = 2
    else:
        comp2 = 3
    
    # Componente 3: Duração do Sono
    duracao_sono = int(respostas['sleepDuration'])
    if duracao_sono > 7:
        comp3 = 0
    elif 6 <= duracao_sono <= 7:
        comp3 = 1
    elif 5 <= duracao_sono < 6:
        comp3 = 2
    else:
        comp3 = 3
    
    # Componente 4: Eficiência Habitual do Sono
    hora_dormir = respostas['bedtime']
    hora_acordar = respostas['wakeTime']
    
    # Calculando a eficiência do sono
    horas_cama = calcular_tempo_na_cama(hora_dormir, hora_acordar)
    eficiencia_sono = (duracao_sono / horas_cama) * 100
    if eficiencia_sono >= 85:
        comp4 = 0
    elif 75 <= eficiencia_sono < 85:
        comp4 = 1
    elif 65 <= eficiencia_sono < 75:
        comp4 = 2
    else:
        comp4 = 3
    
    # Componente 5: Distúrbios do Sono
    disturbios_sono = int(respostas['sleepDisturbances'])
    
    # Componente 6: Uso de Medicamentos para Dormir
    uso_medicacao = int(respostas['sleepMedication'])
    
    # Componente 7: Disfunção Diurna
    disfuncao_diurna = int(respostas['daytimeDysfunction'])

    # Calculando a pontuação total
    pontuacao_total = qualidade_sono + comp2 + comp3 + comp4 + disturbios_sono + uso_medicacao + disfuncao_diurna
    
    return pontuacao_total

def calcular_tempo_na_cama(hora_dormir, hora_acordar):
    # Função para calcular o tempo total na cama baseado nas horas de dormir e acordar
    h_dormir = int(hora_dormir.split(':')[0])
    m_dormir = int(hora_dormir.split(':')[1])
    h_acordar = int(hora_acordar.split(':')[0])
    m_acordar = int(hora_acordar.split(':')[1])
    
    tempo_dormir = h_dormir * 60 + m_dormir
    tempo_acordar = h_acordar * 60 + m_acordar
    
    if tempo_acordar < tempo_dormir:
        tempo_acordar += 24 * 60  # Corrige para o próximo dia
    
    return (tempo_acordar - tempo_dormir) / 60  # Tempo total em horas

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_psqi():
    respostas = {
        'bedtime': request.form['bedtime'],
        'sleepLatency': request.form['sleepLatency'],
        'wakeTime': request.form['wakeTime'],
        'sleepDuration': request.form['sleepDuration'],
        'sleepQuality': request.form['sleepQuality'],
        'sleepDisturbances': request.form['sleepDisturbances'],
        'sleepMedication': request.form['sleepMedication'],
        'daytimeDysfunction': request.form['daytimeDysfunction']
    }

    # Calcular a pontuação do PSQI
    pontuacao_total = calcular_pontuacao_psqi(respostas)

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO psqi_responses (bedtime, sleep_latency, wake_time, sleep_duration, sleep_quality, 
        sleep_disturbances, sleep_medication, daytime_dysfunction, total_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (respostas['bedtime'], respostas['sleepLatency'], respostas['wakeTime'], respostas['sleepDuration'],
          respostas['sleepQuality'], respostas['sleepDisturbances'], respostas['sleepMedication'],
          respostas['daytimeDysfunction'], pontuacao_total))
    conn.commit()
    conn.close()

    return render_template('resultados.html', respostas=respostas, pontuacao_total=pontuacao_total)



