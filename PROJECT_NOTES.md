# Week 2 project notes

## Learning outcomes

By completing this project, you practise:

1. Sending text-generation requests to an AI API.
2. Scraping and extracting readable article content from a public URL.
3. Cleaning and limiting scraped text before sending it to a model.
4. Designing prompts for different audiences and social platforms.
5. Validating structured model output before using it.
6. Exporting generated content into a formatted Word document.

## Suggested walkthrough

- First run: use a short public article and Gemini if you have a key with available quota.
- Inspect `repurposer/extractor.py` to understand fetching, redirect checks and text extraction.
- Inspect `repurposer/prompts.py` and change the voice rules; compare the drafts before and after.
- Inspect `repurposer/generator.py` to see how the same prompt is sent to two providers.
- Inspect `repurposer/exporter.py` to see how the content becomes a `.docx` file.
- Run the unit tests before changing the project.

## Small extension ideas

- Add a manual article-text input for pages that cannot be scraped.
- Add a regenerate button for only one platform.
- Add a short source summary and key-points panel.
- Save previous content packs locally as JSON, without storing API keys.
- Add tests for URL validation using mocked DNS and HTTP responses.
