# 📄 **Complete README.md for Employee Task Approval System**

```markdown
# 📋 Employee Task Approval System

A complete **Employee Task Approval System** built with Django, Kafka (KRaft), Bootstrap, and SQLite. This system allows employees to create tasks and admins to approve/reject them with real-time notifications using Kafka.

---

## 🚀 **Features**

### 👥 **User Management**
- ✅ Custom User Model with Admin/Employee roles
- ✅ User Authentication (Login/Logout)
- ✅ Role-based access control
- ✅ Employee CRUD operations (Admin only)

### 📝 **Task Management**
- ✅ Employees can create tasks
- ✅ Admin can view all tasks
- ✅ Admin can approve/reject tasks
- ✅ Task status tracking (Pending/Approved/Rejected)
- ✅ Real-time notifications via Kafka

### 🔔 **Notifications**
- ✅ Admin gets notification when task is created
- ✅ Employee gets notification when task is approved/rejected
- ✅ Real-time notification updates
- ✅ Mark notifications as read

### 📊 **Analytics Dashboard**
- ✅ Task status distribution chart (Pie chart)
- ✅ Employee performance chart (Bar chart)
- ✅ Daily activity trends (Line chart)
- ✅ Employee performance table
- ✅ Recent activity log
- ✅ CSV/Excel/JSON export

### 💀 **Dead Letter Queue (DLQ)**
- ✅ Automatic retry mechanism (3 attempts)
- ✅ DLQ for failed messages
- ✅ DLQ monitoring dashboard
- ✅ Manual reprocess from UI
- ✅ Critical alerts for permanent failures

### 📈 **Kafka Integration**
- ✅ Event-driven architecture
- ✅ Multiple topics (task-created, task-approved, task-rejected, task-dlq)
- ✅ Multiple consumer groups
- ✅ Message persistence
- ✅ Fault tolerance

---

## 🏗️ **Technology Stack**

| Technology | Purpose |
|------------|---------|
| **Django 4.2** | Web Framework |
| **Kafka (KRaft)** | Message Queue |
| **SQLite** | Database |
| **Bootstrap 5** | Frontend UI |
| **Chart.js** | Charts & Graphs |
| **jQuery** | AJAX calls |
| **openpyxl** | Excel export |

---

## 📁 **Project Structure**

```
employee_task_system/
│
├── manage.py
├── requirements.txt
├── db.sqlite3
│
├── config/
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URLs
│   └── wsgi.py
│
├── accounts/
│   ├── models.py            # Custom User model
│   ├── views.py             # Auth & user management
│   ├── urls.py
│   └── admin.py
│
├── task/
│   ├── models.py            # Task model
│   ├── views.py             # Task CRUD operations
│   ├── urls.py
│   ├── producer.py          # Kafka producer with DLQ
│   ├── consumer.py          # Task consumer (console display)
│   └── dlq_consumer.py      # DLQ consumer
│
├── notification/
│   ├── models.py            # Notification model
│   ├── views.py             # Notification endpoints
│   ├── urls.py
│   └── consumer.py          # Notification consumer
│
├── analytics/
│   ├── models.py            # Analytics & DLQLog models
│   ├── views.py             # Analytics & DLQ dashboard
│   ├── urls.py
│   └── consumer.py          # Analytics consumer
│
└── templates/
    ├── login.html
    ├── admin_dashboard.html
    ├── employee_dashboard.html
    ├── analytics_dashboard.html
    └── dlq_dashboard.html
