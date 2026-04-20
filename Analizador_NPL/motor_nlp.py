# -*- coding: utf-8 -*-
#https://e4you.org/es
import pandas as pd
from collections import Counter, defaultdict
import re
from docx import Document
import pdfplumber
import os
import spacy
from spacy.lang.es.stop_words import STOP_WORDS
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.chart import PieChart, Reference

import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from wordcloud import WordCloud

nlp = spacy.load("es_core_news_sm")

normalizacion = {
    "derechos": "derecho",
    "leyes": "ley",
    "personas": "persona",
    "niños": "niño"
}

def leer_docx(archivo):
    doc = Document(archivo)
    texto = ''
    for parrafo in doc.paragraphs:
        texto += parrafo.text + '\n'
    return texto

def leer_pdf(archivo):
    texto = ''
    with pdfplumber.open(archivo) as pdf:
        for pagina in pdf.pages:
            texto += pagina.extract_text() + '\n'
    return texto

def limpiar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r'[^a-záéíóúüñ\s]', '', texto)
    palabras = texto.split()
    palabras = [palabra for palabra in palabras if palabra not in STOP_WORDS]
    return " ".join(palabras)  

def clasificar_palabras(texto):
    doc = nlp(texto)  
    categorias = {"Sustantivos": Counter(), "Verbos": Counter(), "Adjetivos": Counter(), "Adverbios": Counter() , "Total": Counter()}
    apariciones = defaultdict(lambda: Counter())  
    
    for token in doc:
        if not token.is_alpha: 
            continue
        lemma = token.lemma_
        if lemma in normalizacion:
            lemma = normalizacion[lemma]
        categoria = token.pos_
        
        if categoria == "NOUN":
            categorias["Sustantivos"][lemma] += 1
        elif categoria == "VERB":
             if " " in lemma:
                lemma = lemma.split(" ")[0]
             categorias["Verbos"][lemma] += 1
        elif categoria == "ADJ":
            categorias["Adjetivos"][lemma] += 1
        elif categoria == "ADV":
            categorias["Adverbios"][lemma] += 1
            
        categorias["Total"][lemma] += 1
        apariciones[lemma][categoria] += 1  

    total_palabras_documento = sum(categorias["Total"].values())
    
    for categoria, counter in categorias.items():
        total_palabras_categoria = sum(counter.values())
        df = pd.DataFrame(counter.items(), columns=["Palabra", "Frecuencia"])
        if total_palabras_categoria > 0:
            df["Porcentaje en Categoría"] = (df["Frecuencia"] / total_palabras_categoria) * 100
        else:
            df["Porcentaje en Categoría"] = 0
            
        if total_palabras_documento > 0:
            df["Porcentaje en Documento"] = (df["Frecuencia"] / total_palabras_documento) * 100
        else:
            df["Porcentaje en Documento"] = 0
            
        df = df.sort_values(by="Frecuencia", ascending=False)
        categorias[categoria] = df
    
    return categorias

# --- MODIFICADO: Ahora devuelve las categorías y el texto original ---
def procesar_documento(archivo):
    if archivo.endswith('.docx'):
        texto = leer_docx(archivo)
    elif archivo.endswith('.pdf'):
        texto = leer_pdf(archivo)
    else:
        raise ValueError("El archivo debe ser .docx o .pdf")
    
    texto_original = texto.replace('\n', ' ') # Guardamos el original para las frases
    texto_limpio = limpiar_texto(texto)
    categorias = clasificar_palabras(texto_limpio)
    return categorias, texto_original

def aplicar_formato_excel(archivo):
    wb = load_workbook(archivo)
    for sheet in wb.sheetnames:
        ws = wb[sheet]
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            cell.fill = PatternFill(start_color="D3D3D3", fill_type="solid")
        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            ws.column_dimensions[col_letter].width = (max_length + 2)
            
        if sheet not in ["Resumen Total", "Final"] and ws.max_row > 1:
            limite_fila = min(11, ws.max_row) 
            data = Reference(ws, min_col=2, min_row=2, max_row=limite_fila)          
            labels = Reference(ws, min_col=1, min_row=2, max_row=limite_fila)
            chart = PieChart()
            chart.add_data(data, titles_from_data=False)
            chart.set_categories(labels)
            chart.title = f"Top 10 {sheet}"
            ws.add_chart(chart, "F2") 
    wb.save(archivo)

def guardar_excel_multiple(dfs, nombre_archivo):
    with pd.ExcelWriter(nombre_archivo) as writer:
        for categoria, df in dfs.items():
            df.to_excel(writer, sheet_name=categoria, index=False)
        
        total_por_categoria = {cat: df["Frecuencia"].sum() for cat, df in dfs.items() if cat != "Total"}
        total_general = sum(total_por_categoria.values())
        
        df_totales = pd.DataFrame(list(total_por_categoria.items()), columns=["Categoría", "Total de Palabras"])
        df_totales["Porcentaje en Documento"] = (df_totales["Total de Palabras"] / total_general) * 100 if total_general > 0 else 0
        df_totales.to_excel(writer, sheet_name="Resumen Total", index=False)

def generar_nube_palabras(df, nombre_imagen):
    os.makedirs('static', exist_ok=True)
    diccionario_frec = dict(zip(df['Palabra'], df['Frecuencia']))
    if not diccionario_frec:
        return None
    wordcloud = WordCloud(width=800, height=400, background_color='white', colormap='viridis').generate_from_frequencies(diccionario_frec)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)
    ruta_imagen = os.path.join('static', nombre_imagen)
    plt.savefig(ruta_imagen)
    plt.close()
    return ruta_imagen

