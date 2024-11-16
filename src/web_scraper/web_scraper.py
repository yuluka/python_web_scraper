from groq import Groq, APIStatusError
from openai import OpenAI

from bs4 import BeautifulSoup
from bs4.element import Tag

import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

CONTEXT_LLM: str = """
Tu tarea es extraer información específica del siguiente texto (contenido scrapeado de una página web de una noticia): \n{page_content}
Por favor, sigue estas instrucciones al pie de la letra:
1. **Extracción de información**: Extraer sólo la información que coincida directamente con la descripción proporcionada: Título, Autor, y Fecha de publicación de la noticia.
2. **Sin contenido adicional:** No incluir ningún texto, comentario o explicación adicional en la respuesta.
3. **Respuesta vacía:** Si ninguna información coincide con la descripción, devuelve una cadena vacía ('').
4. **Sólo datos directos:** Tu salida debe contener sólo los datos solicitados explícitamente, sin ningún otro texto.
5. **Formato de salida:** La salida debe estar en formato JSON, con los datos solicitados en campos separados, con los nombres: Título, Autor, Fecha.
"""

def load_urls() -> list[str]:
    """
    Load the URLs to scrape from the source_urls.txt file.

    :return: list of URLs to scrape.
    :rtype: list[str]
    """

    current_dir: str = os.path.dirname(os.path.realpath(__file__))
    current_dir = os.path.dirname(current_dir)
    current_dir = os.path.dirname(current_dir)
    data_path: str = os.path.join(current_dir, "source_urls.txt")

    with open(data_path, "r") as file:
        urls: list[str] = file.readlines()
        urls = [url.strip() for url in urls]

    return urls


def scrape_pages():
    """
    Scrape the pages from the URLs in the source_urls.txt file.
    """

    SOURCE_URLS: list[str] = load_urls()
    # SOURCE_URLS: list[str] = ['https://elpais.com/america-colombia/2024-11-15/el-fin-de-la-tregua-gustavo-petro-y-alvaro-uribe-reviven-sus-fuertes-enfrentamientos-tras-dos-anos-de-tensa-calma.html']
    counter: int = 0

    for url in SOURCE_URLS:
        page_content: str = scrape_page(url)

        relevant_data: dict = extract_relevant_data(page_content)
        file_path: str = f"data/output_{counter}.json"
        counter += 1

        save_data(relevant_data, file_path)


def scrape_page(url: str) -> str:
    """
    Scrape the page content from the given URL.

    :param url: The URL to scrape.
    :type url: str
    :return: The page content.
    :rtype: str
    """

    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Failed to load page: {url}\Error: {response.status_code}")

    return response.text


def extract_relevant_data(page_content: str) -> dict:
    """
    Extract the relevant data from the page content.

    :param page_content: The content of the page.
    :type page_content: str
    :return: The extracted data.
    :rtype: dict
    """
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")

    client = Groq(
        api_key=GROQ_API_KEY,
    )

    clean_content: Tag = clean_page_content(page_content)

    new_content: str = clean_content.main.get_text("\n") if clean_content.main else clean_content.article.get_text("\n")
    links: list[str] = [a["href"] for a in clean_content.find_all("a", href=True)]

    for a in clean_content.find_all("a", href=True):
        if "author" in str(a["href"]).lower() or "autor" in str(a["href"]).lower(): # skip author links
            continue
        
        a.decompose()

    page_content = str(clean_content).replace("<div>", "").replace("</div>", "") # remove div tags

    context: str = CONTEXT_LLM.format(
        page_content=page_content,
    )

    # Send the context to the model and get the response. Retry if there is an error.
    while True:
        try:
            response: str = chat_groq(context, client)
            
            result: dict = json.loads(response)
            result["Contenido"] = new_content
            result["Enlaces"] = links

            break
        except Exception as e:
            print(f"Error: {e}\nEsperando 1 minuto para continuar...")

            time.sleep(65)

    return result
    

def clean_page_content(page_content: str) -> Tag:
    """
    Clean the page content by removing unwanted characters and tags.

    :param page_content: The content of the page.
    :type page_content: str
    :return: The cleaned page content.
    :rtype: Tag
    """

    soup: BeautifulSoup = BeautifulSoup(page_content, "html.parser")

    attrs_to_remove: list[str] = [
        "id", "class", "style", "data-fusion-component", "rel", 
        "data-index", "data-type", "data-custom-type", "target", 
        "dir", "lang"
    ]

    tags_to_remove: list[str] = [
        "script", "svg", "img", "header", "footer", "iframe", 
        "nav", "figure", "noscript", "meta", "button", "input", 
        "style", "picture", "figcaption", "data-autor", "data-bloqueo", 
        "data-board", "data-category", "data-clasecontenido", "data-editorial", 
        "data-id", "data-name", "data-position", "data-publicacion", "data-redactorvisible", 
        "data-seccion", "data-subseccion", "data-tipocontenido"
    ]

    for thrash_tag in soup(tags_to_remove):
        thrash_tag.extract()

    for tag in soup.find_all(True):
        for attr in attrs_to_remove:
            if attr in tag.attrs:
                del tag.attrs[attr]

    return soup.body


def save_data(data: dict, file_path: str):
    """
    Save the extracted data to a JSON file.

    :param data: The extracted data.
    :type data: dict
    :param file_path: The path to save the data.
    :type file_path: str
    """

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def chat_groq(context: str, client: Groq) -> str:
    """
    Sends a message to the llama3 model and returns the response.

    :param context: The message to send to the model.
    :type context: str
    :param client: The Groq client.
    :type client: Groq
    :return: The response from the model.
    :rtype: str
    """

    messages: list[dict] = [
        {"role": "system", "content": context},
    ]

    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        temperature=1,
        max_tokens=8192,
        top_p=1,
        stream=True,
        stop=None,
    )

    response: str = ""

    for chunk in completion:
        response += chunk.choices[0].delta.content or ""

    return response


scrape_pages()