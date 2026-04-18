import random
import time
from timetable_utils import *


# =========================
# BATCH LABS
# =========================
def place_batch_labs(tt, batch_labs, batches, subjects, teacher_busy=None, room_busy=None):

    teacher_busy = teacher_busy or {}
    room_busy = room_busy or {}

    subjects_names = [s["subject_name"] for s in batch_labs]
    random.shuffle(subjects_names)
    n = len(subjects_names)

    sessions = []
    for s in batch_labs:
        for _ in range(s["hours"] // 2):
            sessions.append(s["subject_name"])

    day_slots = {d: [] for d in range(DAYS)}

    d = 0
    for i in range(len(sessions)):
        day_slots[d].append(i)
        d = (d + 1) % DAYS

    for d in day_slots:
        random.shuffle(day_slots[d])

    rotation = random.randint(0, n-1) if n > 0 else 0

    # 🔥 FIX: shuffle only Mon–Fri
    days_order = [0,1,2,3,4]
    random.shuffle(days_order)

    for d in days_order:
        lab_count = 0

        for _ in day_slots[d]:

            if lab_count >= 2:
                break

            # 🔥 slot shuffle
            slot_options = [0, 2, 4]
            random.shuffle(slot_options)

            for s in slot_options:

                if s >= SLOTS - 1:
                    continue

                if not (is_slot_empty(tt, d, s) and is_slot_empty(tt, d, s+1)):
                    continue

                valid = True

                for b in range(batches):
                    sub = subjects_names[(b + rotation) % n]
                    _, teacherId = get_teacher(sub, subjects)
                    room = get_lab(sub, subjects)

                    for slot in [get_slot_code(d, s), get_slot_code(d, s+1)]:
                        if teacherId in teacher_busy and slot in teacher_busy[teacherId]:
                            valid = False
                        if room in room_busy and slot in room_busy[room]:
                            valid = False

                if not valid:
                    continue

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
# COMMON LABS
# =========================
def place_common_labs(tt, common_labs, subjects, teacher_busy=None, room_busy=None):
    
    teacher_busy = teacher_busy or {}
    room_busy = room_busy or {}

    labs_per_day = [0] * DAYS

    # count existing labs
    for d in range(DAYS):
        for s in range(SLOTS):

            if tt[d][s]["COMMON"] and tt[d][s]["COMMON"]["type"] == "lab":
                labs_per_day[d] += 1

            for k in tt[d][s]:
                if k != "COMMON" and tt[d][s][k] and tt[d][s][k]["type"] == "lab":
                    labs_per_day[d] += 1
                    break

        labs_per_day[d] = labs_per_day[d] // 2

    # 🔥 FIX: shuffle Mon–Fri only
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

            # fallback (unchanged)
            if not placed:
                for d in range(DAYS):
                    for s in range(SLOTS - 1):

                        if is_slot_empty(tt, d, s) and is_slot_empty(tt, d, s+1):

                            teacher, teacherId = get_teacher(sub["subject_name"], subjects)
                            room = get_lab(sub["subject_name"], subjects)

                            entry = {
                                "subject": sub["subject_name"],
                                "teacher": teacher,
                                "teacherId": teacherId,
                                "type": "lab",
                                "room": room,
                                "slot": [
                                    get_slot_code(d, s),
                                    get_slot_code(d, s+1)
                                ]
                            }

                            tt[d][s]["COMMON"] = entry
                            tt[d][s+1]["COMMON"] = entry
                            break
                    else:
                        continue
                    break


# =========================
# THEORY (UNCHANGED)
# =========================
def place_theory(tt, theory, subjects, teacher_busy=None, room_busy=None):

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


# =========================
# MAIN
# =========================
def generate_timetable(subjects, existing_timetables=None):

    random.seed(time.time())

    subjects = normalize(subjects)
    random.shuffle(subjects)

    teacher_busy, room_busy = build_constraints(existing_timetables or [])

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

    place_batch_labs(tt, batch_labs, batches, subjects, teacher_busy, room_busy)
    place_common_labs(tt, common_labs, subjects, teacher_busy, room_busy)
    place_theory(tt, theory, subjects, teacher_busy, room_busy)

    return tt