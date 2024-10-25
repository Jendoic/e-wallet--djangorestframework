# E-Wallet API

This project is an e-wallet API built using Django REST Framework. It allows users to perform basic wallet functionalities such as depositing, withdrawing, transferring funds, and viewing transaction history. The API also includes real-time notifications and asynchronous tasks using Celery and Redis.

## Features

- **User Registration and Authentication**: Secure user registration and login functionalities.
- **Deposit Functionality**: Allows users to deposit funds into their wallets via the Paystack payment gateway.
- **Withdrawal Functionality**: Users can withdraw funds from their wallets, with transaction processing and email notifications.
- **Transfer Between Wallets**: Users can transfer funds to other users' wallets.
- **Transaction History**: View transaction history with filters for transaction type, status, and date range.
- **Real-time Notifications**: Users receive real-time notifications for withdrawals, deposits, and transfers.
- **Asynchronous Email Notifications**: Celery is used for sending emails for transactions such as withdrawals and deposits in the background.

## Tech Stack

- **Backend Framework**: Django REST Framework
- **Real-time Notifications**: Django Channels and WebSockets
- **Task Queue**: Celery
- **Message Broker**: Redis
- **Payment Gateway**: Paystack

## Getting Started

### Prerequisites

- Python 3.x
- Django 4.x
- Redis
- Celery
- Docker (Optional, for containerized setup)

### Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/e-wallet-api.git
    cd e-wallet-api
    ```

2. **Set up virtual environment**:
    ```bash
    python3 -m venv env
    source env/bin/activate
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables**:

    Create a `.env` file in the root directory and configure the following:

    ```env
    SECRET_KEY=your_secret_key
    DEBUG=True
    ALLOWED_HOSTS=localhost,127.0.0.1

    # Paystack
    PAYSTACK_SECRET_KEY=your_paystack_secret_key
    PAYSTACK_PUBLIC_KEY=your_paystack_public_key

    # Celery
    CELERY_BROKER_URL=redis://localhost:6379/0
    CELERY_RESULT_BACKEND=redis://localhost:6379/0

    # Database (default is SQLite, configure if using another DB)
    ```

5. **Run database migrations**:
    ```bash
    python manage.py migrate
    ```

6. **Create a superuser**:
    ```bash
    python manage.py createsuperuser
    ```

7. **Start Django development server**:
    ```bash
    python manage.py runserver
    ```

8. **Start Redis** (Ensure Redis is running, or use Docker to start Redis):
    ```bash
    redis-server
    ```

9. **Start Celery worker**:
    ```bash
    celery -A core worker --loglevel=info
    ```

10. **Run Daphne (for real-time WebSocket notifications)**:
    ```bash
    daphne -p 8000 core.asgi:application
    ```

### API Endpoints

1. **User Registration and Login**:
    - `POST /api/v1/register/`: Register a new user.
    - `POST /api/v1/login/`: Log in an existing user.

2. **Deposit Funds**:
    - `POST /api/v1/deposit/`: Deposit money into the wallet using Paystack.

3. **Withdraw Funds**:
    - `POST /api/v1/withdraw/`: Withdraw money from the wallet.

4. **Transfer Funds**:
    - `POST /api/v1/transfer/`: Transfer money to another user's wallet.

5. **Transaction History**:
    - `GET /api/v1/transactions/`: View transaction history with filters.

### Real-time Notifications

- WebSocket endpoint: `ws://localhost:8000/ws/notifications/`
- Users receive real-time notifications on successful deposits, withdrawals, and transfers.

### Testing

- Use Postman or curl to test the API endpoints.
- For real-time notifications, connect via WebSockets using the provided WebSocket endpoint.

