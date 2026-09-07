import telebot
import json
import random
import time
import threading
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import html

TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    # Allow import/tests without TOKEN; strict check happens in __main__
    print("⚠️ WARNING: TOKEN env not set — using placeholder for import only")
    TOKEN = "000000:PLACEHOLDER_FOR_TESTS"
ADMIN_IDS = [str(x).strip() for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

DATA_FILE = "Game_tg.json"

import threading as _threading_module  # ensure Thread available
Thread = _threading_module.Thread

bot = telebot.TeleBot(TOKEN)

telebot.apihelper.CONNECT_TIMEOUT = 30
telebot.apihelper.READ_TIMEOUT = 30

# ===== DATA =====
users, missions, trades, gangs = {}, {}, {}, {}
jail, dead, shield = {}, {}, {}
kill_cd = {}
rob_cd = {}

daily_cd = {}
invites = {}
mission_cd = {}
banned = {}
admin_cd = {}
job_owner = {}
coin_cd = {}
give_cd = {}
group_data = {}
duel_cd = {}
pending_duels = {}
fish_cd = {}
withdraw_input = {}
rps_games = {}
spin_cd = {}
slot_games = {}
military_cd = {}
rps_cd = {}
slot_cd    = {}   # cooldown
mine_games = {}

# Thread-safe save lock (logic unchanged, prevents JSON corruption)
SAVE_LOCK = threading.Lock()

# ===== LOAD/SAVE =====
def load():
    global users, missions, trades, gangs
    global jail, dead, shield
    global daily_cd, kill_cd, rob_cd, invites, mission_cd
    global banned
    global job_owner
    global group_data

    try:
        # 🔥 1. Ensure file exists (CRITICAL FIX)
        if not os.path.exists(DATA_FILE):
            print("⚠️ Data file not found, creating new...")
            with open(DATA_FILE, "w") as f:
                json.dump({}, f)

        # 🔥 2. Load file safely
        with open(DATA_FILE) as f:
            d = json.load(f)

            users = d.get("users", {})
            missions = d.get("missions", {})
            trades = d.get("trades", {})
            gangs = d.get("gangs", {})
            jail = d.get("jail", {})
            dead = d.get("dead", {})
            shield = d.get("shield", {})
            daily_cd = d.get("daily_cd", {})
            kill_cd = d.get("kill_cd", {})
            rob_cd = d.get("rob_cd", {})
            invites = d.get("invites", {})
            mission_cd = d.get("mission_cd", {})
            banned = d.get("banned", {})
            job_owner = d.get("job_owner", {})
            group_data = d.get("group_data", {})

            # 🔥 3. Type safety (important)
            if not isinstance(users, dict): users = {}
            if not isinstance(missions, dict): missions = {}
            if not isinstance(trades, dict): trades = {}
            if not isinstance(gangs, dict): gangs = {}
            if not isinstance(jail, dict): jail = {}
            if not isinstance(dead, dict): dead = {}
            if not isinstance(shield, dict): shield = {}
            if not isinstance(daily_cd, dict): daily_cd = {}
            if not isinstance(kill_cd, dict): kill_cd = {}
            if not isinstance(rob_cd, dict): rob_cd = {}
            if not isinstance(invites, dict): invites = {}
            if not isinstance(mission_cd, dict): mission_cd = {}
            if not isinstance(banned, dict): banned = {}
            if not isinstance(job_owner, dict): job_owner = {}
            if not isinstance(group_data, dict): group_data = {}

        print("✅ Data loaded successfully")

    except Exception as e:
        print("❌ Load error:", e)

        # 🔥 fallback reset (safe) — reset ALL persisted stores
        users, missions, trades, gangs = {}, {}, {}, {}
        jail, dead, shield = {}, {}, {}
        daily_cd, kill_cd, rob_cd, invites, mission_cd = {}, {}, {}, {}, {}
        banned = {}
        job_owner = {}
        group_data = {}




def ensure_chat(chat_id):
    chat_id = str(chat_id)

    users.setdefault(chat_id, {})
    missions.setdefault(chat_id, {})
    trades.setdefault(chat_id, {})
    gangs.setdefault(chat_id, {})

    jail.setdefault(chat_id, {})
    dead.setdefault(chat_id, {})
    shield.setdefault(chat_id, {})

    kill_cd.setdefault(chat_id, {})
    rob_cd.setdefault(chat_id, {})

    daily_cd.setdefault(chat_id, {})
    invites.setdefault(chat_id, {})
    mission_cd.setdefault(chat_id, {})
    banned.setdefault(chat_id, {})
    job_owner.setdefault(chat_id, {})

    return chat_id



def save():
    try:
        data = {
            "users": users,
            "missions": missions,
            "trades": trades,
            "gangs": gangs,
            "jail": jail,
            "dead": dead,
            "shield": shield,
            "daily_cd": daily_cd,
            "kill_cd": kill_cd,
            "rob_cd": rob_cd,
            "invites": invites,
            "mission_cd": mission_cd,
            "banned": banned,
            "job_owner": job_owner,  # 🔥 ADD THIS
            "group_data": group_data
        }
        # Atomic + thread-safe write (same data/logic, no corruption)
        tmp = DATA_FILE + ".tmp"
        with SAVE_LOCK:
            with open(tmp, "w") as f:
                json.dump(data, f)
            os.replace(tmp, DATA_FILE)
            
        
            
    except Exception as e:
        print("Save error:", e)

# ===== CONFIG =====
WEAPONS = {
    "knife": {"price": 800, "rate": 0.6, "risk": 0.1},
    "pistol": {"price": 2000, "rate": 0.65, "risk": 0.2},
    "ak47": {"price": 5000, "rate": 0.75, "risk": 0.3},
    "shotgun": {"price": 8000, "rate": 0.8, "risk": 0.4},
    "Kar98k": {"price" : 15000, "rate":0.85, "risk": 0.6},
    "rpg": {"price": 20000, "rate": 1.0, "risk": 0.7},
    
}


ARMOR = {"price": 3000, "reduce": 0.2}

BREAKER_WEAPONS = {
    "Katana": {"price" : 10000, "rate":0.3, "risk": 0.2},
    "Desert Eagle": {"price" : 25000, "rate":0.5, "risk": 0.6},
    "AWM": {"price" : 35000, "rate":0.75, "risk": 0.7},
    "breaker": {"price": 70000, "rate": 0.85, "risk": 0.85}

}

ZONES = {
    "slums": {"risk": 0.2, "reward": (200, 800)},
    "city": {"risk": 0.4, "reward": (500, 1500)},
    "bank": {"risk": 0.6, "reward": (1000, 3000)},
    "military": {"risk": 0.85, "reward": (2500, 6000)},
    "harbor": {"risk": 0.5, "reward": (800, 2500)},
    "casino": {"risk": 0.7, "reward": (1500, 5000)},

    # 🔥 NEW ZONES
    "arena": {"risk": 0.9, "reward": (3000, 7000)},
    "food": {"risk": 0.1, "reward": (100, 400)},
    "market": {"risk": 0.3, "reward": (400, 1200)},
    "police": {"risk": 0.2, "reward": (200, 600)},
    "mountain": {"risk": 0.75, "reward": (2000, 5500)},
    "garden": {"risk": 0.1, "reward": (50, 300)},
}

LOCATIONS = [
    "slums",
    "city",
    "bank",
    "casino",
    "arena",
    "market",
    "food",
    "police",
    "harbor",
    "military",
    "mountain",
    "garden"
]

# Travel graph (was missing -> /map crashed with NameError).
# Logic preserved: /travel allows any zone for 20000, so every zone
# connects to every other zone.
CONNECTIONS = {loc: [l for l in LOCATIONS if l != loc] for loc in LOCATIONS}


MINE_MULTIS = {
    1: 20,
    2: 15,
    3: 12,
    5: 10,
    10: 4,
    20: 3,
    30: 2,
    50: 1
}



FOODS = {
    "bread": {"price": 100, "heal": 10},
    "burger": {"price": 300, "heal": 25},
    "pizza": {"price": 600, "heal": 50},
    "shawarma": {"price": 800, "heal": 60},
    "biryani": {"price": 1000, "heal": 80},
    "feast": {"price": 1300, "heal": 100}
}

JOB_INFO = {
    "smith": "🔫 Earn from weapon sales",
    "armor": "🛡 Earn from armor purchases",
    "protect": "🛡 Earn from protection shields",
    "bank": "💰 Earn from deposits",
    "police": "🚔 Arrest criminals & earn fines",
    "military": "🪖 Complete missions",
    "harbor": "🌊 Earn from fishing",
    "casino": "🎰 Earn from games",
    "food": "🍗 Earn from food sales",
    "breaker": "💥 Earn from breaker weapons"
}


# ===== USER =====
def get_user(user, chat_id):
    chat_id = str(chat_id)
    uid = str(user.id)

    name = user.first_name or user.username or "Unknown"

    # 🔥 ensure all systems exist
    users.setdefault(chat_id, {})
    missions.setdefault(chat_id, {})
    trades.setdefault(chat_id, {})
    gangs.setdefault(chat_id, {})

    jail.setdefault(chat_id, {})
    dead.setdefault(chat_id, {})
    shield.setdefault(chat_id, {})

    kill_cd.setdefault(chat_id, {})
    rob_cd.setdefault(chat_id, {})

    daily_cd.setdefault(chat_id, {})
    invites.setdefault(chat_id, {})

    # 👤 create user if not exists
    if uid not in users[chat_id]:
        users[chat_id][uid] = {
            "name": name,
            "money": 3000,
            "bank": 0,
            "xp": 0,
            "level": 1,
            "zone": "slums",
            "weapon": None,
            "armor": False,
            "gang": None,

            # 🍗 survival
            "hunger": 100,
            "inventory": [],
            "last_hunger": time.time(),

            # ⚔️ ARENA STATS
            "stats": {
                "strength": 5,
                "muscles": 5,
                "stamina": 5,
                "experience": 0,
                "power": 5
            },

            # 🔥 DUEL STATS (NEW)
            "duel": {
                "wins": 0,
                "losses": 0,
                "total": 0
            },

            "crime": {
                "caught": 0
            }
        }
        save()

    u = users[chat_id][uid]

    # 🔄 update name
    u["name"] = name

    # 🔥 ensure fields for old users
    u.setdefault("hunger", 100)
    u.setdefault("inventory", [])
    u.setdefault("last_hunger", time.time())
    u.setdefault("crime", {"caught": 0})

    # 🔥 ensure stats for old users
    u.setdefault("stats", {
        "strength": 5,
        "muscles": 5,
        "stamina": 5,
        "experience": 0,
        "power": 5
    })

    # 🔥 ensure duel stats for old users (IMPORTANT)
    u.setdefault("duel", {
        "wins": 0,
        "losses": 0,
        "total": 0
    })

    # =========================
    # 💀 STOP IF DEAD
    # =========================
    if uid in dead.get(chat_id, {}):
        return u

    return u




def use_hunger(user_data, amount=1):
    user_data["hunger"] = max(0, user_data["hunger"] - amount)

    if user_data["hunger"] <= 0:
        return False

    return True


# ===== START / HELP =====
@bot.message_handler(commands=['startgame','helpgame'], chat_types=['private','group','supergroup'])
def help_cmd(msg):
    bot.send_message(msg.chat.id, """
<b>🎮 GAME COMMANDS</b>

<blockquote>
🧠 <b>Missions</b>
/mission - Get a mission  
/do - Complete mission  
</blockquote>

<blockquote>
🗺️ <b>Map & Travel</b>
/map - View map  
/travel &lt;zone&gt; - Move area  
</blockquote>

<blockquote>
⚔️ <b>Combat</b>
/kill (reply) - Kill player  
/rob (reply) - Rob player  
/duel (reply) - Duel player  
/revive - Revive (💸 1000)  
</blockquote>

<blockquote>
🏟️ <b>Arena</b>
/arena - Fight system  
/upgrade &lt;stat&gt; - Upgrade stats  
</blockquote>

<blockquote>
🛡️ <b>Protection</b>
/protect - Buy shield  
</blockquote>

<blockquote>
💰 <b>Economy</b>
/daily - Daily reward  
/deposit - Bank (1% fee)  
/withdraw - Withdraw (keypad)  
/give (reply) - Send money  
/accept - Accept transfer  
/decline - Decline transfer  
</blockquote>

<blockquote>
🛒 <b>Shop & Food</b>
/shop - Buy weapons/armor  
/food - Food shop  
/eat &lt;item&gt; - Restore hunger  
</blockquote>

<blockquote>
🎰 <b>Casino</b>
/rps &lt;amt&gt; - RPS (PvP / Bot)  
/slot &lt;amt&gt; - Slot machine  
/spin &lt;amt&gt; - Spin wheel  
/coin heads/tails &lt;amt&gt;  
/color red/black/green &lt;amt&gt;  
</blockquote>

<blockquote>
🌊 <b>Work</b>
/fish - Earn money (harbor)  
</blockquote>

<blockquote>
🚔 <b>Police</b>
/arrest (reply) - Arrest criminals (job only)  
</blockquote>

<blockquote>
🪖 <b>Military</b>
/military - Do missions (job only)  
</blockquote>

<blockquote>
👥 <b>Gangs</b>
/creategang &lt;name&gt;  
/joingang &lt;name&gt;  
/ganginvite (reply)  
/acceptgang  
</blockquote>

<blockquote>
📊 <b>Player</b>
/panel - Full profile + ranks  
/status - Quick info  
/stat - Duel + power stats  
</blockquote>

<blockquote>
💼 <b>Jobs</b>
/myjob - Your job  
/alljob - View all jobs  
</blockquote>

<blockquote>
👑 <b>Admin</b>
/admin  
/ban (reply)  
/unban (reply)  
/broadcast  
/broadcastpvt  
/setjob (reply)  
/removejob  
</blockquote>

""", parse_mode="HTML")




def get_money_rank(money):
    if money < 10000:
        return "Middle"
    elif money < 20000:
        return "Upper"
    elif money < 100000:
        return "Rich"
    elif money < 500000:
        return "👑 King"
    else:
        return "🔥 Emperor"



def get_duel_rank(wins):
    if wins < 5:
        return "🥉 Bronze"
    elif wins < 15:
        return "🥈 Silver"
    elif wins < 30:
        return "🥇 Gold"
    elif wins < 60:
        return "💠 Platinum"
    elif wins < 100:
        return "🔥 Master"
    elif wins < 150:
        return "⚡ Elite"
    elif wins < 250:
        return "🏆 Champion"
    elif wins < 400:
        return "👑 Elite Champion"
    else:
        return "⚔️ Fighter"









@bot.message_handler(commands=['military'])
def military_mission(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 💀 dead check
    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 📍 zone check
    if u["zone"] != "military":
        return bot.send_message(msg.chat.id, "🪖 Go to MILITARY base")

    job_owner.setdefault(chat_id, {})

    owner = job_owner[chat_id].get("military")

    # ❌ no one owns job
    if not owner:
        return bot.send_message(msg.chat.id, "❌ No military officer assigned")

    # ❌ not the owner
    if owner != uid:
        return bot.send_message(msg.chat.id, "🚫 Only the military officer can do missions")

    # ⏳ cooldown
    military_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in military_cd[chat_id] and now - military_cd[chat_id][uid] < 60:
        left = int(60 - (now - military_cd[chat_id][uid]))
        return bot.send_message(msg.chat.id, f"⏳ Wait {left}s before next mission")

    military_cd[chat_id][uid] = now

    # 🎯 success system (LOW RISK)
    success_rate = 0.9

    if random.random() > success_rate:
        loss = random.randint(50, 150)
        u["money"] = max(0, u["money"] - loss)

        save()

        return bot.send_message(
            msg.chat.id,
            f"❌ Mission failed\n💸 Lost: {loss}"
        )

    # 💰 reward
    reward = random.randint(300, 1500)
    u["money"] += reward

    # 💼 pay job system
    pay_job(chat_id, "military", reward // 4)

    save()

    bot.send_message(
        msg.chat.id,
        f"🪖 Mission completed!\n💰 Earned: {reward}"
    )






@bot.message_handler(commands=['alljob'])
def all_jobs(msg):
    chat_id = ensure_chat(msg.chat.id)

    job_owner.setdefault(chat_id, {})
    chat_users = users.get(chat_id, {})

    ALL_JOBS = [
        "smith","armor","protect","bank",
        "police","military","harbor","casino","food","breaker"
    ]

    text = "💼 <b>JOB LIST</b>\n\n"

    for job in ALL_JOBS:
        owner_id = job_owner[chat_id].get(job)
        info = JOB_INFO.get(job, "No description")

        if owner_id and owner_id in chat_users:
            name = html.escape(chat_users[owner_id]["name"])
            text += f"🔹 <b>{job.title()}</b>\n👤 {name}\n📌 {info}\n\n"
        else:
            text += f"🔹 <b>{job.title()}</b>\n❌ Available\n📌 {info}\n\n"

    bot.send_message(msg.chat.id, text, parse_mode="HTML")




@bot.message_handler(commands=['food'])
def food_shop(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    if check_dead_block(msg, uid):
        return

    kb = InlineKeyboardMarkup()

    for f, data in FOODS.items():
        kb.add(
            InlineKeyboardButton(
                f"{f} 🍗 +{data['heal']} 💰{data['price']}",
                callback_data=f"buyfood{f}"
            )
        )

    bot.send_message(msg.chat.id, "🍗 Food Shop:", reply_markup=kb)






@bot.message_handler(commands=['eat'])
def eat(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    if check_dead_block(msg, uid):
        return

    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /eat item")

    item = parts[1].lower()

    u = get_user(msg.from_user, msg.chat.id)

    if item not in u.get("inventory", []):
        return bot.send_message(msg.chat.id, "❌ You don't have that food")

    heal = FOODS[item]["heal"]

    u["hunger"] = min(100, u["hunger"] + heal)
    u["inventory"].remove(item)

    save()

    bot.send_message(
        msg.chat.id,
        f"🍗 Ate {item}\n❤️ Hunger: {u['hunger']}/100"
    )






def is_admin(user_id, chat_id):
    chat_id = str(chat_id)
    user_id = str(user_id)

    if chat_id not in group_data:
        return False

    data = group_data[chat_id]

    return user_id == data["owner"] or user_id in data["admins"]





@bot.message_handler(commands=['addadmin'])
def add_admin(msg):
    chat_id = str(msg.chat.id)
    uid = str(msg.from_user.id)

    if chat_id not in group_data:
        return

    if group_data[chat_id]["owner"] != uid:
        return bot.send_message(chat_id, "❌ Only owner can add admin")

    if not msg.reply_to_message:
        return bot.send_message(chat_id, "Reply to user")

    target = str(msg.reply_to_message.from_user.id)

    if target not in group_data[chat_id]["admins"]:
        group_data[chat_id]["admins"].append(target)

    save()
    bot.send_message(chat_id, "✅ Admin added")





@bot.message_handler(commands=['removeadmin'])
def remove_admin(msg):
    chat_id = str(msg.chat.id)
    uid = str(msg.from_user.id)

    if chat_id not in group_data:
        return

    if group_data[chat_id]["owner"] != uid:
        return bot.send_message(chat_id, "❌ Only owner can remove admin")

    if not msg.reply_to_message:
        return bot.send_message(chat_id, "Reply to user")

    target = str(msg.reply_to_message.from_user.id)

    # ❌ cannot remove owner
    if target == group_data[chat_id]["owner"]:
        return bot.send_message(chat_id, "❌ Cannot remove owner")

    if target in group_data[chat_id]["admins"]:
        group_data[chat_id]["admins"].remove(target)

    save()
    bot.send_message(chat_id, "❌ Admin removed")




@bot.message_handler(commands=['mygroups'])
def mygroups(msg):
    if msg.chat.type != "private":
        return

    uid = str(msg.from_user.id)

    my_groups = []

    for gid, data in group_data.items():
        if data["owner"] == uid:
            try:
                chat = bot.get_chat(int(gid))
                my_groups.append(chat.title)
            except:
                pass

    if not my_groups:
        return bot.send_message(msg.chat.id, "❌ You don’t own any groups")

    text = "📋 <b>Your Groups:</b>\n\n"
    for g in my_groups:
        text += f"• {g}\n"

    bot.send_message(msg.chat.id, text, parse_mode="HTML")






@bot.message_handler(commands=['owner'])
def claim(msg):
    chat_id = str(msg.chat.id)
    uid = str(msg.from_user.id)

    if msg.chat.type == "private":
        return

    # 🔐 ONLY telegram admins can claim
    try:
        admins = bot.get_chat_administrators(msg.chat.id)
        admin_ids = [str(a.user.id) for a in admins]

        if uid not in admin_ids:
            return  # ❌ silent block (no hint)

    except:
        return

    # 🔒 already claimed → only telegram admin can override
    if chat_id in group_data:
        if group_data[chat_id]["owner"] != uid:
            return  # ❌ silent (no info leak)

    group_data[chat_id] = {
        "owner": uid,
        "admins": []
    }

    save()
    bot.send_message(msg.chat.id, "👑 Bot owner set")






@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.from_user.is_bot:
        return

    admin_id = str(msg.from_user.id)
    now = time.time()

    # 🔥 cooldown
    if admin_id in admin_cd and now - admin_cd[admin_id] < 2:
        return

    admin_cd[admin_id] = now

    if not is_admin(msg.from_user.id, msg.chat.id):
        return bot.send_message(msg.chat.id, "❌ Not authorized")

    bot.send_message(msg.chat.id, """
👑 ADMIN PANEL

/ban (reply)
/unban (reply)
/broadcast <msg>
/broadcastpvt <msg>

Use carefully ⚠️
""")
    



@bot.message_handler(commands=['ban'])
def ban_user(msg):
    if msg.from_user.is_bot:
        return

    admin_id = str(msg.from_user.id)
    now = time.time()

    # 🔥 cooldown (admin)
    if admin_id in admin_cd and now - admin_cd[admin_id] < 2:
        return
    admin_cd[admin_id] = now

    # 🔒 admin check
    if not is_admin(msg.from_user.id, msg.chat.id):
        return bot.send_message(msg.chat.id, "❌ Not allowed")

    # 🔁 must reply
    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to user")

    chat_id = str(msg.chat.id)
    target_id = str(msg.reply_to_message.from_user.id)

    # 🔒 protect owner (ADD HERE)
    if target_id == group_data.get(chat_id, {}).get("owner"):
        return  # silent block

    # ❌ cannot ban yourself
    if target_id == admin_id:
        return bot.send_message(msg.chat.id, "❌ Can't ban yourself")

    # 🚫 already banned
    banned.setdefault(chat_id, {})
    if target_id in banned[chat_id]:
        return bot.send_message(msg.chat.id, "⚠️ Already banned")

    # 🚫 apply ban
    banned[chat_id][target_id] = True

    save()
    bot.send_message(msg.chat.id, "🚫 User banned")


@bot.message_handler(commands=['unban'])
def unban_user(msg):
    if msg.from_user.is_bot:
        return

    admin_id = str(msg.from_user.id)
    now = time.time()

    # 🔥 cooldown (admin)
    if admin_id in admin_cd and now - admin_cd[admin_id] < 2:
        return

    admin_cd[admin_id] = now

    if not is_admin(msg.from_user.id, msg.chat.id):
        return bot.send_message(msg.chat.id, "❌ Not allowed")

    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to user")

    chat_id = str(msg.chat.id)
    target_id = str(msg.reply_to_message.from_user.id)

    banned.setdefault(chat_id, {})
    banned[chat_id].pop(target_id, None)

    save()
    bot.send_message(msg.chat.id, "✅ User unbanned")



@bot.message_handler(commands=['broadcast'])
def broadcast(msg):
    if msg.from_user.is_bot:
        return

    admin_id = str(msg.from_user.id)
    now = time.time()

    # 🔥 ONLY BOT OWNER ALLOWED
    if admin_id not in ADMIN_IDS:
        return bot.send_message(msg.chat.id, "🚫 Only bot owner can use this")

    # ⏳ cooldown (optional)
    if admin_id in admin_cd and now - admin_cd[admin_id] < 2:
        return

    admin_cd[admin_id] = now

    # 🔥 message parsing
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /broadcast message")

    text = parts[1].strip()

    count = 0

    # 📢 send to all chats
    for chat_id in list(users.keys()):
        try:
            bot.send_message(chat_id, text, parse_mode="HTML")
            count += 1
            time.sleep(0.05)  # anti rate limit
        except:
            pass

    bot.send_message(msg.chat.id, f"📢 Sent to {count} chats")


@bot.message_handler(commands=['broadcastpvt'])
def broadcast_pvt(msg):
    if msg.from_user.is_bot:
        return

    admin_id = str(msg.from_user.id)
    now = time.time()

    # 🔥 ONLY BOT OWNER
    if admin_id not in ADMIN_IDS:
        return bot.send_message(msg.chat.id, "🚫 Only bot owner can use this")

    # ⏳ cooldown
    if admin_id in admin_cd and now - admin_cd[admin_id] < 2:
        return
    admin_cd[admin_id] = now 

    # 🔥 safer text parsing
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /broadcastpvt message")

    text = parts[1].strip()

    sent = 0
    failed = 0
    sent_users = set()  # 🔥 prevent duplicates

    for chat_id in list(users.keys()):
        for user_id in users[chat_id]:

            # 🚫 skip duplicates
            if user_id in sent_users:
                continue
            sent_users.add(user_id)

            try:
                bot.send_message(int(user_id), text, parse_mode="HTML")
                sent += 1
                time.sleep(0.03)  # anti rate limit
            except:
                failed += 1

    bot.send_message(
        msg.chat.id,
        f"📩 Broadcast Complete\n✅ Sent: {sent}\n❌ Failed: {failed}"
    )



@bot.message_handler(commands=['deposit'])
def deposit(msg):
    print("\n====== DEPOSIT START ======")

    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    print("CHAT_ID:", chat_id, "| TYPE:", type(chat_id))
    print("USER_ID:", uid)

    u = get_user(msg.from_user, msg.chat.id)

    # 💀 dead check
    if check_dead_block(msg, uid):
        print("❌ USER DEAD")
        return

    parts = msg.text.split()
    print("INPUT:", parts)

    if len(parts) < 2:
        print("❌ NO AMOUNT")
        return bot.send_message(msg.chat.id, "Usage: /deposit amount")

    try:
        amt = int(parts[1])
        print("AMOUNT:", amt)
    except:
        print("❌ INVALID AMOUNT FORMAT")
        return bot.send_message(msg.chat.id, "Invalid amount")

    # 🔒 minimum deposit
    if amt < 100:
        print("❌ BELOW MINIMUM")
        return bot.send_message(msg.chat.id, "❌ Minimum deposit is 100")

    if u["money"] < amt:
        print("❌ NOT ENOUGH MONEY")
        return bot.send_message(msg.chat.id, "❌ Not enough cash")

    # 💸 tax
    tax = max(1, int(amt * 0.01))
    final = amt - tax

    print("TAX:", tax)
    print("FINAL DEPOSIT:", final)

    # 💰 apply transaction
    u["money"] -= amt
    u["bank"] += final

    print("USER MONEY AFTER:", u["money"])
    print("USER BANK AFTER:", u["bank"])

    # 🔥 CHECK JOB OWNER BEFORE PAY
    print("JOB_OWNER DATA:", job_owner.get(chat_id))
    print("BANK OWNER:", job_owner.get(chat_id, {}).get("bank"))

    # 🏦 pay job
    print("➡️ CALLING pay_job()")
    pay_job(chat_id, "bank", tax)

    save()

    print("====== DEPOSIT END ======\n")

    bot.send_message(
        msg.chat.id,
        f"🏦 Deposited: {final}\n💸 Fee: {tax} (1%)\n📉 Min deposit: 100"
    ) 








@bot.message_handler(commands=['give'])
def give(msg):
    chat_id = ensure_chat(msg.chat.id)
    sender = str(msg.from_user.id)

    # 💀 dead / banned check
    if check_dead_block(msg, sender):
        return

    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to user")

    if msg.reply_to_message.from_user.is_bot:
        return bot.send_message(msg.chat.id, "🤖 Can't send to bots")

    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /give amount")

    try:
        amt = int(parts[1])
    except:
        return bot.send_message(msg.chat.id, "Invalid amount")

    # 🔒 VALIDATION
    if amt <= 0:
        return bot.send_message(msg.chat.id, "❌ Amount must be positive")

    if amt > 1_000_000:
        return bot.send_message(msg.chat.id, "❌ Max limit is 1,000,000")

    receiver = str(msg.reply_to_message.from_user.id)

    if sender == receiver:
        return bot.send_message(msg.chat.id, "❌ Can't send to yourself")

    u1 = get_user(msg.from_user, msg.chat.id)

    if u1["money"] < amt:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # ⏳ COOLDOWN
    give_cd.setdefault(chat_id, {})
    now = time.time()

    if sender in give_cd[chat_id] and now - give_cd[chat_id][sender] < 5:
        return bot.send_message(msg.chat.id, "⏳ Wait before sending again")

    give_cd[chat_id][sender] = now

    # 🔥 TRADE SYSTEM SAFETY
    trades.setdefault(chat_id, {})

    # ❌ sender already has pending
    if sender in trades[chat_id]:
        return bot.send_message(msg.chat.id, "❌ You already have a pending transfer")

    # ❌ receiver already has pending
    for t in trades[chat_id].values():
        if t["to"] == receiver:
            return bot.send_message(msg.chat.id, "❌ User already has a pending request")

    # ✅ store trade (5-min expiry; accept/decline already check it)
    trades[chat_id][sender] = {
        "to": receiver,
        "amount": amt,
        "expires": now + 300
    }

    bot.send_message(
        msg.chat.id,
        f"💸 Transfer request sent!\nAmount: {amt}\nUse /accept or /decline"
    )
    

@bot.message_handler(commands=['accept'])
def accept(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 🚫 ONLY block banned (NOT dead)
    if uid in banned.get(chat_id, {}):
        return bot.send_message(msg.chat.id, "🚫 You are banned from this game")

    trades.setdefault(chat_id, {})
    dead.setdefault(chat_id, {})

    now = time.time()

    for sender, t in list(trades[chat_id].items()):

        # ✅ only accept your own incoming trade
        if t.get("to") != uid:
            continue

        amt = t.get("amount", 0)

        # ⏳ expiry check
        if "expires" in t and now > t["expires"]:
            del trades[chat_id][sender]
            continue

        # ❌ invalid users safety
        if sender not in users.get(chat_id, {}) or uid not in users.get(chat_id, {}):
            del trades[chat_id][sender]
            return bot.send_message(msg.chat.id, "❌ Invalid users")

        u1 = users[chat_id][sender]
        u2 = users[chat_id][uid]

        # ❌ prevent dead sender exploit
        if sender in dead[chat_id]:
            del trades[chat_id][sender]
            return bot.send_message(msg.chat.id, "❌ Sender is dead, trade cancelled")

        # ❌ sanity checks
        if amt <= 0:
            del trades[chat_id][sender]
            return bot.send_message(msg.chat.id, "❌ Invalid amount")

        if u1["money"] < amt:
            del trades[chat_id][sender]
            return bot.send_message(msg.chat.id, "❌ Sender has no money")

        # 💰 transfer
        u1["money"] -= amt
        u2["money"] += amt

        # 💥 bankruptcy check
        check_bankrupt(chat_id, sender)
        check_bankrupt(chat_id, uid)

        # 🧹 cleanup
        del trades[chat_id][sender]
        save()

        # 💀 optional message if receiver is dead
        if uid in dead[chat_id]:
            return bot.send_message(
                msg.chat.id,
                f"💰 Transfer received (while dead)\nFrom: {u1['name']}\nAmount: {amt}"
            )

        return bot.send_message(
            msg.chat.id,
            f"💰 Transfer received!\nFrom: {u1['name']}\nAmount: {amt}"
        )

    bot.send_message(msg.chat.id, "❌ No pending transfer")





@bot.message_handler(commands=['decline'])
def decline(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 💀 dead / banned check
    if check_dead_block(msg, uid):
        return

    trades.setdefault(chat_id, {})
    now = time.time()

    for sender, t in list(trades[chat_id].items()):
        # only decline your own incoming trade
        if t.get("to") != uid:
            continue

        # 🔥 remove expired trades automatically
        if "expires" in t and now > t["expires"]:
            del trades[chat_id][sender]
            continue

        # 🧹 delete trade
        del trades[chat_id][sender]

        # optional: show sender name safely
        sender_name = users.get(chat_id, {}).get(sender, {}).get("name", "Unknown")

        save()

        return bot.send_message(
            msg.chat.id,
            f"❌ Transfer declined\nFrom: {sender_name}"
        )

    bot.send_message(msg.chat.id, "❌ No pending request")



@bot.message_handler(commands=['map'])
def map_cmd(msg):
    uid = str(msg.from_user.id)
    u = get_user(msg.from_user, msg.chat.id)

    current = u["zone"]
    paths = CONNECTIONS.get(current, [])

    caption = f"""
🗺️ GAME MAP

📍 You are at: {current.upper()}
➡️ You can go to: {", ".join(paths)}

Use: /travel <zone>
"""

    try:
        _base = os.path.dirname(os.path.abspath(__file__))
        _candidates = [
            os.path.join(_base, "maps", "map.jpg"),
            os.path.join(_base, "map", "map.jpg"),
            os.path.join(_base, "map.jpg"),
            "maps/map.jpg",
            "map/map.jpg",
            "map.jpg",
        ]
        _found = next((p for p in _candidates if os.path.exists(p)), None)
        if _found is None:
            raise FileNotFoundError("map image not found")
        with open(_found, "rb") as photo:
            bot.send_photo(msg.chat.id, photo, caption=caption)
    except:
        bot.send_message(msg.chat.id, caption + "\n\n⚠️ Map image not found")



@bot.message_handler(commands=['travel'])
def travel(msg):
    uid = str(msg.from_user.id)

    if check_dead_block(msg, uid):
        return

    kb = InlineKeyboardMarkup(row_width=2)

    for loc in LOCATIONS:
        kb.add(
            InlineKeyboardButton(
                loc.upper(),
                callback_data=f"travel_{uid}_{loc}"
            )
        )

    bot.send_message(
        msg.chat.id,
        "✈️ Select location to travel\n💸 Flight Cost: 20000",
        reply_markup=kb
    )



def number_pad(action):
    kb = InlineKeyboardMarkup(row_width=3)

    nums = ["1","2","3","4","5","6","7","8","9"]  # 🔥 removed 0

    for i in range(0,9,3):
        kb.row(
            InlineKeyboardButton(nums[i], callback_data=f"{action}_{nums[i]}"),
            InlineKeyboardButton(nums[i+1], callback_data=f"{action}_{nums[i+1]}"),
            InlineKeyboardButton(nums[i+2], callback_data=f"{action}_{nums[i+2]}")
        )

    kb.row(
        InlineKeyboardButton("❌", callback_data=f"{action}_clear"),
        InlineKeyboardButton("0", callback_data=f"{action}_0"),
        InlineKeyboardButton("✔️", callback_data=f"{action}_ok")
    )

    return kb

@bot.message_handler(commands=['withdraw'])
def withdraw(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # ❌ removed dead block (dead may withdraw by design)

    # Per-chat buffer (same logic, no cross-group talk)
    _wd_key = f"{chat_id}_{uid}"
    withdraw_input[_wd_key] = ""

    bot.send_message(
        msg.chat.id,
        "💸 Enter amount to withdraw:\n\n0",
        reply_markup=number_pad("wd")
    )

def add_xp(chat_id, uid, amt):
    u = users[chat_id][uid]
    u["xp"] += amt
    if u["xp"] >= u["level"] * 100:
        u["xp"] = 0
        u["level"] += 1



@bot.callback_query_handler(func=lambda c: c.data.startswith("wd_"))
def withdraw_cb(call):
    uid = str(call.from_user.id)
    chat_id = str(call.message.chat.id)

    # Per-chat buffer (same keypad logic, fixes cross-group overwrite)
    _wd_key = f"{chat_id}_{uid}"
    withdraw_input.setdefault(_wd_key, "")
    action = call.data.split("_")[1]

    if action == "clear":
        withdraw_input[_wd_key] = ""

    elif action == "ok":
        if withdraw_input[_wd_key] == "":
            return bot.answer_callback_query(call.id, "Enter amount")

        if withdraw_input[_wd_key] == "0":
            return bot.answer_callback_query(call.id, "Invalid amount")

        amt = int(withdraw_input[_wd_key])
        u = get_user(call.from_user, chat_id)

        if u["bank"] < amt:
            return bot.answer_callback_query(call.id, "Not enough bank")

        if amt <= 0:
            return bot.answer_callback_query(call.id, "Invalid amount")

        u["bank"] -= amt
        u["money"] += amt

        withdraw_input[_wd_key] = ""
        save()

        bot.answer_callback_query(call.id, "Withdrawn")

        return bot.edit_message_text(
            f"💸 Withdrawn: {amt}",
            call.message.chat.id,
            call.message.message_id
        )

    else:
        if len(withdraw_input[_wd_key]) >= 9:
            return bot.answer_callback_query(call.id, "Max 9 digits")

        if withdraw_input[_wd_key] == "0":
            withdraw_input[_wd_key] = action
        else:
            withdraw_input[_wd_key] += action

    current = withdraw_input[_wd_key] if withdraw_input[_wd_key] else "0"

    bot.edit_message_text(
        f"💸 Enter amount to withdraw:\n\n{current}",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=number_pad("wd")
    )

    bot.answer_callback_query(call.id)










@bot.message_handler(commands=['daily','reward'])
def daily(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    # 🔥 ensure dict
    daily_cd.setdefault(chat_id, {})

    # 💀 dead check
    if check_dead_block(msg, uid):
        return

    now = time.time()

    # ⏳ cooldown (24h)
    if uid in daily_cd[chat_id] and now - daily_cd[chat_id][uid] < 86400:
        left = int(86400 - (now - daily_cd[chat_id][uid]))

        hours = left // 3600
        minutes = (left % 3600) // 60

        return bot.send_message(
            msg.chat.id,
            f"⏳ Come back in {hours}h {minutes}m"
        )

    u = get_user(msg.from_user, msg.chat.id)

    reward = 3000
    u["money"] += reward

    # 🔥 FIX: store per chat
    daily_cd[chat_id][uid] = now

    save()

    bot.send_message(
        msg.chat.id,
        f"🎁 Daily reward claimed!\n💰 +{reward}"
    )









def check_bankrupt(chat_id, uid):
    u = users[chat_id][uid]
    total = u["money"] + u.get("bank", 0)

    if total <= -100000:
        users[chat_id][uid].update({
            "money": 3000,
            "bank": 0,
            "xp": 0,
            "level": 1,
            "zone": "slums",
            "weapon": None,
            "armor": False,
            "gang": None,
            "hunger": 100,
            "inventory": [],
            "stats": {
                "strength": 5,
                "muscles": 5,
                "stamina": 5,
                "experience": 0,
                "power": 5
            }
        })
        # Reset must also clear status effects (same starter logic)
        try:
            dead.get(chat_id, {}).pop(uid, None)
            jail.get(chat_id, {}).pop(uid, None)
            shield.get(chat_id, {}).pop(uid, None)
        except Exception:
            pass
        return True
    return False




@bot.message_handler(commands=['setjob'])
def set_job(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 🔒 admin check
    if not is_admin(msg.from_user.id, msg.chat.id):
        return bot.send_message(msg.chat.id, "🚫 Only admin can assign jobs")

    # 🔁 must reply
    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to user")

    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /setjob jobname")

    job = parts[1].lower().strip()
    target_user = msg.reply_to_message.from_user
    target_id = str(target_user.id)

    VALID_JOBS = [
        "smith", "armor", "protect", "bank",
        "police", "military", "harbor", "casino", "food",
        "breaker"
    ]

    if job not in VALID_JOBS:
        return bot.send_message(msg.chat.id, "❌ Invalid job")

    job_owner.setdefault(chat_id, {})

    # 🔥 FIX: REGISTER USER BEFORE ASSIGNING JOB
    get_user(target_user, msg.chat.id)

    # 🔁 overwrite check
    old = job_owner[chat_id].get(job)
    job_owner[chat_id][job] = target_id

    save()

    if old and old != target_id:
        bot.send_message(
            msg.chat.id,
            f"🔁 {job.title()} reassigned to {target_user.first_name}"
        )
    else:
        bot.send_message(
            msg.chat.id,
            f"👑 {job.title()} assigned to {target_user.first_name}"
        )





def pay_job(chat_id, job, amount):
    print("\n====== PAY_JOB START ======")

    chat_id = str(chat_id)
    print("CHAT_ID:", chat_id, "| TYPE:", type(chat_id))

    # ❌ invalid amount
    if not isinstance(amount, (int, float)) or amount <= 0:
        print("❌ INVALID AMOUNT:", amount)
        return

    # 🔒 normalize job
    job = str(job).lower().strip()
    print("JOB:", job)

    # 📦 get owner
    print("JOB_OWNER FULL:", job_owner.get(chat_id))
    owner = job_owner.get(chat_id, {}).get(job)

    if not owner:
        print("❌ NO OWNER FOUND FOR JOB:", job)
        print("====== PAY_JOB END ======\n")
        return

    print("OWNER:", owner)

    users.setdefault(chat_id, {})
    chat_users = users[chat_id]

    print("USERS KEYS:", list(chat_users.keys()))

    # ❌ DO NOT CREATE USER HERE
    user = chat_users.get(owner)
    if not user:
        print("❌ OWNER NOT REGISTERED IN USERS → PAYMENT SKIPPED")
        print("====== PAY_JOB END ======\n")
        return

    # 💰 payout
    before = user.get("money", 0)
    user["money"] = before + int(amount)

    print(f"✅ MONEY ADDED: {amount}")
    print(f"BEFORE: {before} → AFTER: {user['money']}")

    print("====== PAY_JOB END ======\n")


@bot.message_handler(commands=['joblist'])
def joblist(msg):
    chat_id = ensure_chat(msg.chat.id)

    jobs = job_owner.get(chat_id, {})

    if not jobs:
        return bot.send_message(msg.chat.id, "❌ No jobs assigned")

    text = "👑 JOB LIST\n\n"

    for job, uid in jobs.items():
        user = users.get(chat_id, {}).get(uid)

        if user:
            name = user["name"]
        else:
            name = "Unknown"

        text += f"🔹 {job} → {name}\n"

    bot.send_message(msg.chat.id, text)




@bot.message_handler(commands=['removejob'])
def removejob(msg):
    if not is_admin(msg.from_user.id, msg.chat.id):
        return bot.send_message(msg.chat.id, "❌ Not allowed")

    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /removejob job")

    job = parts[1].lower()
    chat_id = ensure_chat(msg.chat.id)

    if job not in job_owner.get(chat_id, {}):
        return bot.send_message(msg.chat.id, "❌ Job not assigned")

    del job_owner[chat_id][job]
    save()

    bot.send_message(msg.chat.id, f"❌ {job} removed")



@bot.message_handler(commands=['myjob'])
def myjob(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    jobs = job_owner.get(chat_id, {})

    found = []

    for job, owner in jobs.items():
        if owner == uid:
            found.append(job)

    if not found:
        return bot.send_message(msg.chat.id, "❌ You have no job")

    bot.send_message(msg.chat.id, f"💼 Your job(s): {', '.join(found)}")





# ===== MISSIONS =====
@bot.message_handler(commands=['mission'], chat_types=['private','group','supergroup'])
def mission(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id)

    if check_dead_block(msg, uid):
        return

    mission_cd.setdefault(chat_id, {})

    now = time.time()

    # ⏳ 2 min cooldown (120 sec)
    if uid in mission_cd[chat_id] and now - mission_cd[chat_id][uid] < 120:
        left = int(120 - (now - mission_cd[chat_id][uid]))
        return bot.send_message(msg.chat.id, f"⏳ Wait {left}s before new mission")

    u = get_user(msg.from_user, msg.chat.id)

    z = ZONES[u["zone"]]

    m = {
        "reward": random.randint(*z["reward"]),
        "risk": z["risk"]
    }

    missions.setdefault(chat_id, {})
    missions[chat_id][uid] = m

    # ✅ set cooldown
    mission_cd[chat_id][uid] = now

    save()

    bot.send_message(msg.chat.id, f"🧠 Reward {m['reward']} | Risk {m['risk']}")

@bot.message_handler(commands=['do'], chat_types=['private','group','supergroup'])
def do(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id)

    if check_dead_block(msg, uid):
        return

    # 🔥 FIX: per chat missions
    if chat_id not in missions or uid not in missions[chat_id]:
        return bot.send_message(msg.chat.id, "No mission")

    m = missions[chat_id][uid]

    # 🔥 get user properly (must exist before use_hunger)
    u = get_user(msg.from_user, msg.chat.id)

    use_hunger(u, 3)

    if random.random() > m["risk"]:
        u["money"] += m["reward"]
        add_xp(chat_id, uid, 30)
        bot.send_message(msg.chat.id, f"✅ +{m['reward']}")
    else:
        loss = int(m["reward"] * 0.3)
        u["money"] -= loss
        bot.send_message(msg.chat.id, f"❌ -{loss}")

    # 🔥 delete mission properly
    del missions[chat_id][uid]

    save()

# ===== SHOP =====
@bot.message_handler(commands=['shop'])
def shop(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    if check_dead_block(msg, uid):
        return

    kb = InlineKeyboardMarkup()

    kb.add(InlineKeyboardButton("🔫 Weapons", callback_data="shop_weapons"))
    kb.add(InlineKeyboardButton("💥 Breakers", callback_data="shop_breakers"))
    kb.add(InlineKeyboardButton("🛡 Armor", callback_data="shop_armor"))
    kb.add(InlineKeyboardButton("🛡 Protect", callback_data="shop_protect"))

    bot.send_message(msg.chat.id, "🛒 Shop Categories:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    uid = str(call.from_user.id)
    chat_id = str(call.message.chat.id)


    if call.data.startswith("wd_"):
        return

    # Pager middle button — answer to stop spinner (no logic change)
    if call.data == "ignore":
        return bot.answer_callback_query(call.id)

    # 💀 dead check (AFTER withdraw)
    # 💀 block only dangerous actions (same list + PvP RPS, same intent)
    BLOCK_WHEN_DEAD = [
        "buy_",
        "buybreaker_",
        "protect_",
        "fight_",
        "rpsbot_",
        "rps_",
        "slotspin_",
        "minebet_",
        "mineopen_",
        "minecash_"
    ]

    if any(call.data.startswith(x) for x in BLOCK_WHEN_DEAD):
        if chat_id in dead and uid in dead[chat_id]:
            bot.answer_callback_query(call.id, "💀 You are dead")
            return
        # Banned users cannot use game buttons either (same as messages)
        if chat_id in banned and uid in banned[chat_id]:
            bot.answer_callback_query(call.id, "🚫 You are banned")
            return

    u = get_user(call.from_user, call.message.chat.id)

    # =========================
    # 🛒 SHOP CATEGORY MENUS
    # =========================
    if call.data == "shop_weapons":
        kb = InlineKeyboardMarkup()
        for w, data in WEAPONS.items():
            kb.add(InlineKeyboardButton(f"{w} 💰{data['price']}", callback_data=f"buy_{w}"))
        kb.add(InlineKeyboardButton("⬅ Back", callback_data="shop_main"))
        bot.edit_message_text("🔫 Weapons:", chat_id, call.message.message_id, reply_markup=kb)
        return

    if call.data == "shop_breakers":
        kb = InlineKeyboardMarkup()
        for w, data in BREAKER_WEAPONS.items():
            kb.add(InlineKeyboardButton(f"{w} 💥 💰{data['price']}", callback_data=f"buybreaker_{w}"))
        kb.add(InlineKeyboardButton("⬅ Back", callback_data="shop_main"))
        bot.edit_message_text("💥 Breakers:", chat_id, call.message.message_id, reply_markup=kb)
        return

    if call.data == "shop_armor":
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🛡 Armor 💰3000", callback_data="buy_armor"))
        kb.add(InlineKeyboardButton("⬅ Back", callback_data="shop_main"))
        bot.edit_message_text("🛡 Armor:", chat_id, call.message.message_id, reply_markup=kb)
        return

    if call.data == "shop_protect":
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🛡 5 min 💰2000", callback_data="protect_300"))
        kb.add(InlineKeyboardButton("🛡 10 min 💰4000", callback_data="protect_600"))
        kb.add(InlineKeyboardButton("🛡 15 min 💰6000", callback_data="protect_900"))
        kb.add(InlineKeyboardButton("⬅ Back", callback_data="shop_main"))
        bot.edit_message_text("🛡 Protection:", chat_id, call.message.message_id, reply_markup=kb)
        return

    if call.data == "shop_main":
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔫 Weapons", callback_data="shop_weapons"))
        kb.add(InlineKeyboardButton("💥 Breakers", callback_data="shop_breakers"))
        kb.add(InlineKeyboardButton("🛡 Armor", callback_data="shop_armor"))
        kb.add(InlineKeyboardButton("🛡 Protect", callback_data="shop_protect"))
        bot.edit_message_text("🛒 Shop Categories:", chat_id, call.message.message_id, reply_markup=kb)
        return


    # =========================
    # 🛡️ PROTECTION SYSTEM
    # =========================
    if call.data.startswith("protect_"):
        try:
            duration = int(call.data.split("_")[1])
        except:
            return bot.answer_callback_query(call.id, "Invalid")

        prices = {300: 2000, 600: 4000, 900: 6000}
        price = prices.get(duration)

        if not price:
            return bot.answer_callback_query(call.id, "Invalid option")

        shield.setdefault(chat_id, {})

        if uid in shield[chat_id]:
            left = int(shield[chat_id][uid] - time.time())
            if left > 0:
                return bot.answer_callback_query(call.id, "Already protected")
            else:
                del shield[chat_id][uid]

        if u["money"] < price:
            return bot.answer_callback_query(call.id, "❌ Not enough money")

        u["money"] -= price
        pay_job(chat_id, "protect", price)

        shield[chat_id][uid] = time.time() + duration

        save()
        bot.answer_callback_query(call.id, "🛡️ Protection activated!")
        return


    # =========================
    # 💥 BREAKER WEAPONS
    # =========================
    if call.data.startswith("buybreaker_"):
        item = call.data.split("_")[1]

        if item in BREAKER_WEAPONS:
            price = BREAKER_WEAPONS[item]["price"]

            if u["money"] >= price:
                u["money"] -= price
                pay_job(chat_id, "breaker", price)

                u["weapon"] = item
                save()

                bot.answer_callback_query(call.id, f"💥 {item} equipped")
            else:
                bot.answer_callback_query(call.id, "❌ Not enough money")

        return


    # =========================
    # 🛒 NORMAL SHOP
    # =========================
    if call.data.startswith("buy_"):
        item = call.data.split("_")[1]

        # 🛡️ ARMOR
        if item == "armor":
            if u["money"] >= ARMOR["price"]:
                u["money"] -= ARMOR["price"]
                pay_job(chat_id, "armor", ARMOR["price"])

                u["armor"] = True
                save()

                bot.answer_callback_query(call.id, "🛡️ Armor purchased")
            else:
                bot.answer_callback_query(call.id, "❌ Not enough money")
            return

        # 🔫 WEAPONS
        if item in WEAPONS:
            price = WEAPONS[item]["price"]

            if u["money"] >= price:
                u["money"] -= price
                pay_job(chat_id, "smith", price)

                u["weapon"] = item
                save()

                bot.answer_callback_query(call.id, f"🔫 {item} equipped")
            else:
                bot.answer_callback_query(call.id, "❌ Not enough money")

        return
    
    # =========================
    # 🍗 FOOD SYSTEM (FINAL FIXED)
    # =========================
    if call.data.startswith("buyfood"):
        item = call.data.replace("buyfood", "", 1)

        if item not in FOODS:
            return bot.answer_callback_query(call.id, "❌ Invalid food")

        price = FOODS[item]["price"]

    # 🎒 inventory check FIRST
        u.setdefault("inventory", [])
        if len(u["inventory"]) >= 20:
            return bot.answer_callback_query(call.id, "🎒 Inventory full")

        if u["money"] < price:
            return bot.answer_callback_query(call.id, "❌ Not enough money")

    # 💰 deduct
        u["money"] -= price

    # 💼 pay seller
        pay_job(chat_id, "food", price)

    # 🎒 add item
        u["inventory"].append(item)

        save()
        bot.answer_callback_query(call.id, f"🍗 Bought {item}")

        return
    

    # =========================
    # ⚔️ ARENA FIGHT (FINAL FIXED)
    # =========================
    if call.data.startswith("fight_"):
        try:
            _, uid1, uid2 = call.data.split("_")

            chat_id = str(call.message.chat.id)
            uid = str(call.from_user.id)

        # ❌ only target can click
            if uid != uid2:
                return bot.answer_callback_query(call.id, "❌ Not your duel")

        # 💀 dead check
            if uid1 in dead.get(chat_id, {}) or uid2 in dead.get(chat_id, {}):
                return bot.answer_callback_query(call.id, "💀 Player dead")

            attacker = users[chat_id][uid1]
            defender = users[chat_id][uid2]

            attacker.setdefault("duel", {"wins":0,"losses":0,"total":0})
            defender.setdefault("duel", {"wins":0,"losses":0,"total":0})

            s1 = attacker["stats"]
            s2 = defender["stats"]

            p1 = s1["strength"] + s1["muscles"] + s1["power"] + random.randint(0, 10)
            p2 = s2["strength"] + s2["muscles"] + s2["power"] + random.randint(0, 10)

            if p1 > p2:
                winner, loser = attacker, defender
            else:
                winner, loser = defender, attacker

            reward = random.randint(1000, 3000)

            winner["money"] += reward
            winner["stats"]["experience"] += 5
            loser["stats"]["experience"] += 2

            winner["duel"]["wins"] += 1
            loser["duel"]["losses"] += 1
            winner["duel"]["total"] += 1
            loser["duel"]["total"] += 1

            winner["hunger"] = max(0, winner["hunger"] - 3)
            loser["hunger"] = max(0, loser["hunger"] - 3)

            duel_cd.setdefault(chat_id, {})
            duel_cd[chat_id][uid1] = time.time()
            duel_cd[chat_id][uid2] = time.time()

            save()

            bot.answer_callback_query(call.id)

            bot.edit_message_text(
            f"""
    ⚔️ <b>FIGHT RESULT</b>

    🏆 Winner: <b>{winner['name']}</b>
    💰 Reward: {reward}
    """,
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML"
            )   

        except Exception as e:
            print("FIGHT ERROR:", e)
            bot.answer_callback_query(call.id, "⚠️ Error")
            return
    

    #=============================
    #rps PvP (was missing -> buttons did nothing, funds locked)
    # Same pot logic as /rps creation: pot = amt*2, winner takes pot.
    #=============================
    if call.data.startswith("rps_") and not call.data.startswith("rpsbot_"):
        try:
            _, p1, p2, move = call.data.split("_")
        except ValueError:
            return bot.answer_callback_query(call.id, "⚠️ Error")
        chat_id = str(call.message.chat.id)
        clicker = str(call.from_user.id)
        if move not in ("rock", "paper", "scissors"):
            return bot.answer_callback_query(call.id, "❌ Invalid move")
        if clicker not in (p1, p2):
            return bot.answer_callback_query(call.id, "❌ Not your duel")
        key = f"{chat_id}_{p1}_{p2}"
        if key not in rps_games:
            return bot.answer_callback_query(call.id, "Expired")
        game = rps_games[key]
        if time.time() - game["time"] > 30:
            # refund both (same as expire thread)
            try:
                users[chat_id][p1]["money"] += game["amt"]
                users[chat_id][p2]["money"] += game["amt"]
            except KeyError:
                pass
            del rps_games[key]
            save()
            return bot.answer_callback_query(call.id, "⏳ Expired (refunded)")
        if clicker in game["choices"]:
            return bot.answer_callback_query(call.id, "Already chosen, wait…")
        game["choices"][clicker] = move
        if len(game["choices"]) < 2:
            save()
            return bot.answer_callback_query(call.id, "✅ Locked! Waiting for opponent…")
        # Both chosen — resolve with same win() rules as bot mode
        m1 = game["choices"][p1]
        m2 = game["choices"][p2]
        amt = game["amt"]
        def _win(a, b):
            return (a == "rock" and b == "scissors") or \
                   (a == "paper" and b == "rock") or \
                   (a == "scissors" and b == "paper")
        if m1 == m2:
            users[chat_id][p1]["money"] += amt
            users[chat_id][p2]["money"] += amt
            result = f"🤝 Draw! Both chose {m1} (refunded)"
        elif _win(m1, m2):
            users[chat_id][p1]["money"] += amt * 2
            result = f"🏆 <b>{html.escape(users[chat_id][p1].get('name','P1'))}</b> wins {amt*2}! ({m1} beats {m2})"
        else:
            users[chat_id][p2]["money"] += amt * 2
            result = f"🏆 <b>{html.escape(users[chat_id][p2].get('name','P2'))}</b> wins {amt*2}! ({m2} beats {m1})"
        pay_job(chat_id, "casino", amt)
        del rps_games[key]
        save()
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            f"⚔️ <b>RPS DUEL RESULT</b>\n\n"
            f"👤 P1: {m1}\n👤 P2: {m2}\n\n{result}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )
        return

    #=============================
    #rps
    #=============================
    if call.data.startswith("rpsbot_"):
        _, uid, move = call.data.split("_")
        # Only the bet owner may click (prevents spending others' lock)
        if str(call.from_user.id) != uid:
            return bot.answer_callback_query(call.id, "❌ Not your game")
        chat_id = str(call.message.chat.id)

        key = f"{chat_id}_{uid}_bot"

        if key not in rps_games:
            return bot.answer_callback_query(call.id, "Expired")

        game = rps_games[key]

    # ⏳ timeout
        if time.time() - game["time"] > 30:
        # refund on timeout
            users[chat_id][uid]["money"] += game["amt"]
            del rps_games[key]
            return bot.answer_callback_query(call.id, "⏳ Expired (refunded)")

        bot_move = random.choice(["rock", "paper", "scissors"])
        u = users[chat_id][uid]
        amt = game["amt"]

        def win(a, b):
            return (a == "rock" and b == "scissors") or \
                   (a == "paper" and b == "rock") or \
                   (a == "scissors" and b == "paper")

    # 🎮 RESULT LOGIC (BET ALREADY LOCKED)
        if move == bot_move:
            u["money"] += amt  # refund
            result = "🤝 Draw (bet refunded)"

        elif win(move, bot_move):
            u["money"] += amt * 2  # win 2x
            result = f"🏆 You win {amt*2}!"

        else:
        # lose → no refund (already deducted)
            result = f"❌ You lost {amt}"

    # 💼 casino earnings (optional, you can reduce if needed)
        pay_job(chat_id, "casino", amt)

        del rps_games[key]
        save()

        bot.answer_callback_query(call.id)

        bot.edit_message_text(
            f"🎰 <b>RPS vs Bot</b>\n\n"
            f"👤 You: {move}\n"
            f"🤖 Bot: {bot_move}\n\n"
            f"{result}",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )

        return
    
    #=========================================
    #slot game 
    #=========================================
    if call.data.startswith("slotspin_"):
        _, uid = call.data.split("_")
        chat_id = str(call.message.chat.id)
        clicker = str(call.from_user.id)

    # ❌ only owner can click
        if clicker != uid:
            return bot.answer_callback_query(call.id, "Not your game")

        key = f"{chat_id}_{uid}"

        if key not in slot_games:
            return bot.answer_callback_query(call.id, "Game expired")

        game = slot_games[key]

    # ⏳ timeout (30s)
        if time.time() - game["time"] > 30:
            users[chat_id][uid]["money"] += game["bet"]  # refund
            del slot_games[key]
            return bot.answer_callback_query(call.id, "⏳ Expired (refunded)")

        bet = game["bet"]
        u = users[chat_id][uid]

    # 🎰 spin result
        r1 = random.choice(SLOT_SYMBOLS)
        r2 = random.choice(SLOT_SYMBOLS)
        r3 = random.choice(SLOT_SYMBOLS)

        result = f"{r1} | {r2} | {r3}"

        win = 0

        if r1 == r2 == r3:
            win = bet * 5
        elif r1 == r2 or r2 == r3 or r1 == r3:
            win = bet * 2

        u["money"] += win

    # 💼 casino job
        pay_job(chat_id, "casino", bet // 5)

        del slot_games[key]
        save()

        bot.answer_callback_query(call.id)

        if win > 0:
            text = f"🎰 {result}\n💰 You won {win}!"
        else:
            text = f"🎰 {result}\n💀 You lost {bet}"

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id
        )

        return
    
    #=============================
    # travel 
    #=============================
    if call.data.startswith("travel_"):

        _, owner, loc = call.data.split("_")

        if str(call.from_user.id) != owner:
            return bot.answer_callback_query(call.id, "❌ Not your menu")

        u = get_user(call.from_user, call.message.chat.id)

        if u["zone"] == loc:
            return bot.answer_callback_query(call.id, "Already there")

        price = 20000

        if u["money"] < price:
            return bot.answer_callback_query(call.id, "❌ Need 20000")

        u["money"] -= price
        u["zone"] = loc

        save()

        bot.edit_message_text(
            f"✈️ Travelled to {loc.upper()}\n💸 Cost: {price}",
            call.message.chat.id,
            call.message.message_id
        )

        return
    
    #=============================
    # mine game 
    #=============================
    if call.data.startswith("minebet_"):

        _, uid, amt, mult = call.data.split("_")

        if str(call.from_user.id) != uid:
            return bot.answer_callback_query(call.id, "❌ Not yours")

        amt = int(amt)
        mult = int(mult)

        # Validate multiplier (same reward table, no KeyError on tamper)
        if mult not in MINE_MULTIS:
            return bot.answer_callback_query(call.id, "❌ Invalid multiplier")

        u = get_user(call.from_user, call.message.chat.id)

        if u["money"] < amt:
            return bot.answer_callback_query(call.id, "No money")

        u["money"] -= amt

        safe_count = MINE_MULTIS[mult]

        safe_tiles = random.sample(range(30), safe_count)

        game_id = f"{call.message.chat.id}_{uid}"

        mine_games[game_id] = {
            "owner": uid,
            "bet": amt,
            "multi": mult,
            "safe": safe_tiles,
            "opened": [],
            "won": amt
        }

        save()

        kb = InlineKeyboardMarkup(row_width=6)

        for i in range(30):
            # .add respects row_width=6 (same 6-col grid; .insert() does not
            # exist in current pyTelegramBotAPI, crashed the game)
            kb.add(
                InlineKeyboardButton(
                    "❓",
                    callback_data=f"mineopen_{game_id}_{i}"
                )
            )

        kb.add(
            InlineKeyboardButton(
                "💰 Collect Winning",
                callback_data=f"minecash_{game_id}"
            )
        )

        bot.edit_message_text(
            f"💣 Mine Game Started\nMultiplier: {mult}x",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb
        )

        return
    
    #=============================
    # mine game - open tile
    #=============================
    if call.data.startswith("mineopen_"):

        parts = call.data.split("_")

        game_id = f"{parts[1]}_{parts[2]}"
        pos = int(parts[3])

        if game_id not in mine_games:
            bot.answer_callback_query(call.id, "Game expired")
            return

        game = mine_games[game_id]

        if str(call.from_user.id) != game["owner"]:
            return bot.answer_callback_query(call.id, "❌ Not your game")

        if pos in game["opened"]:
            return bot.answer_callback_query(call.id, "Already opened")

        game["opened"].append(pos)

        if pos in game["safe"]:

            game["won"] *= game["multi"]

            save()

            bot.answer_callback_query(
                call.id,
                f"✅ Safe! Win: {game['won']}"
            )

        else:

            del mine_games[game_id]

            save()

            return bot.edit_message_text(
                "💣 BOOM!\nYou lost everything",
                call.message.chat.id,
                call.message.message_id
            )
        
    #=============================
    # mine game - cash out  
    #=============================
    if call.data.startswith("minecash_"):

        game_id = call.data.split("minecash_", 1)[1]

        if game_id not in mine_games:
            bot.answer_callback_query(call.id, "Game expired")
            return

        game = mine_games[game_id]

        if str(call.from_user.id) != game["owner"]:
            bot.answer_callback_query(call.id, "❌ Not your game")
            return

        u = get_user(call.from_user, call.message.chat.id)

        u["money"] += game["won"]

        won = game["won"]

        del mine_games[game_id]

        save()

        bot.edit_message_text(
            f"💰 Cashed Out!\nWon: {won}",
            call.message.chat.id,
            call.message.message_id
        )

    #=============================
    # top players
    #=============================
    if call.data.startswith("top_"):

        try:
            page = int(call.data.split("_")[1])
        except (ValueError, IndexError):
            return bot.answer_callback_query(call.id, "⚠️ Error")

        chat_id = str(call.message.chat.id)

        sorted_users = sorted(
            users.get(chat_id, {}).items(),
            key=lambda x: x[1].get("money", 0) + x[1].get("bank", 0),
            reverse=True
        )

        total_pages = max(1, (len(sorted_users)+9)//10)

        if page < 0:
            page = 0

        if page >= total_pages:
            page = total_pages - 1

        text, kb = build_top_page(chat_id, page)

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb
        )

        return

















@bot.message_handler(commands=['kill'])
def kill(msg):
    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to target")

    uid = str(msg.from_user.id)
    tgt_id = str(msg.reply_to_message.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 
    tgt_user = msg.reply_to_message.from_user

    # 🚫 block bots
    if tgt_user.is_bot:
        return bot.send_message(msg.chat.id, "🤖 You can't attack bots")

    if check_dead_block(msg, uid):
        return

    if uid == tgt_id:
        return bot.send_message(msg.chat.id, "❌ You can't kill yourself")
    
    

    now = time.time()

    # 🔥 ensure dicts exist
    dead.setdefault(chat_id, {})
    jail.setdefault(chat_id, {})
    shield.setdefault(chat_id, {})
    kill_cd.setdefault(chat_id, {})

    # 💀 target dead check
    if tgt_id in dead[chat_id]:
        return bot.send_message(
            msg.chat.id,
            f"💀 {tgt_user.first_name} is already dead!"
        )

    # 🔁 cooldown
    if uid in kill_cd[chat_id] and now - kill_cd[chat_id][uid] < 600:
        left = int(600 - (now - kill_cd[chat_id][uid]))
        return bot.send_message(msg.chat.id, f"⏳ Wait {left}s")

    
    
    # 🔥 FIX: user per chat
    atk = get_user(msg.from_user, msg.chat.id)


    # 🛡️ shield check
    if tgt_id in shield[chat_id]:
        if time.time() < shield[chat_id][tgt_id]:

            if atk.get("weapon") == "breaker" and random.random() < 0.6:
                del shield[chat_id][tgt_id]
                bot.send_message(msg.chat.id, "💥 Shield destroyed!")
            else:
                return bot.send_message(msg.chat.id, "🛡️ Target is protected")
        else:
            del shield[chat_id][tgt_id]

    tgt = get_user(msg.reply_to_message.from_user, msg.chat.id)

    if atk.get("gang") and atk["gang"] == tgt.get("gang"):
        return bot.send_message(msg.chat.id, "👥 You can't attack your gang member")

    base = 0.6   # upgraded
    risk = 0.15

    if atk["weapon"]:
        _wtable = {**WEAPONS, **BREAKER_WEAPONS}
        w = _wtable.get(atk["weapon"])
        if w:
            base = min(1.0, w["rate"] + 0.1)
            risk += w["risk"]

    if tgt["armor"]:
        base -= ARMOR["reduce"]

    # 🍗 hunger penalty
    if atk["hunger"] < 30:
        base -= 0.1

    base = max(0.1, min(base, 1.0))

    # ⚔️ result
    if random.random() < base:
        loot = min(1500, tgt["money"])
        tgt["money"] -= loot
        atk["money"] += loot

        # 💀 mark dead (per chat)
        dead[chat_id][tgt_id] = True

        bot.send_message(
            msg.chat.id,
            f"💀 {tgt['name']} is DEAD!\nUse /revive\n💰 {atk['name']} looted {loot}"
        )
    else:
        bot.send_message(msg.chat.id, "❌ Kill failed")

    # 🚔 arrest
    if random.random() < risk:
        jail[chat_id][uid] = now

        users[chat_id][uid].setdefault("crime", {"caught": 0})
        users[chat_id][uid]["crime"]["caught"] += 1

        bot.send_message(msg.chat.id, "🚔 Police caught you!")

    # ⏱️ cooldown
    kill_cd[chat_id][uid] = now

    use_hunger(atk, 3)

    save()


def is_dead(chat_id, uid):
    chat_id = str(chat_id)
    uid = str(uid)

    return chat_id in dead and uid in dead[chat_id]


def check_dead_block(msg, uid, action=None, silent=False):
    chat_id = ensure_chat(msg.chat.id)

    if uid in banned.get(chat_id, {}):
        if not silent:
            bot.send_message(msg.chat.id, "🚫 You are banned from this game")
        return True

    # allow some actions when dead
    if action in ["withdraw", "revive", "status"]:
        return False

    if is_dead(chat_id, uid):
        if not silent:
            bot.send_message(
                msg.chat.id,
                "💀 You are DEAD!\nOnly allowed: /revive /withdraw /status"
            )
        return True

    return False







@bot.message_handler(commands=['protect'])
def protect(msg):
    chat_id = ensure_chat(msg.chat.id) 
    uid = str(msg.from_user.id)

    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    shield.setdefault(chat_id, {})

    # ❌ already protected
    if uid in shield[chat_id]:
        left = int(shield[chat_id][uid] - time.time())
        if left > 0:
            return bot.send_message(
                msg.chat.id,
                f"🛡️ Already protected for {left}s"
            )
        else:
            del shield[chat_id][uid]

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🛡️ 5 min - 💰2000", callback_data="protect_300"),
        InlineKeyboardButton("🛡️ 10 min - 💰4000", callback_data="protect_600"),
        InlineKeyboardButton("🛡️ 15 min - 💰6000", callback_data="protect_900")
    )

    bot.send_message(msg.chat.id, "🛡️ Choose protection:", reply_markup=kb)








@bot.message_handler(commands=['rob'])
def rob(msg):
    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to target")

    uid = str(msg.from_user.id)
    tgt_id = str(msg.reply_to_message.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 
    tgt_user = msg.reply_to_message.from_user

    # 🚫 block bots
    if tgt_user.is_bot:
        return bot.send_message(msg.chat.id, "🤖 You can't rob bots")

    if check_dead_block(msg, uid):
        return

    if uid == tgt_id:
        return bot.send_message(msg.chat.id, "❌ You can't rob yourself")


    
    now = time.time()

    # 🔥 ensure dicts exist
    dead.setdefault(chat_id, {})
    jail.setdefault(chat_id, {})
    rob_cd.setdefault(chat_id, {})

    # 🛡️ shield check (ADD THIS)
    shield.setdefault(chat_id, {})


    # 💀 target dead check
    if tgt_id in dead[chat_id]:
        return bot.send_message(msg.chat.id, "💀 Target is dead")

    # 🚔 jail check
    if uid in jail[chat_id] and now - jail[chat_id][uid] < 120:
        left = int(120 - (now - jail[chat_id][uid]))
        return bot.send_message(msg.chat.id, f"🚔 You're jailed for {left}s")

    # ⏳ cooldown (2 min)
    if uid in rob_cd[chat_id] and now - rob_cd[chat_id][uid] < 120:
        left = int(120 - (now - rob_cd[chat_id][uid]))
        return bot.send_message(msg.chat.id, f"⏳ Wait {left}s")

    # 🔥 FIX: user per chat
    atk = get_user(msg.from_user, msg.chat.id)
    tgt = get_user(msg.reply_to_message.from_user, msg.chat.id)

    use_hunger(atk, 2)



    if tgt_id in shield[chat_id]:
        if time.time() < shield[chat_id][tgt_id]:

            if atk.get("weapon") == "breaker" and random.random() < 0.5:
                del shield[chat_id][tgt_id]
                bot.send_message(msg.chat.id, "💥 Shield broken!")
            else:
                return bot.send_message(msg.chat.id, "🛡️ Target is protected")

    if atk.get("gang") and atk["gang"] == tgt.get("gang"):
        return bot.send_message(msg.chat.id, "👥 You can't attack your gang member")

    if tgt["money"] <= 0:
        return bot.send_message(msg.chat.id, "💸 Target is broke")

    # 🎲 success chance
    success = 0.7

    if atk["weapon"]:
        success += 0.1

    if tgt["armor"]:
        success -= 0.2

    if atk.get("level", 1) > tgt.get("level", 1):
        success += 0.05

    success = max(0.2, min(success, 0.9))

    if random.random() < success:
        if tgt["money"] < 100:
            amt = tgt["money"]
        else:
            amt = random.randint(100, min(1000, tgt["money"]))

        tgt["money"] -= amt
        atk["money"] += amt

        bot.send_message(msg.chat.id, f"💰 Rob success! +{amt}")
    else:
        jail[chat_id][uid] = now

        users[chat_id][uid].setdefault("crime", {"caught": 0})
        users[chat_id][uid]["crime"]["caught"] += 1

        bot.send_message(msg.chat.id, "🚔 Caught by police!")

    # ⏱️ cooldown
    rob_cd[chat_id][uid] = now

    save()



@bot.message_handler(commands=['arrest'])
def arrest(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 💀 dead / banned check
    if check_dead_block(msg, uid):
        return

    # 🔒 must reply
    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to target")

    target = str(msg.reply_to_message.from_user.id)

    # 🚔 check police job
    if job_owner.get(chat_id, {}).get("police") != uid:
        return bot.send_message(msg.chat.id, "🚫 You are not police")

    if target not in users.get(chat_id, {}):
        return bot.send_message(msg.chat.id, "❌ Invalid target")

    u = users[chat_id][target]

    # 🔥 ensure crime exists
    u.setdefault("crime", {"caught": 0})

    # ❌ not criminal
    if u["crime"]["caught"] < 5:
        return bot.send_message(msg.chat.id, "❌ Target is not criminal")

    # 🚔 arrest
    jail.setdefault(chat_id, {})
    jail[chat_id][target] = time.time()

    fine = 2000

    # 💰 fine system
    if u["money"] >= fine:
        u["money"] -= fine
    else:
        u["money"] = 0

    # 💼 pay police
    pay_job(chat_id, "police", fine)

    save()

    bot.send_message(
        msg.chat.id,
        f"🚔 {u['name']} arrested!\n💸 Fine: {fine}"
    )

def is_criminal(u):
    return u.get("crime", {}).get("caught", 0) >= 5


















@bot.message_handler(commands=['revive'])
def revive(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    dead.setdefault(chat_id, {})
    shield.setdefault(chat_id, {})

    # ❌ not dead
    if uid not in dead[chat_id]:
        return bot.send_message(msg.chat.id, "❌ You're not dead")

    u = get_user(msg.from_user, msg.chat.id)

    revive_cost = 1000  # 🔥 NEW PRICE (change here anytime)

    # 💸 not enough money
    if u["money"] < revive_cost:
        return bot.send_message(msg.chat.id, f"💸 Need {revive_cost}")

    # 💰 deduct correct amount
    u["money"] -= revive_cost

    # 💀 remove death
    dead[chat_id].pop(uid, None)

    # 🍗 restore hunger
    u["hunger"] = 100

    # 🛡️ protection
    shield[chat_id][uid] = time.time() + 300

    save()

    bot.send_message(
        msg.chat.id,
        f"❤️ Revived!\n💸 Cost: {revive_cost}\n🍗 Hunger: 100/100\n🛡️ 5 min protection"
    )



@bot.message_handler(commands=['panel'])
def panel(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id)

    u = get_user(msg.from_user, msg.chat.id)

    # 🔥 ensure dicts
    dead.setdefault(chat_id, {})
    shield.setdefault(chat_id, {})
    jail.setdefault(chat_id, {})

    # 🔒 safe duel init
    u.setdefault("duel", {"wins": 0, "losses": 0, "total": 0})

    now = time.time()

    # 💰 money
    wallet = u.get("money", 0)
    bank = u.get("bank", 0)
    total = wallet + bank

    # 💎 ranks
    rank = get_money_rank(total)
    duel_rank = get_duel_rank(u["duel"]["wins"])

    # ⚔️ duel stats
    wins = u["duel"]["wins"]
    losses = u["duel"]["losses"]
    total_fights = u["duel"]["total"]
    winrate = round((wins / total_fights) * 100, 2) if total_fights > 0 else 0

    # 🚨 crime
    crime = u.get("crime", {}).get("caught", 0)

    # =========================
    # 📊 MAIN PANEL
    # =========================
    text = f"""
📊 <b>PLAYER PANEL</b>

👤 <b>{html.escape(str(u['name']))}</b>

💎 Rank: <b>{rank}</b>
⚔️ Duel Rank: <b>{duel_rank}</b>

💰 Wallet: {wallet}
🏦 Bank: {bank}
💼 Total: <b>{total}</b>

🏆 Level: {u.get('level', 1)}
🗺️ Zone: {html.escape(str(u.get('zone', 'Unknown')))}

⚔️ Weapon: {html.escape(str(u.get('weapon', 'None')))}
🛡️ Armor: {u.get('armor', False)}
👥 Gang: {html.escape(str(u.get('gang', 'None')))}

🍗 Hunger: {u.get('hunger',100)}/100
"""

    # =========================
    # ⚔️ DUEL STATS
    # =========================
    text += f"""
<blockquote>
⚔️ Duel Stats
• Fights: {total_fights}
• Wins: {wins}
• Losses: {losses}
• Win Rate: {winrate}%
</blockquote>
"""

    # =========================
    # 🚨 CRIME
    # =========================
    if crime >= 5:
        text += f"\n🚨 <b>CRIMINAL</b> ({crime})"
    elif crime > 0:
        text += f"\n⚠️ Crime: {crime}/5"

    # =========================
    # 📉 STATUS EFFECTS
    # =========================
    if uid in dead[chat_id]:
        text += "\n💀 <b>Status:</b> DEAD"

    # 🛡️ shield
    if uid in shield[chat_id]:
        left = int(shield[chat_id][uid] - now)
        if left > 0:
            text += f"\n🛡️ Protection: {left}s"
        else:
            del shield[chat_id][uid]

    # 🚔 jail
    if uid in jail[chat_id]:
        left = int(120 - (now - jail[chat_id][uid]))
        if left > 0:
            text += f"\n🚔 Jail: {left}s"

    bot.send_message(msg.chat.id, text, parse_mode="HTML")






@bot.message_handler(commands=['status'])
def status(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id)

    u = get_user(msg.from_user, msg.chat.id)

    # 🔥 ensure dicts
    kill_cd.setdefault(chat_id, {})
    rob_cd.setdefault(chat_id, {})
    jail.setdefault(chat_id, {})
    shield.setdefault(chat_id, {})
    dead.setdefault(chat_id, {})

    now = time.time()

    # 💰 totals
    wallet = u.get("money", 0)
    bank = u.get("bank", 0)
    total = wallet + bank

    # 💎 ranks
    rank = get_money_rank(total)
    duel_rank = get_duel_rank(u.get("duel", {}).get("wins", 0))

    # 🚨 crime
    crime = u.get("crime", {}).get("caught", 0)

    # =========================
    # 🧾 BASE PROFILE
    # =========================
    txt = f"""
👤 <b>{u['name']}</b>

💎 Rank: <b>{rank}</b>
⚔️ Duel Rank: <b>{duel_rank}</b>

💰 Wallet: {wallet}
🏦 Bank: {bank}
💼 Total: {total}

⚔️ Weapon: {u.get('weapon', 'None')}
🛡️ Armor: {u.get('armor', False)}
👥 Gang: {u.get('gang', 'None')}

🍗 Hunger: {u.get('hunger',100)}/100
"""

    # =========================
    # 🚨 CRIME STATUS
    # =========================
    if crime >= 5:
        txt += f"\n🚨 <b>Criminal Level:</b> {crime}"
    elif crime > 0:
        txt += f"\n⚠️ Crime: {crime}/5"

    # =========================
    # 📊 STATUS EFFECTS
    # =========================
    if uid in dead[chat_id]:
        txt += "\n💀 <b>Status:</b> DEAD"

    # ⏳ kill cooldown
    if uid in kill_cd[chat_id]:
        left = int(600 - (now - kill_cd[chat_id][uid]))
        if left > 0:
            txt += f"\n⏳ Kill CD: {left}s"

    # 🦹 rob cooldown
    if uid in rob_cd[chat_id]:
        left = int(120 - (now - rob_cd[chat_id][uid]))
        if left > 0:
            txt += f"\n🦹 Rob CD: {left}s"

    # 🚔 jail
    if uid in jail[chat_id]:
        left = int(120 - (now - jail[chat_id][uid]))
        if left > 0:
            txt += f"\n🚔 Jail: {left}s"

    # 🛡️ shield
    if uid in shield[chat_id]:
        left = int(shield[chat_id][uid] - now)
        if left > 0:
            txt += f"\n🛡️ Protection: {left}s"
        else:
            del shield[chat_id][uid]

    bot.send_message(msg.chat.id, txt, parse_mode="HTML")




# ===== GANG =====
@bot.message_handler(commands=['creategang'])
def cg(msg):
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /creategang name")

    name = parts[1]
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    if check_dead_block(msg, uid):
        return

    gangs.setdefault(chat_id, {})

    if name in gangs[chat_id]:
        return bot.send_message(msg.chat.id, "❌ Gang already exists")

    gangs[chat_id][name] = [uid]

    u = get_user(msg.from_user, msg.chat.id)
    u["gang"] = name

    save()
    bot.send_message(msg.chat.id, f"👥 Gang '{name}' created!")

@bot.message_handler(commands=['joingang'])
def jg(msg):
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /joingang name")

    name = parts[1]
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    if check_dead_block(msg, uid):
        return

    if chat_id not in gangs or name not in gangs[chat_id]:
        return bot.send_message(msg.chat.id, "❌ Gang not found")

    # Prevent duplicate membership (same logic, no double entries)
    if uid in gangs[chat_id][name]:
        return bot.send_message(msg.chat.id, "❌ Already in this gang")

    gangs[chat_id][name].append(uid)

    u = get_user(msg.from_user, msg.chat.id)
    u["gang"] = name

    save()
    bot.send_message(msg.chat.id, f"👥 Joined {name}")


@bot.message_handler(commands=['ganginvite'])
def invite(msg):
    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to user to invite")

    uid = str(msg.from_user.id)
    tgt_id = str(msg.reply_to_message.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    u = get_user(msg.from_user, msg.chat.id)

    if not u["gang"]:
        return bot.send_message(msg.chat.id, "❌ You are not in a gang")

    gang = u["gang"]

    invites.setdefault(chat_id, {})
    invites[chat_id][tgt_id] = gang

    bot.send_message(
        msg.chat.id,
        f"📩 {msg.reply_to_message.from_user.first_name}, you are invited to join '{gang}'\nUse /acceptgang"
    )

@bot.message_handler(commands=['acceptgang'])
def acceptgang(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    if chat_id not in invites or uid not in invites[chat_id]:
        return bot.send_message(msg.chat.id, "❌ No invite")

    gang = invites[chat_id][uid]

    gangs.setdefault(chat_id, {})
    gangs[chat_id].setdefault(gang, [])

    if uid not in gangs[chat_id][gang]:
        gangs[chat_id][gang].append(uid)

    u = get_user(msg.from_user, msg.chat.id)
    u["gang"] = gang

    del invites[chat_id][uid]

    save()
    bot.send_message(msg.chat.id, f"👥 Joined {gang}")


#=============casino=====================







casino_cd = {}  # 🔥 add at top


@bot.message_handler(commands=['casino'])
def casino(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 💀 dead / banned check
    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 🗺️ ZONE RESTRICTION
    if u["zone"] != "casino":
        return bot.send_message(msg.chat.id, "🎰 Go to CASINO to play")

    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /casino amount")

    # 🔢 safe parse
    try:
        amt = int(parts[1])
    except:
        return bot.send_message(msg.chat.id, "Invalid amount")

    # ❌ validation
    if amt <= 0:
        return bot.send_message(msg.chat.id, "❌ Amount must be positive")

    if amt > 50000:
        return bot.send_message(msg.chat.id, "❌ Max bet is 50,000")

    if u["money"] < amt:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # ⏳ COOLDOWN (3 sec)
    casino_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in casino_cd[chat_id] and now - casino_cd[chat_id][uid] < 3:
        return bot.send_message(msg.chat.id, "⏳ Slow down")

    casino_cd[chat_id][uid] = now

    # 🎲 GAME LOGIC
    win_chance = 0.45

    # 🔫 weapon bonus
    if u.get("weapon"):
        win_chance += 0.05

    # 🛡 armor reduces luck (balancing)
    if u.get("armor"):
        win_chance -= 0.05

    # 🍗 hunger penalty
    if u["hunger"] < 30:
        win_chance -= 0.1

    win_chance = max(0.2, min(win_chance, 0.7))

    roll = random.random()

    if roll < win_chance:
        profit = amt  # profit = same as bet
        u["money"] += profit

        bot.send_message(
            msg.chat.id,
            f"🎰 WIN!\n💰 Bet: {amt}\n📈 Profit: +{profit}"
        )
    else:
        u["money"] -= amt

        bot.send_message(
            msg.chat.id,
            f"💀 LOST!\n💸 Lost: {amt}"
        )

    # 💼 PAY CASINO OWNER
    pay_job(chat_id, "casino", amt)
    u["hunger"] = max(0, u["hunger"] - 2)

    # 💥 bankruptcy check
    check_bankrupt(chat_id, uid)

    save()


# 🔥 add at top
bet_cd = {}

@bot.message_handler(commands=['bet'])
def bet(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 🗺️ only in casino
    if u["zone"] != "casino":
        return bot.send_message(msg.chat.id, "🎰 Go to CASINO to play")

    parts = msg.text.split()
    if len(parts) < 3:
        return bot.send_message(msg.chat.id, "Usage: /bet number amount (1-10)")

    # 🔢 safe parse
    try:
        num = int(parts[1])
        amt = int(parts[2])
    except:
        return bot.send_message(msg.chat.id, "Invalid input")

    if num < 1 or num > 10:
        return bot.send_message(msg.chat.id, "Pick number 1-10")

    if amt <= 0:
        return bot.send_message(msg.chat.id, "❌ Amount must be positive")

    if amt > 30000:
        return bot.send_message(msg.chat.id, "❌ Max bet is 30,000")

    if u["money"] < amt:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # ⏳ cooldown (3 sec)
    bet_cd.setdefault(chat_id, {})
    now = time.time()
    if uid in bet_cd[chat_id] and now - bet_cd[chat_id][uid] < 3:
        return bot.send_message(msg.chat.id, "⏳ Slow down")
    bet_cd[chat_id][uid] = now

    # 🎲 roll
    roll = random.randint(1, 10)

    if num == roll:
        win = amt * 4  # balanced (was 5x, too OP)
        u["money"] += win
        result = f"🎯 Correct! Number was {roll}\n💰 You won {win}"
    else:
        u["money"] -= amt
        result = f"❌ Wrong! Number was {roll}\n💸 You lost {amt}"

    pay_job(chat_id, "casino", amt)
    check_bankrupt(chat_id, uid)
    save()

    bot.send_message(msg.chat.id, result)





color_cd = {}

@bot.message_handler(commands=['color'])
def color_bet(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 🗺️ casino only
    if u["zone"] != "casino":
        return bot.send_message(msg.chat.id, "🎰 Go to CASINO")

    parts = msg.text.split()
    if len(parts) < 3:
        return bot.send_message(msg.chat.id, "Usage: /color red|black|green amount")

    choice = parts[1].lower()

    try:
        amt = int(parts[2])
    except:
        return bot.send_message(msg.chat.id, "Invalid amount")

    if choice not in ["red", "black", "green"]:
        return bot.send_message(msg.chat.id, "Choose red, black, or green")

    if amt <= 0 or amt > 50000:
        return bot.send_message(msg.chat.id, "Invalid bet amount")

    if u["money"] < amt:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # ⏳ cooldown
    color_cd.setdefault(chat_id, {})
    now = time.time()
    if uid in color_cd[chat_id] and now - color_cd[chat_id][uid] < 3:
        return bot.send_message(msg.chat.id, "⏳ Wait a bit")
    color_cd[chat_id][uid] = now

    # 🎡 roll system
    roll = random.random()

    if roll < 0.45:
        result_color = "red"
    elif roll < 0.9:
        result_color = "black"
    else:
        result_color = "green"

    # 🎯 result
    if choice == result_color:
        if choice == "green":
            win = amt * 5
        else:
            win = amt * 2

        u["money"] += win
        msg_txt = f"🎨 Result: {result_color.upper()}\n💰 You won {win}"
    else:
        u["money"] -= amt
        msg_txt = f"🎨 Result: {result_color.upper()}\n💀 You lost {amt}"

    pay_job(chat_id, "casino", amt)
    check_bankrupt(chat_id, uid)
    save()

    bot.send_message(msg.chat.id, msg_txt)



@bot.message_handler(commands=['rps'])
def rps(msg):
    chat_id = str(msg.chat.id)
    uid = str(msg.from_user.id)

    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    if u.get("zone") != "casino":
        return bot.send_message(msg.chat.id, "🎰 Go to CASINO")

    parts = msg.text.split()

    if len(parts) < 2:
        return bot.send_message(
            msg.chat.id,
            "Usage:\n/rps amount (solo)\nReply /rps amount (vs user)"
        )

    try:
        amt = int(parts[1])
    except:
        return bot.send_message(msg.chat.id, "❌ Invalid amount")

    if amt <= 0 or amt > 100000:
        return bot.send_message(msg.chat.id, "❌ Invalid bet")

    if u["money"] < amt:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # =========================
    # ⏳ COOLDOWN (60 sec)
    # =========================
    rps_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in rps_cd[chat_id]:
        left = int(60 - (now - rps_cd[chat_id][uid]))
        if left > 0:
            return bot.send_message(msg.chat.id, f"⏳ Wait {left}s")

    rps_cd[chat_id][uid] = now

    # =========================
    # ❌ prevent multiple games
    # =========================
    key_check = f"{chat_id}_{uid}"
    for k in rps_games:
        if uid in k:
            return bot.send_message(msg.chat.id, "⏳ Finish current RPS first")

    # =========================
    # 🎯 USER VS USER
    # =========================
    if msg.reply_to_message and not msg.reply_to_message.from_user.is_bot:
        target = str(msg.reply_to_message.from_user.id)
        u2 = get_user(msg.reply_to_message.from_user, msg.chat.id)

        if uid == target:
            return bot.send_message(msg.chat.id, "❌ Can't play yourself")

        if u2["money"] < amt:
            return bot.send_message(msg.chat.id, "❌ Target doesn't have enough money")

        # 🔒 lock money
        u["money"] -= amt
        u2["money"] -= amt

        kb = InlineKeyboardMarkup()
        for move in ["rock", "paper", "scissors"]:
            kb.add(InlineKeyboardButton(move.capitalize(), callback_data=f"rps_{uid}_{target}_{move}"))

        bot.send_message(
            msg.chat.id,
            f"⚔️ <b>RPS DUEL</b>\n\n💰 Pot: {amt*2}\n⏳ 30s to choose",
            reply_markup=kb,
            parse_mode="HTML"
        )

        key = f"{chat_id}_{uid}_{target}"
        rps_games[key] = {
            "p1": uid,
            "p2": target,
            "amt": amt,
            "choices": {},
            "time": now
        }

        # ⏳ auto expire
        def expire():
            time.sleep(30)
            if key in rps_games:
                # refund both players
                users[chat_id][uid]["money"] += amt
                users[chat_id][target]["money"] += amt
                del rps_games[key]

        threading.Thread(target=expire, daemon=True).start()

    # =========================
    # 🤖 BOT MODE (HARDER)
    # =========================
    else:
        u["money"] -= amt

        kb = InlineKeyboardMarkup()
        for move in ["rock", "paper", "scissors"]:
            kb.add(InlineKeyboardButton(move.capitalize(), callback_data=f"rpsbot_{uid}_{move}"))

        bot.send_message(
            msg.chat.id,
            f"🎰 <b>RPS vs BOT</b>\n\n💰 Bet: {amt}\n🏆 Win: {int(amt*2)}\n⏳ 30s",
            reply_markup=kb,
            parse_mode="HTML"
        )

        key = f"{chat_id}_{uid}_bot"
        rps_games[key] = {
            "p1": uid,
            "amt": amt,
            "time": now
        }

    save()

  # 🔥 add at top




SPIN_REWARDS = [
    ("💰 +100", 100),
    ("💰 +250", 250),
    ("💰 +500", 500),
    ("💀 -100", -100),
    ("💀 -250", -250),
    ("🎁 Jackpot +1000", 1000),
    ("😐 Nothing", 0)
]

@bot.message_handler(commands=['spin'])
def spin_wheel(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 💀 dead check
    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 🎰 casino only
    if u.get("zone") != "casino":
        return bot.send_message(msg.chat.id, "🎰 Go to CASINO")

    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /spin amount")

    # 💰 amount
    try:
        amt = int(parts[1])
    except:
        return bot.send_message(msg.chat.id, "❌ Invalid amount")

    if amt <= 0:
        return bot.send_message(msg.chat.id, "❌ Amount must be positive")

    if amt > 100000:
        return bot.send_message(msg.chat.id, "❌ Max bet is 100,000")

    if u["money"] < amt:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # =========================
    # ⏳ COOLDOWN (60 sec)
    # =========================
    spin_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in spin_cd[chat_id]:
        elapsed = now - spin_cd[chat_id][uid]
        if elapsed < 60:
            left = int(60 - elapsed)
            return bot.send_message(msg.chat.id, f"⏳ Wait {left}s before spinning again")

    spin_cd[chat_id][uid] = now

    # =========================
    # 🔒 lock bet
    # =========================
    u["money"] -= amt

    # =========================
    # 🎡 spin result
    # =========================
    reward_text, value = random.choice(SPIN_REWARDS)

    # 💰 apply result
    final = value
    u["money"] += final

    # =========================
    # 💼 casino job earning
    # =========================
    if final > 0:
        pay_job(chat_id, "casino", final // 5)

    # =========================
    # 💥 bankruptcy check
    # =========================
    check_bankrupt(chat_id, uid)

    save()

    # =========================
    # 📩 output
    # =========================
    bot.send_message(
        msg.chat.id,
        f"""
🎡 <b>SPIN RESULT</b>

{reward_text}

💰 Bet: {amt}
📊 Result: {final}
""",
        parse_mode="HTML"
    )



# 🎰 symbols
SLOT_SYMBOLS = ["🍒", "🍋", "🍉", "🔔", "⭐", "💎"]

@bot.message_handler(commands=['slot'])
def slot_game(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 💀 dead check
    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 📍 zone check
    if u.get("zone") != "casino":
        return bot.send_message(msg.chat.id, "🎰 Go to CASINO")

    # =========================
    # ⏳ COOLDOWN (60 sec)
    # =========================
    slot_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in slot_cd[chat_id]:
        elapsed = now - slot_cd[chat_id][uid]
        if elapsed < 60:
            left = int(60 - elapsed)
            return bot.send_message(msg.chat.id, f"⏳ Wait {left}s before playing again")

    # =========================
    # ❌ prevent multiple active games
    # =========================
    key = f"{chat_id}_{uid}"
    if key in slot_games:
        return bot.send_message(msg.chat.id, "⏳ Finish your previous slot first")

    # =========================
    # 💰 get bet
    # =========================
    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /slot <amount>")

    try:
        bet = int(parts[1])
    except:
        return bot.send_message(msg.chat.id, "❌ Invalid amount")

    if bet <= 0:
        return bot.send_message(msg.chat.id, "❌ Bet must be positive")

    if bet > 100000:
        return bot.send_message(msg.chat.id, "❌ Max bet is 100,000")

    if u["money"] < bet:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # 🔒 lock bet
    u["money"] -= bet

    # =========================
    # 🎮 store game
    # =========================
    slot_games[key] = {
        "bet": bet,
        "time": now
    }

    # ⏳ start cooldown
    slot_cd[chat_id][uid] = now

    # =========================
    # 🎯 UI (3x2 grid)
    # =========================
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("🍒", callback_data=f"slotspin_{uid}"),
        InlineKeyboardButton("🍋", callback_data=f"slotspin_{uid}"),
        InlineKeyboardButton("🍉", callback_data=f"slotspin_{uid}")
    )
    kb.add(
        InlineKeyboardButton("🔔", callback_data=f"slotspin_{uid}"),
        InlineKeyboardButton("⭐", callback_data=f"slotspin_{uid}"),
        InlineKeyboardButton("💎", callback_data=f"slotspin_{uid}")
    )

    bot.send_message(
        msg.chat.id,
        f"""
🎰 <b>SLOT MACHINE</b>

💰 Bet: {bet}

Tap any symbol to spin!
""",
        reply_markup=kb,
        parse_mode="HTML"
    )

    save()










@bot.message_handler(commands=['coin'])
def coin_flip(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 💀 dead check
    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 🎰 casino only
    if u.get("zone") != "casino":
        return bot.send_message(msg.chat.id, "🎰 Go to CASINO")

    parts = msg.text.split()
    if len(parts) < 3:
        return bot.send_message(msg.chat.id, "Usage: /coin heads|tails amount")

    choice = parts[1].lower()

    # 💰 amount parsing
    try:
        amt = int(parts[2])
    except:
        return bot.send_message(msg.chat.id, "❌ Invalid amount")

    # 🎯 validation
    if choice not in ["heads", "tails"]:
        return bot.send_message(msg.chat.id, "❌ Choose heads or tails")

    if amt <= 0:
        return bot.send_message(msg.chat.id, "❌ Amount must be positive")

    if amt > 50000:
        return bot.send_message(msg.chat.id, "❌ Max bet is 50,000")

    if u["money"] < amt:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # =========================
    # ⏳ COOLDOWN (60 sec)
    # =========================
    coin_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in coin_cd[chat_id]:
        elapsed = now - coin_cd[chat_id][uid]
        if elapsed < 60:
            left = int(60 - elapsed)
            return bot.send_message(msg.chat.id, f"⏳ Wait {left}s before flipping again")

    coin_cd[chat_id][uid] = now

    # =========================
    # 🎲 FLIP
    # =========================
    result = random.choice(["heads", "tails"])

    # =========================
    # 💰 RESULT LOGIC
    # =========================
    if choice == result:
        profit = amt
        u["money"] += profit
        outcome = f"🎉 You won +{profit}"
    else:
        u["money"] -= amt
        outcome = f"💀 You lost {amt}"

    # =========================
    # 💼 CASINO JOB EARNINGS
    # =========================
    pay_job(chat_id, "casino", amt)

    # =========================
    # 💥 BANKRUPT CHECK
    # =========================
    check_bankrupt(chat_id, uid)

    save()

    # =========================
    # 📩 FINAL MESSAGE
    # =========================
    bot.send_message(
        msg.chat.id,
        f"""
🪙 <b>COIN FLIP</b>

🎯 Your Choice: {choice.upper()}
🎲 Result: {result.upper()}

{outcome}
""",
        parse_mode="HTML"
    )






@bot.message_handler(commands=['fish'])
def fish(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id)

    # 💀 dead / banned check
    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 📍 zone check
    if u["zone"] != "harbor":
        return bot.send_message(msg.chat.id, "⚓ Go to HARBOR")

    # ⏳ COOLDOWN (30 sec)
    fish_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in fish_cd[chat_id] and now - fish_cd[chat_id][uid] < 30:
        left = int(30 - (now - fish_cd[chat_id][uid]))
        return bot.send_message(msg.chat.id, f"⏳ Wait {left}s before fishing again")

    fish_cd[chat_id][uid] = now

    # 🍗 hunger check
    if u["hunger"] < 10:
        return bot.send_message(msg.chat.id, "🍗 Too hungry to fish! Eat first.")

    # 🎲 fail chance
    success_rate = 0.8

    if u["hunger"] < 30:
        success_rate -= 0.2  # weaker if hungry

    if random.random() > success_rate:
        u["hunger"] = max(0, u["hunger"] - 5)
        save()
        return bot.send_message(msg.chat.id, "❌ You failed to catch anything")

    # 💰 reward
    reward = random.randint(300, 1200)

# 💸 30% tax
    tax = int(reward * 0.3)
    final_reward = reward - tax

# 💰 user gets after tax
    u["money"] += final_reward

    # 🍗 hunger cost applies on success too (message already says -5)
    u["hunger"] = max(0, u["hunger"] - 5)

# 💼 give tax to harbor job owner (or system)
    pay_job(chat_id, "harbor", tax)

    save()

    bot.send_message(
        msg.chat.id,
        f"🐟 You caught fish!\n"
        f"💰 Earned: {final_reward}\n"
        f"💸 Tax: -{tax} (30%)\n"
        f"🍗 Hunger: -5"
    )







def build_top_page(chat_id, page=0):

    per_page = 10

    sorted_users = sorted(
        users[chat_id].items(),
        key=lambda x: x[1]["money"] + x[1].get("bank",0),
        reverse=True
    )

    total_pages = max(1, (len(sorted_users)+per_page-1)//per_page)

    start = page * per_page
    end = start + per_page

    text = f"🏆 TOP PLAYERS\nPage {page+1}/{total_pages}\n\n"

    for i, (uid, data) in enumerate(sorted_users[start:end], start+1):
        total = data["money"] + data.get("bank",0)

        text += f"{i}. {data['name']} → {total}\n"

    kb = InlineKeyboardMarkup()

    kb.row(
        InlineKeyboardButton("⬅️ Previous", callback_data=f"top_{page-1}"),
        InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="ignore"),
        InlineKeyboardButton("➡️ Next", callback_data=f"top_{page+1}")
    )

    return text, kb


@bot.message_handler(commands=['top'])
def top_cmd(msg):

    chat_id = ensure_chat(msg.chat.id)

    text, kb = build_top_page(chat_id, 0)

    bot.send_message(
        msg.chat.id,
        text,
        reply_markup=kb
    )


@bot.message_handler(commands=['upgrade'])
def upgrade(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    u = get_user(msg.from_user, msg.chat.id)

    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /upgrade strength")

    stat = parts[1].lower()

    if stat not in u["stats"]:
        return bot.send_message(msg.chat.id, "Invalid stat")

    cost = (u["stats"][stat] + 1) * 500

    if u["money"] < cost:
        return bot.send_message(msg.chat.id, f"Need {cost}")

    u["money"] -= cost
    u["stats"][stat] += 1

    save()

    bot.send_message(msg.chat.id, f"📈 {stat} upgraded to {u['stats'][stat]}")


# store pending duels
@bot.message_handler(commands=['duel'])
def duel(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    if check_dead_block(msg, uid):
        return

    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to a user")

    if msg.reply_to_message.from_user.is_bot:
        return bot.send_message(msg.chat.id, "🤖 Can't duel bots")

    target = str(msg.reply_to_message.from_user.id)

    if uid == target:
        return bot.send_message(msg.chat.id, "❌ You can't duel yourself")

    # ⏳ cooldown
    duel_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in duel_cd[chat_id] and now - duel_cd[chat_id][uid] < 60:
        left = int(60 - (now - duel_cd[chat_id][uid]))
        return bot.send_message(msg.chat.id, f"⏳ Wait {left}s before dueling again")

    u1 = get_user(msg.from_user, msg.chat.id)
    u2 = get_user(msg.reply_to_message.from_user, msg.chat.id)

    if is_dead(chat_id, target):
        return bot.send_message(msg.chat.id, "💀 Target is dead")

    if u1.get("gang") and u1["gang"] == u2.get("gang"):
        return bot.send_message(msg.chat.id, "👥 Can't duel gang member")

    duel_cd[chat_id][uid] = now

    text = f"""
⚔️ <b>DUEL REQUEST</b>

👤 <b>{u1['name']}</b>
STR: {u1['stats']['strength']} | MUS: {u1['stats']['muscles']}
STA: {u1['stats']['stamina']} | PWR: {u1['stats']['power']}

<b>VS</b>

👤 <b>{u2['name']}</b>
STR: {u2['stats']['strength']} | MUS: {u2['stats']['muscles']}
STA: {u2['stats']['stamina']} | PWR: {u2['stats']['power']}
"""

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("⚔️ Fight", callback_data=f"fight_{uid}_{target}")
    )

    bot.send_message(msg.chat.id, text, reply_markup=kb, parse_mode="HTML")

@bot.message_handler(commands=['stat'])
def duel_stats(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    u = get_user(msg.from_user, msg.chat.id)

    import html
    name = html.escape(u['name'])

    # 🔥 ensure duel exists
    u.setdefault("duel", {"wins":0,"losses":0,"total":0})

    d = u["duel"]
    s = u["stats"]

    wins = d["wins"]
    losses = d["losses"]
    total = d["total"]

    # 🧠 fix total (use stored value, not wins+losses)
    total = total if total > 0 else wins + losses

    winrate = round((wins / total) * 100, 2) if total > 0 else 0

    # 🏆 duel rank
    duel_rank = get_duel_rank(wins)

    text = f"""
📊 <b>PLAYER STATS</b>

👤 <b>{name}</b>

<blockquote>
⚔️ Duel Stats
• Rank: {duel_rank}
• Total: {total}
• Wins: {wins}
• Losses: {losses}
• Win Rate: {winrate}%
</blockquote>

<blockquote>
💪 Power Stats
• Strength: {s['strength']}
• Muscles: {s['muscles']}
• Power: {s['power']}
• Stamina: {s['stamina']}
• EXP: {s['experience']}
</blockquote>

<blockquote>
🍗 Hunger: {u.get('hunger',100)}/100
💰 Money: {u['money']}
🏦 Bank: {u.get('bank',0)}
</blockquote>
"""

    bot.send_message(msg.chat.id, text, parse_mode="HTML")



@bot.message_handler(commands=['mine'])
def mine(msg):

    parts = msg.text.split()

    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /mine amount")

    try:
        amt = int(parts[1])
    except:
        return

    uid = str(msg.from_user.id)

    u = get_user(msg.from_user, msg.chat.id)

    if u["money"] < amt:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    kb = InlineKeyboardMarkup(row_width=4)

    mults = [1,2,3,5,10,20,30,50]

    for m in mults:
        kb.add(
            InlineKeyboardButton(
                f"{m}x",
                callback_data=f"minebet_{uid}_{amt}_{m}"
            )
        )

    bot.send_message(
        msg.chat.id,
        "💣 Select Mine Multiplier",
        reply_markup=kb
    )




@bot.message_handler(commands=['arena'])
def arena(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id)

    # 💀 dead check
    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 🗺️ zone check
    if u["zone"] != "arena":
        return bot.send_message(msg.chat.id, "⚔️ Go to ARENA")

    stats = u["stats"]

    # 🧠 power calculation
    power = (
        stats["strength"] +
        stats["muscles"] +
        stats["power"]
    )

    # 🎯 base chance (balanced)
    win_chance = 0.5 + (power / 100)

    # 🍗 hunger penalty
    if u["hunger"] < 30:
        win_chance -= 0.1

    # 🛡 armor bonus
    if u.get("armor"):
        win_chance += 0.05

    # 🔫 weapon bonus
    if u.get("weapon"):
        win_chance += 0.05

    # clamp
    win_chance = max(0.2, min(win_chance, 0.85))

    reward = random.randint(2000, 5000)

    if random.random() < win_chance:
        u["money"] += reward
        stats["experience"] += 5

        msg_txt = f"""
🏆 ARENA WIN

💰 +{reward}
📊 XP +5
🎯 Chance: {round(win_chance, 2)}
"""
    else:
        loss = int(reward * 0.4)
        u["money"] -= loss
        stats["experience"] += 2

        msg_txt = f"""
💀 ARENA LOSS

💸 -{loss}
📊 XP +2
🎯 Chance: {round(win_chance, 2)}
"""

    # 🍗 hunger drain
    u["hunger"] = max(0, u["hunger"] - 3)

    # 💥 bankruptcy check
    check_bankrupt(chat_id, uid)

    save()
    bot.send_message(msg.chat.id, msg_txt)

# ===== TOP =====
# NOTE: /top (paginated, top_cmd) keeps the command. Plain list moved to
# /top10 to avoid double-reply (both handlers fired on /top before).
@bot.message_handler(commands=['top10'])
def top_simple(msg):
    chat_id = ensure_chat(msg.chat.id) 

    # 🔥 get users of THIS chat only
    chat_users = users.get(chat_id, {})

    if not chat_users:
        return bot.send_message(msg.chat.id, "No players yet")

    # 💰 sort by wallet + bank
    s = sorted(
        chat_users.values(),
        key=lambda x: x.get("money", 0) + x.get("bank", 0),
        reverse=True
    )

    txt = "🏆 TOP PLAYERS\n\n"

    for i, u in enumerate(s[:10], 1):
        total = u.get("money", 0) + u.get("bank", 0)
        txt += f"{i}. {u['name']} - 💰 {total} (💵 {u['money']} | 🏦 {u['bank']})\n"

    bot.send_message(msg.chat.id, txt)

# ===== FLASK =====
if __name__ == "__main__":
    # Strict TOKEN check (import uses placeholder, runtime must be real)
    _real_token = os.environ.get("TOKEN")
    if not _real_token:
        print("❌ ERROR: TOKEN env not set. Export TOKEN='123:ABC' and restart.")
        raise SystemExit(1)
    # Load persisted state (was missing -> data ignored on restart)
    load()
    print("🤖 Bot started...")

    # optional: make sure no webhook is set
    try:
        bot.remove_webhook()
    except:
        pass

    while True:
        try:
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=60,
                skip_pending=True
            )
        except Exception as e:
            print("Error:", e)
            time.sleep(5)
