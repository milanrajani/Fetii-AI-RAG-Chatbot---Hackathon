# 🚀 Deployment Guide for FetiiAI

## Option 1: Streamlit Community Cloud (Recommended - FREE)

### Prerequisites
- GitHub account
- Your code pushed to GitHub repository

### Steps:

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Initial commit - FetiiAI app"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/fetii-ai-hackathon.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository: `YOUR_USERNAME/fetii-ai-hackathon`
   - Main file path: `working_app.py`
   - Click "Deploy!"

3. **Set Environment Variables:**
   - In Streamlit Cloud dashboard
   - Go to your app settings
   - Add secret: `OPENAI_API_KEY` = `your_api_key_here`

4. **Upload Data File:**
   - Use the file uploader in the deployed app
   - Or add your data file to the GitHub repository

---

## Option 2: Heroku

### Prerequisites
- Heroku CLI installed
- Heroku account

### Steps:

1. **Create Heroku app:**
   ```bash
   heroku create your-app-name
   ```

2. **Set environment variables:**
   ```bash
   heroku config:set OPENAI_API_KEY=your_api_key_here
   ```

3. **Create Procfile:**
   ```
   web: streamlit run working_app.py --server.port=$PORT --server.address=0.0.0.0
   ```

4. **Deploy:**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

---

## Option 3: Railway

### Steps:

1. **Connect GitHub repository to Railway**
2. **Set environment variables:**
   - `OPENAI_API_KEY` = your API key
3. **Deploy automatically**

---

## Option 4: AWS/GCP/Azure

### For production deployment:

1. **Use Docker:**
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   EXPOSE 8501
   CMD ["streamlit", "run", "working_app.py", "--server.address=0.0.0.0"]
   ```

2. **Deploy to cloud platform**
3. **Set environment variables**
4. **Configure domain and SSL**

---

## Environment Variables Required

- `OPENAI_API_KEY`: Your OpenAI API key

## Data File

- Place `FetiiAI_Data_Austin.xlsx` in the project directory
- Or use the file uploader in the app

## Troubleshooting

- **App won't start**: Check requirements.txt has all dependencies
- **API key not found**: Set environment variable correctly
- **Data not loading**: Ensure file is in correct location
- **Memory issues**: Use smaller data files or optimize data processing
