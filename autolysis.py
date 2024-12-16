import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import httpx
import chardet

# Constants
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjIwMDUzNzVAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.7rXDto5TzajWEQEEQYJeScynPwPB1MSK1nXyTJ6hbRk"

# Function Definitions

def load_data(file_path):
    """Load CSV data with encoding detection."""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    try:
        df = pd.read_csv(file_path, encoding=encoding)
        print(f"Data loaded successfully with encoding: {encoding}")
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

def analyze_data(df):
    """Perform comprehensive data analysis."""
    numeric_df = df.select_dtypes(include=['number'])
    analysis = {
        'summary': df.describe(include='all').to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'correlation': numeric_df.corr().to_dict(),
    }
    # Advanced Analysis
    if not numeric_df.empty:
        analysis['variance'] = numeric_df.var().to_dict()
    return analysis

def visualize_data(df):
    """Generate and save visualizations with enhanced annotations."""
    sns.set(style="whitegrid")
    numeric_columns = df.select_dtypes(include=['number']).columns
    for column in numeric_columns:
        plt.figure()
        sns.histplot(df[column].dropna(), kde=True, color="skyblue")
        plt.title(f'Distribution of {column}')
        plt.xlabel(column)
        plt.ylabel('Frequency')
        plt.annotate(f"Mean: {df[column].mean():.2f}", xy=(0.7, 0.9), xycoords='axes fraction', fontsize=10)
        plt.savefig(f'{column}_distribution.png')
        plt.close()

def generate_narrative(analysis):
    """Generate narrative using LLM."""
    headers = {
        'Authorization': f'Bearer {AIPROXY_TOKEN}',
        'Content-Type': 'application/json'
    }
    prompt = (
        f"Generate an analysis based on the following data insights:\n\n"
        f"## Summary:\n{analysis['summary']}\n\n"
        f"## Missing Values:\n{analysis['missing_values']}\n\n"
        f"## Correlation:\n{analysis['correlation']}\n\n"
        f"Highlight key trends, significant findings, and actionable insights."
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

def main(file_path):
    """Main function to orchestrate the analysis."""
    df = load_data(file_path)
    analysis = analyze_data(df)
    visualize_data(df)
    narrative = generate_narrative(analysis)

    # Save narrative to Markdown
    with open('README.md', 'w') as f:
        f.write("# Data Analysis Report\n")
        f.write("## Insights\n")
        f.write(narrative)
        f.write("\n\n## Visualizations\n")
        for column in df.select_dtypes(include=['number']).columns:
            f.write(f"![{column} Distribution](./{column}_distribution.png)\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <dataset.csv>")
        sys.exit(1)
    main(sys.argv[1])