# --- NUEVA FUNCIÓN: Buscador de Frases en Python ---
def obtener_concordancias(palabra, limite=3):
    resultados = {'favor': [], 'contra': []}
    
    # 1. Leer los textos originales guardados
    try:
        with open('uploads/favor.txt', 'r', encoding='utf-8') as f:
            texto_favor = f.read()
        with open('uploads/contra.txt', 'r', encoding='utf-8') as f:
            texto_contra = f.read()
    except Exception as e:
        return resultados

    # 2. Dividir por puntos para sacar las frases y buscar la palabra
    frases_favor = [frase.strip() for frase in texto_favor.split('.') if palabra.lower() in frase.lower()]
    frases_contra = [frase.strip() for frase in texto_contra.split('.') if palabra.lower() in frase.lower()]

    # 3. Resaltar la palabra en negrita (HTML) y coger solo las primeras (limite)
    for f in frases_favor[:limite]:
        f_resaltada = re.sub(f'(?i)({palabra})', r'<b class="text-blue-700 bg-blue-100 px-1 rounded">\1</b>', f)
        resultados['favor'].append(f_resaltada + ".")
        
    for f in frases_contra[:limite]:
        f_resaltada = re.sub(f'(?i)({palabra})', r'<b class="text-red-700 bg-red-100 px-1 rounded">\1</b>', f)
        resultados['contra'].append(f_resaltada + ".")
        
    return resultados


def generar_informes(ruta_archivo1, ruta_archivo2):
    dfs1, texto_favor = procesar_documento(ruta_archivo1)
    dfs2, texto_contra = procesar_documento(ruta_archivo2)

    # --- NUEVO: Guardamos los textos limpios para poder buscarlos luego ---
    with open('uploads/favor.txt', 'w', encoding='utf-8') as f:
        f.write(texto_favor)
    with open('uploads/contra.txt', 'w', encoding='utf-8') as f:
        f.write(texto_contra)

    ruta_nube_favor = generar_nube_palabras(dfs1["Total"], "nube_favor.png")
    ruta_nube_contra = generar_nube_palabras(dfs2["Total"], "nube_contra.png")

    guardar_excel_multiple(dfs1, "Corpus_a_favor.xlsx")
    guardar_excel_multiple(dfs2, "Corpus_en_contra.xlsx")
    aplicar_formato_excel("Corpus_a_favor.xlsx")
    aplicar_formato_excel("Corpus_en_contra.xlsx")

    dfs_suma = {}
    total_palabras_documento = dfs1["Total"]["Frecuencia"].sum() + dfs2["Total"]["Frecuencia"].sum()

    for categoria in ["Sustantivos", "Verbos", "Adjetivos", "Adverbios", "Total"]:
        df1 = dfs1[categoria].set_index("Palabra")
        df2 = dfs2[categoria].set_index("Palabra")
        df_suma = df1.add(df2, fill_value=0).reset_index()
        total_palabras_categoria = df_suma["Frecuencia"].sum()
        df_suma["Porcentaje en Categoría"] = (df_suma["Frecuencia"] / total_palabras_categoria) * 100 if total_palabras_categoria > 0 else 0
        df_suma["Porcentaje en Documento"] = (df_suma["Frecuencia"] / total_palabras_documento) * 100 if total_palabras_documento > 0 else 0
        df_suma = df_suma.sort_values(by="Frecuencia", ascending=False)
        dfs_suma[categoria] = df_suma
     
    nombre_final = "EB_CyL_2026.xlsx"
    guardar_excel_multiple(dfs_suma, nombre_final)

    df_favor = dfs1["Total"][["Palabra", "Porcentaje en Documento"]].copy()
    df_favor = df_favor.rename(columns={"Porcentaje en Documento": "Porcentaje en Corpus_a_favor"})
    df_contra = dfs2["Total"][["Palabra", "Porcentaje en Documento"]].copy()
    df_contra = df_contra.rename(columns={"Porcentaje en Documento": "Porcentaje en Corpus_en_contra"})
    df_total = dfs_suma["Total"][["Palabra", "Porcentaje en Documento"]].copy()

    df_final = df_total.merge(df_favor, on="Palabra", how="left")
    df_final = df_final.merge(df_contra, on="Palabra", how="left").fillna(0)

    df_final["Ponderación Corpus_a_favor"] = (df_final["Porcentaje en Corpus_a_favor"] / (df_final["Porcentaje en Corpus_a_favor"] + df_final["Porcentaje en Corpus_en_contra"])) * 100
    df_final["Ponderación Corpus_en_contra"] = (df_final["Porcentaje en Corpus_en_contra"] / (df_final["Porcentaje en Corpus_a_favor"] + df_final["Porcentaje en Corpus_en_contra"])) * 100

    df_final = df_final[df_final["Porcentaje en Documento"] > 0.02]

    with pd.ExcelWriter(nombre_final, mode="a", engine="openpyxl", if_sheet_exists="replace") as writer:
        df_final.to_excel(writer, sheet_name="Final", index=False)
        
    aplicar_formato_excel(nombre_final)
    return nombre_final, ruta_nube_favor, ruta_nube_contra