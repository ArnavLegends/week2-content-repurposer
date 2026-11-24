# Week 2 — AI Content Repurposer

A small Streamlit app that takes a **public article URL**, extracts the main text, and turns it into three editable social drafts:

- an X/Twitter thread (5–7 connected posts)
- a LinkedIn post
- an Instagram caption

It supports **Google Gemini** and **OpenAI**. You choose the provider and model in the sidebar. The finished pack can be downloaded as a formatted Word document (`.docx`) or Markdown (`.md`).

## What it uses

- **Python** for the application logic
- **Requests** for downloading public web pages
- **Trafilatura + BeautifulSoup** for article extraction and fallback parsing
- **Gemini API / OpenAI Responses API** for content generation
- **Streamlit** for the web interface
- **python-docx** for the Word export

## Features

- Reads the main article text instead of blindly copying the whole webpage.
- Lets you set the audience, writing voice and angle.
- Uses separate writing requirements for X, LinkedIn and Instagram.
- Includes guardrails against invented statistics, fake personal stories and generic AI-sounding filler.
- Shows the extracted text before you publish anything.
- Flags X thread posts that exceed 280 characters.
- Exports the drafts to Word and Markdown.
- Keeps API keys in the session or local environment; it does not save them in the project.
- Limits page downloads and blocks localhost/private-network targets and unsafe redirect destinations.

## Requirements

- Python **3.10 or newer**
- An API key for either Google Gemini or OpenAI
- Internet access to fetch the article and call the selected API

API usage may cost money. A ChatGPT subscription does not automatically include OpenAI API credits. Check the provider's current pricing and quota before making repeated requests. Gemini availability and free quotas depend on the model and account.

## Setup on Windows

Open Command Prompt in this project folder and run:

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If Python 3.11 is not installed, use an installed Python version 3.10 or newer:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Add your API key

**Option A — enter it in the app:** run the app and paste your key into the password field in the sidebar. This is the easiest option for a first run.

**Option B — use a local `.env` file:** copy `.env.example` to `.env`, then add your key:

```env
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=
```

Or, for OpenAI:

```env
GEMINI_API_KEY=
OPENAI_API_KEY=your_openai_key_here
```

Keep `.env` private. It is excluded by `.gitignore`; never paste a real API key into source code or commit it to GitHub. If a key is accidentally pushed, revoke it at the provider immediately and create a replacement.

## Run the app

```bat
streamlit run app.py
```

Streamlit will print a local address, normally `http://localhost:8501`. Open it in your browser.

## Run the tests

```bat
python -m unittest discover -s tests -v
```

The tests cover prompt construction and validation of the model response. They do not make API calls.

## How to use it

1. Choose Google Gemini or OpenAI in the sidebar.
2. Add your API key and confirm the model name. The defaults are editable; use a model enabled for your account.
3. Set the audience, voice and optional angle.
4. Paste a public blog/article URL and click **Extract article and create drafts**.
5. Review the extracted source text and all three drafts.
6. Edit the copy before publishing, then download the Word or Markdown file.

## Known limitations

- This is an article-page extractor, not a general web crawler.
- Login-protected, paywalled, JavaScript-rendered and bot-blocked pages may not extract correctly.
- It does not bypass site restrictions. Only use it on pages you are allowed to access and process; respect each site's terms and applicable copyright rules.
- The app creates drafts; it does not publish to social networks.
- The character count is checked after generation. The model can still return a long X post, so shorten any flagged post before publishing.
- The URL checks reduce common SSRF risks, but this is a learning project and should receive a security review before public deployment.

## Project structure

```text
week2-content-repurposer/
├── app.py
├── repurposer/
│   ├── __init__.py
│   ├── exporter.py
│   ├── extractor.py
│   ├── generator.py
│   └── prompts.py
├── tests/
│   └── test_logic.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Official documentation

- [OpenAI Python SDK — Responses API](https://developers.openai.com/api/reference/python)
- [Google Gen AI Python SDK](https://googleapis.github.io/python-genai/)
- [Trafilatura — Python usage](https://trafilatura.readthedocs.io/en/latest/usage-python.html)
- [Streamlit — download files](https://docs.streamlit.io/knowledge-base/using-streamlit/how-download-file-streamlit)

## Gemini troubleshooting

The app displays Gemini's HTTP status and sanitized provider message when the API returns an error.

- **HTTP 429:** check quota and rate limits for the Google AI Studio project that owns the key.
- **HTTP 401/403:** check that the key is active and belongs to a project with Gemini API access.
- **HTTP 404:** verify the model ID is available to the project.
- **HTTP 5xx:** this is a Gemini service-side response and is commonly transient. Retry after a short pause; if it continues, try `gemini-3.5-flash-lite` and check Google's Gemini API status.

Update the dependencies after replacing an older project version:

```bat
python -m pip install --upgrade -r requirements.txt
```
