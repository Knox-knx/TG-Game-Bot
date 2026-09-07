# TG Game Bot 🎮

Single-file Telegram RPG for groups — missions, PvP combat, casino,
jobs, gangs, hunger/survival, banking and admin moderation.

> Source: `TG_GAME_BOT.py` (~4412 lines, pyTelegramBotAPI/telebot)
> Full logic breakdown: [`report.txt`](./report.txt)
> Bug + login audit (historical — crashes listed there are fixed): [`error-rep.txt`](./error-rep.txt)

---

## 1. Features

- 🧠 Zone-based missions (`/mission` → `/do`, 12 zones)
- ⚔️ Combat: `/kill` (loot 1500, 10 min CD), `/rob` (100–1000, 2 min CD),
  `/duel` + inline fight, `/arena` (zone-gated), `/upgrade` stats
- 🎰 Casino (zone `casino` only, except `/mine`): `/casino`, `/bet`,
  `/color`, `/coin`, `/rps` (solo + PvP), `/slot`, `/spin`, `/mine`
- 💰 Economy: `/daily` (+3000/24h), `/deposit` (1% fee), `/withdraw`
  (inline keypad), `/give` → `/accept`/`/decline`, `/top`
- 🍗 Survival: hunger 0–100, `/food` shop + `/eat`, penalties on combat
- 🛡️ Protection: `/protect` / shop shields (5/10/15 min), armor, weapons
  + breaker weapons (shield-break)
- 💼 Jobs (10): smith, armor, protect, bank, police, military, harbor,
  casino, food, breaker — owners earn a cut via `pay_job()`
- 👥 Gangs: create/join/invite, friendly-fire block
- 🚔 Crime: `crime.caught`, jail 120 s, `/arrest` (police job, ≥5 crimes)
- 💀 Death: `/revive` 1000 + 5 min shield
- 👑 Admin: group owner claim, admins, ban/unban, bot-owner broadcasts

## 2. Requirements

