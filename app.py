from flask import Flask, jsonify, request
import random
import firebase_admin
from firebase_admin import credentials, firestore
from auth import token_obrigatorio, gerar_token 
from flask_cors import CORS
import os 
from  dotenv import load_dotenv
import json 

load_dotenv()



app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

CORS(app, origins="*")




ADM_USUARIO =  os.getenv("ADM_USUARIO")
ADM_SENHA = os.getenv("ADM_SENHA")


if os.getenv("VERCEL"):
    cred = credentials.Certificate(json.loads(os.getenv("FIREBASE_CREDENTIALS")))
    
else:
 # LOCAL
    cred =  credentials.Certificate("firebase.json")

# carregar as credenciais do firebase
firebase_admin.initialize_app(cred)

# conectar ao firestore
db = firestore.client()


# Rota de Apresentação

@app.route('/', methods = ['GET'])
def root():    
    return jsonify({
        "api":"Charadas ",
        "Version":"1.0",
        "Author":"Guilherme da Costa Silva"
        
    }),200
    
    
# ===========================
#        ROTA DE LOGIN
# ===========================
    
@app.route("/login", methods=["POST"])
def login():
    dados = request.get_json()
    
    if not dados:
        return jsonify({"Error":"Envie os dados para login"}), 400
    
    usuario = dados.get("usuario")
    senha = dados.get("senha")
    
    if not usuario or not senha:
        return jsonify({"Error":"Usuário a senha são obrigatórios!"})
    
    if usuario == ADM_USUARIO and senha == ADM_SENHA:
        token = gerar_token(usuario)
        return jsonify({"message": "Login realizado com sucesso!", "token":token}),200
    
    return jsonify({"Error": "Usuário ou senha inválidos!"}),401
    
    
    
    


# Mostra as charadas

@app.route('/charadas', methods = ['GET'])
def get_charadas():
    charadas = [] #lista vazia
    lista = db.collection("Charadas").stream() # Lista todos os dados
     
    for item in lista:
        charadas.append(item.to_dict())
    
    return jsonify(charadas),200
         

# Randoriza uma das charadas
    
@app.route('/charadas/aleatoria', methods = ['GET'])
def get_charadas_random():
    charadas = [] #lista vazia
    lista = db.collection("Charadas").stream() # Lista todos os dados
     
    for item in lista:
        charadas.append(item.to_dict())
    
    return jsonify(random.choice(charadas)), 200


#Rota 3 - Método GET - retorna charada pelo id
@app.route("/charadas/<int:id>", methods=['GET'])
def get_charada_by_id(id):
    lista = db.collection('Charadas').where('id', '==', id).stream()
    
    for item in lista:
        return jsonify(item.to_dict()), 200
    
    return jsonify({"ERROR!!!":"Charada não encontrada"}), 404
    
    
    
    
    
    
    


# @app.route('/charadas/random', methods= ['GET'])
# def get_charada_random():
#     charada = random.choice(charadas)
#     return jsonify(charada), 200




# Rotas Privadas


# ROTA DE CRIAR UMA NOVA CHARADA

@app.route('/charadas', methods=['POST'])
@token_obrigatorio
def post_charada():
    
    
    dados = request.get_json()
    if not dados or "pergunta" not in dados or "resposta" not in dados:
        return jsonify({"Error": "Dados Inválido"}), 400
    
    try: 
        #Busca pelo contador
        contador_ref = db.collection("contador").document("Controle_id")
        contador_doc = contador_ref.get()
        ultimo_id = contador_doc.to_dict().get("ultimo_id")
        
        #Somar 1 ao ultimo id
        novo_id = ultimo_id + 1
        
        #atualiza o id do contador
        contador_ref.update({"ultimo_id": novo_id})
        
        
        db.collection("Charadas").add({
            "id": novo_id,
            "pergunta": dados["pergunta"],
            "resposta": dados["resposta"]
        })
        
        return jsonify({"message": "Charada criada com sucesso"}), 201
    
    except:
        return jsonify({"ERROR": "Falha no envio da charada"}), 400





# Rota - metodo Put - Alteração total
@app.route('/charadas/<int:id>', methods=['PUT'])
@token_obrigatorio
def charadas_put(id):
   
    
    dados = request.get_json()
    
     # é necessário enviar pergunta e resposta
    if not dados or "pergunta" not in dados or "resposta" not in dados:
        return jsonify({"Error": "Dados Inválido"}), 400
    try:
        docs = db.collection("Charadas").where("id", "==", id).limit(1).get()
        
        if not docs:
            return jsonify({"error": "Charadas não encontrada"}), 404
        
        for doc in docs:
            doc_ref = db.collection("Charadas").document(doc.id)
            doc_ref.update({
                "pergunta": dados["pergunta"],
                "resposta": dados["resposta"]
            })
            
        return jsonify ({"message": "Charada alterada com sucesso"}), 200
               
    except:
        return jsonify({"Error": "Falha no envio da charada"}), 400
        
    
# mudar resposta ou pergunta
@app.route('/charadas/<int:id>', methods=['PATCH'])
@token_obrigatorio
def charadas_patch(id):
    
    
    dados = request.get_json()
    
     # é necessário enviar pergunta e resposta
    if not dados or "pergunta" not in dados or "resposta" not in dados:
        return jsonify({"Error": "Dados Inválido"}), 400
    try:
        docs = db.collection("Charadas").where("id", "==", id).limit(1).get()
        
        if not docs:
            return jsonify({"error": "Charadas não encontrada"}), 404
        
        
        doc_ref = db.collection("Charadas").document(docs[0].id)
        update_charada = {}
        
        if  "perguntas" in dados:
            update_charada["pergunta"] =  dados["pergunta"]
            
        if "resposta" in dados:
            update_charada["resposta"] = dados["resposta"]
            
            doc_ref.update(update_charada)
                
            
        return jsonify ({"message": "Charada alterada com sucesso"}), 200
               
    except:
        return jsonify({"Error": "Falha no envio da charada"}), 400
        







@app.route("/charadas/<int:id>", methods=['DELETE'])
@token_obrigatorio
def delete_charada(id):
    
    docs = db.collection("Charadas").where("id", "==", id).limit(1).get()
    
    
    if not docs:
        return jsonify({"Error": "Charada não encontrada"}), 404
    
    doc_ref = db.collection("Charadas").document(docs[0].id)
    doc_ref.delete()
    return jsonify({"message": "Charada excluída com sucesso"}), 200






@app.errorhandler(404)
def erro404(error):
    return jsonify({"error": "URL não encontrado"}), 404



@app.errorhandler(500)
def erro500(error):
    return jsonify({"error": "URL não encontrado"}), 500















if __name__ == "__main__":
    app.run(debug=True)