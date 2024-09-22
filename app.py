from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Função para conectar ao banco de dados SQLite
def get_db_connection():
    conn = sqlite3.connect('psqi.db')
    conn.row_factory = sqlite3.Row
    return conn

# Função para criar a tabela se ela ainda não existir
def create_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS psqi_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            horadedormir TEXT,
            tempodormir" INTEGER,
            horadeacordar TEXT,
            duraçaosono INTEGER,
            sleep_quality INTEGER,
            sleep_disturbances INTEGER,
            sleep_medication INTEGER,
            daytime_dysfunction INTEGER,
            total_score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Cria a tabela na inicialização do app
create_table()

# Função para calcular a pontuação do PSQI
def calcular_pontuacao_psqi(respostas):
    # Exemplo básico de como calcular a pontuação total com base nas respostas
    total = (respostas['tempodormir'] +
             respostas['horasdesono'] +
             respostas['sleepQuality'] +
             respostas['sleepDisturbances'] +
             respostas['sleepMedication'] +
             respostas['daytimeDysfunction'])
    return total

# Rota para submeter o questionário e salvar os dados
@app.route('/submit', methods=['POST'])
def submit_psqi():
    try:
        # Captura todas as respostas do formulário
        respostas = {
            'horadedormir': request.form['horadedormir'],
            'tempodormir': int(request.form['tempodormir']),
            'horadeacordar': request.form['horadeacordar'],
            'duraçaosono': int(request.form['duraçaosono']),
            'sleepQuality': int(request.form['sleepQuality']),
            'sleepDisturbances': int(request.form['sleepDisturbances']),
            'sleepMedication': int(request.form['sleepMedication']),
            'daytimeDysfunction': int(request.form['daytimeDysfunction'])
        }

        # Calcula a pontuação total
        pontuacao_total = calcular_pontuacao_psqi(respostas)

        # Insere os dados no banco de dados SQLite
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO psqi_responses (horadedormir, tempodormir, horadeacordar, duraçaosono, sleep_quality, 
            sleep_disturbances, sleep_medication, daytime_dysfunction, total_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (respostas['horadedormir'], respostas['tempodormir'], respostas['horadeacordar'], respostas['duraçaosono'],
              respostas['sleepQuality'], respostas['sleepDisturbances'], respostas['sleepMedication'],
              respostas['daytimeDysfunction'], pontuacao_total))
        conn.commit()
        conn.close()

        # Redireciona para a página de resultados com a pontuação total
        return render_template('resultados.html', pontuacao_total=pontuacao_total)
    
    except ValueError:
        return "Erro: Certifique-se de que todos os campos foram preenchidos corretamente."

# Rota para exibir a página principal (formulário do questionário)
@app.route('/')
def index():
    return render_template('formulario.html')

# Inicializa o servidor Flask
if __name__ == '__main__':
    app.run(debug=True)
