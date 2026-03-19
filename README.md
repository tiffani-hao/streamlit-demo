# CUSUM Application demo (Streamlit)

This is a simple demo for demonstration purposes only.

It uses a mock CUSUM algorithm, and the current outputs and visualizations are only prototypes meant to show what the workflow could look like.

---

## What the app demo does 

- Upload a CSV file with monthly case counts
- Run a mock CUSUM calculation =
- Detect possible alerts 
- Show two plots:
  - case counts vs baseline
  - CUSUM monitoring statistic
- Display a summary table of alerts by county

Everything runs locally.

---

## Example data format

The app expects a CSV file with this structure:

```
month,county,cases  
2020-01,King,22  
2020-02,King,21  
2020-03,King,23  
2020-01,Pierce,9  
2020-02,Pierce,8
...
```

Columns:

- **month** → month in `YYYY-MM` format  
- **county** → county name  
- **cases** → case count for that month  

A synthetic dataset is included: ```sample_hiv_2020_2024.csv```

---

## Requirements

Python 3.9 or newer is required.

You can check if Python is installed by running: ```python --version``` in your terminal

If Python is not installed, download it from:
https://www.python.org/downloads/

---

## How to run the app

### 1. Download the project

Either clone the repo:

```
  git clone https://github.com/tiffani-hao/hiv-cusum-demo.git
  
  cd hiv-cusum-demo
```

or download the ZIP from GitHub.

---

### 2. Create a virtual environment

Create the environment: ```python -m venv venv```

Activate it:

Mac / Linux: ```source venv/bin/activate```

windows: ```source venv/bin/activate```

---

### 3. Install required packages

```
pip install -r requirements.txt
```

---

### 4. Run the application

```
python -m streamlit run app.py
```

Then open:
```
http://localhost:8501
```

Upload a dataset and the dashboard will generate alerts and plots.

---

### 5. Quit the application

```
ctrl + c
```

or just close everything

---

## Project structure
```
app.py
mock_algo.py
sample_hiv_2020_2024.csv
requirements.txt
README.md
```

---

## Author

Tiffani Hao  