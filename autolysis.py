import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import httpx
import chardet
import subprocess

# Constants
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjIwMDUzNzVAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.7rXDto5TzajWEQEEQYJeScynPwPB1MSK1nXyTJ6hbRk"

def check_dependencies():
    """Ensure required packages are installed."""
    required_packages = ["pandas", "seaborn", "matplotlib", "chardet", "httpx"]
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing missing package: {package}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def load_data(file_path):
    """Load CSV data with encoding detection."""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    return pd.read_csv(file_path, encoding=encoding)

def analyze_data(df):
    """Perform basic data analysis."""
    numeric_df = df.select_dtypes(include=['number'])  # Select only numeric columns
    analysis = {
        'summary': df.describe(include='all').to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'correlation': numeric_df.corr().to_dict()  # Compute correlation only on numeric columns
    }
    return analysis

def visualize_data(df):
    """Generate and save visualizations."""
    sns.set(style="whitegrid")
    numeric_columns = df.select_dtypes(include=['number']).columns
    for column in numeric_columns:
        plt.figure()
        sns.histplot(df[column].dropna(), kde=True, color="skyblue")
        plt.title(f'Distribution of {column}')
        plt.xlabel(column)
        plt.ylabel('Frequency')
        plt.savefig(f'{column}_distribution.png')
        plt.close()

def generate_narrative(analysis):
    """Generate narrative using LLM."""
    headers = {
        'Authorization': f'Bearer {AIPROXY_TOKEN}',
        'Content-Type': 'application/json'
    }
    prompt = (
        f"Analyze the following data summary and provide detailed insights, "
        f"focusing on missing values, key correlations, and significant observations:\n\n{analysis}"
    )
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = httpx.post(API_URL, headers=headers, json=data, timeout=30.0)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return "Narrative generation failed due to an error."

def save_markdown(analysis, narrative):
    """Save analysis and narrative to a Markdown file."""
    with open('README.md', 'w') as f:
        f.write("# Data Analysis Report\n\n")
        f.write("## Summary\n\n")
        f.write("### Data Insights\n")
        f.write(str(analysis['summary']) + "\n\n")
        f.write("### Missing Values\n")
        f.write(str(analysis['missing_values']) + "\n\n")
        f.write("### Correlation\n")
        f.write(str(analysis['correlation']) + "\n\n")
        f.write("## Narrative\n\n")
        f.write(narrative + "\n\n")
        f.write("## Visualizations\n")
        for file in os.listdir():
            if file.endswith("_distribution.png"):
                f.write(f"![{file}](./{file})\n")

def main(file_path):
    check_dependencies()  # Ensure all dependencies are installed
    df = load_data(file_path)
    analysis = analyze_data(df)
    visualize_data(df)
    narrative = generate_narrative(analysis)
    save_markdown(analysis, narrative)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <dataset.csv>")
        sys.exit(1)
    main(sys.argv[1])