```

---

## 📊 **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                                     │
│                                                                             │
│  ┌──────────────┐              ┌──────────────┐                         │
│  │   Employee   │              │    Admin     │                         │
│  │  Dashboard   │              │  Dashboard   │                         │
│  └──────┬───────┘              └──────┬───────┘                         │
│         │                              │                                 │
│         │ Create Task                  │ Approve/Reject Task             │
│         ▼                              ▼                                 │
└─────────┼──────────────────────────────┼─────────────────────────────────┘
          │                              │
          ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DJANGO BACKEND                                     │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  accounts/   │  │    task/     │  │ notification/│  │  analytics/  │ │
│  │   Views.py   │  │   Views.py   │  │   Views.py   │  │   Views.py   │ │
│  └──────────────┘  └──────┬───────┘  └──────────────┘  └──────────────┘ │
│                           │                                                 │
│                           ▼                                                 │
│                    ┌──────────────┐                                        │
│                    │  Producer.py │  ← Sends messages to Kafka            │
│                    └──────┬───────┘                                        │
└───────────────────────────┼─────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         KAFKA (KRaft)                                      │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ task-created │  │task-approved │  │task-rejected │  │  task-dlq    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CONSUMERS                                          │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   task/      │  │ notification/│  │  analytics/  │  │    dlq/      │ │
│  │ consumer.py  │  │  consumer.py │  │  consumer.py │  │  consumer.py │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 **Installation Guide**

### **Prerequisites**
- Python 3.8+
- Kafka (KRaft)
- Virtual Environment

### **Step 1: Clone the Repository**
```bash
git clone <repository-url>
cd employee_task_system
```

### **Step 2: Create Virtual Environment**
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### **Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 4: Run Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

### **Step 5: Create Superuser**
```bash
python manage.py createsuperuser
```

### **Step 6: Start Kafka**
```bash
cd /path/to/kafka
bin/kafka-server-start.sh config/server.properties
```

### **Step 7: Create Kafka Topics**
```bash
bin/kafka-topics.sh --create --topic task-created --bootstrap-server localhost:9092
bin/kafka-topics.sh --create --topic task-approved --bootstrap-server localhost:9092
bin/kafka-topics.sh --create --topic task-rejected --bootstrap-server localhost:9092
bin/kafka-topics.sh --create --topic task-dlq --bootstrap-server localhost:9092
```

### **Step 8: Start Consumers**
```bash
# Terminal 1 - Task Consumer
python task/consumer.py

# Terminal 2 - DLQ Consumer
python task/dlq_consumer.py

# Terminal 3 - Notification Consumer
python notification/consumer.py

# Terminal 4 - Analytics Consumer
python analytics/consumer.py
```

### **Step 9: Start Django Server**
```bash
python manage.py runserver
```

### **Step 10: Access Application**
```
http://localhost:8000
```

---

## 🔧 **Configuration**

### **Kafka Configuration (config/settings.py)**
```python
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'

KAFKA_TOPICS = {
    'task_created': 'task-created',
    'task_approved': 'task-approved',
    'task_rejected': 'task-rejected',
    'task_dlq': 'task-dlq',
    'notification_dlq': 'notification-dlq',
}

# Retry Configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_MS = 1000
```

---

## 🧪 **Testing**

### **Test Flow**
1. **Login as Admin** → `admin / admin123`
2. **Create Employee** → From Admin Dashboard
3. **Login as Employee** → `employee / employee123`
4. **Create Task** → From Employee Dashboard
5. **Admin Approves Task** → From Admin Dashboard
6. **Employee Gets Notification** → Real-time notification

### **Test Kafka Failure**
```bash
# 1. Stop Kafka
# 2. Create a task (will go to DLQ)
# 3. Check DLQ dashboard: http://localhost:8000/analytics/dlq/
# 4. Restart Kafka
# 5. Click "Reprocess" to send message again
```

### **Test Analytics**
```bash
# 1. Create some tasks
# 2. Approve/Reject some tasks
# 3. Visit: http://localhost:8000/analytics/dashboard/
# 4. See charts and statistics
```

---

## 📊 **API Endpoints**

### **Authentication**
```
POST /login/        - Login user
GET  /logout/       - Logout user
```

### **Employee Management (Admin only)**
```
GET  /accounts/api/employees/              - Get all employees
POST /accounts/api/employees/create/       - Create employee
POST /accounts/api/employees/{id}/update/  - Update employee
DELETE /accounts/api/employees/{id}/delete/ - Delete employee
POST /accounts/api/users/{id}/change-role/ - Change user role
```

### **Task Management**
```
POST /task/create/           - Create a new task
GET  /task/tasks/            - Get all tasks
GET  /task/pending/          - Get pending tasks (Admin)
POST /task/{id}/approve/     - Approve/Reject task (Admin)
```

### **Notifications**
```
GET  /notification/notifications/      - Get unread notifications
POST /notification/{id}/read/          - Mark notification as read
POST /notification/read-all/           - Mark all as read
GET  /notification/unread-count/       - Get unread count
```

### **Analytics**
```
GET  /analytics/dashboard/           - Analytics dashboard
GET  /analytics/dlq/                 - DLQ dashboard
POST /analytics/dlq/{id}/reprocess/  - Reprocess DLQ message
GET  /analytics/download/csv/        - Download CSV
GET  /analytics/download/excel/      - Download Excel
GET  /analytics/download/json/       - Download JSON
```

---

## 🐛 **Troubleshooting**

### **Kafka Connection Error**
```bash
# Check if Kafka is running
ps aux | grep kafka

