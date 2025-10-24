import streamlit as st
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
import sqlite3
from datetime import datetime
import hashlib

# Configuración de Streamlit
st.set_page_config(page_title="IA Simple 2025", page_icon="🌍", layout="centered")
st.markdown("""
<style>
.main {background: linear-gradient(135deg, #0c0c1e 0%, #1a1a3d 100%);}
h1 {font-family: 'Arial', sans-serif; color: #00d4ff; text-shadow: 0 0 10px #00d4ff;}
.stTextInput > div > div > input {background: rgba(255,255,255,0.1); border: 2px solid #00d4ff; border-radius: 10px; color: white;}
.stButton > button {background: #4CAF50; border-radius: 10px; color: white;}
.respuesta {background: rgba(0,212,255,0.1); padding: 15px; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

# Inicializar memoria
conn = sqlite3.connect('ia_memoria.db')
conn.execute('CREATE TABLE IF NOT EXISTS conversaciones (id INTEGER PRIMARY KEY, hash TEXT, pregunta TEXT, respuesta TEXT, timestamp TEXT, categoria TEXT)')
conn.close()

# Clase IA Simple
class IASimple:
    def __init__(self):
        self.nombre = "IA Simple 2025"
        self.vectorizer = TfidfVectorizer()

    def _buscar_web(self, query):
        try:
            url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
            response = requests.get(url)
            return response.json().get('Abstract', 'No se encontró información')
        except:
            return "No se pudo realizar la búsqueda"

    def _consejos_ambientales(self, pregunta):
        consejos = {
            "reciclaje": "🌱 **Consejo:** Separa papel, plástico, vidrio y orgánicos en contenedores distintos. ¡Reduce el uso de plásticos de un solo uso!",
            "contaminación": "🌍 **Consejo:** Usa transporte público o bicicleta para reducir emisiones. Planta árboles para mejorar la calidad del aire.",
            "agua": "💧 **Consejo:** Cierra el grifo mientras te cepillas los dientes y usa regaderas de bajo flujo para ahorrar agua."
        }
        for clave, valor in consejos.items():
            if clave in pregunta.lower():
                return valor
        return None

    def _guardar_memoria(self, pregunta, respuesta, categoria):
        hash_pregunta = hashlib.md5(pregunta.encode()).hexdigest()
        conn = sqlite3.connect('ia_memoria.db')
        conn.execute("INSERT OR REPLACE INTO conversaciones (hash, pregunta, respuesta, timestamp, categoria) VALUES (?, ?, ?, ?, ?)",
                     (hash_pregunta, pregunta, respuesta, datetime.now().isoformat(), categoria))
        conn.commit()
        conn.close()

    def _buscar_memoria(self, pregunta):
        conn = sqlite3.connect('ia_memoria.db')
        cursor = conn.execute("SELECT pregunta, respuesta FROM conversaciones ORDER BY id DESC LIMIT 10")
        historial = [row for row in cursor.fetchall()]
        conn.close()
        if historial:
            preguntas = [row[0] for row in historial]
            vectores = self.vectorizer.fit_transform([pregunta] + preguntas)
            similitudes = self.vectorizer.transform([pregunta]).dot(vectores.T).toarray()[0]
            mejor_idx = similitudes.argmax()
            if similitudes[mejor_idx] > 0.3:
                return historial[mejor_idx][1]
        return None

    def responder(self, pregunta):
        memoria = self._buscar_memoria(pregunta)
        if memoria:
            return memoria, "memoria"

        consejo = self._consejos_ambientales(pregunta)
        if consejo:
            self._guardar_memoria(pregunta, consejo, "medio ambiente")
            return consejo, "ambiental"

        if "busca" in pregunta.lower():
            respuesta = self._buscar_web(pregunta.replace("busca", "").strip() + " site:*.org")
            self._guardar_memoria(pregunta, respuesta, "búsqueda")
            return f"🔍 **Respuesta de búsqueda:**\n{respuesta}", "búsqueda"

        respuestas_base = {
            "hola": "¡Hola! Soy IA Simple 2025, lista para ayudarte, especialmente con temas ambientales. 😊",
            "qué es": "Estoy buscando la mejor respuesta para ti...",
        }
        for clave, valor in respuestas_base.items():
            if clave in pregunta.lower():
                self._guardar_memoria(pregunta, valor, "general")
                return valor, "base"

        respuesta = self._buscar_web(pregunta)
        self._guardar_memoria(pregunta, respuesta, "general")
        return f"🤖 **Respuesta:**\n{respuesta}", "búsqueda"

# Interfaz
st.title("🌍 IA Simple 2025")
st.write("Haz cualquier pregunta, especialmente sobre cuidado del medio ambiente.")

if "messages" not in st.session_state:
    st.session_state.messages = []

ia = IASimple()
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Pregúntame algo..."):
    st.session_state.messages.append({"role": "user", "content": f"**👤 Tú:** {prompt}"})
    with st.chat_message("user"):
        st.markdown(f"**👤 Tú:** {prompt}")

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            respuesta, tipo = ia.responder(prompt)
            st.markdown(f"<div class='respuesta'>{respuesta}</div>", unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": f"**{ia.nombre}:** {respuesta}"})
