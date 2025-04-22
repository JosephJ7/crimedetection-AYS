
# 📊 Ireland Crime Detection Dashboard

An interactive Streamlit dashboard for visualizing crime statistics in Ireland by offence type and offender age. Integrated with Dagster for running data pipelines.

## 📁 Project Structure

```bash
crimedetection-AYS/
├── dashboard/              # Streamlit dashboard app
│   └── dashboard.py        # Main Streamlit app
├── data_pipeline/          # Dagster data pipeline code
│   ├── project_master.py   # Combined Dagster pipeline job
│   ├── dagster_pipe.py     # Individual Dagster pipeline job
│   ├── repository.py       # Repository Definition 
│   └── visualizations.py   # All chart functions used in the dashboard
├── config.py               # Database config (e.g., PostgreSQL engine,MongoDB)
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
└── .venv/                  # Virtual environment (to be created by user)
└── workspace.yaml          # Connects Dagster to pipeline code.
```

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

### Create and activate a virtual environment (Python 3.12)

```bash
# Create virtual environment using Python 3.12
python3.12 -m venv .venv
```

### Activate the virtual environment

#### On macOS/Linux:
```bash
source .venv/bin/activate
```

#### On Windows:
```bash
.venv\Scripts\activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```
## 🧰 Configuration

Ensure your `config.py` file contains the correct PostgreSQL database configuration and MongoDB configuration :

```python
from pymongo import MongoClient
from sqlalchemy import create_engine

# MongoDB connection 
MONGO_URI = <your-mongoDB-connection-string> 
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[<your-database-name>]


# PostgreSQL connection string
PG_CONN_STRING = "postgresql://<your-db-user-name>:<your-db-password>@localhost:5432/<your-database-name>"
pg_engine = create_engine(PG_CONN_STRING)
```

## 🧪 Running the App

### 1. Start the Streamlit Dashboard
```bash
streamlit run .\dashboard\dashboard.py
```

### 2. Run the Dagster Pipeline (manually or via button in UI)
#### To run the pipeline manually:
```bash
dagster job execute -f data_pipeline/project_master.py -j combined_pipeline_job
```
Alternatively, click the "🚀 Run Dagster Job" button from the sidebar in the dashboard to trigger it.


## 🧩 Technologies Used

- **Python**
- **Streamlit**
- **Plotly**
- **Dagster**
- **PostgreSQL**
- **MongoDB**
- **pandas**


## 📸 Screenshots

![alt text](dashboard.png)



## 📜 License

This project is licensed under the [MIT License](LICENSE).


## 🙋‍♂️ Author

- **Joseph J.** – [GitHub Profile](https://github.com/JosephJ7)


## 📬 Contact

For feedback, issues, or suggestions:  
📧 josephjacobie2001@gmail.com  
📁 Or create an [issue](https://github.com/JosephJ7/crimedetection-AYS/issues)

