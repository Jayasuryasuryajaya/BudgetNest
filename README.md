# BudgetNest - Financial Management Platform

BudgetNest is a comprehensive platform for managing personal and family finances. It provides tools for tracking budgets, managing investments, and generating financial reports. The platform integrates with real-time financial data from Alpha Vantage and Finnhub APIs.

---

## Features
- **Personal and Family Budgeting**: Track income, expenses, and savings. Users can manage their financial goals and generate detailed reports.
- **Investment Tracking**: Manage your investment portfolio with real-time market data from Alpha Vantage and Finnhub APIs.
- **Transaction Management**: Record and manage various types of transactions, including recurring, future, and one-time transactions.
- **Savings Challenges**: Set financial goals and track your savings progress.
- **Expense Reports**: Generate detailed financial reports on personal and family finances.

---

## Prerequisites
- **Python 3.8+**
- **Django 4.x+**
- **PostgreSQL** (or another relational database for production)
- API keys for [Alpha Vantage](https://www.alphavantage.co/) and [Finnhub](https://finnhub.io/).

---

## Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/budgetnest.git
cd budgetnest
```

### Step 2: Create and Activate a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate   # For Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the project root with the following content:
```bash
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
FINHUB_API_KEY=your_finhub_api_key_here
```

### Step 5: Configure the Database
Edit the `settings.py` file to configure the database connection (e.g., PostgreSQL, SQLite). Then, apply the migrations:
```bash
python manage.py migrate
```

### Step 6: Create a Superuser (for Admin Access)
```bash
python manage.py createsuperuser
```

### Step 7: Run the Development Server
```bash
python manage.py runserver
```
### Step 8:
Access the platform at `http://127.0.0.1:8000/`.

**To use the platform's services, you need to register; you cannot use the superuser created previously.**

---

## APIs Used

### 1. Alpha Vantage API
Alpha Vantage provides real-time and historical data for stocks, foreign exchange, and cryptocurrencies.
- [API Documentation](https://www.alphavantage.co/documentation/)
- [Get Your API Key](https://www.alphavantage.co/support/#api-key)

### 2. Finnhub API
Finnhub offers market data for stocks, forex, cryptocurrencies, and more.
- [API Documentation](https://finnhub.io/docs/api)
- [Get Your API Key](https://finnhub.io/register)

---

## Usage

After setting up the project, you can access different functionalities of BudgetNest:

1. **Personal and Family Budgeting**: Manage your income, expenses, and savings under separate accounts.
2. **Transaction Management**: Add, edit, and delete various types of transactions, including future and recurring transactions.
3. **Investment Tracking**: Get real-time updates on your stock and cryptocurrency investments using the integrated APIs.
4. **Reports**: Generate comprehensive financial reports on personal and family finances.

---

## Contributing

Contributions are welcome! Please follow these steps to contribute:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

---

## Contact

For any questions, suggestions, or feedback, feel free to contact the project maintainers at:
- **Email**: giacomo.bia.co@gmail.com
