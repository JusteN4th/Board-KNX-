from flask import Flask, request, send_file
import mysql.connector
import qrcode
import io
import uuid
import os

app = Flask(__name__)

# Fonction pour se connecter à la base de données MySQL
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'db'),
        user=os.environ.get('DB_USER', 'klx_user'),
        password=os.environ.get('DB_PASSWORD', 'klx_password'),
        database=os.environ.get('DB_NAME', 'klx_doc_db')
    )

@app.route('/')
def accueil():
    return """
    <h1>Bienvenue sur l'IHM du Banc KLX</h1>
    <ul>
        <li><a href="/admin/creer-apprenti">Espace Formateur : Créer un accès Apprenti</a></li>
    </ul>
    """

@app.route('/admin/creer-apprenti', methods=['GET', 'POST'])
def creer_apprenti():
    # Page pour le formateur
    html_form = """
    <h2>Créer un accès pour un apprenti</h2>
    <form method="POST">
        Nom de l'apprenti : <input type="text" name="username" required>
        <button type="submit">Générer le QR Code</button>
    </form>
    """
    
    if request.method == 'POST':
        username = request.form['username']
        # Génération d'un token unique pour l'apprenti
        token = str(uuid.uuid4())
        
        # Enregistrement dans la base de données
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, role, enrollment_token) VALUES (%s, 'apprenti', %s)", (username, token))
            conn.commit()
            
            # Le lien que le QR code va contenir (qui pointe vers notre serveur)
            # En production, ce sera l'IP réelle du serveur, ex: https://192.168.x.x/enroll?token=...
            lien_enrolement = f"https://{request.host}/enroll?token={token}"
            
            return f"""
            <h3>Compte créé pour {username} !</h3>
            <p>Demandez à l'apprenti de scanner ce QR Code avec son téléphone ou sa tablette :</p>
            <img src="/api/qrcode?data={lien_enrolement}" alt="QR Code d'enrôlement">
            <br><br>
            <a href="/admin/creer-apprenti">Créer un autre compte</a>
            """
        except mysql.connector.Error as err:
            return f"Erreur : Ce nom d'apprenti existe peut-être déjà. ({err})"
        finally:
            cursor.close()
            conn.close()
            
    return html_form

# Une route technique ("API") pour générer l'image du QR Code à la volée
@app.route('/api/qrcode')
def generer_qr():
    data = request.args.get('data')
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

