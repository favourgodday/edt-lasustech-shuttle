from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from database import EDTShuttleDB
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ===== INITIALIZE DATABASE =====
db = EDTShuttleDB()

# ===== CONFIGURATION =====
ADMIN_PHONE_NUMBER = os.getenv('ADMIN_PHONE', 'whatsapp:+2349081617382')

# ===== ZONE DEFINITIONS =====
SHORT_ZONES = ['ICT', 'Activities Centre', 'Activities']
GATES = ['First Gate', 'Shuttle Park', 'Second Gate', 'Third Gate']
STANDARD_ZONES = [
    'College of Agriculture',
    'College of Applied Social Sciences',
    'College of Basic Sciences',
    'College of Engineering and Technology',
    'College of Environmental Design and Technology',
    'Library'
]

ALL_ZONES = SHORT_ZONES + GATES + STANDARD_ZONES

# ===== PRICING LOGIC =====
def calculate_fare(pickup, dropoff):
    """Calculate fare based on zone rules"""
    p = pickup.lower()
    d = dropoff.lower()
    
    short_zones_lower = [z.lower() for z in SHORT_ZONES]
    gates_lower = [z.lower() for z in GATES]
    standard_zones_lower = [z.lower() for z in STANDARD_ZONES]
    
    # Rule 1: Gate ↔ Short Zone = ₦125
    if (p in gates_lower and d in short_zones_lower) or (d in gates_lower and p in short_zones_lower):
        return 125, 100  # (student_pays, driver_gets)
    
    # Rule 2: Short ↔ Short = ₦125
    if p in short_zones_lower and d in short_zones_lower:
        return 125, 100
    
    # Rule 3: Gate ↔ Standard Zone = ₦225
    if (p in gates_lower and d in standard_zones_lower) or (d in gates_lower and p in standard_zones_lower):
        return 225, 200
    
    # Rule 4: Inter-College/Zone = ₦200
    return 200, 175

# ===== CONVERSATION STATE =====
conversation_state = {}