# Check port
netstat -tlnp | grep 9092

# Restart Kafka
bin/kafka-server-start.sh config/server.properties
```

### **Consumer Not Working**
```bash
# Check consumer logs
tail -f task_errors.log

# Restart consumer
python task/consumer.py
```

### **DLQ Not Showing Data**
```bash
# Check DLQ topic
bin/kafka-console-consumer.sh --topic task-dlq --bootstrap-server localhost:9092 --from-beginning

# Check DLQLog in database
python manage.py shell
>>> from analytics.models import DLQLog
>>> DLQLog.objects.all()
```

### **CSRF Error**
```bash
# Clear browser cache and cookies
# Re-login
```

---

## 📝 **Access Credentials**

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Employee | employee | employee123 |

---

## 🚀 **Production Deployment**

### **Using Docker**
```yaml
# docker-compose.yml
version: '3.8'
services:
  kafka:
    image: apache/kafka:latest
    ports:
      - "9092:9092"
  
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - kafka
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
```

### **Using Supervisor (Process Management)**
```ini
# /etc/supervisor/conf.d/task_system.conf
[program:task_consumer]
command=python /path/to/task/consumer.py
directory=/path/to/project
autostart=true
autorestart=true

[program:dlq_consumer]
command=python /path/to/task/dlq_consumer.py
directory=/path/to/project
autostart=true
autorestart=true

[program:notification_consumer]
command=python /path/to/notification/consumer.py
directory=/path/to/project
autostart=true
autorestart=true

[program:analytics_consumer]
command=python /path/to/analytics/consumer.py
directory=/path/to/project
autostart=true
autorestart=true

[program:django]
command=gunicorn config.wsgi:application
directory=/path/to/project
autostart=true
autorestart=true
```

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📄 **License**

This project is licensed under the MIT License.

---

## 📧 **Contact**

For any queries, please contact:
- Email: your-email@example.com
- GitHub: your-username

---

## 🙏 **Acknowledgments**

- Django Framework
- Apache Kafka
- Bootstrap
- Chart.js
- All open-source libraries used

---

## 📊 **Key Features Summary**

| Feature | Status | Description |
|---------|--------|-------------|
| User Authentication | ✅ | Login/Logout with roles |
| Employee Management | ✅ | CRUD operations (Admin) |
| Task Creation | ✅ | Employees can create tasks |
| Task Approval | ✅ | Admin approves/rejects |
| Real-time Notifications | ✅ | Kafka-powered notifications |
| Analytics Dashboard | ✅ | Charts, tables, filters |
| CSV/Excel/JSON Export | ✅ | Download analytics data |
| DLQ (Dead Letter Queue) | ✅ | Automatic retry + manual reprocess |
| Kafka Integration | ✅ | Event-driven architecture |
| Bootstrap UI | ✅ | Responsive design |

---

## 🎯 **Quick Start Commands**

```bash
# Clone and setup
git clone <repo>
cd employee_task_system
python -m venv env
source env/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser

# Start Kafka
bin/kafka-server-start.sh config/server.properties

# Start consumers
python task/consumer.py &
python task/dlq_consumer.py &
python notification/consumer.py &
python analytics/consumer.py &

# Start Django
python manage.py runserver

# Access application
# http://localhost:8000
```

---

## 🎉 **Thank You!**


```