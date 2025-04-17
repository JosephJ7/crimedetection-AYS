
# 📊 Ireland Crime Detection Dashboard

An interactive Streamlit dashboard for visualizing crime statistics in Ireland by offence type and offender age. Integrated with Dagster for running data pipelines.

## 📁 Project Structure


crimedetection-AYS/
├── dashboard/              # Streamlit dashboard app
│   └── app.py              # Main Streamlit app
├── data_pipeline/          # Dagster data pipeline code
│   ├── project_master.py   # Combined Dagster pipeline job
│   └── visualizations.py   # All chart functions used in the dashboard
├── config.py               # Database config (e.g., PostgreSQL engine)
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
└── .venv/                  # (Optional) Virtual environment


## 🚀 Features

- 📈 Interactive visualizations using Plotly and Streamlit
- 🧠 Dagster integration for data pipeline execution
- 🗃️ Filter by offence type, age group, Garda division, and more
- 📊 Line charts, bar charts, heatmaps, area charts, and animations
- ⚙️ Clean sidebar controls for dataset selection and job status



## 🛠️ Installation

### Clone the repository
```bash
git clone https://github.com/<your-username>/crimedetection-AYS.git
cd crimedetection-AYS
```

### Create and activate a virtual environment (optional but recommended)
```bash
python -m venv .venv
source .venv/bin/activate      # On Windows: .venv\Scripts\activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```


## 🧪 Running the App

### 1. Start the Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```

### 2. Run the Dagster Pipeline (manually or via button in UI)
```bash
dagster job execute -f data_pipeline/project_master.py -j combined_pipeline_job
```


## 🧩 Technologies Used

- **Python**
- **Streamlit**
- **Plotly**
- **Dagster**
- **PostgreSQL**
- **pandas**


## 📸 Screenshots

> _(Optional - Add screenshots of your dashboard here for visual context)_


## 🧰 Configuration

Ensure your `config.py` file contains the correct PostgreSQL database configuration:

```python
from sqlalchemy import create_engine

pg_engine = create_engine("postgresql://user:password@localhost:5432/dbname")
```


## 📝 License

This project is licensed under the [MIT License](LICENSE).


## 🙋‍♂️ Author

- **Joseph J.** – [GitHub Profile](https://github.com/JosephJ7)


## 📬 Contact

For feedback, issues, or suggestions:  
📧 josephjacobie2001@gmail.com  
📁 Or create an [issue](https://github.com/JosephJ7/crimedetection-AYS/issues)