@app.route("/whatsapp", methods=['POST'])
def whatsapp_bot():
    """EDT Lasustech Shuttle Bot - Zone-Based Campus Transport"""
    
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    
    print(f"📩 Received from {sender}: {incoming_msg}")
    
    resp = MessagingResponse()
    msg = resp.message()
    
    # Get or create user
    user = db.get_user(sender)
    if not user:
        db.create_user(sender)
        user = db.get_user(sender)
    
    # Get conversation state
    if sender not in conversation_state:
        conversation_state[sender] = {'state': 'idle'}
    
    state = conversation_state[sender]
    command = incoming_msg.upper()
    
    # ==================== DRIVER COMMANDS ====================
    
    if command.startswith('REGISTERDRIVER'):
        if sender == ADMIN_PHONE_NUMBER:
            parts = incoming_msg.split()
            if len(parts) >= 5:
                name = parts[1]
                phone = parts[2]
                if not phone.startswith('whatsapp:'):
                    phone = f'whatsapp:{phone}'
                contact = parts[3].lower()
                zone = parts[4]
                device = parts[5].lower() if len(parts) > 5 else 'smartphone'
                vehicle = parts[6] if len(parts) > 6 else 'Keke'
                
                if db.add_driver(name, phone, contact, zone, device, vehicle):
                    response = f"""✅ *DRIVER REGISTERED!*

👤 Name: {name}
📞 Phone: {phone}
📱 Contact: {contact.upper()}
📍 Zone: {zone}
🔧 Device: {device.upper()}
🚗 Vehicle: {vehicle.upper()}

Driver can now receive ride notifications! 🚀"""
                else:
                    response = "❌ Driver already exists."
            else:
                response = """❌ *FORMAT ERROR*

REGISTERDRIVER Name Phone Contact Zone Device Vehicle

Example:
REGISTERDRIVER Musa +2348012345678 whatsapp Engineering smartphone Keke"""
        else:
            response = "❌ Admin only."
        
        msg.body(response)
        return str(resp)
    
    if command == 'DRIVERHI':
        driver = db.get_driver(sender)
        if driver:
            response = f"""🚗 *WELCOME BACK, {driver['name'].upper()}!*

*Your Status:*
{'🟢 Available' if driver['is_available'] else '🔴 Busy'}
📍 Zone: {driver['current_zone']}
🚗 Vehicle: {driver['vehicle_type']}

*Career Stats:*
✅ Rides: {driver['total_rides_completed']}
💰 Earnings: ₦{driver['total_earnings']:,.0f}

*Commands:*
AVAILABLE - Go online
BUSY - Go offline
ZONE [Location] - Update zone
MYSTATS - Detailed stats"""
        else:
            response = """🚗 *DRIVER REGISTRATION*

Not registered yet. Contact admin:
+2349081617382"""
        
        msg.body(response)
        return str(resp)
    
    if command == 'AVAILABLE':
        driver = db.get_driver(sender)
        if driver:
            db.mark_driver_available(sender)
            response = f"""✅ *YOU'RE NOW AVAILABLE!*

🟢 Online for rides
📍 Zone: {driver['current_zone']}

Type BUSY to go offline."""
        else:
            response = "❌ Not registered as driver."
        
        msg.body(response)
        return str(resp)
    
    if command == 'BUSY':
        driver = db.get_driver(sender)
        if driver:
            db.mark_driver_busy(sender)
            response = f"""🔴 *YOU'RE NOW BUSY*

Offline - won't receive rides

Type AVAILABLE to go back online."""
        else:
            response = "❌ Not registered as driver."
        
        msg.body(response)
        return str(resp)
    
    if command.startswith('ZONE '):
        driver = db.get_driver(sender)
        if driver:
            parts = incoming_msg.split(maxsplit=1)
            if len(parts) >= 2:
                new_zone = parts[1].title()
                db.update_driver_zone(sender, new_zone)
                response = f"""✅ *ZONE UPDATED!*

📍 New Zone: {new_zone}

Type AVAILABLE to start receiving rides."""
            else:
                response = "❌ Specify zone. Example: ZONE Engineering"
        else:
            response = "❌ Not registered as driver."
        
        msg.body(response)
        return str(resp)
    
    if command == 'MYSTATS':
        driver = db.get_driver(sender)
        if driver:
            response = f"""📊 *YOUR DRIVER STATS*

👤 {driver['name']}
📍 Zone: {driver['current_zone']}

*TOTALS:*
✅ Rides: {driver['total_rides_completed']}
💰 Earnings: ₦{driver['total_earnings']:,.0f}

*BREAKDOWN:*
Your cut varies by route:
- Short routes: ₦100/ride
- Standard routes: ₦200/ride
- Inter-college: ₦175/ride

Contact admin for payout."""
        else:
            response = "❌ Not registered as driver."
        
        msg.body(response)
        return str(resp)
    
    if command == 'STATUS':
        driver = db.get_driver(sender)
        if driver:
            status_emoji = "🟢" if driver['is_available'] else "🔴"
            status_text = "Available" if driver['is_available'] else "Busy"
            
            response = f"""📍 *YOUR CURRENT STATUS*

{status_emoji} Status: {status_text}
📍 Zone: {driver['current_zone']}
🚗 Vehicle: {driver['vehicle_type']}
📱 Device: {driver['device_type']}

*Quick Actions:*
AVAILABLE - Go online
BUSY - Go offline
ZONE [Location] - Change zone
MYSTATS - View earnings"""
        else:
            response = "❌ Not registered as driver."
        
        msg.body(response)
        return str(resp)
    
    # ==================== STUDENT COMMANDS ====================
    
    if command in ['HI', 'HELLO', 'START', 'HEY', 'JOIN']:
        if not user['name']:
            response = """🚌 *WELCOME TO EDT LASUSTECH SHUTTLE!*

Your official campus transport system.

What's your name?

(Just reply with your first name)"""
            state['state'] = 'awaiting_name'
        else:
            response = f"""🚌 *WELCOME BACK, {user['name'].upper()}!*

Official LASUSTECH campus shuttle service.

*Your Account:*
Rides left: {user['rides_left']}
Total spent: ₦{user['total_spent']:,.0f}

*Zone-Based Pricing:*
🟢 Short Routes (ICT/Activities) = ₦125
🔵 Standard Routes (Colleges/Library) = ₦225
🔵 Inter-College Routes = ₦200

*Commands:*
RIDE - Book a shuttle
BALANCE - Check rides
BUY - Purchase rides
ZONES - See all zones
PRICE - Pricing breakdown
HELP - All commands

Type RIDE to book now! 🚀"""
        
        msg.body(response)
        return str(resp)
    
    if state.get('state') == 'awaiting_name':
        name = incoming_msg.title()
        db.update_user_name(sender, name)
        
        response = f"""✅ *Welcome, {name}!*

Your account is ready! 🎉

*Zone-Based Pricing:*
🟢 Short Routes (ICT/Activities) = ₦125
🔵 Standard Routes (Colleges/Library) = ₦225
🔵 Inter-College Routes = ₦200

*Commands:*
RIDE - Book shuttle
BUY - Purchase rides
ZONES - See all zones
PRICE - Pricing breakdown
HELP - All commands

Type RIDE to start! 🚌"""
        
        state['state'] = 'idle'
        msg.body(response)
        return str(resp)
    
    if command == 'ZONES':
        response = """📍 *OFFICIAL SHUTTLE ZONES*

🟢 *SHORT ROUTES (₦125):*
- ICT
- Activities Centre

🔵 *STANDARD ROUTES (₦225):*
- College of Agriculture
- College of Applied Social Sciences
- College of Basic Sciences
- College of Engineering and Technology
- College of Environmental Design and Technology
- Library

🔵 *GATES (₦225):*
- First Gate / Shuttle Park
- Second Gate
- Third Gate

*INTER-COLLEGE:* ₦200
(e.g., Engineering ↔ Agriculture)

Type RIDE to book! 🚌"""
        
        msg.body(response)
        return str(resp)
    
    if command == 'PRICE' or command == 'PRICING':
        response = """💰 *WHERE YOUR MONEY GOES*

🟢 *SHORT ROUTES (₦125):*
₦100 → Driver
₦25 → Platform

🔵 *STANDARD ROUTES (₦225):*
₦200 → Driver
₦25 → Platform

🔵 *INTER-COLLEGE (₦200):*
₦175 → Driver
₦25 → Platform

*What the ₦25 covers:*
📱 WhatsApp bot maintenance
☁️ Server & database hosting
🔧 24/7 system uptime
🛡️ Driver verification
📊 Ride tracking & history
💬 Customer support

Fair, transparent, reliable! ✨"""
        
        msg.body(response)
        return str(resp)
    
    if command == 'RIDE':
        user = db.get_user(sender)
        
        if user['rides_left'] <= 0:
            response = """❌ *No rides left!*

Type BUY to purchase rides.

Pricing starts at ₦125! 🚌"""
        else:
            response = f"""🚌 *WHERE ARE YOU, {user['name']}?*

Select your PICKUP location:

🟢 *SHORT ZONES:*
1. ICT
2. Activities Centre

🔵 *COLLEGES:*
3. Agriculture
4. Applied Social Sciences
5. Basic Sciences
6. Engineering and Technology
7. Environmental Design and Technology

🔵 *OTHER:*
8. Library
9. First Gate / Shuttle Park
10. Second Gate
11. Third Gate

Reply with the NUMBER (1-11)"""
            
            state['state'] = 'awaiting_pickup'
        
        msg.body(response)
        return str(resp)
    
    if state.get('state') == 'awaiting_pickup':
        zone_map = {
            '1': 'ICT',
            '2': 'Activities Centre',
            '3': 'College of Agriculture',
            '4': 'College of Applied Social Sciences',
            '5': 'College of Basic Sciences',
            '6': 'College of Engineering and Technology',
            '7': 'College of Environmental Design and Technology',
            '8': 'Library',
            '9': 'First Gate',
            '10': 'Second Gate',
            '11': 'Third Gate'
        }
        
        if incoming_msg in zone_map:
            pickup = zone_map[incoming_msg]
            state['pickup'] = pickup
            
            response = f"""✅ Pickup: *{pickup}*

Now, where are you GOING?

🟢 *SHORT ZONES:*
1. ICT
2. Activities Centre

🔵 *COLLEGES:*
3. Agriculture
4. Applied Social Sciences
5. Basic Sciences
6. Engineering and Technology
7. Environmental Design and Technology

🔵 *OTHER:*
8. Library
9. First Gate / Shuttle Park
10. Second Gate
11. Third Gate

Reply with the NUMBER (1-11)"""
            
            state['state'] = 'awaiting_dropoff'
        else:
            response = "❌ Invalid option. Reply with a number (1-11):"
        
        msg.body(response)
        return str(resp)
    
    if state.get('state') == 'awaiting_dropoff':
        zone_map = {
            '1': 'ICT',
            '2': 'Activities Centre',
            '3': 'College of Agriculture',
            '4': 'College of Applied Social Sciences',
            '5': 'College of Basic Sciences',
            '6': 'College of Engineering and Technology',
            '7': 'College of Environmental Design and Technology',
            '8': 'Library',
            '9': 'First Gate',
            '10': 'Second Gate',
            '11': 'Third Gate'
        }
        
        if incoming_msg in zone_map:
            dropoff = zone_map[incoming_msg]
            pickup = state['pickup']
            
            if pickup.lower() == dropoff.lower():
                response = "❌ Pickup and drop-off can't be the same!\n\nType RIDE to start over."
                state['state'] = 'idle'
            else:
                student_fare, driver_pay = calculate_fare(pickup, dropoff)
                
                state['dropoff'] = dropoff
                state['fare'] = student_fare
                state['driver_pay'] = driver_pay
                
                response = f"""📍 *ROUTE SUMMARY*

🔼 From: {pickup}
🔽 To: {dropoff}

💰 Fare: ₦{student_fare}

Any specific drop-off instructions for the driver?

Reply:
- SKIP - No special instructions
- Or type your note (e.g., "Near the cafeteria")"""
                
                state['state'] = 'awaiting_instructions'
        else:
            response = "❌ Invalid option. Reply with a number (1-11):"
        
        msg.body(response)
        return str(resp)
    
    if state.get('state') == 'awaiting_instructions':
        instructions = incoming_msg if incoming_msg.upper() != 'SKIP' else None
        
        pickup = state['pickup']
        dropoff = state['dropoff']
        fare = state['fare']
        driver_pay = state['driver_pay']
        
        # Find available driver
        drivers = db.get_available_drivers(zone=pickup)
        
        if not drivers:
            response = f"""⚠️ *NO DRIVERS AVAILABLE*

📍 Route: {pickup} → {dropoff}

No drivers online in {pickup} area right now.

*Your ride was NOT deducted!*

Try again in a few minutes.
Type RIDE to retry."""
            
            state['state'] = 'idle'
        else:
            driver_name, driver_phone, driver_pref, device_type, vehicle_type = drivers[0]
            
            # Deduct ride
            db.use_ride(sender)
            
            # Mark driver busy
            db.mark_driver_busy(driver_phone)
            
            # Record ride
            db.record_ride(sender, f"{pickup} → {dropoff}", fare, driver_phone, driver_name)
            
            # Update driver earnings
            db.update_driver_earnings(driver_phone, driver_pay)
            
            # Get updated balance
            user = db.get_user(sender)
            
            inst_text = f"\n📝 Note: {instructions}" if instructions else ""
            
            response = f"""✅ *SHUTTLE CONFIRMED!*

📍 Route: {pickup} → {dropoff}
💰 Fare: ₦{fare}
⏱️ ETA: 3-5 minutes

🚗 Driver: {driver_name} ({vehicle_type})
📞 Contact: {driver_phone}{inst_text}

*Rides remaining:* {user['rides_left']}

Your driver has been notified! 🚀"""
            
            state['state'] = 'idle'
            state.pop('pickup', None)
            state.pop('dropoff', None)
            state.pop('fare', None)
            state.pop('driver_pay', None)
        
        msg.body(response)
        return str(resp)
    
    if command == 'BALANCE':
        user = db.get_user(sender)
        
        response = f"""💰 *YOUR BALANCE*

Name: {user['name']}
Rides remaining: *{user['rides_left']}*
Total spent: ₦{user['total_spent']:,.0f}

*Pricing:*
🟢 Short routes: ₦125
🔵 Standard routes: ₦225
🔵 Inter-college: ₦200

Type BUY to purchase rides."""
        
        msg.body(response)
        return str(resp)
    
    if command == 'HISTORY':
        user = db.get_user(sender)
        rides = db.get_user_rides(sender, limit=10)
        
        if not rides:
            response = f"""📜 *RIDE HISTORY*

No rides yet, {user['name']}!

Type RIDE to book your first shuttle! 🚌"""
        else:
            response = f"""📜 *YOUR RIDE HISTORY*

Last {len(rides)} rides:

"""
            for i, ride in enumerate(rides, 1):
                dest, cost, timestamp = ride
                time_str = timestamp.split('.')[0]
                response += f"{i}. {dest} - ₦{cost:.0f}\n   {time_str}\n\n"
            
            response += f"*Total spent:* ₦{user['total_spent']:,.0f}"
        
        msg.body(response)
        return str(resp)
    
    if command == 'BUY':
        response = """💳 *PURCHASE RIDES*

🟢 Short Routes = ₦125
🔵 Standard Routes = ₦225
🔵 Inter-College = ₦200

*Payment details coming soon!*

For now, contact admin:
+2349081617382

We're setting up automated payments! 🚀"""
        
        msg.body(response)
        return str(resp)
    
    # ==================== ADMIN COMMANDS ====================
    
    if command == 'ADMIN':
        if sender == ADMIN_PHONE_NUMBER:
            stats = db.get_stats()
            
            response = f"""🎛️ *EDT SHUTTLE ADMIN DASHBOARD*

*OVERVIEW:*
Users: {stats['total_users']}
Total Rides: {stats['total_rides']}
Revenue: ₦{stats['total_revenue']:,.0f}

*TODAY:*
Rides: {stats['today_rides']}
Your Cut: ₦{stats['today_rides'] * 25:,.0f}

*COMMANDS:*
USERS - All users
DRIVERS - All drivers
TODAY - Today's activity
EXPORT - Export data"""
        else:
            response = "❌ Admin only."
        
        msg.body(response)
        return str(resp)
    
    if command == 'USERS' and sender == ADMIN_PHONE_NUMBER:
        users = db.get_all_users(20)
        
        if not users:
            response = "📋 No users yet!"
        else:
            response = f"📋 *ALL USERS* (Top 20)\n\n"
            
            for i, user_data in enumerate(users, 1):
                name, phone, rides, spent, _ = user_data
                phone_display = phone[-4:]
                response += f"{i}. {name or 'No name'} (...{phone_display})\n"
                response += f"   Rides: {rides} | Spent: ₦{spent:,.0f}\n\n"
            
            response += f"Total: {len(users)} users"
        
        msg.body(response)
        return str(resp)
    
    if command == 'LOWBAL' and sender == ADMIN_PHONE_NUMBER:
        users = db.get_low_balance_users(3)
        
        if not users:
            response = "✅ *NO LOW BALANCE USERS*\n\nEveryone has 3+ rides! 🎉"
        else:
            response = f"⚠️ *LOW BALANCE ALERT*\n\n{len(users)} users need top-up:\n\n"
            
            for i, user_data in enumerate(users, 1):
                name, phone, rides = user_data
                phone_display = phone[-4:]
                
                if rides == 0:
                    emoji = "🔴"
                elif rides == 1:
                    emoji = "🟡"
                else:
                    emoji = "🟢"
                
                response += f"{emoji} {name or 'No name'} (...{phone_display}): {rides} rides\n"
            
            response += f"\n💡 Tip: Remind them to BUY!"
        
        msg.body(response)
        return str(resp)
    
    if command == 'DRIVERS' and sender == ADMIN_PHONE_NUMBER:
        drivers = db.get_all_drivers()
        
        if not drivers:
            response = "🚗 No drivers yet!"
        else:
            response = "🚗 *REGISTERED DRIVERS*\n\n"
            for i, d in enumerate(drivers, 1):
                name, phone, pref, zone, available, device, vehicle, rides, earnings = d
                status = "🟢" if available else "🔴"
                response += f"{i}. {name} {status}\n"
                response += f"   Zone: {zone} | Rides: {rides}\n"
                response += f"   Earnings: ₦{earnings:,.0f}\n\n"
        
        msg.body(response)
        return str(resp)
    
    if command == 'TODAY' and sender == ADMIN_PHONE_NUMBER:
        rides, purchases = db.get_today_activity()
        
        response = f"📅 *TODAY'S ACTIVITY*\n\n"
        
        if rides:
            response += f"🚗 *RIDES ({len(rides)})*\n"
            for dest, name, time in rides[:10]:
                time_str = time.split('.')[0].split(' ')[1][:5]
                response += f"• {name} → {dest} at {time_str}\n"
        else:
            response += "🚗 *RIDES:* None yet"
        
        msg.body(response)
        return str(resp)
    
    if command == 'EXPORT' and sender == ADMIN_PHONE_NUMBER:
        conn = sqlite3.connect('edt_shuttle.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM rides')
        ride_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(amount) FROM transactions WHERE type = "purchase"')
        total_rev = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT destination, COUNT(*) as count
            FROM rides
            GROUP BY destination
            ORDER BY count DESC
            LIMIT 5
        ''')
        top_dests = cursor.fetchall()
        
        conn.close()
        
        response = f"""📦 *DATA EXPORT REPORT*

*OVERVIEW:*
Total Users: {user_count}
Total Rides: {ride_count}
Total Revenue: ₦{total_rev:,.0f}
Your Profit: ₦{ride_count * 25:,.0f}

*TOP ROUTES:*
"""
        
        for i, (dest, count) in enumerate(top_dests, 1):
            response += f"{i}. {dest}: {count} rides\n"
        
        response += f"""
*AVERAGES:*
Avg rides/user: {ride_count / user_count if user_count > 0 else 0:.1f}
Avg spent/user: ₦{total_rev / user_count if user_count > 0 else 0:,.0f}"""
        
        msg.body(response)
        return str(resp)
    
    if command == 'HELP':
        response = f"""📋 *EDT SHUTTLE COMMANDS*

*Student:*
RIDE - Book shuttle
BALANCE - Check rides
ZONES - See all zones
PRICE - Pricing breakdown
HISTORY - Past rides
BUY - Purchase rides

*Driver:*
DRIVERHI - Driver dashboard
AVAILABLE - Go online
BUSY - Go offline
ZONE [Location] - Update zone
MYSTATS - View earnings
STATUS - Check status

*Admin:*
ADMIN - Dashboard
USERS - All users
DRIVERS - All drivers
TODAY - Today's activity
LOWBAL - Low balance users
EXPORT - Data report

Built for LASUSTECH students 🚌"""
        
        msg.body(response)
        return str(resp)
    
    if command == 'RESET':
        state['state'] = 'idle'
        response = "✅ Reset! Type HI to start fresh."
        msg.body(response)
        return str(resp)
    
    if command == 'TESTMODE':
        db.add_rides(sender, 10)
        user = db.get_user(sender)
        response = f"🔧 *TEST MODE*\n\n10 free rides added!\nTotal: {user['rides_left']}\n\nType RIDE to test! 🚀"
        msg.body(response)
        return str(resp)
    
    # UNKNOWN COMMAND
    response = f"""❓ Didn't understand "{incoming_msg}"

Try:
RIDE - Book shuttle
BALANCE - Check rides
ZONES - See all zones
PRICE - Pricing breakdown
HELP - All commands"""
    
    msg.body(response)
    return str(resp)


if __name__ == "__main__":
    print("=" * 60)
    print("🚌 EDT LASUSTECH SHUTTLE BOT STARTING...")
    print("=" * 60)
    print("📱 WhatsApp: http://localhost:5000")
    print("⚡ Zone-based pricing enabled")
    print("🟢 Short routes: ₦125 (driver gets ₦100)")
    print("🔵 Standard routes: ₦225 (driver gets ₦200)")
    print("🔵 Inter-college: ₦200 (driver gets ₦175)")
    print("💾 Database: ENABLED")
    print("🚗 Driver system: ENABLED")
    print("=" * 60)
    app.run(debug=True, port=5000)