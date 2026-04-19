import random
import time
from timetable_utils import *


# =========================
# 🔥 NEW: MDM SLOT SYNC FUNCTION
# =========================
def get_mdm_fixed_slots(existing_timetables):

    fixed_slots = set()

    for doc in existing_timetables:
        tt = doc.get("timetable", {})

        for d in range(DAYS):
            day = f"day{d}"

            if day not in tt:
                continue

            for s in range(SLOTS):
                slot_key = f"slot{s}"

                if slot_key not in tt[day]:
                    continue

                cell = tt[day][slot_key]

                for key in cell:
                    entry = cell[key]

                    if not entry:
                        continue

                    subject = entry.get("subject", "")

                    if subject and subject.strip().lower() == "mdm":
                        slot_val = entry.get("slot")

                        if isinstance(slot_val, list):
                            for sl in slot_val:
                                fixed_slots.add(sl)
                        else:
                            fixed_slots.add(slot_val)

    return fixed_slots


# =========================
# 🔥 NEW: FORCE MDM PLACEMENT
# =========================
def force_place_mdm(tt, subjects, mdm_slots):

    if not mdm_slots:
        return

    for slot_code in mdm_slots:

        day_map = {"M":0,"T":1,"W":2,"TH":3,"F":4,"S":5}

        if slot_code.startswith("TH"):
            d = 3
            s = int(slot_code[2:]) - 1
        else:
            d = day_map.get(slot_code[0], 0)
            s = int(slot_code[1:]) - 1

        tt[d][s]["COMMON"] = None
        for k in tt[d][s]:
            if k != "COMMON":
                tt[d][s][k] = None

        teacher, teacherId = get_teacher("MDM", subjects)

        tt[d][s]["COMMON"] = {
            "subject": "MDM",
            "teacher": teacher,
            "teacherId": teacherId,
            "type": "theory",
            "room": "CLASS",
            "slot": slot_code
        }