- Python 3.10+
- `pyTelegramBotAPI` (`pip install pyTelegramBotAPI`)
- A bot token from [@BotFather](https://t.me/BotFather)
- Map image: `maps/map.jpg` (already in repo, shown by `/map`)

No database — state is `Game_tg.json` (auto-created).

## 3. Setup

```bash
pip install pyTelegramBotAPI
export TOKEN="123456:ABC-..."          # required
export ADMIN_IDS="111111111,222222222" # optional, bot-owner broadcasts
python TG_GAME_BOT.py
```

> Run from the folder containing `TG_GAME_BOT.py` — `Game_tg.json`
> resolves via relative path; the map is loaded from `maps/map.jpg`
> (falls back to `map/map.jpg`, then root `map.jpg`).

### Environment

| Var | Required | Purpose |
|-----|----------|---------|
| `TOKEN` | ✅ | Bot token. Startup exits with a clear error if missing. |
| `ADMIN_IDS` | ❌ | Comma IDs allowed `/broadcast`, `/broadcastpvt`. Empty = both disabled. |

## 4. Group bootstrapping (important)

1. Add bot to group, make it admin if you use `/owner` checks.
2. A Telegram group admin runs `/owner` — becomes bot-owner for that chat
   (`group_data[chat] = {owner, admins: []}`).
3. Owner runs `/setjob <job> (reply)` to assign the 10 jobs,
   `/addadmin (reply)` to add moderators.
4. Players run any command once to auto-register (3000 cash, slums).
5. Travel costs 20000 (`/travel` buttons) — use `/daily` + missions first.

Without `/owner`, `/admin /ban /unban /setjob /removejob /addadmin`
all refuse (by design).

## 5. Commands

### Missions / Map

| Cmd | CD / Cost | Notes |
|-----|-----------|-------|
| `/mission` | 120 s | Reward/risk from current zone |
| `/do` | — | Completes mission: success `+reward` + 30 XP, fail `-30%` (hunger −3) |
| `/map` | — | Shows zone + neighbors with `maps/map.jpg` photo |
| `/travel` | 20000 | Inline buttons for 12 zones |

### Combat

| Cmd | CD | Notes |
|-----|----|-------|
| `/kill (reply)` | 600 s | Loot ≤1500, jail risk, shield/armor/hunger modify odds |
| `/rob (reply)` | 120 s | Loot 100–1000, jail 120 s on fail |
| `/duel (reply)` | 60 s | Inline ⚔️ Fight, winner +1000–3000 minted |
| `/arena` | — | Zone `arena` only; win `+2000–5000` + 5 XP, loss `−40%` + 2 XP (hunger −3) |
| `/upgrade <stat>` | money | `(stat+1)*500`, no cap |
| `/revive` | 1000 | Clears dead, hunger 100, 5 min shield |
| `/arrest (reply)` | — | Police job only, target crime ≥5, fine 2000 |

### Economy

| Cmd | Notes |
|-----|-------|
| `/daily` | +3000 / 24 h per chat |
| `/deposit <amt>` | Min 100, 1% fee to bank owner |
| `/withdraw` | Keypad UI, 9-digit max |
| `/give <amt> (reply)` → `/accept` / `/decline` | 1–1M, 5 s CD, pending guards |
| `/panel` `/status` `/stat` `/top` | Profile / ranks / leaderboard |

### Shop / Food

| Cmd | Notes |
|-----|-------|
| `/shop` | Weapons / Breakers / Armor 3000 / Shields |
| `/food` + `/eat <item>` | Inventory cap 20, hunger restore |
| `/protect` | Same shields as shop |

### Casino (zone `casino` unless noted)

| Cmd | Limits | Payout |
|-----|--------|--------|
| `/casino <amt>` | ≤50k, 3 s | Win +amt / lose −amt |
| `/bet <1-10> <amt>` | ≤30k, 3 s | Hit +4x |
| `/color <r/b/g> <amt>` | ≤50k, 3 s | r/b 2x, g 5x |
| `/coin <h/t> <amt>` | ≤50k, 60 s | Win +amt |
| `/rps <amt>` | ≤100k, 60 s | Solo vs bot 2x; PvP pot 2x (both pick, timeout refunds) |
| `/slot <amt>` | ≤100k, 60 s | Triple 5x, pair 2x |
| `/spin <amt>` | ≤100k, 60 s | Random −250…+1000 (bet sunk) |
| `/mine <amt>` | no CD/zone | Pick 1–50x, open tiles, cash out |
| `/fish` | harbor, 30 s | 300–1200 minus 30% tax |

### Gangs / Jobs / Admin

```
/creategang <name> /joingang <name> /ganginvite (reply) /acceptgang
/myjob /joblist /alljob
/setjob <job> (reply, admin) /removejob <job> (admin)
/owner /addadmin (reply, owner) /removeadmin (reply, owner) /mygroups
/admin /ban (reply) /unban (reply)
/broadcast <msg> (bot-owner) /broadcastpvt <msg> (bot-owner)
```

## 6. Game data

- **Zones (12):** slums, city, bank, military, harbor, casino, arena,
  food, market, police, mountain, garden — each has risk + reward range.
- **Weapons:** knife 800 → rpg 20000. **Breakers:** Katana 10k →
  breaker 70k. **Armor:** 3000. **Foods:** bread 100 → feast 1300.
- **Ranks:** money Middle → Emperor; duels Bronze → Fighter.
- **New player:** money 3000, bank 0, level 1, slums, hunger 100,
  stats 5/5/5/5, duel 0/0/0.

## 7. Architecture

```
Telegram → handlers → ensure_chat/get_user → logic → save() → Game_tg.json
                    ↘ check_dead_block (ban/dead gate)
                    ↘ pay_job (mint cut to job owner)
                    ↘ inline callbacks (shop/travel/games)
```

- Per-chat namespacing: `users[chat][uid]`, etc. — groups never share money.
- RAM-first, JSON snapshot on every mutation. Cooldowns mostly RAM-only.
- `pay_job()` **mints** (does not transfer) — job owners print money.
- Polling only (`infinity_polling`, auto-retry 5 s).

## 8. Known issues

> The crashes once listed here (`/do`, `/rob`, `/arena`, `/map`,
> RPS-PvP, `/mine` cash-out, missing `load()`, `TOKEN` guard, duplicate
> `/top`, breaker-weapon `KeyError`) are **fixed and covered by 48
> automated checks**. `error-rep.txt` is kept as the historical audit.
> Remaining design notes (not crashes): `pay_job()` mints owner cuts,
> `/spin` has negative expected value by design, `/mine` has no cooldown,
> most cooldowns are RAM-only.

## 9. Project layout

```
TG-Files/
├── TG_GAME_BOT.py   # everything
├── Game_tg.json     # auto-created state (15 keys, git-ignored)
├── maps/map.jpg     # /map image (tracked)
├── report.txt       # full logic report
├── error-rep.txt    # historical bug + login audit
└── README.md        # this file
```

## 10. Quick dev checks

```bash
python3 -m py_compile TG_GAME_BOT.py
python3 /tmp/opencode/test_bot.py   # 48 checks: every def block + links
```
