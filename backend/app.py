from flask import Flask, request, jsonify
import heapq
import os
from graphviz import Digraph
from flask_cors import CORS
from flask import send_from_directory

app = Flask(__name__)
CORS(app, resources={r"/encriptar": {"origins": "http://localhost:3000"}}) #habilita CORS para todas las rutas 

class NodoHuffman:
    def __init__(self, caracter, frecuencia):
        self.caracter = caracter #caracter
        self.frecuencia = frecuencia #frecuencia de caracteres
        self.izquierda = None #rama izquierda
        self.derecha = None

    def __lt__(self, otro):
        return self.frecuencia < otro.frecuencia

def generar_arbol(texto):
    frecuencias = {}
    for caracter in texto:
        frecuencias[caracter] = frecuencias.get(caracter, 0) + 1

    # Ordenamos manualmente los caracteres en orden ascendente por frecuencia
    caracteres_ordenados = sorted(frecuencias.items(), key=lambda x: (x[1], x[0])) 

    heap = [NodoHuffman(caracter, freq) for caracter, freq in caracteres_ordenados]
    heapq.heapify(heap)

    while len(heap) > 1:
        izquierda = heapq.heappop(heap)  # Extraemos el menor
        derecha = heapq.heappop(heap)  # Extraemos el siguiente menor

        # Aseguramos que los nodos con mayor frecuencia se coloquen a la derecha
        if izquierda.frecuencia > derecha.frecuencia:
            izquierda, derecha = derecha, izquierda

        nodo = NodoHuffman(None, izquierda.frecuencia + derecha.frecuencia)
        nodo.izquierda = izquierda
        nodo.derecha = derecha
        heapq.heappush(heap, nodo)

    return heap[0]


def generar_codigos(raiz, codigo_actual="", codigos={}):
    if raiz is None:
        return
    if raiz.caracter is not None:
        codigos[raiz.caracter] = codigo_actual
    generar_codigos(raiz.izquierda, codigo_actual + "0", codigos)
    generar_codigos(raiz.derecha, codigo_actual + "1", codigos)
    return codigos

def exportar_arbol_pdf(raiz, nombre_archivo="arbol_huffman"):
    dot = Digraph(comment="Árbol de Huffman")
    def agregar_nodos(nodo, parent_id=None, label=""):
        if nodo is None:
            return
        nodo_id = f"{id(nodo)}"
        dot.node(nodo_id, label=f"{nodo.frecuencia}\n {nodo.caracter or ''}")
        if parent_id:
            dot.edge(parent_id, nodo_id, label=label)
        agregar_nodos(nodo.izquierda, nodo_id, "0")
        agregar_nodos(nodo.derecha, nodo_id, "1")
    agregar_nodos(raiz)
    dot.render(nombre_archivo, format="pdf", cleanup=True)
    return f"{nombre_archivo}.pdf"

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    return send_from_directory('.', filename)  # Sirve archivos desde la carpeta actual

@app.route("/descargar_pdf", methods = ["GET"])
def descargaar_pdf():
    archivo_pdf ="arbol_huffman.pdf"
    if os.path.exists(archivo_pdf):
        return send_from_directory('.', archivo_pdf, as_attachment=True)
    return jsonify({"Error": "Archivo no encontrado"}),

@app.route("/encriptar", methods=["POST"])#solo POST
def encriptar():
    data = request.get_json()
    texto = data.get("texto", "")
    raiz = generar_arbol(texto)
    codigos = generar_codigos(raiz)
    texto_encriptado = " ".join([codigos[caracter] for caracter in texto])
    pdf_path = exportar_arbol_pdf(raiz)
    return jsonify({
        "encriptado": texto_encriptado,
        "codigos": codigos, #agregamos  los codigo a la respuesta 
        "pdf_path": f"/pdf/{pdf_path}"  # Cambia la ruta para usar el endpoint nuevo
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)