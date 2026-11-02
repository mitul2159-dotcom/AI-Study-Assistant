# LearnSphere AI — AI-Powered Personalized Study Assistant

A unified, multi-page Streamlit website combining both PCs' features in one application, with a redesigned landing page and consistent styling.

## Included features

### Study materials and personal revision (PC 1)
- Ask questions about a PDF with page citations
- PDF summaries and exam revision notes
- MCQ quiz generation and saved quiz history
- Learning-gap analysis based on quiz mistakes
- AI flashcards with spaced repetition
- Timed mock exam mode
- Personalized study coach and exam-date planning
- Learning progress dashboard backed by SQLite
- Ask questions across multiple PDFs
- Lecture-to-study-material converter for audio, video, TXT, PDF, and DOCX transcripts
- Local speech-to-text with Faster Whisper; no paid transcription API

### Coding and concept learning (PC 2)
- Prerequisite Knowledge Mapper with a visual learning roadmap
- Coding Practice Bridge with exercises, hints, tests, and feedback
- Multilingual Learning Assistant
- AI Code Debugging Tutor
- Algorithm Step Visualizer for sorting and searching

### UI improvements
- New LearnSphere AI landing page
- Unified colors, typography, buttons, input styling, and card-based feature navigation
- Feature pages remain separate for easier navigation, but run as one website

## Requirements

- Windows 10/11
- Python 3.10+
- Ollama installed and running
- Local Ollama models used by the current feature modules:
  - `qwen2.5:7b` — PC 1 study materials
  - `qwen2.5-coder:3b` — PC 2 coding/concept tools
- Optional compiler/runtime for coding tests:
  - Python
  - Java (`javac`, `java`)
  - C++ (`g++`)
  - C (`gcc`)
  - JavaScript (`node`)

The first Faster Whisper audio/video run may download its speech model. Transcription is performed locally after the model is available. Very large recordings can take time on CPU.

## Windows setup

Open PowerShell in the extracted project folder.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Install Ollama from https://ollama.com/ if needed, then download both models:

```powershell
ollama pull qwen2.5:7b
ollama pull qwen2.5-coder:3b
```

Check that they are installed:

```powershell
ollama list
```

## Run the website

From the project root (the folder containing `Home.py`):

```powershell
python -m streamlit run Home.py
```

Streamlit will print a local URL, usually `http://localhost:8501`. Open that address in your browser.

## Project structure

```text
Integrated_AI_Study_Assistant/
├── Home.py
├── requirements.txt
├── README.md
├── pages/
│   ├── 1_Prerequisite_Knowledge_Mapper.py
│   ├── 2_Coding_Practice_Bridge.py
│   ├── 3_Multilingual_Learning_Assistant.py
│   ├── 4_AI_Code_Debugging_Tutor.py
│   ├── 5_Algorithm_Step_Visualizer.py
│   └── 6_Study_Materials_Hub.py
└── modules/
    ├── ui_theme.py
    └── feature helper modules...
```

## Important notes before evaluation

1. Run the app from the project root so imports work.
2. Both Ollama models must be installed because the two feature sets use different models.
3. Keep `study_assistant.db` in the project root; it is created automatically when the Study Materials Hub runs.
4. The code-runner uses local subprocesses and is **not a secure sandbox for untrusted code**. Use it only for a trusted local demo.
5. PDF text extraction does not perform OCR on scanned PDFs; use a text-based PDF for reliable citations.
6. To preserve your original work, test this merged folder first before replacing or deleting either PC's original folder.


### Readability-focused brutalist styling
The shared theme uses strong black borders and hard shadows with high-contrast text, clearer labels, visible tabs and expanders, readable inputs/dropdowns, and keyboard-focus outlines.