# =========================
# BATCH LABS (FIXED EDGE BUG)
# =========================
def place_batch_labs(tt, batch_labs, batches, subjects, teacher_busy=None, room_busy=None):
    
    teacher_busy = teacher_busy or {}
    room_busy = room_busy or {}

    subjects_names = [s["subject_name"] for s in batch_labs]
    random.shuffle(subjects_names)
    n = len(subjects_names)

    # 🔥 CREATE SESSIONS
    sessions = []
    for s in batch_labs:
        for _ in range(s["hours"] // 2):
            sessions.append(s["subject_name"])

    # 🔥 GUARANTEE DISTRIBUTION (NO LOSS)
    day_slots = {d: [] for d in range(DAYS)}

    days = list(range(5))  # Mon–Fri
    random.shuffle(days)

    # ensure each session gets a different day first
    for i, session in enumerate(sessions):
        d = days[i % len(days)]
        day_slots[d].append(session)

    # shuffle within day
    for d in day_slots:
        random.shuffle(day_slots[d])

    rotation = random.randint(0, n-1) if n > 0 else 0

    days_order = [0,1,2,3,4]
    random.shuffle(days_order)

    for d in days_order:
        lab_count = 0

        for _ in day_slots[d]:

            # 🔥 ONLY ONE LAB PER DAY
            if lab_count >= 1:
                break

            slot_options = [0, 2, 4]
            random.shuffle(slot_options)

            for s in slot_options:

                if s + 1 >= SLOTS:
                    continue

                if not is_slot_empty(tt, d, s) or not is_slot_empty(tt, d, s+1):
                    continue

                if tt[d][s]["COMMON"] or tt[d][s+1]["COMMON"]:
                    continue

                valid = True

                # 🔥 SMART CONSTRAINT
                for b in range(batches):
                    sub = subjects_names[(b + rotation) % n]
                    _, teacherId = get_teacher(sub, subjects)
                    room = get_lab(sub, subjects)

                    teacher_conflict = False
                    room_conflict = False

                    for slot in [get_slot_code(d, s), get_slot_code(d, s+1)]:
                        if teacherId in teacher_busy and slot in teacher_busy[teacherId]:
                            teacher_conflict = True
                        if room in room_busy and slot in room_busy[room]:
                            room_conflict = True

                    if teacher_conflict and room_conflict:
                        valid = False
                        break

                if not valid:
                    continue

                # 🔥 PLACE LAB
                for b in range(batches):
                    sub = subjects_names[(b + rotation) % n]
                    teacher, teacherId = get_teacher(sub, subjects)
                    room = get_lab(sub, subjects)

                    entry = {
                        "subject": sub,
                        "teacher": teacher,
                        "teacherId": teacherId,
                        "type": "lab",
                        "room": room,
                        "slot": [get_slot_code(d, s), get_slot_code(d, s+1)]
                    }

                    tt[d][s][f"B{b+1}"] = entry
                    tt[d][s+1][f"B{b+1}"] = entry

                rotation += 1
                lab_count += 1
                break

# =========================
# COMMON LABS (UNCHANGED)
# =========================
def place_common_labs(tt, common_labs, subjects, teacher_busy=None, room_busy=None):
    
    teacher_busy = teacher_busy or {}
    room_busy = room_busy or {}

    # 🔥 helper
    def is_same_subject_block(tt, d, s, subject):
        for i in [s, s+1]:
            if 0 <= i < SLOTS:
                if isinstance(tt[d][i]["COMMON"], dict):
                    if tt[d][i]["COMMON"].get("subject") == subject:
                        return True
        return False

    labs_per_day = [0] * DAYS

    # count existing labs
    for d in range(DAYS):
        for s in range(SLOTS):

            if (
                isinstance(tt[d][s]["COMMON"], dict) and
                tt[d][s]["COMMON"].get("type") == "lab"
            ):
                labs_per_day[d] += 1

            for k in tt[d][s]:
                if k != "COMMON" and tt[d][s][k] and tt[d][s][k]["type"] == "lab":
                    labs_per_day[d] += 1
                    break

        labs_per_day[d] //= 2

    days_order = [0,1,2,3,4]
    random.shuffle(days_order)

    for sub in common_labs:

        sessions = sub["hours"] // 2

        for _ in range(sessions):

            placed = False

            for d in days_order:

                if labs_per_day[d] >= 2:
                    continue

                for s in [0, 2, 4]:

                    if s >= SLOTS - 1:
                        continue

                    if not (is_slot_empty(tt, d, s) and is_slot_empty(tt, d, s+1)):
                        continue

                    # 🔥 BLOCK-LEVEL CHECK
                    if s - 2 >= 0:
                        if is_same_subject_block(tt, d, s-2, sub["subject_name"]):
                            continue

                    if s + 2 < SLOTS:
                        if is_same_subject_block(tt, d, s+2, sub["subject_name"]):
                            continue

                    teacher, teacherId = get_teacher(sub["subject_name"], subjects)
                    room = get_lab(sub["subject_name"], subjects)

                    slot1 = get_slot_code(d, s)
                    slot2 = get_slot_code(d, s+1)

                    if (
                        slot1 in teacher_busy.get(teacherId, set()) or
                        slot2 in teacher_busy.get(teacherId, set())
                    ):
                        continue

                    if (
                        slot1 in room_busy.get(room, set()) or
                        slot2 in room_busy.get(room, set())
                    ):
                        continue

                    entry = {
                        "subject": sub["subject_name"],
                        "teacher": teacher,
                        "teacherId": teacherId,
                        "type": "lab",
                        "room": room,
                        "slot": [slot1, slot2]
                    }

                    tt[d][s]["COMMON"] = entry
                    tt[d][s+1]["COMMON"] = entry

                    labs_per_day[d] += 1
                    placed = True
                    break

                if placed:
                    break
# =========================
# THEORY (UNCHANGED)
# =========================
def place_theory(tt, theory, subjects, teacher_busy=None, room_busy=None, mdm_slots=None):

    pool = []
    for s in theory:
        pool.extend([s["subject_name"]] * s["hours"])

    random.shuffle(pool)

    idx = 0

    for d in range(DAYS):
        used = set()

        for s in range(SLOTS):

            if not is_slot_empty(tt, d, s):
                continue

            for _ in range(len(pool)):
                sub = pool[idx % len(pool)]
                idx += 1

                if sub not in used:

                    if sub.strip().lower() == "mdm" and mdm_slots:
                        if get_slot_code(d, s) not in mdm_slots:
                            continue

                    teacher, teacherId = get_teacher(sub, subjects)

                    tt[d][s]["COMMON"] = {
                        "subject": sub,
                        "teacher": teacher,
                        "teacherId": teacherId,
                        "type": "theory",
                        "room": "CLASS",
                        "slot": get_slot_code(d, s)
                    }

                    used.add(sub)
                    break
def reserve_mdm_slots(tt, mdm_slots):
    if not mdm_slots:
        return

    day_map = {"M":0,"T":1,"W":2,"TH":3,"F":4,"S":5}

    for slot_code in mdm_slots:

        if slot_code.startswith("TH"):
            d = 3
            s = int(slot_code[2:]) - 1
        else:
            d = day_map.get(slot_code[0], 0)
            s = int(slot_code[1:]) - 1

        # 🔥 BLOCK SLOT (DO NOT PLACE ANYTHING HERE)
        tt[d][s]["COMMON"] = {
    "type": "blocked"
}

def place_mdm_final(tt, subjects, mdm_slots):
    
    if not mdm_slots:
        return

    day_map = {"M":0,"T":1,"W":2,"TH":3,"F":4,"S":5}

    teacher, teacherId = get_teacher("MDM", subjects)

    for slot_code in mdm_slots:

        if slot_code.startswith("TH"):
            d = 3
            s = int(slot_code[2:]) - 1
        else:
            d = day_map.get(slot_code[0], 0)
            s = int(slot_code[1:]) - 1

        tt[d][s]["COMMON"] = {
            "subject": "MDM",
            "teacher": teacher,
            "teacherId": teacherId,
            "type": "theory",
            "room": "CLASS",
            "slot": slot_code
        }

# =========================
# MAIN
# =========================
def generate_timetable(subjects, existing_timetables=None):

    random.seed(time.time())

    subjects = normalize(subjects)
    random.shuffle(subjects)

    teacher_busy, room_busy = build_constraints(existing_timetables or [])

    mdm_slots = get_mdm_fixed_slots(existing_timetables or [])

    batch_labs = []
    common_labs = []
    theory = []

    for s in subjects:
        if is_batch_lab(s):
            batch_labs.append(s)
        elif is_common_lab(s):
            common_labs.append(s)
        elif is_theory(s):
            theory.append(s)

    batches = get_batches(subjects)

    tt = empty_tt(batches)
    reserve_mdm_slots(tt, mdm_slots)

    place_batch_labs(tt, batch_labs, batches, subjects, teacher_busy, room_busy)
    place_common_labs(tt, common_labs, subjects, teacher_busy, room_busy)
    place_theory(tt, theory, subjects, teacher_busy, room_busy, mdm_slots)

    place_mdm_final(tt, subjects, mdm_slots)

    

    return tt