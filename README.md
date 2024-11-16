# Python web scraper

## Author

Yuluka Gigante Muriel


## Overview

This repository contains the implementation of a simple Web scraper designed to extract information from Colombian news pages. The scraper is prepared to extract the title, author, publication date, content and URLs of a news item (works especially well on the pages of El Pais, Blu Radio, and El Espectador).


## How to use it

To use this project you must follow these steps:

1. Install the dependencies listed in 'requirements.txt':

    ```bash
    pip install -r requirements.txt
    ```

2. Get the necessary API key:

    As this scraper uses a LLM to extract certain data, it is necessary to get an API key to use it. In this case, I'm using a model from Groq, so you can get the key on:

    - [Groq](https://console.groq.com/keys)

    Once you have the key you'll use, create a `.env` file at the root of the project, and write `GROQ_API_KEY=«the_groq_key»`.

3. Collect the pages:

    You'll need to collect the URLs you want to scrape. 

    This repo already contains a set of pre-selected URLs, stored in `source_urls.txt`, which have been tested and work well. However, if you want to use different pages, just overwrite the URLs in file mentioned above.

    **Note:** Make sure that the pages you choose follow a similar structure to the ones I chose. Otherwise, the scraper will fail to extract the information. The news items that I have noticed that work best are the ones from the sites:

    - [El País](https://www.elpais.com.co)
    - [Blu Radio](https://www.bluradio.com)
    - [El Espectador](https://www.elespectador.com)

4. Run the `web_scraper.py` script:

    To start the scraper, run the following command:

    ```bash
    python ./src/web_scraper/web_scraper.py
    ```

    Once the script is running, it'll begin to scrape the pages. If an error occur during the interaction with the LLM, it will be shown to you via console and the program will wait 65 seconds before retrying. However, make sure that the page you pass it is not too large or the context window will full up and the program will fail everytime.

    the information of each page will be saved in a `.json` file, in the `data` folder. The structure in which the information is stored is:

    ```json
    {
        "Título": "Title",
        "Autor": "Author",
        "Fecha": "Publication date",
        "Contenido": "Content",
        "Enlaces": [
            "Mentioned links"
        ],
    }
    ```


I hope you find this useful.