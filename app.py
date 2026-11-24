from __future__ import annotations

import os
import re

import streamlit as st
from dotenv import load_dotenv

from repurposer.exporter import build_markdown_document, build_word_document
from repurposer.extractor import ArticleExtractionError, extract_article
from repurposer.generator import ContentGenerationError, generate_content

load_dotenv()

st.set_page_config(
    page_title="Content Repurposer",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .stApp { background: #f6f7f5; }
      .block-container { max-width: 1120px; padding-top: 2rem; padding-bottom: 3rem; }
      .hero { padding: 1.35rem 1.5rem; border: 1px solid #dce2dc; border-radius: 18px; background: #ffffff; margin-bottom: 1.2rem; }
      .eyebrow { color: #31745b; text-transform: uppercase; letter-spacing: .12em; font-size: .72rem; font-weight: 700; }
      .hero h1 { margin: .3rem 0 .4rem 0; color: #1d2b25; }
      .hero p { margin: 0; color: #5d6962; font-size: 1rem; }
      .hint { color: #69766e; font-size: .88rem; }
      div[data-testid="stDownloadButton"] button { border-radius: 10px; }
      div[data-testid="stTextArea"] textarea { background: #fff; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Week 2 · AI APIs & Web Scraping</div>
      <h1>One article. Three social-ready drafts.</h1>
      <p>Paste a public article link, shape the voice, and turn the useful bits into content for X, LinkedIn and Instagram.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("AI provider")
    provider = st.selectbox("Choose a provider", ["Google Gemini", "OpenAI"])

    if provider == "Google Gemini":
        api_key = st.text_input(
            "Gemini API key",
            value=os.getenv("GEMINI_API_KEY", ""),
            type="password",
            help="The key is used for this session and is not written to a file.",
        )
        default_model = "gemini-3.8-flash"
    else:
        api_key = st.text_input(
            "OpenAI API key",
            value=os.getenv("OPENAI_API_KEY", ""),
            type="password",
            help="The key is used for this session and is not written to a file.",
        )
        default_model = "gpt-5.5"

    model = st.text_input("Model", value=default_model, help="You can edit this if your account uses a different model name.")
    st.caption("API usage may incur charges depending on your provider account and model.")
    st.divider()
    st.subheader("Writing direction")
    tone = st.selectbox(
        "Voice",
        ["Conversational and clear", "Professional but approachable", "Educational and thoughtful", "Bold but not clickbait", "Casual and friendly"],
    )
    audience = st.text_input("Who is this for?", value="Curious readers interested in this topic", max_chars=120)
    angle = st.text_input("Anything to emphasise?", placeholder="e.g. practical takeaways, the business impact, beginner-friendly explanation", max_chars=180)
    st.caption("Keep API keys private. Never commit them to GitHub.")

with st.form("article_form"):
    article_url = st.text_input(
        "Article URL",
        placeholder="https://example.com/blog/your-article",
        help="Use a public blog/article page. Login-only, paywalled and JavaScript-heavy pages may not work.",
    )
    submitted = st.form_submit_button("Extract article and create drafts", type="primary", use_container_width=True)

if submitted:
    if not article_url.strip():
        st.error("Paste an article URL first.")
    elif not api_key.strip():
        st.error("Add your provider API key in the sidebar first.")
    else:
        try:
            with st.spinner("Reading the article..."):
                article = extract_article(article_url)
            st.session_state["article"] = article
            with st.spinner("Writing the three versions..."):
                drafts = generate_content(
                    provider=provider,
                    api_key=api_key,
                    model=model,
                    article=article,
                    audience=audience,
                    tone=tone,
                    angle=angle,
                )
            st.session_state["drafts"] = drafts
            st.success("Your content pack is ready.")
        except ArticleExtractionError as exc:
            st.error(str(exc))
        except ContentGenerationError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Something unexpected happened ({type(exc).__name__}). Check your inputs and try again.")

article = st.session_state.get("article")
drafts = st.session_state.get("drafts")

if article:
    word_count = len(article["text"].split())
    st.markdown("### Source article")
    st.write(f"**{article['title']}**")
    st.caption(f"{article['url']}  ·  approximately {word_count:,} words used")
    with st.expander("Preview extracted text"):
        st.text(article["text"][:5000] + ("\n\n[Preview shortened]" if len(article["text"]) > 5000 else ""))

if drafts and article:
    st.divider()
    st.markdown("### Your drafts")
    x_tab, linkedin_tab, instagram_tab = st.tabs(["X / Twitter thread", "LinkedIn", "Instagram"])

    with x_tab:
        st.caption("A connected thread. Check the character counts before posting.")
        for index, post in enumerate(drafts["x_thread"], start=1):
            st.text_area(f"Post {index} · {len(post)} characters", value=post, height=105, key=f"x_post_{index}")
            if len(post) > 280:
                st.warning(f"Post {index} is over the usual 280-character limit. Shorten it before publishing.")

    with linkedin_tab:
        st.text_area("LinkedIn draft", value=drafts["linkedin_post"], height=300, key="linkedin_draft")
        st.caption(f"{len(drafts['linkedin_post'].split())} words")

    with instagram_tab:
        st.text_area("Instagram caption", value=drafts["instagram_caption"], height=260, key="instagram_draft")
        st.caption(f"{len(drafts['instagram_caption'].split())} words")

    # Pull the latest text-area values so any edits are included in both exports.
    edited_drafts = {
        "x_thread": [st.session_state.get(f"x_post_{index}", post) for index, post in enumerate(drafts["x_thread"], start=1)],
        "linkedin_post": st.session_state.get("linkedin_draft", drafts["linkedin_post"]),
        "instagram_caption": st.session_state.get("instagram_draft", drafts["instagram_caption"]),
    }

    st.divider()
    st.markdown("### Take your content with you")
    col1, col2 = st.columns(2)
    safe_title = re.sub(r"[^a-zA-Z0-9]+", "-", article.get("title", "article")).strip("-").lower()[:45] or "article"
    with col1:
        docx_bytes = build_word_document(article, edited_drafts)
        st.download_button(
            "Download formatted Word document",
            data=docx_bytes,
            file_name=f"content-pack-{safe_title}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    with col2:
        markdown_bytes = build_markdown_document(article, edited_drafts)
        st.download_button(
            "Download Markdown copy",
            data=markdown_bytes,
            file_name=f"content-pack-{safe_title}.md",
            mime="text/markdown",
            use_container_width=True,
        )

st.markdown("<p class='hint'>A first draft, not an autopublish button. Read it once, check the source facts, then make it sound like you.</p>", unsafe_allow_html=True)
