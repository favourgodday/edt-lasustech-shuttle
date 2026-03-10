# 🚌 EDT Lasustech Shuttle Bot

**Official WhatsApp-based campus transport system for Lagos State University of Science and Technology (LASUSTECH)**

---

## 🚀 Overview

EDT Lasustech Shuttle is a student-built mobility solution that connects LASUSTECH students with verified keke drivers through WhatsApp. No app download required — just send a message and your ride is booked.

**Built by students, for students.**

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎯 Zone-Based Pricing | Fixed fares (₦125-₦225) — no negotiation |
| 🚗 Automated Driver Assignment | Instant matching with nearest available driver |
| 📊 Real-Time Ride Tracking | Full ride history and spending logs |
| 🎛️ Admin Dashboard | Monitor users, drivers, revenue, and analytics |
| 💰 Driver Earnings Management | Automatic tracking and weekly payout calculations |
| 📱 WhatsApp Integration | No app download — works on any phone |

---

## 🗺️ Zones & Pricing

| Route Type | Destinations | Student Pays | Driver Gets |
|------------|--------------|--------------|-------------|
| 🟢 Short Routes | ICT, Activities Centre | ₦125 | ₦100 |
| 🔵 Standard Routes | All Colleges, Library, Gates | ₦225 | ₦200 |
| 🔵 Inter-College | College to College | ₦200 | ₦175 |

**Platform Fee:** ₦25 per ride (covers server, API, support, and growth)

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3, Flask |
| Database | SQLite (local) → PostgreSQL-ready (cloud) |
| Messaging | Twilio WhatsApp API |
| Hosting | Railway.app (cloud) |
| Version Control | GitHub |

---

## 📋 Student Commands

| Command | Function |
|---------|----------|
| `HI` | Welcome & registration |
| `RIDE` | Book a shuttle |
| `BALANCE` | Check ride credits |
| `BUY` | Purchase rides |
| `ZONES` | View all zones |
| `PRICE` | Pricing breakdown |
| `HISTORY` | Past rides |
| `HELP` | All commands |

---

## 🚗 Driver Commands

| Command | Function |
|---------|----------|
| `DRIVERHI` | Driver dashboard |
| `AVAILABLE` | Go online for rides |
| `BUSY` | Go offline |
| `ZONE [Location]` | Update current zone |
| `MYSTATS` | View earnings & rides |
| `STATUS` | Check current status |

---

## 🎛️ Admin Commands

| Command | Function |
|---------|----------|
| `ADMIN` | Dashboard overview |
| `USERS` | All users list |
| `DRIVERS` | All drivers list |
| `TODAY` | Today's activity |
| `LOWBAL` | Low balance users alert |
| `EXPORT` | Data export report |

---

## 🏗️ Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python edt_shuttle_bot.py