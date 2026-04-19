# 🚀 Growth_AI | B2B Sales Intelligence Platform

Growth_AI is a premium, AI-powered sales intelligence platform designed for modern B2B teams. It helps businesses identify high-value opportunities, generate hyper-personalized outreach strategies, and accelerate market expansion using state-of-the-art Generative AI.

![Growth_AI Banner](https://img.shields.io/badge/AI-Powered-7C3AED?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=MongoDB&logoColor=white)

## ✨ Key Features

- **🤖 AI Strategy Engine**: Generate comprehensive B2B market strategies, competitor analyses, and location intelligence using Google Gemini.
- **📜 Strategy History**: Search, filter, and manage all your past AI-generated reports in a beautiful, glassmorphic dashboard.
- **📄 Professional PDF Export**: Download your strategic reports as professionally formatted PDFs with one click.
- **💬 Strategic Chat**: Discuss generated reports with a context-aware AI consultant to dive deeper into specific growth areas.
- **📊 Activity Analytics**: Visualize your strategic output and industry focus with real-time Plotly dashboards.
- **🔐 Secure Authentication**: Full user account management with encrypted passwords and email verification.

## 🛠️ Technology Stack

- **Frontend**: Streamlit (Premium Custom CSS & Animations)
- **AI Engine**: Google Gemini (via `google-generativeai`)
- **Database**: MongoDB Atlas
- **Security**: BCrypt Password Hashing
- **Analytics**: Plotly & Pandas
- **Export**: FPDF2 (Optimized for Unicode)

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- MongoDB Atlas Account
- Google AI Studio API Key

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Devendra440/Growth_ai.git
   ```

2. **Setup Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key
   MONGO_URI=your_mongodb_connection_string
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASS=your_app_password
   ```

5. **Run the App**:
   ```bash
   streamlit run app.py
   ```

---

## 📸 Screenshots

*(Add screenshots of your dashboard here to wow your users!)*

---
© 2026 Growth_AI Intelligence Platform. Built for the future of B2B sales.
